"""Hive API Module."""
import asyncio

from aiohttp import ClientSession, ClientResponse
from typing import Optional
from .custom_logging import Logger
# from pyhiveapi import Data


class Hive_Async:
    """Hive API Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Hive API initialisation."""
        self.log = Logger()
        self.urls = {
            "login": "https://beekeeper.hivehome.com/1.0/cognito/login",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "base": "https://beekeeper-uk.hivehome.com/1.0",
            "weather": "https://weather.prod.bgchprod.info/weather",
            "holiday_mode": "/holiday-mode",
            "all": "/nodes/all?products=true&devices=true&actions=true",
            "devices": "/devices",
            "products": "/products",
            "actions": "/actions",
            "nodes": "/nodes/{0}/{1}",
        }
        self.headers = {
            "content-type": "application/json",
            "Accept": "*/*",
        }
        self.timeout = 10
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }
        self.websession = ClientSession = websession

    async def request(self, method: str, url: str, **kwargs) -> ClientResponse:
        """Make a request."""
        data = kwargs.get('data', None)
        async with self.websession.request(method, url, headers=self.headers, data=data) as resp:
            if method != "delete":
                await resp.json(content_type=None)
                self.json_return.update({"original": resp.status})
                self.json_return.update({"parsed": await resp.json(content_type=None)})

    async def login(self, username, password):
        """Login to the Hive API."""
        url = self.urls["login"]
        j = '{{"username": "{0}", "password": "{1}"}}'.format(
            username, password)
        try:
            await self.request('post', url, data=j)
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def check_token(self, token):
        """Get a long lived token"""
        self.headers.update({"authorization": "Bearer " + token})
        self.headers.update({"X-Omnia-Client": "swagger"})
        self.headers.update({"X-MQTT-Client-ID": "swagger_MQTT_client"})
        self.headers.update(
            {"Accept": "application/vnd.alertme.zoo-6.6.0+json"})
        url = self.urls["long_lived"]
        try:
            await self.request('get', url)
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def create_token(self, token):
        """Get a long lived token"""
        self.headers.update({"authorization": "Bearer " + token})
        self.headers.update({"X-Omnia-Client": "swagger"})
        self.headers.update({"X-MQTT-Client-ID": "swagger_MQTT_client"})
        self.headers.update(
            {"Accept": "application/vnd.alertme.zoo-6.6.0+json"})
        url = self.urls["long_lived"]
        j = '{ "accessTokens": [ { "description": "HA access token" } ] }'
        try:
            await self.request('post', url,  data=j)
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def remove_token(self, token, token_id):
        """Get a long lived token"""
        self.headers.update({"X-Omnia-Access-Token": token})
        self.headers.update({"X-Omnia-Client": "swagger"})
        self.headers.update({"X-MQTT-Client-ID": "swagger_MQTT_client"})
        self.headers.update(
            {"Accept": "application/vnd.alertme.zoo-6.6.0+json"})
        url = self.urls["long_lived"] + "/" + token_id
        try:
            await self.request('delete', url)
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_all(self, token):
        """Build and query all endpoint."""
        self.headers.update({"authorization": token})
        url = self.urls["base"] + self.urls["all"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_devices(self, token):
        """Call the get devices endpoint."""
        self.headers.update({"authorization": token})
        url = self.urls["base"] + self.urls["devices"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_products(self, token):
        """Call the get products endpoint."""
        self.headers.update({"authorization": token})
        url = self.urls["base"] + self.urls["products"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_actions(self, token):
        """Call the get actions endpoint."""
        self.headers.update({"authorization": token})
        url = self.urls["base"] + self.urls["actions"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def motion_sensor(self, token, sensor, fromepoch, toepoch):
        """Call a way to get motion sensor info."""
        self.headers.update({"authorization": token})
        url = (
            self.urls["base"]
            + self.urls["products"]
            + "/"
            + sensor["type"]
            + "/"
            + sensor["id"]
            + "/events?from="
            + str(fromepoch)
            + "&to="
            + str(toepoch)
        )
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_weather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        t_url = self.urls["weather"] + weather_url
        url = t_url.replace(" ", "%20")
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            await self.error()

        return self.json_return

    async def set_state(self, token, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        self.headers.update({"authorization": token})
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) +
                 '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = self.urls["base"] + self.urls["nodes"].format(n_type, n_id)
        try:
            await self.request('post', url,  data=jsc)
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            await self.error()

        return self.json_return

    async def set_action(self, token, n_id, data):
        """Set the state of a Action."""
        self.headers.update({"authorization": token})
        jsc = data
        url = self.urls["base"] + self.urls["actions"] + "/" + n_id
        try:
            await self.request('put', url,  data=jsc)
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            await self.error()

        return self.json_return

    async def error(self):
        """An error has occured iteracting wth the Hive API."""
        self.json_return.update({"original": "Error making API call"})
        self.json_return.update({"parsed": "Error making API call"})
        await self.log.log("API_ERROR", "ERROR", "Error attempting API call")
