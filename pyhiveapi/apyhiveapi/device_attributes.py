"""Hive Device Attribute Module."""
from .helper.const import HIVETOHA
from .helper.logger import Logger


class Attributes:
    """Device Attributes Code."""

    def __init__(self, session=None):
        """Initialise attributes."""
        self.session = session
        self.session.log = Logger()
        self.type = "Attribute"

    async def state_attributes(self, n_id, _type):
        """Get HA State Attributes."""
        attr = {}

        if n_id in self.session.data.products or n_id in self.session.data.devices:
            attr.update({"available": (await self.online_offline(n_id))})
            if n_id in self.session.config.battery:
                battery = await self.battery(n_id)
                if battery is not None:
                    attr.update({"battery": str(battery) + "%"})
            if n_id in self.session.config.mode:
                attr.update({"mode": (await self.get_mode(n_id))})
        return attr

    async def online_offline(self, n_id):
        """Check if device is online."""
        state = None

        try:
            data = self.session.data.devices[n_id]
            state = data["props"]["online"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_mode(self, n_id):
        """Get sensor mode."""
        state = None
        final = None

        try:
            data = self.session.data.products[n_id]
            state = data["state"]["mode"]
            final = HIVETOHA[self.type].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def battery(self, n_id):
        """Get device battery level."""
        state = None
        final = None

        try:
            data = self.session.data.devices[n_id]
            state = data["props"]["battery"]
            final = state
            await self.session.log.error_check(n_id, self.type, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final
