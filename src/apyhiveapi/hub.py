"""Hive Hub Module."""

from .helper.const import HIVETOHA


class HiveHub:
    """Hive hub.

    Returns:
        object: Returns a hub object.
    """

    hub_type = "Hub"
    log_type = "Sensor"

    def __init__(self, session: object = None):
        """Initialise hub.

        Args:
            session (object, optional): session to interact with Hive account. Defaults to None.
        """
        self.session = session

    async def get_smoke_status(self, device: dict):
        """Get the hub smoke status.

        Args:
            device (dict): device to get status for

        Returns:
            str: Return smoke status.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["sensors"]["SMOKE_CO"]["active"]
            final = HIVETOHA[self.hub_type]["Smoke"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def get_dog_bark_status(self, device: dict):
        """Get dog bark status.

        Args:
            device (dict): Device to get status for.

        Returns:
            str: Return status.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["sensors"]["DOG_BARK"]["active"]
            final = HIVETOHA[self.hub_type]["Dog"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def get_glass_break_status(self, device: dict):
        """Get the glass detected status from the Hive hub.

        Args:
            device (dict): Device to get status for.

        Returns:
            str: Return status.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["sensors"]["GLASS_BREAK"]["active"]
            final = HIVETOHA[self.hub_type]["Glass"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final
