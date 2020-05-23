"""Hive Weather Module."""
import asyncio
from .custom_logging import Logger
from .hive_data import Data


class Weather:
    """Hive Weather Code."""

    def __init__(self):
        self.log = Logger()

    async def temperature(self, device):
        """Get Hive Weather temperature."""
        await self.log.log("Weather", "Temp", "Getting outside temp.")
        return Data.w_temperature_value
