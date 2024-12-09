"""Hive Session Module."""
# pylint: skip-file
import asyncio
import copy
import json
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


class hive_session:
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
        self.api = API(hive_session=self, websession=websession)
        self.helper = HiveHelper(self)
        self.attr = HiveAttributes(self)
        self.log = Logger(self)
        self.update_lock = asyncio.Lock()
        self.tokens = Map(
            {
                "token_data": {},
                "token_created": datetime.now() - timedelta(seconds=4000),
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
                "homeID": None,
                "last_updated": datetime.now(),
                "mode": [],
                "scan_interval": timedelta(seconds=120),
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
                "min_max": {},
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
        path = os.path.dirname(os.path.realpath(__file__)) + "/data/" + file
        path = path.replace("/pyhiveapi/", "/apyhiveapi/")
        with open(path) as j:
            data = json.loads(j.read())

        return data

    def add_list(self, entityType: str, data: dict, **kwargs: dict):
        """Add entity to the list.

        Args:
            type (str): Type of entity
            data (dict): Information to create entity.

        Returns:
            dict: Entity.
        """
        device = self.helper.get_device_data(data)
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
                "haType": entityType,
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
            self.logger.error(error)

        self.device_list[entityType].append(formatted_data)
        return formatted_data

    async def update_interval(self, new_interval: timedelta):
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

    async def use_file(self, username: str = None):
        """Update to check if file is being used.

        Args:
            username (str, optional): Looks for use@file.com. Defaults to None.
        """
        using_file = True if username == "use@file.com" else False
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

    async def sms_2fa(self, code, session):
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
        except HiveInvalidDeviceAuthentication:
            raise HiveInvalidDeviceAuthentication

        if "AuthenticationResult" in result:
            await self.update_tokens(result)
            self.tokens.token_expiry = timedelta(seconds=0)
        return result

    async def hive_refresh_tokens(self):
        """Refresh Hive tokens.

        Returns:
            boolean: True/False if update was successful
        """
        result = None

        if self.config.file:
            return None
        else:
            expiry_time = self.tokens.token_created + self.tokens.token_expiry
            if datetime.now() >= expiry_time:
                result = await self.auth.refresh_token(
                    self.tokens.token_data["refreshToken"]
                )

                if "AuthenticationResult" in result:
                    await self.update_tokens(result)
                else:
                    raise HiveFailedToRefreshTokens

        return result

    async def update_data(self, device: dict):
        """Get latest data for Hive nodes - rate limiting.

        Args:
            device (dict): Device requesting the update.

        Returns:
            boolean: True/False if update was successful
        """
        updated = False
        ep = self.config.last_update + self.config.scan_interval
        if datetime.now() >= ep and not self.update_lock.locked():
            try:
                await self.update_lock.acquire()
                await self.get_devices(device["hiveID"])
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
            api_resp_d = await self.api.get_alarm()
            if operator.contains(str(api_resp_d["original"]), "20") is False:
                raise HTTPException
            elif api_resp_d["parsed"] is None:
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
        has_camera_image = False
        has_camera_recording = False

        if self.config.file:
            camera_image = self.open_file("camera.json")
            camera_recording = self.open_file("camera.json")
        elif self.tokens is not None:
            camera_image = await self.api.get_camera_image(device)
            has_camera_recording = bool(
                camera_image["parsed"]["events"][0]["hasRecording"]
            )
            if has_camera_recording:
                camera_recording = await self.api.get_camera_recording(
                    device, camera_image["parsed"]["events"][0]["eventId"]
                )

            if operator.contains(str(camera_image["original"]), "20") is False:
                raise HTTPException
            elif camera_image["parsed"] is None:
                raise HiveApiError
        else:
            raise NoApiToken

        has_camera_image = bool(camera_image["parsed"]["events"][0])

        self.data.camera[device["id"]] = {}
        self.data.camera[device["id"]]["cameraImage"] = None
        self.data.camera[device["id"]]["cameraRecording"] = None

        if camera_image is not None and has_camera_image:
            self.data.camera[device["id"]] = {}
            self.data.camera[device["id"]]["cameraImage"] = camera_image["parsed"][
                "events"
            ][0]
        if camera_recording is not None and has_camera_recording:
            self.data.camera[device["id"]]["cameraRecording"] = camera_recording[
                "parsed"
            ]

    async def get_devices(self, n_id: str):
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
                api_resp_d = await self.api.get_all()
                if operator.contains(str(api_resp_d["original"]), "20") is False:
                    raise HTTPException
                elif api_resp_d["parsed"] is None:
                    raise HiveApiError

            api_resp_p = api_resp_d["parsed"]
            temp_products = {}
            temp_devices = {}
            temp_actions = {}

            for hive_type in api_resp_p:
                if hive_type == "user":
                    self.data.user = api_resp_p[hive_type]
                    self.config.userID = api_resp_p[hive_type]["id"]
                if hive_type == "products":
                    for a_product in api_resp_p[hive_type]:
                        temp_products.update({a_product["id"]: a_product})
                if hive_type == "devices":
                    for a_device in api_resp_p[hive_type]:
                        temp_devices.update({a_device["id"]: a_device})
                        if a_device["type"] == "siren":
                            self.config.alarm = True
                        # if aDevice["type"] == "hivecamera":
                        #    await self.getCamera(aDevice)
                if hive_type == "actions":
                    for a_action in api_resp_p[hive_type]:
                        temp_actions.update({a_action["id"]: a_action})
                if hive_type == "homes":
                    self.config.homeID = api_resp_p[hive_type]["homes"][0]["id"]

            if len(temp_products) > 0:
                self.data.products = copy.deepcopy(temp_products)
            if len(temp_devices) > 0:
                self.data.devices = copy.deepcopy(temp_devices)
            self.data.actions = copy.deepcopy(temp_actions)
            if self.config.alarm:
                await self.get_alarm()
            self.config.last_update = datetime.now()
            get_nodes_successful = True
        except (OSError, RuntimeError, HiveApiError, ConnectionError, HTTPException):
            get_nodes_successful = False

        return get_nodes_successful

    async def start_session(self, config: dict = {}):
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
            config.get("options", {}).get("scan_interval", self.config.scan_interval)
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
            await self.get_devices("No_ID")
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
        for a_product in self.data.products:
            p = self.data.products[a_product]
            if "error" in p:
                continue
            # Only consider single items or heating groups
            if (
                p.get("isGroup", False)
                and self.data.products[a_product]["type"] not in HIVE_TYPES["Heating"]
            ):
                continue
            product_list = PRODUCTS.get(self.data.products[a_product]["type"], [])
            for code in product_list:
                eval("self." + code)

            if self.data.products[a_product]["type"] in hive_type:
                self.config.mode.append(p["id"])

        hive_type = HIVE_TYPES["Thermo"] + HIVE_TYPES["Sensor"]
        for a_device in self.data["devices"]:
            d = self.data.devices[a_device]
            device_list = DEVICES.get(self.data.devices[a_device]["type"], [])
            for code in device_list:
                eval("self." + code)

            if self.data["devices"][a_device]["type"] in hive_type:
                self.config.battery.append(d["id"])

        if "action" in HIVE_TYPES["Switch"]:
            for action in self.data["actions"]:
                a = self.data["actions"][action]  # noqa: F841
                eval("self." + ACTIONS)

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
        elif action == "from_epoch":
            date = datetime.fromtimestamp(int(date_time)).strftime(pattern)
            return date