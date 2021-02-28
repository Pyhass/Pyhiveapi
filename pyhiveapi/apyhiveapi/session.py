"""Hive Session Module."""
import asyncio
import copy
import json
import operator
import os
import time
from datetime import datetime, timedelta

from aiohttp.web import HTTPException

if __name__ == "pyhiveapi.session":
    from ..api.hive_api import HiveApi  # noqa: F401
    from ..api.hive_auth import HiveAuth  # noqa: F401
else:
    from ..api.hive_async_api import HiveApiAsync
    from ..api.hive_auth_async import HiveAuthAsync

from .device_attributes import Attributes
from .helper.const import HIVE_TYPES
from .helper.hive_exceptions import (HiveApiError, HiveReauthRequired,
                                     HiveUnknownConfiguration)
from .helper.hive_helper import HiveHelper
from .helper.logger import Logger
from .helper.map import Map


class Session:
    """Hive Session Code."""

    sessionType = "Session"

    def __init__(self, username=None, password=None, websession=None):
        """Initialise the base variable values."""
        self.auth = None
        if __name__ == "pyhiveapi.session":
            self.api = HiveApi()
            if None not in (username, password):
                self.auth = HiveAuth(username=username, password=password)
        else:
            self.api = HiveApiAsync(websession=websession)
            if None not in (username, password):
                self.auth = HiveAuthAsync(username=username, password=password)

        self.helper = HiveHelper()
        self.attr = Attributes(self)
        self.log = Logger()
        self.updateLock = asyncio.Lock()
        self.tokens = Map(
            {
                "tokenCreated": datetime.now() - timedelta(seconds=4000),
                "tokenExpiry": timedelta(seconds=1800),
            }
        )
        self.update = Map(
            {
                "lastUpdated": datetime.now(),
                "intervalSeconds": timedelta(seconds=120),
            }
        )
        self.config = Map(
            {
                "Mode": [],
                "BATTERY": [],
                "sensors": False,
                "file": False,
                "errorList": {},
            }
        )
        self.data = Map(
            {"products": {}, "devices": {}, "actions": {}, "user": {}, "minMax": {}}
        )
        self.devices = {}
        self.ha_devices = {}

    def openFile(self, file):
        """Open a file."""
        path = os.path.dirname(os.path.realpath(__file__)) + "/helper/" + file
        with open(path) as j:
            data = json.loads(j.read())

        return data

    def add_list(self, type, data, **kwargs):
        """Add entity to the list."""
        add = False if kwargs.get("custom") and not self.config.sensors else True
        device = self.helper.getDeviceData(data)
        device_name = (
            device["state"]["name"]
            if device["state"]["name"] != "Receiver"
            else "Heating"
        )
        formatted_data = {}

        if add:
            try:
                formatted_data = {
                    "hiveID": data.get("id", ""),
                    "hiveName": device_name,
                    "hiveType": data.get("type", ""),
                    "haType": type,
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
            except KeyError as e:
                self.logger.error(e)

            self.devices[type].append(formatted_data)
        return add

    def updateInterval(self, new_interval):
        """Update the scan interval."""
        interval = timedelta(seconds=new_interval)
        if interval < timedelta(seconds=15):
            interval = timedelta(seconds=15)
        self.update.intervalSeconds = interval

    def useFile(self, username=None):
        """Update to check if file is being used."""
        using_file = True if username == "use@file.com" else False
        if using_file:
            self.config.file = True

    def updateTokens(self, tokens):
        """Update session tokens."""
        if "AccessToken" in tokens:
            self.tokens.update(
                {
                    "token": tokens["tokens"]["IdToken"],
                    "refreshToken": tokens["tokens"]["RefreshToken"],
                    "accessToken": tokens["tokens"]["AccessToken"],
                }
            )

        return self.tokens

    def login(self):
        """Login to hive account."""
        if not self.auth:
            raise HiveUnknownConfiguration

        result = self.auth.login()
        self.updateTokens(result)
        return result

    def sms_2fa(self, code, session):
        """Complete 2FA auth."""
        result = self.auth.sms_2fa(code, session)
        self.updateTokens(result)
        return result

    def hiveRefreshTokens(self):
        """Refresh Hive tokens."""
        updated = False

        if self.config.file:
            return None
        else:
            expiry_time = self.tokens.tokenCreated + self.tokens.tokenExpiry
            if datetime.now() >= expiry_time:
                updated = self.api.refreshTokens()

        return updated

    def updateData(self, device):
        """Get latest data for Hive nodes - rate limiting."""
        self.updateLock.acquire()
        updated = False
        try:
            ep = self.update.lastUpdate + self.update.intervalSeconds
            if datetime.now() >= ep:
                self.getDevices(device["hiveID"])
                updated = True
        finally:
            self.updateLock.release()

        return updated

    def getDevices(self, n_id):
        """Get latest data for Hive nodes."""
        get_nodes_successful = False
        api_resp_d = None

        try:
            asyncio.sleep(1)
            if self.config.file:
                api_resp_d = self.openFile("data.json")
            elif self.tokens is not None:
                self.hiveRefreshTokens()
                api_resp_d = self.api.getAll()
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
                if hiveType == "products":
                    for aProduct in api_resp_p[hiveType]:
                        tmpProducts.update({aProduct["id"]: aProduct})
                if hiveType == "devices":
                    for aDevice in api_resp_p[hiveType]:
                        tmpDevices.update({aDevice["id"]: aDevice})
                if hiveType == "actions":
                    for aAction in api_resp_p[hiveType]:
                        tmpActions.update({aAction["id"]: aAction})

            if len(tmpProducts) > 0:
                self.data.products = copy.deepcopy(tmpProducts)
            if len(tmpDevices) > 0:
                self.data.devices = copy.deepcopy(tmpDevices)
            self.data.actions = copy.deepcopy(tmpActions)
            self.update.lastUpdate = datetime.now()
            get_nodes_successful = True
        except (OSError, RuntimeError, HiveApiError, ConnectionError, HTTPException):
            get_nodes_successful = False

        return get_nodes_successful

    def startSession(self, config=None):
        """Setup the Hive platform."""
        self.config.sensors = config.get("add_sensors", False)
        self.updateInterval(config["options"]["scan_interval"])
        self.useFile(config.get("username", False))

        if config["tokens"] is not None and not self.config["file"]:
            self.updateTokens(config["tokens"])
        elif self.config.file:
            self.logger.log(
                "No_ID",
                self.sessionType,
                "Loading up a hive session with a preloaded file.",
            )
        else:
            raise HiveUnknownConfiguration

        try:
            self.getDevices("No_ID")
        except HTTPException:
            return HTTPException

        if self.data.devices == {} or self.data.products == {}:
            raise HiveReauthRequired

        return self.createDevices()

    def createDevices(self):
        """Create list of devices."""
        self.devices["binary_sensor"] = []
        self.devices["climate"] = []
        self.devices["light"] = []
        self.devices["sensor"] = []
        self.devices["switch"] = []
        self.devices["water_heater"] = []

        for aProduct in self.data.products:
            p = self.data.products[aProduct]
            if p.get("isGroup", False):
                continue

            if self.data.products[aProduct]["type"] == "sense":
                self.add_list(
                    "binary_sensor",
                    p,
                    haName="Glass Detection",
                    hiveType="GLASS_BREAK",
                )
                self.add_list(
                    "binary_sensor",
                    p,
                    haName="Smoke Detection",
                    hiveType="SMOKE_CO",
                )
                self.add_list(
                    "binary_sensor",
                    p,
                    haName="Dog Bark Detection",
                    hiveType="DOG_BARK",
                )

            if self.data.products[aProduct]["type"] in HIVE_TYPES["Heating"]:

                self.config["MODE"].append(p["id"])
                self.add_list(
                    "climate",
                    p,
                    temperatureunit=self.data["user"]["temperatureUnit"],
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" Current Temperature",
                    hiveType="CurrentTemperature",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" Target Temperature",
                    hiveType="TargetTemperature",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" State",
                    hiveType="Heating_State",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" Mode",
                    hiveType="Heating_Mode",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" Boost",
                    hiveType="Heating_Boost",
                    custom=True,
                )

            if self.data.products[aProduct]["type"] in HIVE_TYPES["Hotwater"]:
                self.add_list("water_heater", p)
                self.add_list(
                    "sensor",
                    p,
                    haName="Hotwater State",
                    hiveType="Hotwater_State",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName="Hotwater Mode",
                    hiveType="Hotwater_Mode",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName="Hotwater Boost",
                    hiveType="Hotwater_Boost",
                    custom=True,
                )

            if self.data.products[aProduct]["type"] in HIVE_TYPES["Switch"]:
                self.config["MODE"].append(p["id"])
                self.add_list("switch", p)
                self.add_list(
                    "sensor",
                    p,
                    haName=" Mode",
                    hiveType="Mode",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" Availability",
                    hiveType="Availability",
                    custom=True,
                )

            if self.data.products[aProduct]["type"] in HIVE_TYPES["Light"]:
                self.config["MODE"].append(p["id"])
                self.add_list("light", p)
                self.add_list(
                    "sensor",
                    p,
                    haName=" Mode",
                    hiveType="Mode",
                    custom=True,
                )
                self.add_list(
                    "sensor",
                    p,
                    haName=" Availability",
                    hiveType="Availability",
                    custom=True,
                )

            if self.data.products[aProduct]["type"] in HIVE_TYPES["Sensor"]:
                self.add_list("binary_sensor", p)

        for aDevice in self.data["devices"]:
            d = self.data["devices"][aDevice]
            if (
                self.data["devices"][aDevice]["type"] in HIVE_TYPES["Thermo"]
                or self.data["devices"][aDevice]["type"] in HIVE_TYPES["Sensor"]
            ):
                self.config["BATTERY"].append(d["id"])
                self.add_list(
                    "sensor",
                    d,
                    haName=" Battery Level",
                    hiveType="Battery",
                )
                self.add_list(
                    "sensor",
                    d,
                    haName=" Availability",
                    hiveType="Availability",
                    custom=True,
                )

            if self.data["devices"][aDevice]["type"] in HIVE_TYPES["Hub"]:
                self.add_list(
                    "binary_sensor",
                    d,
                    haName="Hive Hub Status",
                    hiveType="Connectivity",
                )

        if "action" in HIVE_TYPES["Switch"]:
            for action in self.data["actions"]:
                a = self.data["actions"][action]
                self.add_list(
                    "switch",
                    a,
                    hiveName=a["name"],
                    haName=a["name"],
                    hiveType="action",
                )

        self.logger.log("No_ID", self.sessionType, "Hive component has initialised")

        return self.devices

    @staticmethod
    def epochtime(date_time, pattern, action):
        """date/time conversion to epoch."""
        if action == "to_epoch":
            pattern = "%d.%m.%Y %H:%M:%S"
            epochtime = int(time.mktime(time.strptime(str(date_time), pattern)))
            return epochtime
        elif action == "from_epoch":
            date = datetime.fromtimestamp(int(date_time)).strftime(pattern)
            return date
