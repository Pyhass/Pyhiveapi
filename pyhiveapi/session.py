""" Hive Session Module."""
import asyncio
import json
import operator
import os
import time
from datetime import datetime, timedelta

from aiohttp.web import HTTPException

from .api.hive_async_api import HiveAsync
from .device_attributes import Attributes
from .helper.hive_data import Data
from .helper.hive_exceptions import HiveApiError
from .helper.hive_helper import HiveHelper
from .helper.logger import Logger


class Session:
    """Hive Session Code"""

    sessionType = "Session"

    def __init__(self):
        """Initialise the base variable values."""
        self.updateLock = asyncio.Lock()
        self.api_lock = asyncio.Lock()
        self.api = HiveAsync()
        self.logger = Logger()
        self.helper = HiveHelper()
        self.attr = Attributes()
        self.devices = {}

    async def openFile(self, file):
        path = os.path.dirname(os.path.realpath(__file__)) + "/" + file
        with open(path, "r") as j:
            data = json.loads(j.read())

        return data

    async def add_list(self, name, data, **kwargs):
        """Add entity to the list"""
        add = True
        if kwargs.get("custom") and not Data.sensors:
            add = False

        if add:
            formatted_data = {}
            try:
                formatted_data = {
                    "hiveID": data.get("id", ""),
                    "hiveName": data.get("state", {}).get("name", ""),
                    "hiveType": data.get("type", ""),
                    "haType": name,
                    "deviceData": data.get("props", None),
                    "parentDevice": data.get("parent", None),
                    "isGroup": data.get("isGroup", False),
                }
                if kwargs.get("haName", "FALSE")[0] == " ":
                    kwargs["haName"] = (
                        data.get("state", {}).get("name", "")
                        + kwargs["haName"]
                    )
                else:
                    formatted_data["haName"] = formatted_data["hiveName"]
                formatted_data.update(kwargs)
            except (KeyError):
                await self.logger.log(
                    "No_ID",
                    self.sessionType,
                    "Could not setup device - " + str(data),
                )

            self.devices[name].append(formatted_data)
        return add

    async def updateInterval(self, new_interval):
        "Update the scan interval."
        interval = timedelta(seconds=new_interval)
        if interval < timedelta(seconds=15):
            interval = timedelta(seconds=15)
        Data.intervalSeconds = interval
        text = "Scan interval updated to " + str(Data.intervalSeconds)
        await self.logger.log("No_ID", self.sessionType, text)

    async def useFile(self, username=None):
        "Update the scan interval."
        using_file = True if username == "use@file.com" else False
        if using_file:
            Data.file = True
            text = "Using a file."
            await self.logger.log("No_ID", self.sessionType, text)

    async def hiveRefreshTokens(self):
        """Refresh Hive tokens."""
        updated = False

        if Data.file:
            await self.logger.log(
                "No_ID",
                self.sessionType,
                "useFile is active - Cannot refresh tokens.",
            )
            return None
        else:
            await self.logger.log(
                "No_ID",
                self.sessionType,
                "Checking if new tokens are required",
            )

            expiry_time = Data.tokenCreated + Data.tokenExpiry
            if datetime.now() >= expiry_time:
                await self.logger.log(
                    "No_ID", self.sessionType, "Attempting to refresh tokens."
                )
                updated = await self.api.refreshTokens()

        return updated

    async def updateData(self, device):
        """Get latest data for Hive nodes - rate limiting."""
        await self.logger.checkDebugging(Data.debugList)
        await self.updateLock.acquire()
        updated = False
        try:
            ep = Data.lastUpdate + Data.intervalSeconds
            if datetime.now() >= ep:
                await self.getDevices(device["hiveID"])
                updated = True
        finally:
            self.updateLock.release()

        return updated

    async def getDevices(self, n_id):
        """Get latest data for Hive nodes."""
        get_nodes_successful = False
        api_resp_d = None

        if self.api_lock.locked():
            return True

        try:
            await self.api_lock.acquire()
            await asyncio.sleep(1)
            if Data.file:
                await self.logger.log(n_id, "API", "Using file")
                api_resp_d = await self.openFile("data.json")
            elif Data.tokens is not None:
                await self.logger.log(
                    n_id, "Session", "Getting hive device info"
                )
                await self.hiveRefreshTokens()
                api_resp_d = await self.api.getAll()
                if (
                    operator.contains(str(api_resp_d["original"]), "20")
                    is False
                ):
                    await self.logger.error_check(
                        n_id,
                        "ERROR",
                        "Failed_API",
                        resp=api_resp_d["original"],
                    )
                    raise HTTPException
                elif api_resp_d["parsed"] is None:
                    raise HiveApiError

            api_resp_p = api_resp_d["parsed"]
            tmpProducts = {}
            tmpDevices = {}
            tmpActions = {}

            for hiveType in api_resp_p:
                if hiveType == "user":
                    Data.user = api_resp_p[hiveType]
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
                Data.products = tmpProducts
            if len(tmpDevices) > 0:
                Data.devices = tmpDevices
            Data.actions = tmpActions
            Data.lastUpdate = datetime.now()
            get_nodes_successful = True
        except (
            IOError,
            RuntimeError,
            HiveApiError,
            ConnectionError,
            HTTPException,
        ):
            await self.logger.log(
                "No_ID", "API", "Api didn't receive any data"
            )
            get_nodes_successful = False
        finally:
            self.api_lock.release()

        return get_nodes_successful

    async def startSession(self, config):
        """Setup the Hive platform."""
        Data.sensors = config.get("add_sensors", False)
        await self.logger.checkDebugging(config["options"].get("debug", []))
        await self.logger.log(
            "No_ID", self.sessionType, "Initialising Hive Component."
        )
        await self.updateInterval(config["options"]["scan_interval"])
        await self.useFile(config.get("username", False))

        if config["tokens"] is not None and not Data.file:
            await self.logger.log(
                "No_ID", self.sessionType, "Logging into Hive."
            )
            Data.tokens.update({"token": config["tokens"]["IdToken"]})
            Data.tokens.update(
                {"refreshToken": config["tokens"]["RefreshToken"]}
            )
            Data.tokens.update(
                {"accessToken": config["tokens"]["AccessToken"]}
            )
        elif Data.file:
            await self.logger.log(
                "No_ID",
                self.sessionType,
                "Loading up a hive session with a preloaded file.",
            )
        else:
            return "UNKNOWN_CONFIGURATION"

        try:
            await self.getDevices("No_ID")
        except HTTPException:
            return HTTPException

        if Data.devices == {} or Data.products == {}:
            await self.logger.log(
                "No_ID", self.sessionType, "Failed to get data"
            )
            return "INVALID_REAUTH"

        await self.logger.log(
            "No_ID", self.sessionType, "Creating list of devices"
        )
        self.devices["binary_sensor"] = []
        self.devices["climate"] = []
        self.devices["light"] = []
        self.devices["sensor"] = []
        self.devices["switch"] = []
        self.devices["water_heater"] = []

        for aProduct in Data.products:
            p = Data.products[aProduct]
            if p.get("isGroup", False):
                continue

            if Data.products[aProduct]["type"] == "sense":
                await self.add_list(
                    "binary_sensor",
                    p,
                    haName="Glass Detection",
                    hiveType="GLASS_BREAK",
                    device_id=p["parent"],
                    device_name=p["state"]["name"],
                )
                await self.add_list(
                    "binary_sensor",
                    p,
                    haName="Smoke Detection",
                    hiveType="SMOKE_CO",
                    device_id=p["parent"],
                    device_name=p["state"]["name"],
                )
                await self.add_list(
                    "binary_sensor",
                    p,
                    haName="Dog Bark Detection",
                    hiveType="DOG_BARK",
                    device_id=p["parent"],
                    device_name=p["state"]["name"],
                )

            if Data.products[aProduct]["type"] in Data.HIVE_TYPES["Heating"]:
                device_id = p["props"].get("zone", p["id"])
                device_name = (
                    "Heating"
                    if p["state"]["name"] == "Receiver"
                    else p["state"]["name"]
                )
                for device in Data.devices:
                    try:
                        if (
                            Data.devices[device]["type"]
                            in Data.HIVE_TYPES["Thermo"]
                        ):
                            device = Data.devices[device]
                            if p["parent"] == device["props"]["zone"]:
                                device_id = device["id"]
                                device_name = device["state"]["name"]
                                break
                        elif p["type"] == "trvcontrol":
                            device_id = p["props"]["trvs"][0]
                            break
                    except KeyError:
                        self.logger.error_check(
                            "API",
                            p["type"],
                            "API",
                            info="Something has gone wrong.",
                        )

                Data.MODE.append(p["id"])
                await self.add_list(
                    "climate",
                    p,
                    device_id=device_id,
                    device_name=device_name,
                    temperatureunit=Data.user["temperatureUnit"],
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Current Temperature",
                    hiveType="CurrentTemperature",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Target Temperature",
                    hiveType="TargetTemperature",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" State",
                    hiveType="Heating_State",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Mode",
                    hiveType="Heating_Mode",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Boost",
                    hiveType="Heating_Boost",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )

            if Data.products[aProduct]["type"] in Data.HIVE_TYPES["Hotwater"]:
                device_id = p["props"].get("zone", p["id"])
                device_name = p["state"].get("name", "Hotwater")
                for device in Data.devices:
                    try:
                        if (
                            Data.devices[device]["type"]
                            in Data.HIVE_TYPES["Thermo"]
                        ):
                            device = Data.devices[device]
                            if p["parent"] == device["props"]["zone"]:
                                device_id = device["id"]
                                device_name = device["state"]["name"]
                    except KeyError:
                        self.logger._LOGGER.error("Something has gone wrong")

                await self.add_list(
                    "water_heater",
                    p,
                    device_id=device_id,
                    device_name=device_name,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName="Hotwater State",
                    hiveType="Hotwater_State",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName="Hotwater Mode",
                    hiveType="Hotwater_Mode",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName="Hotwater Boost",
                    hiveType="Hotwater_Boost",
                    device_id=device_id,
                    device_name=device_name,
                    custom=True,
                )

            if Data.products[aProduct]["type"] in Data.HIVE_TYPES["Switch"]:
                Data.MODE.append(p["id"])
                await self.add_list(
                    "switch",
                    p,
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Mode",
                    hiveType="Mode",
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Availability",
                    hiveType="Availability",
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                    custom=True,
                )

            if Data.products[aProduct]["type"] in Data.HIVE_TYPES["Light"]:
                Data.MODE.append(p["id"])
                await self.add_list(
                    "light",
                    p,
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Mode",
                    hiveType="Mode",
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                    custom=True,
                )
                await self.add_list(
                    "sensor",
                    p,
                    haName=" Availability",
                    hiveType="Availability",
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                    custom=True,
                )

            if Data.products[aProduct]["type"] in Data.HIVE_TYPES["Sensor"]:
                await self.add_list(
                    "binary_sensor",
                    p,
                    device_id=p["id"],
                    device_name=p["state"]["name"],
                )

        for aDevice in Data.devices:
            d = Data.devices[aDevice]
            if (
                Data.devices[aDevice]["type"] in Data.HIVE_TYPES["Thermo"]
                or Data.devices[aDevice]["type"] in Data.HIVE_TYPES["Sensor"]
            ):
                Data.BATTERY.append(d["id"])
                await self.add_list(
                    "sensor",
                    d,
                    haName=" Battery Level",
                    hiveType="Battery",
                    device_id=d["id"],
                    device_name=d["state"]["name"],
                )
                await self.add_list(
                    "sensor",
                    d,
                    haName=" Availability",
                    hiveType="Availability",
                    device_id=d["id"],
                    device_name=d["state"]["name"],
                    custom=True,
                )

            if Data.devices[aDevice]["type"] in Data.HIVE_TYPES["Hub"]:
                await self.add_list(
                    "binary_sensor",
                    d,
                    haName="Hive Hub Status",
                    hiveType="Connectivity",
                    device_id=d["id"],
                    device_name=d["state"]["name"],
                )

        if "action" in Data.HIVE_TYPES["Switch"]:
            for action in Data.actions:
                a = Data.actions[action]
                await self.add_list(
                    "switch",
                    a,
                    hiveName=a["name"],
                    haName=a["name"],
                    hiveType="action",
                )

        await self.logger.log(
            "No_ID", self.sessionType, "Hive component has initialised"
        )

        return self.devices

    @staticmethod
    async def epochtime(date_time, pattern, action):
        """ date/time conversion to epoch"""
        if action == "to_epoch":
            pattern = "%d.%m.%Y %H:%M:%S"
            epochtime = int(
                time.mktime(time.strptime(str(date_time), pattern))
            )
            return epochtime
        elif action == "from_epoch":
            date = datetime.fromtimestamp(int(date_time)).strftime(pattern)
            return date
