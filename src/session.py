"""Hive Session Module."""

# pylint: disable=C0103,R0914,R0915,W0613,W0212,W0706,W0707,W1514,C0301,C0209,R1719,R1705,R1720,R1710

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
)
from .helper.hive_helper import HiveHelper
from .helper.hivedataclasses import Device
from .helper.map import Map

_SCAN_INTERVAL = timedelta(seconds=120)

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
        self.update_lock = asyncio.Lock()
        self._refresh_lock = asyncio.Lock()
        self.tokens = Map(
            {
                "token_data": {},
                "token_created": datetime.min,
                "token_expiry": timedelta(seconds=3600),
            }
        )
        self.config = Map(
            {
                "battery": [],
                "error_list": {},
                "file": False,
                "home_id": None,
                "last_update": datetime.now(),
                "mode": [],
                "scan_interval": _SCAN_INTERVAL,
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
            }
        )
        self.entity_cache = {}
        self.device_list = {}
        self.hub_id = None
        self._last_poll_slow = False
        self._slow_poll_threshold = 3
        self._refresh_threshold = 0.90
        self._update_task = None

    @staticmethod
    def _entity_cache_key(device) -> str:
        """Build a stable cache key for an entity instance."""
        return "|".join(
            [
                str(getattr(device, "ha_type", "")),
                str(getattr(device, "hive_id", "")),
                str(getattr(device, "hive_type", "")),
            ]
        )

    def get_cached_device(self, device):
        """Get cached state for a specific entity."""
        cache_key = self._entity_cache_key(device)
        return self.entity_cache.get(cache_key)

    def set_cached_device(self, device, dev_data: dict):
        """Store cached state for a specific entity."""
        self.entity_cache[self._entity_cache_key(device)] = dev_data
        return dev_data

    def should_use_cached_data(self):
        """Determine whether callers should use cached entity state.

        Returns:
            bool: True when the last poll was slow or another task is currently polling.
        """
        if self._last_poll_slow:
            return True
        if self.update_lock.locked():
            current_task = asyncio.current_task()
            return self._update_task is None or current_task is not self._update_task
        return False

    async def _pollDevices(self) -> bool:
        """Fetch latest device state from the Hive API."""
        return await self.getDevices("No_ID")

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

    def addList(self, entity_type: str, data: dict, **kwargs) -> Device:
        """Add entity to the device list.

        Args:
            entity_type (str): HA entity type (e.g. "climate", "sensor").
            data (dict): Raw product or device data from the Hive API.

        Returns:
            Device: Created device entity, or None on error.
        """
        try:
            device_data = self.helper.getDeviceData(data)
            device_name = (
                device_data["state"]["name"]
                if device_data["state"]["name"] != "Receiver"
                else "Heating"
            )

            ha_name = kwargs.get("ha_name", "")
            if ha_name.startswith(" "):
                ha_name = device_name + ha_name
            elif not ha_name:
                ha_name = device_name

            device_obj = Device(
                hive_id=data.get("id", ""),
                hive_name=device_name,
                hive_type=kwargs.get("hive_type", data.get("type", "")),
                ha_type=entity_type,
                device_id=device_data["id"],
                device_name=device_name,
                device_data=device_data.get("props", data.get("props", {})),
                parent_device=self.hub_id,
                is_group=data.get("isGroup", False),
                ha_name=ha_name,
                category=kwargs.get("category"),
                temperature_unit=kwargs.get("temperature_unit"),
            )

            if data.get("type", "") == "hub":
                self.device_list["parent_device"].append(device_obj)
                self.device_list[entity_type].append(device_obj)
            else:
                self.device_list[entity_type].append(device_obj)

            return device_obj
        except KeyError as error:
            _LOGGER.error(error)
            return None

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
            "updateTokens — Final session tokens: IdToken: len=%d tail=…%s | "
            "AccessToken: len=%d tail=…%s | "
            "RefreshToken: %s | "
            "ExpiresIn: %s | token_created: %s | token_expiry: %s",
            len(self.tokens.token_data.get("token", "")),
            self.tokens.token_data.get("token", "")[-4:],
            len(self.tokens.token_data.get("accessToken", "")),
            self.tokens.token_data.get("accessToken", "")[-4:],
            (
                "present (len=%d tail=…%s)"
                % (
                    len(self.tokens.token_data.get("refreshToken", "")),
                    self.tokens.token_data.get("refreshToken", "")[-4:],
                )
                if self.tokens.token_data.get("refreshToken")
                else "not present"
            ),
            data.get("ExpiresIn", "N/A"),
            self.tokens.token_created,
            self.tokens.token_expiry,
        )

        return self.tokens

    async def login(self):
        """Login to hive account with business logic routing.

        Business Rules:
        1) Login successfully - tokens returned, no device login or SMS2FA needed
        2) Check for device login or SMS challenges
        3) Direct flow to one of the two
        4) If device login, process ends but check if device is registered
        5) If SMS, follow on with device registration

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

        # Rule 1: Login successful - tokens returned, no challenges needed
        if result and "AuthenticationResult" in result:
            auth_keys = list(result["AuthenticationResult"].keys())
            _LOGGER.debug(
                "login - Login successful — AuthenticationResult keys: %s", auth_keys
            )
            await self.updateTokens(result)
            return result

        # Rule 2 & 3: Check for device login or SMS challenges and route
        challenge_name = result.get("ChallengeName")
        _LOGGER.debug("login - Challenge detected: %s", challenge_name)

        if challenge_name == self.auth.DEVICE_VERIFIER_CHALLENGE:
            # Rule 4: Device login flow - check if device is registered
            _LOGGER.debug("login - Routing to device login flow")
            return await self._handleDeviceLoginChallenge(result)
        if challenge_name == self.auth.SMS_MFA_CHALLENGE:
            # Rule 5: SMS flow - will need device registration after 2FA
            _LOGGER.debug("login - Routing to SMS 2FA flow (requires user input)")
            return result
        _LOGGER.error("login - Unsupported challenge: %s", challenge_name)
        raise HiveUnknownConfiguration

    async def _handleDeviceLoginChallenge(self, login_result):
        """Handle device login challenge.

        Args:
            login_result (dict): Result from initial login with DEVICE_SRP_AUTH challenge.

        Returns:
            dict: Authentication result with tokens.

        Raises:
            HiveReauthRequired: If device login encounters SMS_MFA (device not remembered).
            HiveInvalidDeviceAuthentication: If device is not registered.
        """
        _LOGGER.debug("_handleDeviceLoginChallenge - Processing device login")

        # Check if device is registered before attempting device login
        is_registered = await self.auth.is_device_registered()
        if not is_registered:
            _LOGGER.warning(
                "_handleDeviceLoginChallenge - Device not registered, "
                "cannot complete device login. User must complete SMS 2FA."
            )
            raise HiveInvalidDeviceAuthentication

        # Device is registered, proceed with device login
        _LOGGER.debug("_handleDeviceLoginChallenge - Device is registered, proceeding")
        result = await self.auth.device_login()

        # Check if device login returned SMS_MFA challenge (device not remembered by Cognito)
        if result and result.get("ChallengeName") == self.auth.SMS_MFA_CHALLENGE:
            _LOGGER.error(
                "_handleDeviceLoginChallenge - Device login failed: SMS MFA challenge detected. "
                "Device is not remembered by Cognito. User must reauthenticate."
            )
            raise HiveReauthRequired

        if result and "AuthenticationResult" in result:
            auth_keys = list(result["AuthenticationResult"].keys())
            _LOGGER.debug(
                "_handleDeviceLoginChallenge - Device login successful — AuthenticationResult keys: %s",
                auth_keys,
            )
            await self.updateTokens(result)

        return result

    async def sms2fa(self, code, session):
        """Login to hive account with 2 factor authentication.

        After successful SMS 2FA, checks if device needs registration and
        handles it automatically (Rule 5).

        Raises:
            HiveUnknownConfiguration: Login information is unknown.

        Returns:
            dict: result of the authentication request with device data if registered.
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

    async def _retryLogin(self):
        """Attempt login with retries and backoff.

        This is called when token refresh fails. It attempts to login again,
        which may succeed via device login or may require user interaction (SMS 2FA).

        Raises:
            HiveReauthRequired: User interaction required (SMS 2FA challenge).
            HiveInvalidDeviceAuthentication: Device credentials are invalid.
            HiveApiError: API error or no internet connection.
        """
        last_err = None
        for delay_s in (0, 5, 10):
            try:
                if delay_s:
                    _LOGGER.debug(
                        "_retryLogin - Retrying login in %s seconds.", delay_s
                    )
                    await asyncio.sleep(delay_s)
                result = await self.login()

                # Check if login returned SMS_MFA challenge (requires user interaction)
                if (
                    result
                    and result.get("ChallengeName") == self.auth.SMS_MFA_CHALLENGE
                ):
                    _LOGGER.error(
                        "_retryLogin - Login requires SMS 2FA. User must reauthenticate."
                    )
                    raise HiveReauthRequired

                last_err = None
                break
            except (HiveInvalidUsername, HiveInvalidPassword):
                _LOGGER.error(
                    "_retryLogin - Login failed with invalid credentials, reauthentication required."
                )
                raise HiveReauthRequired
            except HiveReauthRequired:
                # Propagate reauthentication requirement immediately
                raise
            except HiveApiError as err:
                _LOGGER.error("_retryLogin - Login attempt failed: %s", err)
                last_err = err
        if last_err is not None:
            _LOGGER.error("_retryLogin - All login retries exhausted.")
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
                "hiveRefreshTokens - Session token expiry time ( Current: %s | Expiry: %s)",
                datetime.now(),
                expiry_time,
            )
            if datetime.now() >= expiry_time or force_refresh:
                async with self._refresh_lock:
                    # Re-check after acquiring lock — another caller may have already refreshed
                    expiry_time = self.tokens.token_created + (
                        self.tokens.token_expiry * self._refresh_threshold
                    )
                    if datetime.now() < expiry_time and not force_refresh:
                        return result
                    actual_expiry = self.tokens.token_created + self.tokens.token_expiry
                    _LOGGER.debug(
                        "hiveRefreshTokens - Session Token created: %s | Actual expiry: %s | "
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
                                "hiveRefreshTokens - Token refresh — AuthenticationResult keys: %s",
                                auth_keys,
                            )
                            await self.updateTokens(result)
                            new_expiry = (
                                self.tokens.token_created + self.tokens.token_expiry
                            )
                            _LOGGER.debug(
                                "hiveRefreshTokens - Session Token refresh successful. New expiry: %s",
                                new_expiry,
                            )
                    except (HiveRefreshTokenExpired, HiveFailedToRefreshTokens) as exc:
                        _LOGGER.warning(
                            "Session Token refresh failed (%s), falling back to login.",
                            type(exc).__name__,
                        )
                        if not force_refresh:
                            await self._retryLogin()
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
            current_task = asyncio.current_task()
            if self.update_lock.locked() and (
                self._update_task is None or current_task is not self._update_task
            ):
                _LOGGER.debug("updateData - Update poll already in progress")
                return updated
            async with self.update_lock:
                # Re-check after acquiring lock — another caller may have already updated
                ep = self.config.last_update + self.config.scan_interval
                if datetime.now() < ep:
                    return updated
                self._update_task = current_task
                try:
                    _LOGGER.debug("Polling Hive API for device updates.")
                    updated = await self._pollDevices()
                    if updated:
                        _LOGGER.debug(
                            "updateData - Device update completed successfully."
                        )
                    else:
                        _LOGGER.debug(
                            "updateData - Device update failed, will retry after scan interval."
                        )
                finally:
                    if self._update_task is current_task:
                        self._update_task = None

        return updated

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
                    await self._retryLogin()
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
                if api_call_duration > self._slow_poll_threshold:
                    _LOGGER.debug(
                        "getDevices - Hive API response took %.1fs — marking poll as slow.",
                        api_call_duration,
                    )
                    self._last_poll_slow = True
                else:
                    self._last_poll_slow = False
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
                if hiveType == "actions":
                    for aAction in api_resp_p[hiveType]:
                        tmpActions.update({aAction["id"]: aAction})
                if hiveType == "homes":
                    self.config.home_id = api_resp_p[hiveType]["homes"][0]["id"]

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
            self.config.last_update = datetime.now()
            get_nodes_successful = True
        except HiveReauthRequired:
            _LOGGER.error("Reauthentication required, propagating to caller.")
            self.config.last_update = datetime.now()
            raise
        except asyncio.TimeoutError:
            _LOGGER.warning("Hive API request timed out — keeping cached device data.")
            self._last_poll_slow = True
            self.config.last_update = (
                datetime.now() - self.config.scan_interval + timedelta(seconds=30)
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
                datetime.now() - self.config.scan_interval + timedelta(seconds=30)
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

        self.device_list["parent_device"] = []
        self.device_list["binary_sensor"] = []
        self.device_list["climate"] = []
        self.device_list["light"] = []
        self.device_list["sensor"] = []
        self.device_list["switch"] = []
        self.device_list["water_heater"] = []

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

            for config in DEVICES.get(self.data.devices[aDevice]["type"], []):
                kwargs = {}
                if config.ha_name:
                    kwargs["ha_name"] = config.ha_name
                if config.hive_type:
                    kwargs["hive_type"] = config.hive_type
                if config.category:
                    kwargs["category"] = config.category
                try:
                    self.addList(config.entity_type, d, **kwargs)
                except Exception as e:
                    _LOGGER.error(
                        "Failed to create device entity for %s: %s",
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
        _LOGGER.debug(
            "createDevices - Processing %d actions", len(self.data["actions"])
        )
        for action_id in self.data["actions"]:
            action = self.data["actions"][action_id]
            try:
                self.addList(
                    "switch", action, ha_name=action["name"], hive_type="action"
                )
            except Exception as e:
                _LOGGER.error(
                    "Failed to create action entity for %s: %s",
                    action_id,
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

            for config in PRODUCTS.get(product_type, []):
                kwargs = {}
                if config.ha_name:
                    kwargs["ha_name"] = config.ha_name
                if config.hive_type:
                    kwargs["hive_type"] = config.hive_type
                if config.category:
                    kwargs["category"] = config.category
                if config.entity_type == "climate":
                    kwargs["temperature_unit"] = self.data["user"].get(
                        "temperatureUnit"
                    )
                elif config.temperature_unit is not None:
                    kwargs["temperature_unit"] = config.temperature_unit
                try:
                    self.addList(config.entity_type, p, **kwargs)
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
            len(self.device_list.get("parent_device", [])),
            len(self.device_list.get("binary_sensor", [])),
            len(self.device_list.get("climate", [])),
            len(self.device_list.get("light", [])),
            len(self.device_list.get("sensor", [])),
            len(self.device_list.get("switch", [])),
            len(self.device_list.get("water_heater", [])),
        )

        return self.device_list

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
