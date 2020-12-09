"""Hive Hub Module."""
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_data import Data
from .helper import Hive_Helper


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
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting smoke detection status")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["sensors"]["SMOKE_CO"]["active"]
            final = Data.HIVETOHA[self.type]["Smoke"].get(state, state)
            await self.log.log(device["hive_id"], self.type + "_Extra", "Status is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def hub_dog_bark(self, device):
        """Get the online status of the Hive hub."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting barking detection status")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["sensors"]["DOG_BARK"]["active"]
            final = Data.HIVETOHA[self.type]["Dog"].get(state, state)
            await self.log.log(device["hive_id"], self.type + "_Extra", "Status is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def hub_glass(self, device):
        """Get the glass detected status from the Hive hub."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting glass detection status")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["sensors"]["GLASS_BREAK"]["active"]
            final = Data.HIVETOHA[self.type]["Glass"].get(state, state)
            await self.log.log(device["hive_id"], self.type + "_Extra", "Status is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final
