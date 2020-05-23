"""Hive Hub Module."""
import asyncio
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_data import Data


class Hub:
    """ Hive Hub Code. """

    def __init__(self):
        """Initialise."""
        self.log = Logger()
        self.attr = Attributes()
        self.type = "Hub"
        self.log_type = "Sensor"

    async def hub_smoke(self, device):
        """Get the online status of the Hive hub."""
        await self.log.log(device["hive_id"], "Extra", "Getting smoke detection status")
        online = await self.attr.online_offline(device["hub_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["props"]["sensors"]["SMOKE_CO"]["active"]
                final = Data.HIVETOHA[self.type]["Smoke"].get(state, state)
                await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", final)
            final = Data.HIVETOHA[self.type]["Smoke"].get(state, state)
            Data.NODES[device["hive_id"]]["Smoke"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Smoke"]

    async def hub_dog_bark(self, device):
        """Get the online status of the Hive hub."""
        await self.log.log(device["hive_id"], "Extra", "Getting barking detection status")
        online = await self.attr.online_offline(device["hub_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["props"]["sensors"]["DOG_BARK"]["active"]
                final = Data.HIVETOHA[self.type]["Dog"].get(state, state)
                await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", final)
            final = Data.HIVETOHA[self.type]["Dog"].get(state, state)
            Data.NODES[device["hive_id"]]["Dog"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Dog"]

    async def hub_glass(self, device):
        """Get the glass detected status from the Hive hub."""
        await self.log.log(device["hive_id"], "Extra", "Getting glass detection status")
        online = await self.attr.online_offline(device["hub_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["props"]["sensors"]["GLASS_BREAK"]["active"]
                final = Data.HIVETOHA[self.type]["Glass"].get(state, state)
                await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", final)
            final = Data.HIVETOHA[self.type]["Glass"].get(state, state)
            Data.NODES[device["hive_id"]]["Glass"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Glass"]
