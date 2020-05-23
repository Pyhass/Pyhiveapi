"""Hive Switch Module."""
import asyncio
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async


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
        online = await self.attr.online_offline(device["hive_id"])
        error = await self.log.error_check(device["hive_id"], self.type, online)

        dev_data = {}
        if device["hive_id"] in Data.devices:
            data = Data.devices[device["hive_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "state": await self.get_state(device),
                        "power_usage": await self.get_power_usage(device),
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

    async def get_state(self, device):
        """Get plug current state."""
        await self.log.log(device["hive_id"], "Extra", "Getting state of switch")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["status"]
                await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=state)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA["Switch"].get(state, state)
            Data.NODES[device["hive_id"]]["State"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["State"]

    async def get_power_usage(self, device):
        """Get smart plug current power usage."""
        await self.log.log(device["hive_id"], "Extra", "Getting power consumption.")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["props"]["powerConsumption"]
                await self.log.log(device["hive_id"], "Extra",
                                   "Power consumption is {0}", info=state)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = state
            Data.NODES[device["hive_id"]]["Power"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Power"]

    async def turn_on(self, device):
        """Set smart plug to turn on."""
        await self.log.log(device["hive_id"], "Extra", "Powering switch")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id,
                                             data["type"],
                                             data["id"],
                                             status="ON")
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Switched on - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_off(self, device):
        """Set smart plug to turn off."""
        await self.log.log(device["hive_id"], "Extra", "Turning off switch.")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(
                Data.sess_id,
                data["type"],
                data["id"],
                status="OFF")
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Switch off - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
