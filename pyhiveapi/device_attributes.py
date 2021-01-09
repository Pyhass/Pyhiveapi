"""Hive Device Attribute Module."""
from .helper.hive_data import Data
from .helper.hive_helper import HiveHelper as Helper
from .helper.logger import Logger


class Attributes:
    """Device Attributes Code."""

    def __init__(self):
        self.log = Logger()
        self.type = "Attribute"

    async def state_attributes(self, n_id, _type):
        """Get HA State Attributes"""
        attr = {}

        if n_id in Data.products or n_id in Data.devices:
            attr.update({"available": (await self.online_offline(n_id))})
            if n_id in Data.BATTERY:
                battery = await self.battery(n_id)
                if battery is not None:
                    attr.update({"battery": str(battery) + "%"})
            if n_id in Data.MODE:
                attr.update({"mode": (await self.get_mode(n_id))})
        return attr

    async def online_offline(self, n_id):
        """Check if device is online"""
        state = None

        try:
            data = Data.devices[n_id]
            state = data["props"]["online"]
        except KeyError as e:
            Helper.error(e)

        return state

    async def get_mode(self, n_id):
        """Get sensor mode."""
        state = None
        final = None

        try:
            data = Data.products[n_id]
            state = data["state"]["mode"]
            final = Data.HIVETOHA[self.type].get(state, state)
        except KeyError as e:
            Helper.error(e)

        return final

    async def battery(self, n_id):
        """Get device battery level."""
        state = None
        final = None

        try:
            data = Data.devices[n_id]
            state = data["props"]["battery"]
            final = state
            await self.log.error_check(n_id, self.type, state)
        except KeyError as e:
            Helper.error(e)

        return final
