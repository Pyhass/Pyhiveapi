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
        self.cameraBaseUrl = "prod.hcam.bgchtest.info"
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": f"{self.baseUrl}/cognito/login",
            "refresh": f"{self.baseUrl}/cognito/refresh-token",
            "holiday_mode": f"{self.baseUrl}/holiday-mode",
            "all": f"{self.baseUrl}/nodes/all?products=true&devices=true&actions=true",
            "alarm": f"{self.baseUrl}/security-lite?homeId=",
            "cameraImages": f"https://event-history-service.{self.cameraBaseUrl}/v1/events/cameras?latest=true&cameraId={{0}}",
            "cameraRecordings": f"https://event-history-service.{self.cameraBaseUrl}/v1/playlist/cameras/{{0}}/events/{{1}}.m3u8",
            "devices": f"{self.baseUrl}/devices",
            "products": f"{self.baseUrl}/products",
            "actions": f"{self.baseUrl}/actions",
            "nodes": f"{self.baseUrl}/nodes/{{0}}/{{1}}",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "weather": "https://weather.prod.bgchprod.info/weather",
        }
        self.timeout = 10
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }
        self.session = hiveSession
        self.websession = ClientSession() if websession is None else websession

    async def request(
        self, method: str, url: str, camera: bool = False, **kwargs
    ) -> ClientResponse:
        """Make a request."""
        data = kwargs.get("data", None)

        try:
            if camera:
                headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.session.tokens.tokenData['token']}",
                    "x-jwt-token": self.session.tokens.tokenData["token"],
                }
            else:
                headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "authorization": self.session.tokens.tokenData["token"],
                }
        except KeyError:
            if "sso" in url:
                pass
            else:
                raise NoApiToken

        async with self.websession.request(
            method, url, headers=headers, data=data
        ) as resp:
            await resp.text()
            if operator.contains(str(resp.status), "20"):
                return resp

        if resp.status == HTTP_UNAUTHORIZED:
            self.session.logger.error(
                f"Hive token has expired when calling {url} - "
                f"HTTP status is - {resp.status}"
            )
        elif url is not None and resp.status is not None:
            self.session.logger.error(
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
        """Refresh tokens - DEPRECATED NOW BY AWS TOKEN MANAGEMENT."""
        url = self.urls["refresh"]
        if self.session is not None:
            tokens = self.session.tokens.tokenData
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) + '" ' for i, t in tokens.items())
            )
            + "}"
        )
        try:
            await self.request("post", url, data=jsc)

            if self.json_return["original"] == 200:
                info = self.json_return["parsed"]
                if "token" in info:
                    await self.session.updateTokens(info)
                    self.baseUrl = info["platform"]["endpoint"]
                    self.cameraBaseUrl = info["platform"]["cameraPlatform"]
                return True
        except (ConnectionError, OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def getAll(self):
        """Build and query all endpoint."""
        json_return = {}
        url = self.urls["all"]
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getAlarm(self):
        """Build and query alarm endpoint."""
        json_return = {}
        url = self.urls["alarm"] + self.session.config.homeID
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getCameraImage(self, device):
        """Build and query alarm endpoint."""
        json_return = {}
        url = self.urls["cameraImages"].format(device["props"]["hardwareIdentifier"])
        try:
            resp = await self.request("get", url, True)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getCameraRecording(self, device, eventId):
        """Build and query alarm endpoint."""
        json_return = {}
        url = self.urls["cameraRecordings"].format(
            device["props"]["hardwareIdentifier"], eventId
        )
        try:
            resp = await self.request("get", url, True)
            recUrl = await resp.text()
            json_return.update({"original": resp.status})
            json_return.update({"parsed": recUrl.split("\n")[3]})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getDevices(self):
        """Call the get devices endpoint."""
        json_return = {}
        url = self.urls["devices"]
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getProducts(self):
        """Call the get products endpoint."""
        json_return = {}
        url = self.urls["products"]
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getActions(self):
        """Call the get actions endpoint."""
        json_return = {}
        url = self.urls["actions"]
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def motionSensor(self, sensor, fromepoch, toepoch):
        """Call a way to get motion sensor info."""
        json_return = {}
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
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def getWeather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        json_return = {}
        t_url = self.urls["weather"] + weather_url
        url = t_url.replace(" ", "%20")
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError, ConnectionError):
            await self.error()

        return json_return

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

    async def setAlarm(self, **kwargs):
        """Set the state of the alarm."""
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) + '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = f"{self.urls['alarm']}{self.session.config.homeID}"
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
        url = self.urls["actions"] + "/" + n_id
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
        raise web_exceptions.HTTPError

    async def isFileBeingUsed(self):
        """Check if running in file mode."""
        if self.session.config.file:
            raise FileInUse()
