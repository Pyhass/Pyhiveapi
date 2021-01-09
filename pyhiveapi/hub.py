"""Hive Hub Module."""
from .helper.hive_data import Data
from .session import Session


class Hub(Session):
    """ Hive Hub Code. """

    hubType = "Hub"
    logType = "Sensor"

    async def hub_smoke(self, device):
        """Get the online status of the Hive hub."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["props"]["sensors"]["SMOKE_CO"]["active"]
            final = Data.HIVETOHA[self.hubType]["Smoke"].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def hub_dog_bark(self, device):
        """Get the online status of the Hive hub."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["props"]["sensors"]["DOG_BARK"]["active"]
            final = Data.HIVETOHA[self.hubType]["Dog"].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def hub_glass(self, device):
        """Get the glass detected status from the Hive hub."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["props"]["sensors"]["GLASS_BREAK"]["active"]
            final = Data.HIVETOHA[self.hubType]["Glass"].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final
