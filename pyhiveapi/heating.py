""""Hive Heating Module. """
import asyncio
from datetime import datetime
from typing import Optional
from aiohttp import ClientSession
from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async


class Heating:
    """Hive Heating Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Initialise."""
        self.hive = Hive_Async(websession)
        self.session = Session(websession)
        self.log = Logger()
        self.attr = Attributes()
        self.type = "Heating"

    async def get_heating(self, device):
        await self.log.log(device["hive_id"], self.type, "Getting heating data.")
        online = await self.attr.online_offline(device["device_id"])
        error = await self.log.error_check(device["hive_id"], self.type, online)

        dev_data = {}
        if device["device_id"] in Data.devices:
            data = Data.devices[device["device_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "temperatureunit": device["temperatureunit"],
                        "min_temp": await self.min_temperature(device),
                        "max_temp": await self.max_temperature(device),
                        "current_temperature": await self.current_temperature(device),
                        "target_temperature": await self.target_temperature(device),
                        "action": await self.current_operation(device),
                        "mode": await self.get_mode(device),
                        "boost": await self.boost(device),
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["device_id"],
                                                                       device["hive_type"])
                        }
        if not error:
            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=dev_data)

        return dev_data

    @staticmethod
    async def min_temperature(device):
        """Get heating minimum target temperature."""
        if device["hive_type"] == "nathermostat":
            return Data.products[device["hive_id"]]["props"]["minHeat"]
        return 5

    @staticmethod
    async def max_temperature(device):
        """Get heating maximum target temperature."""
        if device["hive_type"] == "nathermostat":
            return Data.products[device["hive_id"]]["props"]["maxHeat"]
        return 32

    async def current_temperature(self, device):
        """Get heating current temperature."""
        from datetime import datetime

        await self.log.log(device["hive_id"], "Extra", "Getting current temp")
        online = await self.attr.online_offline(device["device_id"])
        f_state = None
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["props"]["temperature"]

                if device["hive_id"] in Data.p_minmax:
                    if Data.p_minmax[device["hive_id"]]["TodayDate"] != datetime.date(
                        datetime.now()
                    ):
                        Data.p_minmax[device["hive_id"]]["TodayMin"] = 1000
                        Data.p_minmax[device["hive_id"]]["TodayMax"] = -1000
                        Data.p_minmax[device["hive_id"]]["TodayDate"] = datetime.date(
                            datetime.now())

                        if state < Data.p_minmax[device["hive_id"]]["TodayMin"]:
                            Data.p_minmax[device["hive_id"]
                                          ]["TodayMin"] = state

                        if state > Data.p_minmax[device["hive_id"]]["TodayMax"]:
                            Data.p_minmax[device["hive_id"]
                                          ]["TodayMax"] = state

                        if state < Data.p_minmax[device["hive_id"]]["RestartMin"]:
                            Data.p_minmax[device["hive_id"]
                                          ]["RestartMin"] = state

                        if state > Data.p_minmax[device["hive_id"]]["RestartMax"]:
                            Data.p_minmax[device["hive_id"]
                                          ]["RestartMax"] = state
                else:
                    data = {
                        "TodayMin": state,
                        "TodayMax": state,
                        "TodayDate": str(datetime.date(datetime.now())),
                        "RestartMin": state,
                        "RestartMax": state,
                    }
                    Data.p_minmax[device["hive_id"]] = data
                f_state = round(float(state), 1)
                await self.log.log(device["hive_id"], "Extra",
                                   "Current Temp is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = f_state
            Data.NODES[device["hive_id"]]["CurrentTemp"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["CurrentTemp"]

    async def minmax_temperatures(self, device):
        """Min/Max Temp"""
        await self.log.log(device["hive_id"], "Extra", "Getting Min/Max temp")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.p_minmax:
            if online:
                state = Data.p_minmax[device["hive_id"]]
                await self.log.log(device["hive_id"], "Extra", "Min/Max is {0}", info=state)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = state
            Data.NODES[device["hive_id"]]["minmax"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["minmax"]

    async def target_temperature(self, device):
        """Get heating target temperature."""
        await self.log.log(device["hive_id"], "Extra", "Getting target temp")
        online = await self.attr.online_offline(device["device_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = round(float(data["state"].get("target", None)))
                state = round(float(data["state"].get("heat", state)))
                await self.log.log(device["hive_id"], "Extra",
                                   "Target temp is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = state
            Data.NODES[device["hive_id"]]["TargetTemp"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["TargetTemp"]

    async def get_mode(self, device):
        """Get heating current mode."""
        await self.log.log(device["hive_id"], "Extra", "Getting mode")
        online = await self.attr.online_offline(device["device_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["mode"]
                if state == "BOOST":
                    state = data["props"]["previous"]["mode"]
                await self.log.log(device["hive_id"], "Extra", "Mode is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[device["hive_id"]]["Mode"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Mode"]

    async def get_state(self, device):
        """Get heating current state."""
        await self.log.log(device["hive_id"], "Extra", "Getting state")
        online = await self.attr.online_offline(device["device_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                current_temp = await self.current_temperature(device)
                target_temp = await self.target_temperature(device)
                if current_temp < target_temp:
                    state = "ON"
                else:
                    state = "OFF"
                await self.log.log(device["hive_id"], "Extra", "State is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[device["hive_id"]]["State"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["State"]

    async def current_operation(self, device):
        """Get heating current operation."""
        await self.log.log(device["hive_id"], "Extra", "Getting current operation")
        online = await self.attr.online_offline(device["device_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["props"]["working"]
                await self.log.log(device["hive_id"], "Extra",
                                   "Current operation is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = state
            Data.NODES[device["hive_id"]]["Current_Operation"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Current_Operation"]

    async def boost(self, device):
        """Get heating boost current status."""
        await self.log.log(device["hive_id"], "Extra", "Getting boost status")
        online = await self.attr.online_offline(device["device_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = Data.HIVETOHA["Boost"].get(
                    data["state"].get("boost", False), "ON")
                await self.log.log(device["hive_id"], "Extra",
                                   "Boost state is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = state
            Data.NODES[device["hive_id"]]["Boost"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Boost"]

    async def get_boost_time(self, device):
        """Get heating boost time remaining."""
        if await self.boost(device) == "ON":
            await self.log.log(device["hive_id"], "Extra", "Getting boost time")
            online = await self.attr.online_offline(device["device_id"])
            state = None
            final = None

            if device["hive_id"] in Data.products:
                if online:
                    data = Data.products[device["hive_id"]]
                    state = data["state"]["boost"]
                    await self.log.log(
                        device["hive_id"], self.type, "Time left on boost is {0}", info=str(state)
                    )
                await self.log.error_check(device["hive_id"], "Extra", online)
                final = state
                Data.NODES[device["hive_id"]]["Boost_Time"] = final
            else:
                await self.log.error_check(device["hive_id"], "ERROR", "Failed")

            return final if final is None else Data.NODES[device["hive_id"]]["Boost_Time"]
        return None

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "MANUAL", "OFF"]

    async def get_schedule_now_next_later(self, device):
        """Hive get heating schedule now, next and later."""
        await self.log.log(device["hive_id"], "Extra", "Getting schedule")
        state = await self.attr.online_offline(device["device_id"])
        current_mode = await self.get_mode(device)
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if state != "Offline" and current_mode == "SCHEDULE":
                data = Data.products[device["hive_id"]]
                state = await self.session.p_get_schedule_nnl(
                    Session(), (data["state"]["schedule"])
                )
                await self.log.log(device["hive_id"], "Extra",
                                   "Schedule is {0}", info=str(state))
            await self.log.error_check(device["hive_id"], "Extra", state)
            final = state
            Data.NODES[device["hive_id"]]["snnl"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["snnl"]

    async def set_target_temperature(self, device, new_temp):
        """Set heating target temperature."""
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"],  target=new_temp)

            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True
                await self.log.log(device["hive_id"], "API", "Temperature set - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_mode(self, device, new_mode):
        """Set heating mode."""
        await self.session.hive_api_logon()
        final = False

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], mode=new_mode)

            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True
                await self.log.log(device["hive_id"], "API", "Mode updated - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_boost_on(self, device, mins, temp):
        """Turn heating boost on."""
        if mins > 0 and temp >= await self.min_temperature(device):
            if temp <= await self.max_temperature(device):
                await self.log.log(device["hive_id"], "Extra", "Enabling boost for {0}")
                await self.session.hive_api_logon()
                final = False

                if device["hive_id"] in Data.products:
                    data = Data.products[device["hive_id"]]
                    resp = await self.hive.set_state(Data.sess_id, data["type"],
                                                     device["hive_id"], mode="BOOST", boost=mins, target=temp)

                    if resp["original"] == 200:
                        await self.session.get_devices(device["hive_id"])
                        final = True
                        await self.log.log(
                            device["hive_id"], "API", "Boost enabled - " +
                            "API response 200"
                        )
                    else:
                        await self.log.error_check(
                            device["hive_id"], "ERROR", "Failed_API", resp=resp["original"]
                        )

                return final
        return None

    async def turn_boost_off(self, device):
        """Turn heating boost off."""
        await self.log.log(self.type, "Disabling boost for {0}", device["hive_id"])
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            await self.session.get_devices(device["hive_id"])
            if await self.boost(device) == "ON":
                prev_mode = data["props"]["previous"]["mode"]
                if prev_mode == "MANUAL" or prev_mode == "OFF":
                    pre_temp = data["props"]["previous"].get("target", 7)
                    resp = await self.hive.set_state(Data.sess_id, data["type"],
                                                     device["hive_id"],
                                                     mode=prev_mode,
                                                     target=pre_temp)
                else:
                    resp = await self.hive.set_state(Data.sess_id, data["type"],
                                                     device["hive_id"], mode=prev_mode)
                if resp["original"] == 200:
                    await self.session.get_devices(device["hive_id"])
                    final = True
                    await self.log.log(
                        device["hive_id"], "API", "Boost disabled - " + "API response 200")
                else:
                    await self.log.error_check(
                        device["hive_id"], "ERROR", "Failed_API", resp=resp["original"]
                    )

        return final
