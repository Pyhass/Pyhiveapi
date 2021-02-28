"""Hive API Module."""
import asyncio

from aiohttp import ClientSession

from .hive_async_api import HiveApiAsync


class HiveApi:
    """Hive API Code."""

    def __init__(self):
        """Hive API initialisation."""
        self.session = ClientSession()
        self.loop = asyncio.get_event_loop()
        self.asyncAPI = HiveApiAsync(self.session)

    def getLoginInfo(self):
        """Get login properties to make the login request."""
        result = self.asyncAPI.getLoginInfo()
        return result

    def refreshTokens(self):
        """Get new session tokens."""
        result = self.loop.run_until_complete(self.asyncAPI.refreshTokens())
        return result

    def getAllData(self):
        """Build and query all endpoint."""
        result = self.loop.run_until_complete(self.asyncAPI.getAll())
        return result

    def getDevices(self):
        """Call the get devices endpoint."""
        result = self.loop.run_until_complete(self.asyncAPI.getDevices())
        return result

    def getProducts(self):
        """Call the get products endpoint."""
        result = self.loop.run_until_complete(self.asyncAPI.getProducts())
        return result

    def getActions(self):
        """Call the get actions endpoint."""
        result = self.loop.run_until_complete(self.asyncAPI.getActions())
        return result

    def motionSensor(self, sensor, fromepoch, toepoch):
        """Call a way to get motion sensor info."""
        result = self.loop.run_until_complete(
            self.asyncAPI.motionSensor(sensor, fromepoch, toepoch)
        )
        return result

    def getWeather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        result = self.loop.run_until_complete(self.asyncAPI.getWeather(weather_url))
        return result

    def setState(self, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        result = self.loop.run_until_complete(self.asyncAPI.setState(n_type, n_id))
        return result

    def setAction(self, n_id, data):
        """Set the state of a Action."""
        result = self.loop.run_until_complete(self.asyncAPI.setAction(n_id, data))
        return result
