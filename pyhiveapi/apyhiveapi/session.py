"""Hive Session Module."""
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
        self.log = Logger(self)
        self.updateLock = asyncio.Lock()
        self.tokens = Map(
            {
                "tokenData": {},
                "tokenCreated": datetime.now() - timedelta(seconds=4000),
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
        self.deviceList = {}

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

            self.deviceList[entityType].append(formatted_data)
        return formatted_data

    async def updateInterval(self, new_interval: timedelta):
        """Update the scan interval.

        Args:
            new_interval (int): New interval for polling.
        """
        if type(new_interval) == int:
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
            raise HiveUnknownConfiguration

        try:
            result = await self.auth.sms_2fa(code, session)
        except HiveInvalid2FACode:
            print("invalid_code")
        except HiveApiError:
            print("no_internet_available")

        if "AuthenticationResult" in result:
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
            raise HiveUnknownConfiguration

        try:
            result = await self.auth.deviceLogin()
        except HiveInvalidDeviceAuthentication:
            raise HiveInvalidDeviceAuthentication

        if "AuthenticationResult" in result:
            await self.updateTokens(result)
            self.tokens.tokenExpiry = timedelta(seconds=0)
        return result

    async def hiveRefreshTokens(self):
        """Refresh Hive tokens.

        Returns:
            boolean: True/False if update was successful
        """
        result = None

        if self.config.file:
            return None
        else:
            expiry_time = self.tokens.tokenCreated + self.tokens.tokenExpiry
            if datetime.now() >= expiry_time:
                result = await self.auth.refreshToken(
                    self.tokens.tokenData["refreshToken"]
                )

                if "AuthenticationResult" in result:
                    await self.updateTokens(result)
                else:
                    raise HiveFailedToRefreshTokens

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
        if datetime.now() >= ep and not self.updateLock.locked():
            try:
                await self.updateLock.acquire()
                await self.getDevices(device["hiveID"])
                if len(self.deviceList["camera"]) > 0:
                    for camera in self.data.camera:
                        await self.getCamera(self.devices[camera])
                updated = True
            finally:
                self.updateLock.release()

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
        if self.config.file:
            cameraImage = self.openFile("camera.json")
            cameraRecording = self.openFile("camera.json")
        elif self.tokens is not None:
            cameraImage = await self.api.getCameraImage(device)
            if cameraImage["parsed"]["events"][0]["hasRecording"] is True:
                cameraRecording = await self.api.getCameraRecording(
                    device, cameraImage["parsed"]["events"][0]["eventId"]
                )

            if operator.contains(str(cameraImage["original"]), "20") is False:
                raise HTTPException
            elif cameraImage["parsed"] is None:
                raise HiveApiError
        else:
            raise NoApiToken

        self.data.camera[device["id"]] = {}
        self.data.camera[device["id"]]["cameraImage"] = None
        self.data.camera[device["id"]]["cameraRecording"] = None

        if cameraImage is not None:
            self.data.camera[device["id"]] = {}
            self.data.camera[device["id"]]["cameraImage"] = cameraImage["parsed"][
                "events"
            ][0]
        if cameraRecording is not None:
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
                api_resp_d = self.openFile("data.json")
            elif self.tokens is not None:
                await self.hiveRefreshTokens()
                api_resp_d = await self.api.getAll()
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
                        if aDevice["type"] == "hivecamera":
                            await self.getCamera(aDevice)
                if hiveType == "actions":
                    for aAction in api_resp_p[hiveType]:
                        tmpActions.update({aAction["id"]: aAction})
                if hiveType == "homes":
                    self.config.homeID = api_resp_p[hiveType]["homes"][0]["id"]

            if len(tmpProducts) > 0:
                self.data.products = copy.deepcopy(tmpProducts)
            if len(tmpDevices) > 0:
                self.data.devices = copy.deepcopy(tmpDevices)
            self.data.actions = copy.deepcopy(tmpActions)
            if self.config.alarm:
                await self.getAlarm()
            self.config.lastUpdate = datetime.now()
            get_nodes_successful = True
        except (OSError, RuntimeError, HiveApiError, ConnectionError, HTTPException):
            get_nodes_successful = False

        return get_nodes_successful

    async def startSession(self, config: dict = {}):
        """Setup the Hive platform.

        Args:
            config (dict, optional): Configuration for Home Assistant to use. Defaults to {}.

        Raises:
            HiveUnknownConfiguration: Unknown configuration identifed.
            HiveReauthRequired: Tokens have expired and reauthentication is required.

        Returns:
            list: List of devices
        """
        await self.useFile(config.get("username", self.config.username))
        await self.updateInterval(
            config.get("options", {}).get("scan_interval", self.config.scanInterval)
        )

        if config != {}:
            if "tokens" in config and not self.config.file:
                await self.updateTokens(config["tokens"], False)

            if "device_data" in config and not self.config.file:
                self.auth.deviceGroupKey = config["device_data"][0]
                self.auth.deviceKey = config["device_data"][1]
                self.auth.devicePassword = config["device_data"][2]

            if not self.config.file and "tokens" not in config:
                raise HiveUnknownConfiguration

        try:
            await self.getDevices("No_ID")
        except HTTPException:
            return HTTPException

        if self.data.devices == {} or self.data.products == {}:
            raise HiveReauthRequired

        return await self.createDevices()

    async def createDevices(self):
        """Create list of devices.

        Returns:
            list: List of devices
        """
        self.deviceList["alarm_control_panel"] = []
        self.deviceList["binary_sensor"] = []
        self.deviceList["camera"] = []
        self.deviceList["climate"] = []
        self.deviceList["light"] = []
        self.deviceList["sensor"] = []
        self.deviceList["switch"] = []
        self.deviceList["water_heater"] = []

        hive_type = HIVE_TYPES["Heating"] + HIVE_TYPES["Switch"] + HIVE_TYPES["Light"]
        for aProduct in self.data.products:
            p = self.data.products[aProduct]
            if p.get("isGroup", False):
                continue
            product_list = PRODUCTS.get(self.data.products[aProduct]["type"], [])
            for code in product_list:
                eval("self." + code)

            if self.data.products[aProduct]["type"] in hive_type:
                self.config.mode.append(p["id"])

        hive_type = HIVE_TYPES["Thermo"] + HIVE_TYPES["Sensor"]
        for aDevice in self.data["devices"]:
            d = self.data.devices[aDevice]
            device_list = DEVICES.get(self.data.devices[aDevice]["type"], [])
            for code in device_list:
                eval("self." + code)

            if self.data["devices"][aDevice]["type"] in hive_type:
                self.config.battery.append(d["id"])

        if "action" in HIVE_TYPES["Switch"]:
            for action in self.data["actions"]:
                a = self.data["actions"][action]  # noqa: F841
                eval("self." + ACTIONS)

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
