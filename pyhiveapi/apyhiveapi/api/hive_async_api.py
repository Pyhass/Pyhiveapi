"""Hive API Module."""

import json
import operator
from typing import Optional

import requests
import urllib3
from aiohttp import ClientResponse, ClientSession, web_exceptions
from pyquery import PyQuery

from ..helper.const import HTTP_UNAUTHORIZED
from ..helper.hive_exceptions import FileInUse, NoApiToken

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HiveApiAsync:
    """Hive API Code."""

    def __init__(self, hiveSession=None, websession: Optional[ClientSession] = None):
        """Hive API initialisation."""
        self.baseUrl = "https://beekeeper.hivehome.com/1.0"
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": self.baseUrl + "/cognito/login",
            "refresh": self.baseUrl + "/cognito/refresh-token",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "weather": "https://weather.prod.bgchprod.info/weather",
            "holiday_mode": "/holiday-mode",
            "all": self.baseUrl + "/nodes/all?products=true&devices=true&actions=true",
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
        self.session = hiveSession
        self.websession = ClientSession() if websession is None else websession

    async def request(self, method: str, url: str, **kwargs) -> ClientResponse:
        """Make a request."""
        data = kwargs.get("data", None)
        await self.session.log.log(
            "No_ID",
            "API",
            "Request is - {0}:{1}  Body is {2}",
            info=[method, url, data],
        )

        try:
            self.headers.update({"authorization": self.session.tokens.token})
        except KeyError:
            if "sso" in url:
                pass
            else:
                self.session.log.log("No_ID", "API", "ERROR - NO API TOKEN")
                raise NoApiToken

        async with self.websession.request(
            method, url, headers=self.headers, data=data
        ) as resp:
            await resp.json(content_type=None)
            self.json_return.update({"original": resp.status})
            self.json_return.update({"parsed": await resp.json(content_type=None)})

        if operator.contains(str(resp.status), "20"):
            await self.session.log.log(
                "API", "API", "Response is - {0}", info=[str(resp.status)]
            )
        elif resp.status == HTTP_UNAUTHORIZED:
            await self.session.log.LOGGER.error(
                f"Hive token as expired when calling {url} - "
                f"HTTP status is - {resp.status}"
            )
        elif url is not None and resp.status is not None:
            await self.session.log.LOGGER.error(
                f"Something has gone wrong calling {url} - "
                f"HTTP status is - {resp.status}"
            )

    def getLoginInfo(self):
        """Get login properties to make the login request."""
        url = "https://sso.hivehome.com/"

        data = requests.get(url=url, verify=False, timeout=self.timeout)
        html = PyQuery(data.content)
        json_data = json.loads(
            '{"'
            + (html("script:first").text())
            .replace(",", ', "')
            .replace("=", '":')
            .replace("window.", "")
            + "}"
        )

        loginData = {}
        loginData.update({"UPID": json_data["HiveSSOPoolId"]})
        loginData.update({"CLIID": json_data["HiveSSOPublicCognitoClientId"]})
        loginData.update({"REGION": json_data["HiveSSOPoolId"]})
        return loginData

    async def refreshTokens(self):
        """Refresh tokens."""
        url = self.urls["refresh"]
        jsc = (
            "{"
            + ",".join(
                (
                    '"' + str(i) + '": ' '"' + str(t) + '" '
                    for i, t in self.session.tokens.token.items()
                )
            )
            + "}"
        )
        try:
            await self.request("post", url, data=jsc)

            if self.json_return["original"] == 200:
                info = self.json_return["parsed"]
                if "token" in info:
                    self.session.updateTokens(info)
                    self.urls.update({"base": info["platform"]["endpoint"]})
                    self.urls.update({"camera": info["platform"]["cameraPlatform"]})
                return True
        except (ConnectionError, OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getAll(self):
        """Build and query all endpoint."""
        url = self.urls["all"]
        try:
            await self.request("get", url)
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getDevices(self):
        """Call the get devices endpoint."""
        url = self.urls["devices"]
        try:
            await self.request("get", url)
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getProducts(self):
        """Call the get products endpoint."""
        url = self.urls["products"]
        try:
            await self.request("get", url)
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getActions(self):
        """Call the get actions endpoint."""
        url = self.urls["actions"]
        try:
            await self.request("get", url)
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def motionSensor(self, sensor, fromepoch, toepoch):
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
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getWeather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        t_url = self.urls["weather"] + weather_url
        url = t_url.replace(" ", "%20")
        try:
            await self.request("get", url)
        except (OSError, RuntimeError, ZeroDivisionError, ConnectionError):
            await self.error()

        return self.json_return

    async def setState(self, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) + '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = self.urls["nodes"].format(n_type, n_id)
        try:
            await self.isFileBeingUsed()
            await self.request("post", url, data=jsc)
        except (FileInUse, OSError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}
            else:
                await self.error()

        return self.json_return

    async def setAction(self, n_id, data):
        """Set the state of a Action."""
        jsc = data
        url = self.urls["base"] + self.urls["actions"] + "/" + n_id
        try:
            await self.isFileBeingUsed()
            await self.request("put", url, data=jsc)
        except (FileInUse, OSError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}
            else:
                await self.error()

        return self.json_return

    async def error(self):
        """An error has occurred iteracting with the Hive API."""
        await self.session.log.log("API_ERROR", "ERROR", "Error attempting API call")
        raise web_exceptions.HTTPError

    async def isFileBeingUsed(self):
        """Check if running in file mode."""
        if self.session.config.file:
            raise FileInUse()
