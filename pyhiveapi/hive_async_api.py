"""Hive API Module."""
from .hive_exceptions import FileInUse, NoApiToken

from aiohttp import ClientSession, ClientResponse
from aiohttp.web import HTTPBadRequest
from pyquery import PyQuery
from datetime import datetime
from typing import Optional
from .custom_logging import Logger
from .hive_data import Data

import operator


class Hive_Async:
    """Hive API Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Hive API initialisation."""
        self.log = Logger()
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": "https://beekeeper.hivehome.com/1.0/cognito/login",
            "refresh": "https://beekeeper.hivehome.com/1.0/cognito/refresh-token",
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
        api_sucessful = False
        count = 0
        await self.log.log(
            'API', 'API', "Request is - {0}:{1}  Body is {2}", info=[method, url, data])

        while not api_sucessful:
            try:
                self.headers.update(
                    {"authorization": Data.s_tokens["token"]})
            except KeyError:
                self.log.log('API', 'API', 'ERROR - NO API TOKEN')
                raise NoApiToken

            async with self.websession.request(method, url, headers=self.headers, data=data) as resp:
                if method != "delete":
                    await resp.json(content_type=None)
                    self.json_return.update({"original": resp.status})
                    self.json_return.update({"parsed": await resp.json(content_type=None)})
                    await self.log.log('API', 'API', "Response is - {0}", info=[str(resp.status)])

            if operator.contains(str(resp.status), '20'):
                api_sucessful = True
            elif resp.status == 401 and count < 2:
                await self.refreshTokens()
                count += 1
            else:
                raise HTTPBadRequest

    async def refreshTokens(self):
        """Refresh tokens"""
        url = self.urls["refresh"]
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) +
                 '" ' for i, t in Data.s_tokens.items())
            )
            + "}"
        )
        try:
            await self.request('post', url,  data=jsc)

            if self.json_return["original"] == 200:
                info = self.json_return["parsed"]
                if "token" in info:
                    Data.s_tokens.update({"token": info["token"]})
                    Data.s_tokens.update(
                        {"refreshToken": info["refreshToken"]})
                    Data.s_tokens.update(
                        {"accessToken": info["accessToken"]})

                    self.urls.update({"base": info["platform"]["endpoint"]})
                    self.urls.update(
                        {"camera": info["platform"]["cameraPlatform"]})

                    Data.s_token_update = datetime.now()
                    Data.s_entity_update_flag = "N"
                return True
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getLoginInfo(self):
        """Get login properties to make the login request."""
        url = self.urls['properties']
        try:
            html = await self.request('get', url)
            pq = PyQuery(html)
            poolID = ''
            clientID = ''
            region = ''
            return poolID, clientID, region
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

    async def getAll(self):
        """Build and query all endpoint."""
        url = self.urls["base"] + self.urls["all"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_devices(self):
        """Call the get devices endpoint."""
        url = self.urls["base"] + self.urls["devices"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_products(self, token):
        """Call the get products endpoint."""
        url = self.urls["base"] + self.urls["products"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_actions(self):
        """Call the get actions endpoint."""
        url = self.urls["base"] + self.urls["actions"]
        try:
            await self.request('get', url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def motion_sensor(self, token, sensor, fromepoch, toepoch):
        """Call a way to get motion sensor info."""
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

    async def set_state(self, n_type, n_id, **kwargs):
        """Set the state of a Device."""
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
            await self.is_file_being_used()
            await self.request('post', url,  data=jsc)
        except (FileInUse, IOError, RuntimeError, ConnectionError)as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}
            else:
                await self.error()

        return self.json_return

    async def set_action(self, n_id, data):
        """Set the state of a Action."""
        jsc = data
        url = self.urls["base"] + self.urls["actions"] + "/" + n_id
        try:
            await self.is_file_being_used()
            await self.request('put', url,  data=jsc)
        except (FileInUse, IOError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}
            else:
                await self.error()

        return self.json_return

    async def error(self):
        """An error has occured iteracting wth the Hive API."""
        self.json_return.update({"original": "Error making API call"})
        self.json_return.update({"parsed": "Error making API call"})
        await self.log.log("API_ERROR", "ERROR", "Error attempting API call")

    async def is_file_being_used(self):
        """Check if running in file mode."""
        if Data.s_file:
            raise FileInUse()
