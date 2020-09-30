"""Hive Action Module."""
import asyncio
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async


class Action:
    """Hive Action Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Initialise."""
        self.hive = Hive_Async(websession)
        self.session = Session(websession)
        self.log = Logger()
        self.attr = Attributes()
        self.type = "Action"

    async def get_action(self, device):
        """Get smart plug current power usage."""
        await self.log.log(device["hive_id"], self.type, "Getting action data.")
        dev_data = {}

        if device["hive_id"] in Data.actions:
            data = Data.actions[device["hive_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "state": await self.get_state(device),
                        "power_usage": None,
                        "device_data": {},
                        "custom": device.get("custom", None)
                        }

        await self.log.log(device["hive_id"], self.type,
                           "action update {0}", info=dev_data)
        return dev_data

    async def get_state(self, device):
        """Get action state."""
        await self.log.log(device["hive_id"], "Extra", "Getting state")
        state = None
        final = None

        if device["hive_id"] in Data.actions:
            data = Data.actions[device["hive_id"]]
            final = data["enabled"]
            Data.NODES[device["hive_id"]]["State"] = final
            await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=final)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]].get("State")

    async def turn_on(self, device):
        """Set action turn on."""
        import json
        await self.log.log(device["hive_id"], "Extra", "Enabling action")
        final = False

        if device["hive_id"] in Data.actions:
            await self.session.hive_api_logon()
            data = Data.actions[device["hive_id"]]
            data.update({"enabled": True})
            send = json.dumps(data)
            resp = await self.hive.set_action(Data.sess_id, device["hive_id"], send)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Enabled action - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_off(self, device):
        """Set action to turn off."""
        import json
        await self.log.log(device["hive_id"], "Extra", "Disabling action")
        final = False

        if device["hive_id"] in Data.actions:
            await self.session.hive_api_logon()
            data = Data.actions[device["hive_id"]]
            data.update({"enabled": False})
            send = json.dumps(data)
            resp = await self.hive.set_action(Data.sess_id, device["hive_id"], send)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Disabled action - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
