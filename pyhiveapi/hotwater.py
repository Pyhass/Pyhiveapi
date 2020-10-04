""""Hive Hotwater Module. """
import asyncio
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async


class Hotwater:
    """Hive Hotwater Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Initialise."""
        self.hive = Hive_Async(websession)
        self.session = Session(websession)
        self.log = Logger()
        self.attr = Attributes()
        self.type = "Hotwater"

    async def get_hotwater(self, device):
        """Get light data."""
        await self.log.log(device["hive_id"], self.type, "Getting hot water data.")
        online = await self.attr.online_offline(device["hive_id"])
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
                        "current_operation": await self.get_mode(device),
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["hive_id"],
                                                                       device["hive_type"])
                        }

        if not error:
            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=dev_data)

        return dev_data

    async def get_mode(self, device):
        """Get hotwater current mode."""
        await self.log.log(device["hive_id"], "Extra", "Getting mode")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["mode"]
                if state == "BOOST":
                    state = data["props"]["previous"]["mode"]
                final = Data.HIVETOHA[self.type].get(state, state)
                await self.log.log(device["hive_id"], "Extra", "Mode is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[device["hive_id"]]["Mode"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Mode"]

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "ON", "OFF"]

    async def get_boost(self, device):
        """Get hot water current boost status."""
        await self.log.log(device["hive_id"], "Extra", "Getting boost")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["boost"]
                final = Data.HIVETOHA["Boost"].get(state, "ON")
                await self.log.log(device["hive_id"], "Extra", "Boost is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA["Boost"].get(state, "ON")
            Data.NODES[device["hive_id"]]["Boost"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Boost"]

    async def get_boost_time(self, device):
        """Get hotwater boost time remaining."""
        if await self.get_boost(device["hive_id"]) == "ON":
            await self.log.log(device["hive_id"], "Extra", "Getting boost time")
            online = await self.attr.online_offline(device["hive_id"])
            state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["boost"]
                await self.log.log(device["hive_id"], "Extra",
                                   "Boost time is {0}", info=state)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = state
            Data.NODES[device["hive_id"]]["Boost_Time"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Boost_Time"]

    async def get_state(self, device):
        """Get hot water current state."""
        await self.log.log(device["hive_id"], "Extra", "Getting state")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["status"]
                mode_current = await self.get_mode(device["hive_id"])
                if mode_current == "SCHEDULE":
                    if await self.get_boost(device["hive_id"]) == "ON":
                        state = "ON"
                    else:
                        snan = self.session.p_get_schedule_nnl(
                            data["state"]["schedule"]
                        )
                        state = snan["now"]["value"]["status"]
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[device["hive_id"]]["State"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["State"]

    async def get_schedule_now_next_later(self, device):
        """Hive get hotwater schedule now, next and later."""
        await self.log.log(device["hive_id"], "Extra", "Getting schedule info.")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            mode_current = await self.get_mode(device)
            if not online and mode_current == "SCHEDULE":
                data = Data.products[device["hive_id"]]
                state = self.session.p_get_schedule_nnl(
                    data["state"]["schedule"])
                final = state
                Data.NODES[device["hive_id"]]["snnl"] = final
                await self.log.log(device["hive_id"], "Extra", "Schedule is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def set_mode(self, device, new_mode):
        """Set hot water mode."""
        await self.log.log(device["hive_id"], "Extra", "Setting Mode")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], mode=new_mode)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(
                    device["hive_id"], "API", "Mode set to {0} - API response 200", info=new_mode
                )
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

            return final

    async def turn_boost_on(self, device, mins):
        """Turn hot water boost on."""
        await self.log.log(device["hive_id"], "Extra", "Turning on boost")
        final = False

        if mins > 0 and device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], mode="BOOST",
                                             boost=mins)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Boost on - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_boost_off(self, device):
        """Turn hot water boost off."""
        await self.log.log(device["hive_id"], "Extra", "Turning off boost")
        final = False

        if device["hive_id"] in Data.products and await self.get_boost(device["hive_id"]) == "ON":
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            prev_mode = data["props"]["previous"]["mode"]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], mode=prev_mode)
            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True
                await self.log.log(device["hive_id"], "API", "Boost off - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
