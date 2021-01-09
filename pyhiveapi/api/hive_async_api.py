"""Hive API Module."""
import json
import operator
from datetime import datetime
from typing import Optional

import urllib3
from aiohttp import ClientResponse, ClientSession, web_exceptions
from pyquery import PyQuery

from pyhiveapi.helper.const import HTTP_UNAUTHORIZED

from ..helper.hive_data import Data
from ..helper.hive_exceptions import FileInUse, NoApiToken
from ..helper.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HiveAsync:
    """Hive API Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Hive API initialisation."""
        self.log = Logger()
        self.baseUrl = "https://beekeeper.hivehome.com/1.0"
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": self.baseUrl + "/cognito/login",
            "refresh": self.baseUrl + "/cognito/refresh-token",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "weather": "https://weather.prod.bgchprod.info/weather",
            "holiday_mode": "/holiday-mode",
            "all": self.baseUrl
            + "/nodes/all?products=true&devices=true&actions=true",
            "devices": self.baseUrl + "/devices",
            "products": self.baseUrl + "/products",
            "actions": self.baseUrl + "/actions",
            "nodes": self.baseUrl + "/nodes/{0}/{1}",
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
        websession = Data.haWebsession if websession is None else websession
        self.websession = ClientSession() if websession is None else websession

    async def request(self, method: str, url: str, **kwargs) -> ClientResponse:
        """Make a request."""
        data = kwargs.get("data", None)
        await self.log.log(
            "No_ID",
            "API",
            "Request is - {0}:{1}  Body is {2}",
            info=[method, url, data],
        )

        try:
            self.headers.update({"authorization": Data.tokens["token"]})
        except KeyError:
            if "sso" in url:
                pass
            else:
                self.log.log("No_ID", "API", "ERROR - NO API TOKEN")
                raise NoApiToken

        async with self.websession.request(
            method, url, headers=self.headers, data=data
        ) as resp:
            await resp.json(content_type=None)
            self.json_return.update({"original": resp.status})
            self.json_return.update(
                {"parsed": await resp.json(content_type=None)}
            )

        if operator.contains(str(resp.status), "20"):
            await self.log.log(
                "API", "API", "Response is - {0}", info=[str(resp.status)]
            )
        elif resp.status == HTTP_UNAUTHORIZED:
            await self.log.error_check(
                "No_ID", "ERROR", "Failed_API", resp=resp["original"]
            )

        else:
            self.log.LOGGER.error(
                f"Something has gone wrong calling {url} - "
                f"HTTP status is - {resp.status}"
            )

    async def refreshTokens(self):
        """Refresh tokens"""
        url = self.urls["refresh"]
        jsc = (
            "{"
            + ",".join(
                (
                    '"' + str(i) + '": ' '"' + str(t) + '" '
                    for i, t in Data.tokens.items()
                )
            )
            + "}"
        )
        try:
            await self.request("post", url, data=jsc)

            if self.json_return["original"] == 200:
                info = self.json_return["parsed"]
                if "token" in info:
                    Data.tokens.update({"token": info["token"]})
                    Data.tokens.update({"refreshToken": info["refreshToken"]})
                    Data.tokens.update({"accessToken": info["accessToken"]})

                    self.urls.update({"base": info["platform"]["endpoint"]})
                    self.urls.update(
                        {"camera": info["platform"]["cameraPlatform"]}
                    )
                    Data.tokenCreated = datetime.now()
                return True
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getLoginInfo(self):
        """Get login properties to make the login request."""
        url = self.urls["properties"]
        try:
            data = await self.request("get", url)
            html = PyQuery(data.content)
            json_data = json.loads(
                '{"'
                + (html("script:first").text())
                .replace(",", ', "')
                .replace("=", '":')
                .replace("window.", "")
                + "}"
            )

            Data.loginData.update({"UPID": json_data["HiveSSOPoolId"]})
            Data.loginData.update(
                {"CLIID": json_data["HiveSSOPublicCognitoClientId"]}
            )
            Data.loginData.update({"REGION": json_data["HiveSSOPoolId"]})
            return Data.loginData
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

    async def getAll(self):
        """Build and query all endpoint."""
        url = self.urls["all"]
        try:
            await self.request("get", url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getDevices(self):
        """Call the get devices endpoint."""
        url = self.urls["devices"]
        try:
            await self.request("get", url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_products(self, token):
        """Call the get products endpoint."""
        url = self.urls["products"]
        try:
            await self.request("get", url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_actions(self):
        """Call the get actions endpoint."""
        url = self.urls["actions"]
        try:
            await self.request("get", url)
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
            await self.request("get", url)
        except (IOError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_weather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        t_url = self.urls["weather"] + weather_url
        url = t_url.replace(" ", "%20")
        try:
            await self.request("get", url)
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            await self.error()

        return self.json_return

    async def set_state(self, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        jsc = (
            "{"
            + ",".join(
                (
                    '"' + str(i) + '": ' '"' + str(t) + '" '
                    for i, t in kwargs.items()
                )
            )
            + "}"
        )

        url = self.urls["nodes"].format(n_type, n_id)
        try:
            await self.is_file_being_used()
            await self.request("post", url, data=jsc)
        except (FileInUse, IOError, RuntimeError, ConnectionError) as e:
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
            await self.request("put", url, data=jsc)
        except (FileInUse, IOError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}
            else:
                await self.error()

        return self.json_return

    async def error(self):
        """An error has occured iteracting wth the Hive API."""
        await self.log.log("API_ERROR", "ERROR", "Error attempting API call")
        raise web_exceptions.HTTPError

    async def is_file_being_used(self):
        """Check if running in file mode."""
        if Data.file:
            raise FileInUse()
