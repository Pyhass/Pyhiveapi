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
from typing import Optional

from aiohttp.web import HTTPException

from apyhiveapi import API, Auth

from .device_attributes import HiveAttributes
from .helper.const import DEVICES, HIVE_TYPES, PRODUCTS
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
from .helper.hivedataclasses import Device
from .helper.logger import Logger
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
                "token_data": {},
                "token_created": datetime.min,
                "token_expiry": timedelta(seconds=3600),
            }
        )
        self.config = Map(
            {
                "alarm": False,
                "battery": [],
                "camera": False,
                "errorList": {},
                "file": False,
                "home_id": None,
                "last_update": datetime.now(),
                "mode": [],
                "scan_interval": timedelta(seconds=120),
                "user_id": None,
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
        self.devices = {}
        self.deviceList = {}
        self.hub_id = None
        self._lastPollSlow = False
        self._slowPollThreshold = 3
        self._refresh_threshold = 0.90

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

    def addList(self, entity_type: str, data: dict, **kwargs: dict) -> Optional[Device]:
        """Add entity to the list.

        Args:
            entityType (str): Type of entity
            data (dict): Information to create entity.
            **kwargs: Additional device attributes (ha_name, category, etc.)

        Returns:
            Optional[Device]: Device dataclass instance, or None on error.
        """
        try:
            device = self.helper.getDeviceData(data)
            device_name = (
                device["state"]["name"]
                if device["state"]["name"] != "Receiver"
                else "Heating"
            )

            # Handle ha_name logic
            ha_name = kwargs.get("ha_name", device_name)
            if ha_name and ha_name[0] == " ":
                ha_name = device_name + ha_name

            # Create Device instance
            device_obj = Device(
                hive_id=data.get("id", ""),
                hive_name=device_name,
                hive_type=data.get("type", ""),
                ha_type=entity_type,
                device_id=device["id"],
                device_name=device_name,
                device_data=device.get("props", data.get("props", {})),
                parent_device=self.hub_id,
                is_group=data.get("isGroup", False),
                ha_name=ha_name,
                category=kwargs.get("category"),
                temperature_unit=kwargs.get("temperatureunit"),
            )

            if data.get("type", "") == "hub":
                self.deviceList["parent_device"].append(device_obj)
                self.deviceList[entity_type].append(device_obj)
            else:
                self.deviceList[entity_type].append(device_obj)

            return device_obj
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
        self.config.scan_interval = interval

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
        if "AuthenticationResult" in tokens:
            data = tokens.get("AuthenticationResult")
            self.tokens.token_data.update({"token": data["IdToken"]})
            if "RefreshToken" in data:
                self.tokens.token_data.update({"refreshToken": data["RefreshToken"]})
            self.tokens.token_data.update({"accessToken": data["AccessToken"]})
            if update_expiry_time:
                self.tokens.token_created = datetime.now()
        elif "token" in tokens:
            data = tokens
            self.tokens.token_data.update({"token": data["token"]})
            self.tokens.token_data.update({"refreshToken": data["refreshToken"]})
            self.tokens.token_data.update({"accessToken": data["accessToken"]})

        if "ExpiresIn" in data:
            self.tokens.token_expiry = timedelta(seconds=data["ExpiresIn"])

        _LOGGER.debug(
            "updateTokens — IdToken: len=%d tail=…%s | "
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

        _LOGGER.debug("Attempting login to Hive account.")
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
            _LOGGER.debug("Login successful — AuthenticationResult keys: %s", auth_keys)
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

        _LOGGER.debug("Submitting 2FA code.")
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
                "2FA login successful — AuthenticationResult keys: %s", auth_keys
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

        _LOGGER.debug("Attempting device login.")
        try:
            result = await self.auth.device_login()
        except HiveInvalidDeviceAuthentication:
            _LOGGER.error("Device login failed: invalid device credentials.")
            raise

        if result and "AuthenticationResult" in result:
            auth_keys = list(result["AuthenticationResult"].keys())
            _LOGGER.debug(
                "Device login successful — AuthenticationResult keys: %s", auth_keys
            )
            await self.updateTokens(result)
        return result

    async def _retryDeviceLogin(self):
        """Attempt device login with retries and backoff.

        Raises:
            HiveReauthRequired: All retry attempts have been exhausted.
        """
        last_err = None
        for delay_s in (0, 5, 10):
            try:
                if delay_s:
                    _LOGGER.debug("Retrying device login in %s seconds.", delay_s)
                    await asyncio.sleep(delay_s)
                await self.deviceLogin()
                last_err = None
                break
            except HiveInvalidDeviceAuthentication as err:
                _LOGGER.error(
                    "Device login failed with invalid credentials, reauthentication required."
                )
                raise HiveReauthRequired from err
            except HiveApiError as err:
                _LOGGER.error("Device login attempt failed: %s", err)
                last_err = err
        if last_err is not None:
            _LOGGER.error(
                "All device login retries exhausted, reauthentication required."
            )
            raise HiveReauthRequired from last_err

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
            expiry_time = self.tokens.token_created + (
                self.tokens.token_expiry * self._refresh_threshold
            )
            # Refresh at 90% of token lifetime to prevent expiration during API calls
            _LOGGER.debug(
                "Session token expiry time ( Current: %s | Expiry: %s)",
                datetime.now(),
                expiry_time,
            )
            if datetime.now() >= expiry_time or force_refresh:
                async with self._refreshLock:
                    # Re-check after acquiring lock — another caller may have already refreshed
                    expiry_time = self.tokens.token_created + (
                        self.tokens.token_expiry * self._refresh_threshold
                    )
                    if datetime.now() < expiry_time and not force_refresh:
                        return result
                    actual_expiry = self.tokens.token_created + self.tokens.token_expiry
                    _LOGGER.debug(
                        "Session Token created: %s | Actual expiry: %s | "
                        "Early refresh (×%s): %s | Now: %s | Force refresh: %s",
                        self.tokens.token_created,
                        actual_expiry,
                        self._refresh_threshold,
                        expiry_time,
                        datetime.now(),
                        force_refresh,
                    )
                    try:
                        result = await self.auth.refresh_token(
                            self.tokens.token_data["refreshToken"]
                        )

                        if result and "AuthenticationResult" in result:
                            auth_keys = list(result["AuthenticationResult"].keys())
                            _LOGGER.debug(
                                "Token refresh — AuthenticationResult keys: %s",
                                auth_keys,
                            )
                            await self.updateTokens(result)
                            new_expiry = (
                                self.tokens.token_created + self.tokens.token_expiry
                            )
                            _LOGGER.debug(
                                "Session Token refresh successful. New expiry: %s",
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
        ep = self.config.last_update + self.config.scan_interval
        if datetime.now() >= ep:
            async with self.updateLock:
                # Re-check after acquiring lock — another caller may have already updated
                ep = self.config.last_update + self.config.scan_interval
                if datetime.now() < ep:
                    return updated
                _LOGGER.debug("Polling Hive API for device updates.")
                updated = await self.getDevices(device["hiveID"])
                if updated and len(self.deviceList["camera"]) > 0:
                    for camera in self.data.camera:
                        await self.getCamera(self.devices[camera])
                if updated:
                    _LOGGER.debug("Device update completed successfully.")
                else:
                    _LOGGER.debug(
                        "Device update failed, will retry after scan interval."
                    )

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
                _LOGGER.debug("Loading device data from file.")
                api_resp_d = self.openFile("data.json")
            elif self.tokens is not None:
                await self.hiveRefreshTokens()
                _LOGGER.debug("Fetching all devices from Hive API.")
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
                                    "Retrying API call in %ss after device re-login.",
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
                    _LOGGER.warning(
                        "Hive API response took %.1fs — marking poll as slow.",
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
                    self.config.user_id = api_resp_p[hiveType]["id"]
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
                    self.config.home_id = api_resp_p[hiveType]["homes"][0]["id"]

            _LOGGER.debug(
                "API returned %d products, %d devices, %d actions.",
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
            self.config.last_updated = datetime.now()
            get_nodes_successful = True
        except HiveReauthRequired:
            _LOGGER.error("Reauthentication required, propagating to caller.")
            self.config.last_update = datetime.now()
            raise
        except asyncio.TimeoutError:
            _LOGGER.warning("Hive API request timed out — keeping cached device data.")
            self._lastPollSlow = True
            self.config.last_update = (
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
            self.config.last_update = (
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
        _LOGGER.debug("Starting Hive session.")
        await self.useFile(config.get("username", self.config.username))
        await self.updateInterval(
            config.get("options", {}).get("scan_interval", self.config.scan_interval)
        )

        if config != {}:
            if "tokens" in config and not self.config.file:
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
        self.deviceList["parent_device"] = []
        self.deviceList["alarm_control_panel"] = []
        self.deviceList["binary_sensor"] = []
        self.deviceList["camera"] = []
        self.deviceList["climate"] = []
        self.deviceList["light"] = []
        self.deviceList["sensor"] = []
        self.deviceList["switch"] = []
        self.deviceList["water_heater"] = []

        hive_type = HIVE_TYPES["Thermo"] + HIVE_TYPES["Sensor"]
        for device_id, device_data in self.data["devices"].items():
            if device_data["type"] == "hub":
                self.hub_id = device_id
                break

        for device_id, device_data in self.data["devices"].items():
            entity_configs = DEVICES.get(device_data["type"], [])

            for config in entity_configs:
                kwargs = self.helper._build_kwargs(config)
                self.addList(config.entity_type, device_data, **kwargs)

            if device_data["type"] in hive_type:
                self.config.battery.append(device_data["id"])

        hive_type = HIVE_TYPES["Heating"] + HIVE_TYPES["Switch"] + HIVE_TYPES["Light"]
        for product_id, product_data in self.data.products.items():
            if "error" in product_data:
                continue

            # Skip non-heating groups
            if (
                product_data.get("isGroup", False)
                and product_data["type"] not in HIVE_TYPES["Heating"]
            ):
                continue

            entity_configs = PRODUCTS.get(product_data["type"], [])

            for config in entity_configs:
                kwargs = self.helper._build_kwargs(config)

                try:
                    self.addList(config.entity_type, product_data, **kwargs)
                except (NameError, AttributeError) as e:
                    product_name = product_data["state"].get("name", "Unknown")
                    _LOGGER.warning(f"Device {product_name} cannot be setup - {e}")

            if product_data["type"] in hive_type:
                self.config.mode.append(product_data["id"])

        _LOGGER.debug(
            "Device discovery found: %d parent, %d binary_sensor, %d climate, %d light, %d sensor, %d switch, %d water_heater",
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
