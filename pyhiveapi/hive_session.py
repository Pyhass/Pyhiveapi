""" Hive Session Module."""
import operator
import os
import time
import json
import asyncio
import operator
from typing import Optional
from aiohttp import ClientSession
from aiohttp.web import HTTPException
from datetime import datetime, timedelta


from .hive_data import Data
from .custom_logging import Logger
from .hive_async_api import Hive_Async
from .device_attributes import Attributes
from .hive_exceptions import HiveApiError


class Session:
    """Hive Session Code"""

    def __init__(self, websession: Optional[ClientSession] = None, init=None):
        """Initialise the base variable values."""
        self.update_lock = asyncio.Lock()
        self.api_lock = asyncio.Lock()
        self.hive = Hive_Async(websession)
        self.log = Logger()
        self.attr = Attributes()
        self.devices = {}
        self.type = "Session"
        self.init = init

    async def open_file(self, file):
        path = os.path.dirname(os.path.realpath(
            __file__)) + '/' + file
        with open(path, 'r') as j:
            data = json.loads(j.read())

        return data

    async def add_list(self, name, data, **kwargs):
        """Add entity to the list"""
        add = True
        if kwargs.get("custom") and not Data.s_sensors:
            add = False

        if add:
            formatted_data = {}
            try:
                formatted_data = {"hive_id": data.get("id", ""),
                                  "hive_name": data.get("state", {}).get("name", ""),
                                  "hive_type": data.get("type", ""),
                                  "ha_type": name,
                                  "device_data": data.get("props", None),
                                  "parent_device": data.get("parent", None)
                                  }
                if kwargs.get("ha_name", "FALSE")[0] == " ":
                    kwargs["ha_name"] = data.get("state", {}).get(
                        "name", "") + kwargs["ha_name"]
                else:
                    formatted_data["ha_name"] = formatted_data["hive_name"]
                formatted_data.update(kwargs)
            except (KeyError):
                await self.log.log("No_ID", self.type, "Could not setup device - " + str(data))

            self.devices[name].append(formatted_data)
        return add

    async def update_interval(self, new_interval):
        "Update the scan interval."
        interval = timedelta(seconds=new_interval)
        if interval < timedelta(seconds=15):
            interval = timedelta(seconds=15)
        Data.s_interval_seconds = interval
        text = "Scan interval updated to " + str(Data.s_interval_seconds)
        await self.log.log("No_ID", self.type, text)

    async def use_file(self, username=None):
        "Update the scan interval."
        using_file = True if username == "use@file.com" else False
        if using_file:
            Data.s_file = True
            text = "Using a file."
            await self.log.log("No_ID", self.type, text)

    # DEPRECATED - no longer in use refesh token is the replacement.
    async def hive_api_logon(self):
        """Log in to the Hive API and get the Session Data."""

        if Data.s_file:
            return None
        else:
            await self.log.log("No_ID", self.type, "Checking if login is required.")

            expiry_time = Data.s_token_update + Data.s_token_expiry
            if datetime.now >= expiry_time or Data.s_tokens is None:
                await self.log.log("No_ID", self.type, "Attempting to login to Hive.")

                resp_p = await self.hive.login(Data.s_username, Data.s_password)

                if resp_p["original"] == 200:
                    info = resp_p["parsed"]
                    if "token" in info and "user" in info and "platform" in info:
                        Data.s_tokens = info["token"]
                        Data.s_token_update = datetime.now()

                        self.hive.urls.update(
                            {"base": info["platform"]["endpoint"]})

    async def hive_refresh_tokens(self):
        """Refresh Hive tokens."""
        updated = False

        if Data.s_file:
            await self.log.log("No_ID", self.type, "use_file is active - Cannot refresh tokens.")
            return None
        else:
            await self.log.log("No_ID", self.type, "Checking if new tokens are required")

            expiry_time = Data.s_token_update + Data.s_token_expiry
            if datetime.now() >= expiry_time or Data.s_entity_update_flag == "Y":
                await self.log.log("No_ID", self.type, "Attempting to refresh tokens.")
                updated = await self.hive.refreshTokens()

        return updated

    async def update_data(self, device):
        """Get latest data for Hive nodes - rate limiting."""
        await self.log.check_debuging(Data.d_list)
        await self.update_lock.acquire()
        updated = True
        try:
            ep = Data.s_last_update + Data.s_interval_seconds
            if datetime.now() >= ep:
                await self.get_devices(device["hive_id"])
        except:
            updated = False
        finally:
            self.update_lock.release()

        return updated

    async def get_devices(self, n_id):
        """Get latest data for Hive nodes."""
        get_nodes_successful = False
        api_resp_d = None

        if self.api_lock.locked():
            return True

        try:
            await self.api_lock.acquire()
            await asyncio.sleep(1)
            if Data.s_file:
                await self.log.log(n_id, "API", "Using file")
                api_resp_d = await self.open_file("data.json")
            elif Data.s_tokens is not None:
                await self.log.log(n_id, "Session", "Getting hive device info")
                await self.hive_refresh_tokens()
                api_resp_d = await self.hive.getAll()
                if operator.contains(str(api_resp_d["original"]), '20') == False:
                    await self.log.error_check(
                        n_id, "ERROR", "Failed_API", resp=api_resp_d["original"])
                    raise HTTPException
                elif api_resp_d["parsed"] is None:
                    raise HiveApiError

            api_resp_p = api_resp_d["parsed"]

            for hive_type in api_resp_p:
                if hive_type == "user":
                    Data.user = api_resp_p[hive_type]
                if hive_type == "products":
                    Data.products = {}
                    for a_product in api_resp_p[hive_type]:
                        Data.products.update({a_product["id"]: a_product})
                if hive_type == "devices":
                    Data.devices = {}
                    for a_device in api_resp_p[hive_type]:
                        Data.devices.update({a_device["id"]: a_device})
                if hive_type == "actions":
                    Data.actions = {}
                    for a_action in api_resp_p[hive_type]:
                        Data.actions.update({a_action["id"]: a_action})

            Data.s_last_update = datetime.now()
            get_nodes_successful = True
        except (IOError, RuntimeError, HiveApiError, ConnectionError, HTTPException):
            await self.log.log("No_ID", "API", "Api didn't receive any data")
            get_nodes_successful = False
        finally:
            self.api_lock.release()

        return get_nodes_successful

    @staticmethod
    async def p_minutes_to_time(minutes_to_convert):
        """Convert minutes string to datetime."""
        hours_converted, minutes_converted = divmod(minutes_to_convert, 60)
        converted_time = datetime.strptime(
            str(hours_converted) + ":" + str(minutes_converted), "%H:%M"
        )
        converted_time_string = converted_time.strftime("%H:%M")
        return converted_time_string

    @staticmethod
    async def p_get_schedule_nnl(hive_api_schedule):
        """Get the schedule now, next and later of a given nodes schedule."""
        schedule_now_and_next = {}
        date_time_now = datetime.now()
        date_time_now_day_int = date_time_now.today().weekday()

        days_t = (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )

        days_rolling_list = list(days_t[date_time_now_day_int:] + days_t)[:7]

        full_schedule_list = []

        for day_index in range(0, len(days_rolling_list)):
            current_day_schedule = hive_api_schedule[days_rolling_list[day_index]]
            current_day_schedule_sorted = sorted(
                current_day_schedule, key=operator.itemgetter("start"), reverse=False
            )

            for current_slot in range(0, len(current_day_schedule_sorted)):
                current_slot_custom = current_day_schedule_sorted[current_slot]

                slot_date = datetime.now() + timedelta(days=day_index)
                slot_time = await Session.p_minutes_to_time(
                    current_slot_custom["start"])
                slot_time_date_s = slot_date.strftime(
                    "%d-%m-%Y") + " " + slot_time
                slot_time_date_dt = datetime.strptime(
                    slot_time_date_s, "%d-%m-%Y %H:%M"
                )
                if slot_time_date_dt <= date_time_now:
                    slot_time_date_dt = slot_time_date_dt + timedelta(days=7)

                current_slot_custom["Start_DateTime"] = slot_time_date_dt
                full_schedule_list.append(current_slot_custom)

        fsl_sorted = sorted(
            full_schedule_list, key=operator.itemgetter("Start_DateTime"), reverse=False
        )

        schedule_now = fsl_sorted[-1]
        schedule_next = fsl_sorted[0]
        schedule_later = fsl_sorted[1]

        schedule_now["Start_DateTime"] = schedule_now["Start_DateTime"] - timedelta(
            days=7
        )

        schedule_now["End_DateTime"] = schedule_next["Start_DateTime"]
        schedule_next["End_DateTime"] = schedule_later["Start_DateTime"]
        schedule_later["End_DateTime"] = fsl_sorted[2]["Start_DateTime"]

        schedule_now_and_next["now"] = schedule_now
        schedule_now_and_next["next"] = schedule_next
        schedule_now_and_next["later"] = schedule_later

        return schedule_now_and_next

    async def start_session(self, tokens, update, config):
        """Setup the Hive platform."""
        Data.s_sensors = config.get("add_sensors", False)
        Data.s_entity_update_flag = update
        await self.log.check_debuging(config["options"].get("debug", []))
        await self.log.log("No_ID", self.type, "Initialising Hive Component.")
        await self.update_interval(config["options"]["scan_interval"])
        await self.use_file(config.get("username", False))

        if tokens is not None and not Data.s_file:
            await self.log.log("No_ID", self.type, "Logging into Hive.")
            Data.s_tokens.update(
                {"token": tokens["IdToken"]})
            Data.s_tokens.update(
                {"refreshToken": tokens["RefreshToken"]})
            Data.s_tokens.update(
                {"accessToken": tokens["AccessToken"]})
        elif Data.s_file:
            await self.log.log("No_ID", self.type, "Loading up a hive session with a preloaded file.")
        else:
            return "UNKNOWN_CONFIGURATION"

        try:
            await self.get_devices("No_ID")
        except HTTPException:
            return HTTPException

        if Data.devices == {} or Data.products == {}:
            await self.log.log("No_ID", self.type, "Failed to get data")
            return "INVALID_REAUTH"

        await self.log.log("No_ID", self.type, "Creating list of devices")
        self.devices["binary_sensor"] = []
        self.devices["climate"] = []
        self.devices["light"] = []
        self.devices["sensor"] = []
        self.devices["switch"] = []
        self.devices["water_heater"] = []

        for a_product in Data.products:
            p = Data.products[a_product]
            if Data.products[a_product]["type"] == "sense":
                await self.add_list("binary_sensor", p, ha_name="Glass Detection",
                                    hive_type="GLASS_BREAK",
                                    device_id=p["parent"], device_name=p["state"]["name"])
                await self.add_list("binary_sensor", p, ha_name="Smoke Detection",
                                    hive_type="SMOKE_CO",
                                    device_id=p["parent"], device_name=p["state"]["name"])
                await self.add_list("binary_sensor", p, ha_name="Dog Bark Detection",
                                    hive_type="DOG_BARK",
                                    device_id=p["parent"], device_name=p["state"]["name"])

            if Data.products[a_product]["type"] in Data.HIVE_TYPES["Heating"]:
                device_id = p["props"].get("zone", p["id"])
                device_name = p["state"].get("name", "Heating")
                for device in Data.devices:
                    try:
                        if Data.devices[device]["type"] in Data.HIVE_TYPES["Thermo"]:
                            device = Data.devices[device]
                            if p["parent"] == device["props"]["zone"]:
                                device_id = device["id"]
                                device_name = device["state"]["name"]
                                break
                        elif p["type"] == 'trvcontrol':
                            device_id = p["props"]["trvs"][0]
                    except:
                        pass
                Data.MODE.append(p["id"])
                await self.add_list("climate", p, device_id=device_id, device_name=device_name,
                                    temperatureunit=Data.user["temperatureUnit"])
                await self.add_list("sensor", p, ha_name=" Current Temperature",
                                    hive_type="CurrentTemperature", device_id=device_id,
                                    device_name=device_name, custom=True)
                await self.add_list("sensor", p, ha_name=" Target Temperature",
                                    hive_type="TargetTemperature", device_id=device_id,
                                    device_name=device_name, custom=True)
                await self.add_list("sensor", p, ha_name=" State",
                                    hive_type="Heating_State", device_id=device_id,
                                    device_name=device_name, custom=True)
                await self.add_list("sensor", p, ha_name=" Mode",
                                    hive_type="Heating_Mode", device_id=device_id,
                                    device_name=device_name, custom=True)
                await self.add_list("sensor", p, ha_name=" Boost",
                                    hive_type="Heating_Boost", device_id=device_id,
                                    device_name=device_name, custom=True)

            if Data.products[a_product]["type"] in Data.HIVE_TYPES["Hotwater"]:
                device_id = p["props"].get("zone", p["id"])
                device_name = p["state"].get("name", "Hotwater")
                for device in Data.devices:
                    try:
                        if Data.devices[device]["type"] in Data.HIVE_TYPES["Thermo"]:
                            device = Data.devices[device]
                            if p["parent"] == device["props"]["zone"]:
                                device_id = device["id"]
                                device_name = device["state"]["name"]
                    except:
                        pass
                await self.add_list("water_heater", p, device_id=device_id, device_name=device_name)
                await self.add_list("sensor", p, ha_name="Hotwater State",
                                    hive_type="Hotwater_State", device_id=device_id,
                                    device_name=device_name, custom=True)
                await self.add_list("sensor", p, ha_name="Hotwater Mode",
                                    hive_type="Hotwater_Mode", device_id=device_id,
                                    device_name=device_name, custom=True)
                await self.add_list("sensor", p, ha_name="Hotwater Boost",
                                    hive_type="Hotwater_Boost", device_id=device_id,
                                    device_name=device_name, custom=True)

            if Data.products[a_product]["type"] in Data.HIVE_TYPES["Switch"]:
                Data.MODE.append(p["id"])
                await self.add_list("switch", p, device_id=p["id"], device_name=p["state"]["name"])
                await self.add_list("sensor", p, ha_name=" Mode", hive_type="Mode", device_id=p["id"],
                                    device_name=p["state"]["name"], custom=True)
                await self.add_list("sensor", p, ha_name=" Availability", hive_type="Availability", device_id=p["id"],
                                    device_name=p["state"]["name"], custom=True)

            if Data.products[a_product]["type"] in Data.HIVE_TYPES["Light"]:
                Data.MODE.append(p["id"])
                await self.add_list("light", p, device_id=p["id"], device_name=p["state"]["name"])
                await self.add_list("sensor", p, ha_name=" Mode", hive_type="Mode", device_id=p["id"],
                                    device_name=p["state"]["name"], custom=True)
                await self.add_list("sensor", p, ha_name=" Availability", hive_type="Availability", device_id=p["id"],
                                    device_name=p["state"]["name"], custom=True)

            if Data.products[a_product]["type"] in Data.HIVE_TYPES["Sensor"]:
                await self.add_list("binary_sensor", p, device_id=p["id"], device_name=p["state"]["name"])

        for a_device in Data.devices:
            d = Data.devices[a_device]
            if (
                    Data.devices[a_device]["type"] in Data.HIVE_TYPES["Thermo"]
                    or Data.devices[a_device]["type"] in Data.HIVE_TYPES["Sensor"]):
                Data.BATTERY.append(d["id"])
                await self.add_list("sensor", d, ha_name=" Battery Level",
                                    hive_type="Battery", device_id=d["id"], device_name=d["state"]["name"])
                await self.add_list("sensor", d, ha_name=" Availability",
                                    hive_type="Availability", device_id=d["id"], device_name=d["state"]["name"],
                                    custom=True)

            if Data.devices[a_device]["type"] in Data.HIVE_TYPES["Hub"]:
                await self.add_list("binary_sensor", d, ha_name=" Online Status",
                                    hive_type="Connectivity", device_id=d["id"], device_name=d["state"]["name"])

        if "action" in Data.HIVE_TYPES["Switch"]:
            for action in Data.actions:
                a = Data.actions[action]
                await self.add_list("switch", a, hive_name=a["name"],
                                    ha_name=a["name"],
                                    hive_type="action")

        await self.log.log("No_ID", self.type, "Hive component has initialised")

        return self.devices

    @staticmethod
    async def epochtime(date_time, pattern, action):
        """ date/time conversion to epoch"""
        if action == "to_epoch":
            pattern = "%d.%m.%Y %H:%M:%S"
            epochtime = int(time.mktime(
                time.strptime(str(date_time), pattern)))
            return epochtime
        elif action == "from_epoch":
            date = datetime.fromtimestamp(int(date_time)).strftime(pattern)
            return date
