"""Hive Session Module."""

import asyncio
import copy
import json
import operator
import time
from datetime import datetime, timedelta

from aiohttp.web import HTTPException
from apyhiveapi import API, Auth

from . import PATH
from .device_attributes import HiveAttributes
from .helper.const import HIVE_TYPES
from .helper.hive_exceptions import (
    HiveApiError,
    HiveFailedToRefreshTokens,
    HiveInvalid2FACode,
    HiveInvalidDeviceAuthentication,
    HiveInvalidPassword,
    HiveInvalidUsername,
    HiveReauthRequired,
    HiveUnknownConfiguration,
    NoApiToken,
)
from .helper.hive_helper import HiveHelper
from .helper.logger import Logger
from .helper.map import Map


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
        web_session: object = None,
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
        self.api = API(hiveSession=self, websession=web_session)
        self.helper = HiveHelper(self)
        self.attr = HiveAttributes(self)
        self.log = Logger(self)
        self.update_lock = asyncio.Lock()
        self.tokens = Map(
            {
                "tokenData": {},
                "tokenCreated": datetime.now() - timedelta(seconds=4000),
                "tokenExpiry": timedelta(seconds=3600),
            }
        )
        self.config = Map(
            {
                "battery": [],
                "errorList": {},
                "file": False,
                "home_id": None,
                "lastUpdated": datetime.now(),
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
        self.devices = {}
        self.device_list = {}

    def open_file(self, file: str):
        """Open a file.

        Args:
            file (str): File location

        Returns:
            dict: Data from the chosen file.
        """
        path = PATH + file
        with open(path, encoding="utf-8") as json_file:
            data = json.loads(json_file.read())

        return data

    def add_list(self, entity_type: str, data: dict, **kwargs: dict):
        """Add entity to the list.

        Args:
            type (str): Type of entity
            data (dict): Information to create entity.

        Returns:
            dict: Entity.
        """
        device = self.helper.getDeviceData(data)
        device_name = (
            device["state"]["name"]
            if device["state"]["name"] != "Receiver"
            else "Heating"
        )
        formatted_data = {}

        try:
            formatted_data = {
                "hiveID": data.get("id", ""),
                "hiveName": device_name,
                "hiveType": data.get("type", ""),
                "haType": entity_type,
                "deviceData": device.get("props", data.get("props", {})),
                "parentDevice": data.get("parent", None),
                "isGroup": data.get("isGroup", False),
                "device_id": device["id"],
                "device_name": device_name,
            }

            if kwargs.get("haName", "FALSE")[0] == " ":
                kwargs["haName"] = device_name + kwargs["haName"]
            else:
                formatted_data["haName"] = device_name
            formatted_data.update(kwargs)
        except KeyError as error:
            self.log.error(error)

        self.device_list[entity_type].append(formatted_data)
        return formatted_data

    async def update_interval(self, new_interval: timedelta):
        """Update the scan interval.

        Args:
            new_interval (int): New interval for polling.
        """
        if isinstance(new_interval, int):
            new_interval = timedelta(seconds=new_interval)
            if new_interval < timedelta(seconds=15):
                new_interval = timedelta(seconds=15)
            self.config.scanInterval = new_interval

    async def use_file(self, username: str = None):
        """Update to check if file is being used.

        Args:
            username (str, optional): Looks for use@file.com. Defaults to None.
        """
        using_file = bool(username == "use@file.com")
        if using_file:
            self.config.file = True

    async def update_tokens(self, tokens: dict, update_expiry_time: bool = True):
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

        try:
            result = await self.auth.login()
        except HiveInvalidUsername:
            print("invalid_username")
        except HiveInvalidPassword:
            print("invalid_password")
        except HiveApiError:
            print("no_internet_available")

        if "AuthenticationResult" in result:
            await self.update_tokens(result)
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
            raise HiveUnknownConfiguration

        try:
            result = await self.auth.sms_2fa(code, session)
        except HiveInvalid2FACode:
            print("invalid_code")
        except HiveApiError:
            print("no_internet_available")

        if "AuthenticationResult" in result:
            await self.update_tokens(result)
        return result

    async def device_login(self):
        """Login to hive account using device authentication.

        Raises:
            HiveUnknownConfiguration: Login information is unknown.
            HiveInvalidDeviceAuthentication: Device information is unknown.

        Returns:
            dict: result of the authentication request.
        """
        result = None
        if not self.auth:
            raise HiveUnknownConfiguration

        try:
            result = await self.auth.device_login()
        except HiveInvalidDeviceAuthentication as exc:
            raise HiveInvalidDeviceAuthentication from exc

        if "AuthenticationResult" in result:
            await self.update_tokens(result)
            self.tokens.tokenExpiry = timedelta(seconds=0)
        return result

    async def hive_refresh_tokens(self):
        """Refresh Hive tokens.

        Returns:
            boolean: True/False if update was successful
        """
        result = None

        if self.config.file:
            return None

        expiry_time = self.tokens.tokenCreated + self.tokens.tokenExpiry
        if datetime.now() >= expiry_time:
            result = await self.auth.refresh_token(
                self.tokens.tokenData["refreshToken"]
            )

            if "AuthenticationResult" in result:
                await self.update_tokens(result)
            else:
                raise HiveFailedToRefreshTokens

        return result

    async def update_data(self):
        """Get latest data for Hive nodes - rate limiting.

        Returns:
            boolean: True/False if update was successful
        """
        updated = False
        expiry_time = self.config.lastUpdate + self.config.scanInterval
        if datetime.now() >= expiry_time and not self.update_lock.locked():
            try:
                await self.update_lock.acquire()
                await self.get_devices()
                if len(self.device_list["camera"]) > 0:
                    for camera in self.data.camera:
                        await self.get_camera(self.devices[camera])
                updated = True
            finally:
                self.update_lock.release()

        return updated

    async def get_alarm(self):
        """Get alarm data.

        Raises:
            HTTPException: HTTP error has occurred updating the devices.
            HiveApiError: An API error code has been returned.
        """
        if self.config.file:
            api_resp_d = self.open_file("alarm.json")
        elif self.tokens is not None:
            api_resp_d = await self.api.getAlarm()
            if operator.contains(str(api_resp_d["original"]), "20") is False:
                raise HTTPException
            if api_resp_d["parsed"] is None:
                raise HiveApiError

        self.data.alarm = api_resp_d["parsed"]

    async def get_camera(self, device):
        """Get camera data.

        Raises:
            HTTPException: HTTP error has occurred updating the devices.
            HiveApiError: An API error code has been returned.
        """
        camera_image = None
        camera_recording = None
        if self.config.file:
            camera_image = self.open_file("cameraImage.json")
            camera_recording = self.open_file("cameraRecording.json")
        elif self.tokens is not None:
            camera_image = await self.api.getCameraImage(device)
            if camera_image["parsed"]["events"][0]["hasRecording"] is True:
                camera_recording = await self.api.getCameraRecording(
                    device, camera_image["parsed"]["events"][0]["eventId"]
                )

            if operator.contains(str(camera_image["original"]), "20") is False:
                raise HTTPException
            if camera_image["parsed"] is None:
                raise HiveApiError
        else:
            raise NoApiToken

        self.data.camera[device["id"]] = {}
        self.data.camera[device["id"]]["cameraImage"] = None
        self.data.camera[device["id"]]["cameraRecording"] = None

        if camera_image is not None:
            self.data.camera[device["id"]] = {}
            self.data.camera[device["id"]]["cameraImage"] = camera_image["parsed"][
                "events"
            ][0]
        if camera_recording is not None:
            self.data.camera[device["id"]]["cameraRecording"] = camera_recording[
                "parsed"
            ]

    async def get_devices(self):
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
                api_resp_d = self.open_file("data.json")
            elif self.tokens is not None:
                await self.hive_refresh_tokens()
                api_resp_d = await self.api.getAll()
                if operator.contains(str(api_resp_d["original"]), "20") is False:
                    raise HTTPException
                if api_resp_d["parsed"] is None:
                    raise HiveApiError

            api_resp_p = api_resp_d["parsed"]
            tmp_products = {}
            tmp_devices = {}
            tmp_actions = {}

            for hive_type in api_resp_p:
                if hive_type == "user":
                    self.data.user = api_resp_p[hive_type]
                    self.config.userID = api_resp_p[hive_type]["id"]
                if hive_type == "products":
                    for product in api_resp_p[hive_type]:
                        tmp_products.update({product["id"]: product})
                if hive_type == "devices":
                    for device in api_resp_p[hive_type]:
                        tmp_devices.update({device["id"]: device})
                        if device["type"] == "siren":
                            await self.get_alarm()
                        if device["type"] == "hivecamera":
                            await self.get_camera(device)
                if hive_type == "actions":
                    for action in api_resp_p[hive_type]:
                        tmp_actions.update({action["id"]: action})
                if hive_type == "homes":
                    self.config.home_id = api_resp_p[hive_type]["homes"][0]["id"]

            if len(tmp_products) > 0:
                self.data.products = copy.deepcopy(tmp_products)
            if len(tmp_devices) > 0:
                self.data.devices = copy.deepcopy(tmp_devices)
            self.data.actions = copy.deepcopy(tmp_actions)
            self.config.lastUpdate = datetime.now()
            get_nodes_successful = True
        except (OSError, RuntimeError, HiveApiError, ConnectionError, HTTPException):
            get_nodes_successful = False

        return get_nodes_successful

    async def start_session(self, config: dict):
        """Setup the Hive platform.

        Args:
            config (dict, optional): Configuration for Home Assistant to use. Defaults to {}.

        Raises:
            HiveUnknownConfiguration: Unknown configuration identifed.
            HiveReauthRequired: Tokens have expired and reauthentication is required.

        Returns:
            list: List of devices
        """
        await self.use_file(config.get("username", self.config.username))
        await self.update_interval(
            config.get("options", {}).get("scan_interval", self.config.scanInterval)
        )

        if config != {}:
            if "tokens" in config and not self.config.file:
                await self.update_tokens(config["tokens"], False)

            if "device_data" in config and not self.config.file:
                self.auth.device_group_key = config["device_data"][0]
                self.auth.device_key = config["device_data"][1]
                self.auth.device_password = config["device_data"][2]

            if not self.config.file and "tokens" not in config:
                raise HiveUnknownConfiguration

        try:
            await self.get_devices()
        except HTTPException:
            return HTTPException

        if self.data.devices == {} or self.data.products == {}:
            raise HiveReauthRequired

        return await self.create_devices()

    async def create_devices(self):
        """Create list of devices.

        Returns:
            list: List of devices
        """
        self.device_list["alarm_control_panel"] = []
        self.device_list["binary_sensor"] = []
        self.device_list["camera"] = []
        self.device_list["climate"] = []
        self.device_list["light"] = []
        self.device_list["sensor"] = []
        self.device_list["switch"] = []
        self.device_list["water_heater"] = []

        hive_type = HIVE_TYPES["Heating"] + HIVE_TYPES["Switch"] + HIVE_TYPES["Light"]
        for product in self.data.products:
            current_product = self.data.products[product]
            if current_product.get("isGroup", False):
                continue
            await self.helper.call_products_to_add(
                self.data.products[product]["type"], current_product
            )

            if self.data.products[product]["type"] in hive_type:
                self.config.mode.append(current_product["id"])

        hive_type = HIVE_TYPES["Thermo"] + HIVE_TYPES["Sensor"]
        for device in self.data["devices"]:
            current_device = self.data.devices[device]
            await self.helper.call_devices_to_add(
                self.data.devices[device]["type"], current_device
            )

            if self.data["devices"][device]["type"] in hive_type:
                self.config.battery.append(current_device["id"])

        if "action" in HIVE_TYPES["Switch"]:
            for action in self.data["actions"]:
                current_action = self.data["actions"][action]
                await self.helper.call_action_to_add(current_action)

        return self.device_list

    @staticmethod
    def epoch_time(date_time: any, pattern: str, action: str):
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
            epoch_time = int(time.mktime(time.strptime(str(date_time), pattern)))
            return epoch_time
        if action == "from_epoch":
            date = datetime.fromtimestamp(int(date_time)).strftime(pattern)
            return date
        return None
