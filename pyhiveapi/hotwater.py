""""Hive Hotwater Module. """
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async
from .helper import Hive_Helper


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
        online = await self.attr.online_offline(device["device_id"])
        dev_data = {}

        if online:
            Hive_Helper.device_recovered(device["device_id"])
            data = Data.devices[device["device_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "status": {
                            "current_operation": await self.get_mode(device)},
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["device_id"],
                                                                       device["hive_type"])
                        }

            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=dev_data['status'])
            Data.ha_devices.update({device['hive_id']: dev_data})
            return dev_data
        else:
            await self.log.error_check(device["device_id"], "ERROR", online)
            return device

    async def get_mode(self, device):
        """Get hotwater current mode."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting mode")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = Data.HIVETOHA[self.type].get(state, state)
            await self.log.log(device["hive_id"], self.type + "_Extra", "Mode is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "ON", "OFF"]

    async def get_boost(self, device):
        """Get hot water current boost status."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting boost")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["boost"]
            final = Data.HIVETOHA["Boost"].get(state, "ON")
            await self.log.log(device["hive_id"], self.type + "_Extra", "Boost is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_boost_time(self, device):
        """Get hotwater boost time remaining."""
        state = None
        final = None
        if await self.get_boost(device) == "ON":
            await self.log.log(device["hive_id"], self.type + "_Extra", "Getting boost time")
            if device["hive_id"] in Data.products:
                data = Data.products[device["hive_id"]]
                state = data["state"]["boost"]
                await self.log.log(device["hive_id"], self.type + "_Extra",
                                   "Boost time is {0}", info=[state])
                final = state
            else:
                await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_state(self, device):
        """Get hot water current state."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting state")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["status"]
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                if await self.get_boost(device) == "ON":
                    state = "ON"
                else:
                    snan = await self.session.p_get_schedule_nnl(
                        data["state"]["schedule"])
                    state = snan["now"]["value"]["status"]

            final = Data.HIVETOHA[self.type].get(state, state)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_schedule_now_next_later(self, device):
        """Hive get hotwater schedule now, next and later."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting schedule info.")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                data = Data.products[device["hive_id"]]
                state = await self.session.p_get_schedule_nnl(
                    data["state"]["schedule"])
            final = state
            await self.log.log(device["hive_id"], self.type + "_Extra", "Schedule is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def set_mode(self, device, new_mode):
        """Set hot water mode."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Setting Mode to {0}", info=[new_mode])
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], mode=new_mode)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(
                    device["hive_id"], "API", "Mode set to {0} - " + device["hive_name"], info=[new_mode]
                )
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

            return final

    async def turn_boost_on(self, device, mins):
        """Turn hot water boost on."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Turning on boost")
        final = False

        if mins > 0 and device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], mode="BOOST",
                                             boost=mins)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Boost on - " + device["hive_name"])
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_boost_off(self, device):
        """Turn hot water boost off."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Turning off boost")
        final = False

        if device["hive_id"] in Data.products and await self.get_boost(device) == "ON":
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            prev_mode = data["props"]["previous"]["mode"]
            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], mode=prev_mode)
            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True
                await self.log.log(device["hive_id"], "API", "Boost off - " + device["hive_name"])
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
