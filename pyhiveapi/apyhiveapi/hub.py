"""Hive Hub Module."""

from .helper.const import HIVETOHA


class Hub:
    """Hive Hub Code."""

    hubType = "Hub"
    logType = "Sensor"

    def __init__(self, session=None):
        """Initialise hub."""
        self.session = session

    async def hubSmoke(self, device):
        """Get the online status of the Hive hub."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["sensors"]["SMOKE_CO"]["active"]
            final = HIVETOHA[self.hubType]["Smoke"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def hubDogBark(self, device):
        """Get the online status of the Hive hub."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["sensors"]["DOG_BARK"]["active"]
            final = HIVETOHA[self.hubType]["Dog"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def hubGlass(self, device):
        """Get the glass detected status from the Hive hub."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["sensors"]["GLASS_BREAK"]["active"]
            final = HIVETOHA[self.hubType]["Glass"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final
