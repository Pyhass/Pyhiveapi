"""Hive Switch Module."""
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async
from .helper import Hive_Helper


class Plug():
    """Hive Switch Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Initialise."""
        self.hive = Hive_Async(websession)
        self.session = Session(websession)
        self.log = Logger()
        self.attr = Attributes()
        self.type = "Switch"

    async def get_plug(self, device):
        """Get smart plug data."""
        await self.log.log(device["hive_id"], self.type, "Getting switch data.")
        online = await self.attr.online_offline(device["device_id"])

        dev_data = {}
        if online:
            Hive_Helper.device_recovered(device["device_id"])
            data = Data.devices[device["hive_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "status": {
                            "state": await self.get_state(device),
                            "power_usage": await self.get_power_usage(device)},
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["hive_id"],
                                                                       device["hive_type"])
                        }

            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=[dev_data["status"]])
            Data.ha_devices.update({device['hive_id']: dev_data})
            return dev_data
        else:
            await self.log.error_check(device["device_id"], "ERROR", online)
            return device

    async def get_state(self, device):
        """Get plug current state."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting state of switch")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["status"]
            await self.log.log(device["hive_id"], self.type + "_Extra", "Status is {0}", info=[state])
            final = Data.HIVETOHA["Switch"].get(state, state)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_power_usage(self, device):
        """Get smart plug current power usage."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting power consumption.")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["powerConsumption"]
            await self.log.log(device["hive_id"], self.type + "_Extra",
                               "Power consumption is {0}", info=[state])
            final = state
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def turn_on(self, device):
        """Set smart plug to turn on."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Powering switch")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(data["type"],
                                             data["id"],
                                             status="ON")
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Switched on - " + device["hive_name"])
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_off(self, device):
        """Set smart plug to turn off."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Turning off switch.")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(
                data["type"],
                data["id"],
                status="OFF")
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Switch off - " + device["hive_name"])
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
