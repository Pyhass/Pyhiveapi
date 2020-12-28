"""Hive Hub Module."""
from .hive_session import Session
from .hive_data import Data


class Hub(Session):
    """ Hive Hub Code. """
    hubType = 'Hub'
    logType = 'Sensor'

    async def hub_smoke(self, device):
        """Get the online status of the Hive hub."""
        await self.logger.log(device["hiveID"], self.logType + "_Extra", "Getting smoke detection status")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["sensors"]["SMOKE_CO"]["active"]
            final = Data.HIVETOHA[self.hubType]["Smoke"].get(state, state)
            await self.logger.log(device["hiveID"], self.logType + "_Extra", "Status is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def hub_dog_bark(self, device):
        """Get the online status of the Hive hub."""
        await self.logger.log(device["hiveID"], self.logType + "_Extra", "Getting barking detection status")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["sensors"]["DOG_BARK"]["active"]
            final = Data.HIVETOHA[self.hubType]["Dog"].get(state, state)
            await self.logger.log(device["hiveID"], self.logType + "_Extra", "Status is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def hub_glass(self, device):
        """Get the glass detected status from the Hive hub."""
        await self.logger.log(device["hiveID"], self.logType + "_Extra", "Getting glass detection status")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["sensors"]["GLASS_BREAK"]["active"]
            final = Data.HIVETOHA[self.hubType]["Glass"].get(state, state)
            await self.logger.log(device["hiveID"], self.logType + "_Extra", "Status is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final
