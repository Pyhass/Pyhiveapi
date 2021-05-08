"""Hive Device Attribute Module."""
from .helper.const import HIVETOHA
from .helper.logger import Logger


class HiveAttributes:
    """Device Attributes Code."""

    def __init__(self, session: object = None):
        """Initialise attributes.

        Args:
            session (object, optional): Session to interact with hive account. Defaults to None.
        """
        self.session = session
        self.session.log = Logger()
        self.type = "Attribute"

    async def stateAttributes(self, n_id: str, _type: str):
        """Get HA State Attributes.

        Args:
            n_id (str): The id of the device.
            _type (str): The device type.

        Returns:
            dict: Set of attributes.
        """
        attr = {}

        if n_id in self.session.data.products or n_id in self.session.data.devices:
            attr.update({"available": (await self.onlineOffline(n_id))})
            if n_id in self.session.config.battery:
                battery = await self.getBattery(n_id)
                if battery is not None:
                    attr.update({"battery": str(battery) + "%"})
            if n_id in self.session.config.mode:
                attr.update({"mode": (await self.getMode(n_id))})
        return attr

    async def onlineOffline(self, n_id: str):
        """Check if device is online.

        Args:
            n_id (str): The id of the device.

        Returns:
            boolean: True/False if device online.
        """
        state = None

        try:
            data = self.session.data.devices[n_id]
            state = data["props"]["online"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def getMode(self, n_id: str):
        """Get sensor mode.

        Args:
            n_id (str): The id of the device

        Returns:
            str: The mode of the device.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[n_id]
            state = data["state"]["mode"]
            final = HIVETOHA[self.type].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getBattery(self, n_id: str):
        """Get device battery level.

        Args:
            n_id (str): The id of the device.

        Returns:
            str: Battery level of device.
        """
        state = None
        final = None

        try:
            data = self.session.data.devices[n_id]
            state = data["props"]["battery"]
            final = state
            await self.session.log.errorCheck(n_id, self.type, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final
