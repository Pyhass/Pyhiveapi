"""Hive Session Module."""

# pylint: skip-file
import asyncio
import copy
import json
import logging
import operator
import os
import time
from datetime import datetime, timedelta

from aiohttp.web import HTTPException

from apyhiveapi import API, Auth

from .device_attributes import HiveAttributes
from .helper.const import ACTIONS, DEVICES, HIVE_TYPES, PRODUCTS
from .helper.hive_exceptions import (
    HiveApiError,
    HiveAuthError,
    HiveFailedToRefreshTokens,
    HiveInvalid2FACode,
    HiveInvalidDeviceAuthentication,
    HiveInvalidPassword,
    HiveInvalidUsername,
    HiveReauthRequired,
    HiveRefreshTokenExpired,
    HiveUnknownConfiguration,
    NoApiToken,
)
from .helper.hive_helper import HiveHelper
from .helper.map import Map

_LOGGER = logging.getLogger(__name__)


class HiveSession:
    """Hive Session Code.

    Raises:
        HiveUnknownConfiguration: Unknown configuration.
        HTTPException: HTTP error has occurred.
        HiveApiError: Hive has retuend an error code.
        HiveReauthRequired: Tokens have expired and reauthentiction is required.

    Returns:
        object: Session object.
    """

    sessionType = "Session"

    def __init__(
        self,
        username: str = None,
        password: str = None,
        websession: object = None,
    ):
        """Initialise the base variable values.

        Args:
            username (str, optional): Hive username. Defaults to None.
            password (str, optional): Hive Password. Defaults to None.
            websession (object, optional): Websession for api calls. Defaults to None.
        """
        self.auth = Auth(
            username=username,
            password=password,
        )
        self.api = API(hiveSession=self, websession=websession)
        self.helper = HiveHelper(self)
        self.attr = HiveAttributes(self)
        self.updateLock = asyncio.Lock()
        self._refreshLock = asyncio.Lock()
        self.tokens = Map(
            {
                "tokenData": {},
                "tokenCreated": datetime.min,
                "tokenExpiry": timedelta(seconds=3600),
            }
        )
        self.config = Map(
            {
                "alarm": False,
                "battery": [],
                "camera": False,
                "errorList": {},
                "file": False,
                "homeID": None,
                "lastUpdate": datetime.now(),
                "mode": [],
                "scanInterval": timedelta(seconds=120),
                "userID": None,
                "username": username,
            }
        )
        self.data = Map(
            {
                "products": {},
                "devices": {},
                "actions": {},
                "user": {},
                "minMax": {},
                "alarm": {},
                "camera": {},
            }
        )
        self.entityCache = {}
        self.deviceList = {}
        self.hub_id = None
        self._lastPollSlow = False
        self._slowPollThreshold = 3
        self._refreshThreshold = 0.90
        self._updateTask = None

    @staticmethod
    def _entityCacheKey(device: dict):
        """Build a stable cache key for an entity instance."""
        return "|".join(
            [
                str(device.get("haType", "")),
                str(device.get("hiveID", "")),
                str(device.get("hiveType", "")),
            ]
        )

    def getCachedDevice(self, device: dict):
        """Get cached state for a specific entity."""
        cache_key = self._entityCacheKey(device)
        return self.entityCache.get(cache_key)

    def setCachedDevice(self, device: dict, dev_data: dict):
        """Store cached state for a specific entity."""
        self.entityCache[self._entityCacheKey(device)] = dev_data
        return dev_data

    def shouldUseCachedData(self):
        """Determine whether callers should use cached entity state.

        Returns:
            bool: True when the last poll was slow or another task is currently polling.
        """
        if self._lastPollSlow:
            return True
        if self.updateLock.locked():
            current_task = asyncio.current_task()
            return self._updateTask is None or current_task is not self._updateTask
        return False

    def openFile(self, file: str):
        """Open a file.

        Args:
            file (str): File location

        Returns:
            dict: Data from the chosen file.
        """
        path = os.path.dirname(os.path.realpath(__file__)) + "/data/" + file
        path = path.replace("/pyhiveapi/", "/apyhiveapi/")
        with open(path) as j:
            data = json.loads(j.read())

        return data

    def addList(self, entityType: str, data: dict, **kwargs: dict):
        """Add entity to the list.

        Args:
            type (str): Type of entity
            data (dict): Information to create entity.

        Returns:
            dict: Entity.
        """
        try:
            device = self.helper.getDeviceData(data)
            device_name = (
                device["state"]["name"]
                if device["state"]["name"] != "Receiver"
                else "Heating"
            )
            formatted_data = {}

            formatted_data = {
                "hiveID": data.get("id", ""),
                "hiveName": device_name,
                "hiveType": data.get("type", ""),
                "haType": entityType,
                "deviceData": device.get("props", data.get("props", {})),
                "parentDevice": self.hub_id,
                "isGroup": data.get("isGroup", False),
                "device_id": device["id"],
                "device_name": device_name,
            }

            if kwargs.get("haName", "FALSE")[0] == " ":
                kwargs["haName"] = device_name + kwargs["haName"]
            else:
                formatted_data["haName"] = device_name

            formatted_data.update(kwargs)

            if data.get("type", "") == "hub":
                self.deviceList["parent"].append(formatted_data)
                self.deviceList[entityType].append(formatted_data)
            else:
                self.deviceList[entityType].append(formatted_data)

            return formatted_data
        except KeyError as error:
            _LOGGER.error(error)
            return None

    async def updateInterval(self, new_interval: timedelta):
        """Update the scan interval.

        Args:
            new_interval (int): New interval for polling.
        """
        if isinstance(new_interval, int):
            new_interval = timedelta(seconds=new_interval)

        interval = new_interval
        if interval < timedelta(seconds=15):
            interval = timedelta(seconds=15)
        self.config.scanInterval = interval

    async def useFile(self, username: str = None):
        """Update to check if file is being used.

        Args:
            username (str, optional): Looks for use@file.com. Defaults to None.
        """
        using_file = True if username == "use@file.com" else False
        if using_file:
            self.config.file = True

    async def updateTokens(self, tokens: dict, update_expiry_time: bool = True):
        """Update session tokens.

        Args:
            tokens (dict): Tokens from API response.
            refresh_interval (Boolean): Should the refresh internval be updated

        Returns:
            dict: Parsed dictionary of tokens
        """
        data = {}
        _LOGGER.debug(
            "updateTokens - Input tokens: %s", self.helper._sanitize_payload(tokens)
        )
        if "AuthenticationResult" in tokens:
            data = tokens.get("AuthenticationResult")
            self.tokens.tokenData.update({"token": data["IdToken"]})
            if "RefreshToken" in data:
                self.tokens.tokenData.update({"refreshToken": data["RefreshToken"]})
            self.tokens.tokenData.update({"accessToken": data["AccessToken"]})
            if update_expiry_time:
                self.tokens.tokenCreated = datetime.now()
        elif "token" in tokens:
            data = tokens
            self.tokens.tokenData.update({"token": data["token"]})
            self.tokens.tokenData.update({"refreshToken": data["refreshToken"]})
            self.tokens.tokenData.update({"accessToken": data["accessToken"]})

        if "ExpiresIn" in data:
            self.tokens.tokenExpiry = timedelta(seconds=data["ExpiresIn"])

        _LOGGER.debug(
            "updateTokens — Final session tokens: IdToken: len=%d tail=…%s | "
            "AccessToken: len=%d tail=…%s | "
            "RefreshToken: %s | "
            "ExpiresIn: %s | tokenCreated: %s | tokenExpiry: %s",
            len(self.tokens.tokenData.get("token", "")),
            self.tokens.tokenData.get("token", "")[-4:],
            len(self.tokens.tokenData.get("accessToken", "")),
            self.tokens.tokenData.get("accessToken", "")[-4:],
            (
                "present (len=%d tail=…%s)"
                % (
                    len(self.tokens.tokenData.get("refreshToken", "")),
                    self.tokens.tokenData.get("refreshToken", "")[-4:],
                )
                if self.tokens.tokenData.get("refreshToken")
                else "not present"
            ),
            data.get("ExpiresIn", "N/A"),
            self.tokens.tokenCreated,
            self.tokens.tokenExpiry,
        )

        return self.tokens

    async def login(self):
        """Login to hive account.

        Raises:
            HiveUnknownConfiguration: Login information is unknown.

        Returns:
            dict: result of the authentication request.
        """
        result = None
        if not self.auth:
            raise HiveUnknownConfiguration

        _LOGGER.debug("login - Attempting login to Hive account.")
        try:
            result = await self.auth.login()
        except HiveInvalidUsername:
            _LOGGER.error("Login failed: invalid username.")
            raise
        except HiveInvalidPassword:
            _LOGGER.error("Login failed: invalid password.")
            raise
        except HiveApiError:
            _LOGGER.error("Login failed: API error or no internet connection.")
            raise

        if result and "AuthenticationResult" in result:
            auth_keys = list(result["AuthenticationResult"].keys())
            _LOGGER.debug(
                "login - Login successful — AuthenticationResult keys: %s", auth_keys
            )
            await self.updateTokens(result)
        return result

    async def sms2fa(self, code, session):
        """Login to hive account with 2 factor authentication.

        Raises:
            HiveUnknownConfiguration: Login information is unknown.

        Returns:
            dict: result of the authentication request.
        """
        result = None
        if not self.auth:
            _LOGGER.error("2FA failed: authentication not initialised.")
            raise HiveUnknownConfiguration

        _LOGGER.debug("sms_2fa - Submitting 2FA code.")
        try:
            result = await self.auth.sms_2fa(code, session)
        except HiveInvalid2FACode:
            _LOGGER.error("2FA failed: invalid code entered.")
            raise
        except HiveApiError:
            _LOGGER.error("2FA failed: API error or no internet connection.")
            raise

        if result and "AuthenticationResult" in result:
            auth_keys = list(result["AuthenticationResult"].keys())
            _LOGGER.debug(
                "sms_2fa - 2FA login successful — AuthenticationResult keys: %s",
                auth_keys,
            )
            await self.updateTokens(result)
        return result

    async def deviceLogin(self):
        """Login to hive account using device authentication.

        Raises:
            HiveUnknownConfiguration: Login information is unknown.
            HiveInvalidDeviceAuthentication: Device information is unknown.

        Returns:
            dict: result of the authentication request.
        """
        result = None
        if not self.auth:
            _LOGGER.error("Device login failed: authentication not initialised.")
            raise HiveUnknownConfiguration

        _LOGGER.debug("deviceLogin - Attempting device login.")
        try:
            result = await self.auth.device_login()
        except HiveInvalidDeviceAuthentication:
            _LOGGER.error("Device login failed: invalid device credentials.")
            raise

        if result and "AuthenticationResult" in result:
            auth_keys = list(result["AuthenticationResult"].keys())
            _LOGGER.debug(
                "deviceLogin - Device login successful — AuthenticationResult keys: %s",
                auth_keys,
            )
            await self.updateTokens(result)
        return result

    async def _retryDeviceLogin(self):
        """Attempt device login with retries and backoff.

        Raises:
            HiveInvalidDeviceAuthentication: Device credentials are invalid.
            HiveApiError: API error or no internet connection.
        """
        last_err = None
        for delay_s in (0, 5, 10):
            try:
                if delay_s:
                    _LOGGER.debug(
                        "deviceLogin - Retrying device login in %s seconds.", delay_s
                    )
                    await asyncio.sleep(delay_s)
                await self.deviceLogin()
                last_err = None
                break
            except HiveInvalidDeviceAuthentication:
                _LOGGER.error(
                    "Device login failed with invalid credentials, reauthentication required."
                )
            except HiveApiError as err:
                _LOGGER.error("Device login attempt failed: %s", err)
                last_err = err
        if last_err is not None:
            _LOGGER.error(
                "All device login retries exhausted, but device login may resolve the issue."
            )
            # Don't raise HiveReauthRequired - let the caller handle the error
            # Device login itself should resolve 403 issues when successful
            return

        await self.hiveRefreshTokens(force_refresh=True)

    async def hiveRefreshTokens(self, force_refresh: bool = False):
        """Refresh Hive tokens.

        Args:
            force_refresh (bool): Whether to force a token refresh regardless of expiry.

        Returns:
            boolean: True/False if update was successful
        """
        result = None

        if self.config.file:
            return None
        else:
            expiry_time = self.tokens.tokenCreated + (
                self.tokens.tokenExpiry * self._refreshThreshold
            )
            # Refresh at 90% of token lifetime to prevent expiration during API calls
            _LOGGER.debug(
                "hiveRefreshTokens - Session token expiry time ( Current: %s | Expiry: %s)",
                datetime.now(),
                expiry_time,
            )
            if datetime.now() >= expiry_time or force_refresh:
                async with self._refreshLock:
                    # Re-check after acquiring lock — another caller may have already refreshed
                    expiry_time = self.tokens.tokenCreated + (
                        self.tokens.tokenExpiry * self._refreshThreshold
                    )
                    if datetime.now() < expiry_time and not force_refresh:
                        return result
                    actual_expiry = self.tokens.tokenCreated + self.tokens.tokenExpiry
                    _LOGGER.debug(
                        "hiveRefreshTokens - Session Token created: %s | Actual expiry: %s | "
                        "Early refresh (×%s): %s | Now: %s | Force refresh: %s",
                        self.tokens.tokenCreated,
                        actual_expiry,
                        self._refreshThreshold,
                        expiry_time,
                        datetime.now(),
                        force_refresh,
                    )
                    try:
                        result = await self.auth.refresh_token(
                            self.tokens.tokenData["refreshToken"]
                        )

                        if result and "AuthenticationResult" in result:
                            auth_keys = list(result["AuthenticationResult"].keys())
                            _LOGGER.debug(
                                "hiveRefreshTokens - Token refresh — AuthenticationResult keys: %s",
                                auth_keys,
                            )
                            await self.updateTokens(result)
                            new_expiry = (
                                self.tokens.tokenCreated + self.tokens.tokenExpiry
                            )
                            _LOGGER.debug(
                                "hiveRefreshTokens - Session Token refresh successful. New expiry: %s",
                                new_expiry,
                            )
                    except (HiveRefreshTokenExpired, HiveFailedToRefreshTokens) as exc:
                        _LOGGER.warning(
                            "Session Token refresh failed (%s), falling back to device login.",
                            type(exc).__name__,
                        )
                        if not force_refresh:
                            await self._retryDeviceLogin()
                        else:
                            _LOGGER.error(
                                "Token refresh failed during retry attempt, giving up."
                            )
                            raise HiveReauthRequired from exc
                    except HiveApiError:
                        _LOGGER.error("API error during token refresh.")
                        raise

        return result

    async def updateData(self, device: dict):
        """Get latest data for Hive nodes - rate limiting.

        Args:
            device (dict): Device requesting the update.

        Returns:
            boolean: True/False if update was successful
        """
        updated = False
        ep = self.config.lastUpdate + self.config.scanInterval
        if datetime.now() >= ep:
            current_task = asyncio.current_task()
            if self.updateLock.locked() and (
                self._updateTask is None or current_task is not self._updateTask
            ):
                _LOGGER.debug("updateData - Update poll already in progress")
                return updated
            async with self.updateLock:
                # Re-check after acquiring lock — another caller may have already updated
                ep = self.config.lastUpdate + self.config.scanInterval
                if datetime.now() < ep:
                    return updated
                self._updateTask = current_task
                try:
                    _LOGGER.debug("updateData - Polling Hive API for device updates.")
                    updated = await self.getDevices(device["hiveID"])
                    if updated and len(self.deviceList["camera"]) > 0:
                        for camera in self.data.camera:
                            camera_device = self.data.devices.get(camera)
                            if camera_device is not None:
                                await self.getCamera(camera_device)
                    if updated:
                        _LOGGER.debug(
                            "updateData - Device update completed successfully."
                        )
                    else:
                        _LOGGER.debug(
                            "updateData - Device update failed, will retry after scan interval."
                        )
                finally:
                    if self._updateTask is current_task:
                        self._updateTask = None

        return updated

    async def getAlarm(self):
        """Get alarm data.

        Raises:
            HTTPException: HTTP error has occurred updating the devices.
            HiveApiError: An API error code has been returned.
        """
        if self.config.file:
            api_resp_d = self.openFile("alarm.json")
        elif self.tokens is not None:
            api_resp_d = await self.api.getAlarm()
            if operator.contains(str(api_resp_d["original"]), "20") is False:
                raise HTTPException
            elif api_resp_d["parsed"] is None:
                raise HiveApiError

        self.data.alarm = api_resp_d["parsed"]

    async def getCamera(self, device):
        """Get camera data.

        Raises:
            HTTPException: HTTP error has occurred updating the devices.
            HiveApiError: An API error code has been returned.
        """
        cameraImage = None
        cameraRecording = None
        hasCameraImage = False
        hasCameraRecording = False

        if self.config.file:
            cameraImage = self.openFile("camera.json")
            cameraRecording = self.openFile("camera.json")
        elif self.tokens is not None:
            cameraImage = await self.api.getCameraImage(device)
            hasCameraRecording = bool(
                cameraImage["parsed"]["events"][0]["hasRecording"]
            )
            if hasCameraRecording:
                cameraRecording = await self.api.getCameraRecording(
                    device, cameraImage["parsed"]["events"][0]["eventId"]
                )

            if operator.contains(str(cameraImage["original"]), "20") is False:
                raise HTTPException
            elif cameraImage["parsed"] is None:
                raise HiveApiError
        else:
            raise NoApiToken

        hasCameraImage = bool(cameraImage["parsed"]["events"][0])

        self.data.camera[device["id"]] = {}
        self.data.camera[device["id"]]["cameraImage"] = None
        self.data.camera[device["id"]]["cameraRecording"] = None

        if cameraImage is not None and hasCameraImage:
            self.data.camera[device["id"]] = {}
            self.data.camera[device["id"]]["cameraImage"] = cameraImage["parsed"][
                "events"
            ][0]
        if cameraRecording is not None and hasCameraRecording:
            self.data.camera[device["id"]]["cameraRecording"] = cameraRecording[
                "parsed"
            ]

    async def getDevices(self, n_id: str):
        """Get latest data for Hive nodes.

        Args:
            n_id (str): ID of the device requesting data.

        Raises:
            HTTPException: HTTP error has occurred updating the devices.
            HiveApiError: An API error code has been returned.

        Returns:
            boolean: True/False if update was successful.
        """
        get_nodes_successful = False
        api_resp_d = None

        try:
            if self.config.file:
                _LOGGER.debug("getDevices - Loading device data from file.")
                api_resp_d = self.openFile("data.json")
            elif self.tokens is not None:
                _LOGGER.debug("getDevices - Refreshing tokens before fetching devices.")
                await self.hiveRefreshTokens()
                _LOGGER.debug("getDevices - Fetching all devices from Hive API.")
                api_call_start = time.monotonic()
                try:
                    api_resp_d = await self.api.getAll()
                except HiveAuthError:
                    _LOGGER.warning(
                        "Auth error (401/403) after token refresh, "
                        "falling back to full device re-login."
                    )
                    await self._retryDeviceLogin()
                    last_auth_err = None
                    for api_retry_delay in (0, 5, 10):
                        try:
                            if api_retry_delay:
                                _LOGGER.debug(
                                    "getDevices - Retrying API call in %ss after device re-login.",
                                    api_retry_delay,
                                )
                                await asyncio.sleep(api_retry_delay)
                            api_resp_d = await self.api.getAll()
                            last_auth_err = None
                            break
                        except HiveAuthError as retry_err:
                            _LOGGER.warning(
                                "API call still rejected after device re-login (attempt delay=%ss).",
                                api_retry_delay,
                            )
                            last_auth_err = retry_err
                    if last_auth_err is not None:
                        raise HiveReauthRequired from last_auth_err
                api_call_duration = time.monotonic() - api_call_start
                if api_call_duration > self._slowPollThreshold:
                    _LOGGER.debug(
                        "getDevices - Hive API response took %.1fs — marking poll as slow.",
                        api_call_duration,
                    )
                    self._lastPollSlow = True
                else:
                    self._lastPollSlow = False
                if operator.contains(str(api_resp_d["original"]), "20") is False:
                    raise HTTPException
                elif api_resp_d["parsed"] is None:
                    raise HiveApiError

            api_resp_p = api_resp_d["parsed"]
            tmpProducts = {}
            tmpDevices = {}
            tmpActions = {}

            for hiveType in api_resp_p:
                if hiveType == "user":
                    self.data.user = api_resp_p[hiveType]
                    self.config.userID = api_resp_p[hiveType]["id"]
                if hiveType == "products":
                    for aProduct in api_resp_p[hiveType]:
                        tmpProducts.update({aProduct["id"]: aProduct})
                if hiveType == "devices":
                    for aDevice in api_resp_p[hiveType]:
                        tmpDevices.update({aDevice["id"]: aDevice})
                        if aDevice["type"] == "siren":
                            self.config.alarm = True
                        # if aDevice["type"] == "hivecamera":
                        #    await self.getCamera(aDevice)
                if hiveType == "actions":
                    for aAction in api_resp_p[hiveType]:
                        tmpActions.update({aAction["id"]: aAction})
                if hiveType == "homes":
                    self.config.homeID = api_resp_p[hiveType]["homes"][0]["id"]

            _LOGGER.debug(
                "getDevices - API returned %d products, %d devices, %d actions.",
                len(tmpProducts),
                len(tmpDevices),
                len(tmpActions),
            )
            if len(tmpProducts) > 0:
                self.data.products = copy.deepcopy(tmpProducts)
            if len(tmpDevices) > 0:
                self.data.devices = copy.deepcopy(tmpDevices)
            self.data.actions = copy.deepcopy(tmpActions)
            if self.config.alarm:
                await self.getAlarm()
            self.config.lastUpdate = datetime.now()
            get_nodes_successful = True
        except HiveReauthRequired:
            _LOGGER.error("Reauthentication required, propagating to caller.")
            self.config.lastUpdate = datetime.now()
            raise
        except asyncio.TimeoutError:
            _LOGGER.warning("Hive API request timed out — keeping cached device data.")
            self._lastPollSlow = True
            self.config.lastUpdate = (
                datetime.now() - self.config.scanInterval + timedelta(seconds=30)
            )
            get_nodes_successful = False
        except (
            OSError,
            RuntimeError,
            HiveApiError,
            ConnectionError,
            HTTPException,
        ) as err:
            _LOGGER.error("Failed to fetch devices: %s", err)
            self.config.lastUpdate = (
                datetime.now() - self.config.scanInterval + timedelta(seconds=30)
            )
            get_nodes_successful = False

        return get_nodes_successful

    async def startSession(self, config: dict = None):
        """Setup the Hive platform.

        Args:
            config (dict, optional): Configuration for Home Assistant to use. Defaults to {}.

        Raises:
            HiveUnknownConfiguration: Unknown configuration identified.
            HiveReauthRequired: Tokens have expired and reauthentication is required.

        Returns:
            list: List of devices
        """
        if config is None:
            config = {}
        _LOGGER.debug("startSession - Starting Hive session.")
        _LOGGER.debug(
            "startSession - Config: %s", self.helper._sanitize_payload(config)
        )
        await self.useFile(config.get("username", self.config.username))
        await self.updateInterval(
            config.get("options", {}).get("scan_interval", self.config.scanInterval)
        )

        if config != {}:
            if "tokens" in config and not self.config.file:
                _LOGGER.debug("startSession - Updating tokens from config")
                await self.updateTokens(config["tokens"], False)

            if "username" in config and not self.config.file:
                self.auth.username = config["username"]

            if "password" in config and not self.config.file:
                self.auth.password = config["password"]

            if "device_data" in config and not self.config.file:
                self.auth.device_group_key = config["device_data"][0]
                self.auth.device_key = config["device_data"][1]
                self.auth.device_password = config["device_data"][2]

            if not self.config.file and "tokens" not in config:
                raise HiveUnknownConfiguration

        try:
            await self.getDevices("No_ID")
        except HTTPException:
            raise

        if self.data.devices == {} or self.data.products == {}:
            _LOGGER.error(
                "No devices or products returned from Hive API, reauthentication required."
            )
            raise HiveReauthRequired

        return await self.createDevices()

    async def createDevices(self):
        """Create list of devices.

        Returns:
            list: List of devices
        """
        _LOGGER.info("createDevices - Starting device discovery process")

        self.deviceList["parent"] = []
        self.deviceList["alarm_control_panel"] = []
        self.deviceList["binary_sensor"] = []
        self.deviceList["camera"] = []
        self.deviceList["climate"] = []
        self.deviceList["light"] = []
        self.deviceList["sensor"] = []
        self.deviceList["switch"] = []
        self.deviceList["water_heater"] = []

        hive_type = HIVE_TYPES["Thermo"] + HIVE_TYPES["Sensor"]

        # Find hub device first
        for aDevice in self.data["devices"]:
            if self.data["devices"][aDevice]["type"] == "hub":
                self.hub_id = aDevice
                hub_name = (
                    self.data["devices"][aDevice].get("state", {}).get("name", aDevice)
                )
                _LOGGER.debug(
                    "createDevices - Found hub device: %s (ID: %s)", hub_name, aDevice
                )
                break
        else:
            _LOGGER.warning("createDevices - No hub device found in device list")

        # Process devices
        device_count = 0
        for aDevice in self.data["devices"]:
            d = self.data.devices[aDevice]
            device_name = d.get("state", {}).get("name", aDevice)
            device_type = d.get("type", "Unknown")
            _LOGGER.debug(
                "createDevices - Processing device: %s (%s - %s)",
                device_name,
                aDevice,
                device_type,
            )

            device_list = DEVICES.get(self.data.devices[aDevice]["type"], [])
            for code in device_list:
                try:
                    eval("self." + code)
                except Exception as e:
                    _LOGGER.error(
                        "Failed to execute device code '%s' for %s: %s",
                        code,
                        device_name,
                        str(e),
                    )

            if self.data["devices"][aDevice]["type"] in hive_type:
                self.config.battery.append(d["id"])
                _LOGGER.debug(
                    "createDevices - Added device %s to battery monitoring list",
                    device_name,
                )

            device_count += 1

        # Process actions
        if "action" in HIVE_TYPES["Switch"]:
            _LOGGER.debug(
                "createDevices - Processing %d actions", len(self.data["actions"])
            )
            for action in self.data["actions"]:
                a = self.data["actions"][action]  # noqa: F841
                try:
                    eval("self." + ACTIONS)
                except Exception as e:
                    _LOGGER.error(
                        "Failed to execute action code for action %s: %s",
                        action,
                        str(e),
                    )

        # Process products
        hive_type = HIVE_TYPES["Heating"] + HIVE_TYPES["Switch"] + HIVE_TYPES["Light"]
        product_count = 0
        for aProduct in self.data.products:
            p = self.data.products[aProduct]
            if "error" in p:
                _LOGGER.warning(
                    "Skipping product %s due to error: %s", aProduct, p["error"]
                )
                continue

            product_name = p.get("state", {}).get("name", aProduct)
            product_type = p.get("type", "Unknown")
            _LOGGER.debug(
                "createDevices - Processing product: %s (%s - %s)",
                product_name,
                aProduct,
                product_type,
            )

            # Only consider single items or heating groups
            if (
                p.get("isGroup", False)
                and self.data.products[aProduct]["type"] not in HIVE_TYPES["Heating"]
            ):
                _LOGGER.debug(
                    "createDevices - Skipping group product currently not supported %s (type: %s)",
                    product_name,
                    product_type,
                )
                continue

            product_list = PRODUCTS.get(product_type, [])
            for code in product_list:
                try:
                    eval("self." + code)
                except (NameError, AttributeError) as e:
                    _LOGGER.warning(
                        "createDevices - Device %s cannot be setup - %s",
                        product_name,
                        e,
                    )

            if product_type in hive_type:
                self.config.mode.append(p["id"])
                _LOGGER.debug(
                    "createDevices - Added product %s to mode list", product_name
                )

            product_count += 1

        _LOGGER.info(
            "Device discovery completed: %d devices, %d products processed. "
            "Found: %d parent, %d binary_sensor, %d climate, %d light, %d sensor, %d switch, %d water_heater",
            device_count,
            product_count,
            len(self.deviceList.get("parent", [])),
            len(self.deviceList.get("binary_sensor", [])),
            len(self.deviceList.get("climate", [])),
            len(self.deviceList.get("light", [])),
            len(self.deviceList.get("sensor", [])),
            len(self.deviceList.get("switch", [])),
            len(self.deviceList.get("water_heater", [])),
        )

        return self.deviceList

    @staticmethod
    def epochTime(date_time: any, pattern: str, action: str):
        """date/time conversion to epoch.

        Args:
            date_time (any): epoch time or date and time to use.
            pattern (str): Pattern for converting to epoch.
            action (str): Convert from/to.

        Returns:
            any: Converted time.
        """
        if action == "to_epoch":
            pattern = "%d.%m.%Y %H:%M:%S"
            epochtime = int(time.mktime(time.strptime(str(date_time), pattern)))
            return epochtime
        elif action == "from_epoch":
            date = datetime.fromtimestamp(int(date_time)).strftime(pattern)
            return date
