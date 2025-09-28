"""Hive API Module."""

import json
from typing import Optional

import requests
import urllib3
from aiohttp import ClientResponse, ClientSession, web_exceptions
from pyquery import PyQuery

from ..helper.const import HTTP_UNAUTHORIZED
from ..helper.hive_exceptions import FileInUse, HiveApiError, NoApiToken

# from ..session import HiveSession

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HiveApiAsync:
    """Hive API Code."""

    def __init__(
        self,
        hive_session=None,
        websession: Optional[ClientSession] = None,
    ) -> None:
        """Hive API initialisation."""
        self.base_url = "https://beekeeper.hivehome.com/1.0"
        self.camera_base_url = "prod.hcam.bgchtest.info"
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": f"{self.base_url}/cognito/login",
            "refresh": f"{self.base_url}/cognito/refresh-token",
            "holiday_mode": f"{self.base_url}/holiday-mode",
            "all": f"{self.base_url}/nodes/all?products=true&devices=true&actions=true",
            "alarm": f"{self.base_url}/security-lite?homeId=",
            "camera_images": f"https://event-history-service.{self.camera_base_url}"
            "/v1/events/cameras?latest=true&cameraId={{0}}",
            "camera_recordings": f"https://event-history-service.{self.camera_base_url}"
            "/v1/playlist/cameras/{{0}}/events/{{1}}.m3u8",
            "devices": f"{self.base_url}/devices",
            "products": f"{self.base_url}/products",
            "actions": f"{self.base_url}/actions",
            "nodes": f"{self.base_url}/nodes/{{0}}/{{1}}",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "weather": "https://weather.prod.bgchprod.info/weather",
        }
        self.timeout = 10
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }
        self.session = hive_session
        self.websession = websession

    async def request(
        self, method: str, url: str, camera: bool = False, **kwargs
    ) -> ClientResponse:
        """Make a request."""
        data = kwargs.get("data", None)

        headers = {}
        try:
            if camera:
                headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.session.tokens.tokenData['token']}",
                    "x-jwt-token": self.session.tokens.tokenData["token"],
                    "User-Agent": "Hive/12.04.0 iOS/18.3.1 Apple",
                }
            else:
                headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "Authorization": self.session.tokens.tokenData["token"],
                    "User-Agent": "Hive/12.04.0 iOS/18.3.1 Apple",
                }
        except KeyError:
            if "sso" not in url:
                raise NoApiToken from None

        async with self.websession.request(
            method, url, headers=headers, data=data
        ) as resp:
            await resp.text()
            if str(resp.status).startswith("20"):
                return resp

        if resp.status == HTTP_UNAUTHORIZED:
            self.session.logger.error(
                "Hive token has expired when calling %s - HTTP status is - %d",
                url,
                resp.status,
            )
        else:
            self.session.logger.error(
                "Something has gone wrong calling %s - HTTP status is - %d",
                url,
                resp.status,
            )

        raise HiveApiError

    def get_login_info(self):
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

        login_data = {}
        login_data.update({"UPID": json_data["HiveSSOPoolId"]})
        login_data.update({"CLIID": json_data["HiveSSOPublicCognitoClientId"]})
        login_data.update({"REGION": json_data["HiveSSOPoolId"]})
        return login_data

    # async def refresh_tokens(self) -> bool:
    #     """Refresh tokens - DEPRECATED NOW BY AWS TOKEN MANAGEMENT."""
    #     url = self.urls["refresh"]
    #     if self.session is None:
    #         raise NoSessionError from None
    #     tokens = self.session.tokens.token_data
    #     jsc = json.dumps({str(i): str(t) for i, t in tokens.items()})
    #     try:
    #         await self.request("POST", url, data=jsc)
    #         if self.json_return["original"] == 200:
    #             info = self.json_return["parsed"]
    #             if "token" in info:
    #                 await self.session.update_tokens(info)
    #                 self.base_url = info["platform"]["endpoint"]
    #                 self.camera_base_url = info["platform"]["cameraPlatform"]
    #             return True
    #     except (ConnectionError, OSError, RuntimeError, ZeroDivisionError):
    #         await self.error()

    #     return self.json_return

    async def get_all(self):
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

    async def get_alarm(self):
        """Build and query alarm endpoint."""
        json_return = {}
        url = self.urls["alarm"] + self.session.config.home_id
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def get_camera_image(self, device):
        """Build and query alarm endpoint."""
        json_return = {}
        url = self.urls["camera_images"].format(device["props"]["hardwareIdentifier"])
        try:
            resp = await self.request("get", url, True)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def get_camera_recording(self, device, event_id):
        """Build and query alarm endpoint."""
        json_return = {}
        url = self.urls["camera_recordings"].format(
            device["props"]["hardwareIdentifier"], event_id
        )
        try:
            resp = await self.request("get", url, True)
            rec_url = await resp.text()
            json_return.update({"original": resp.status})
            json_return.update({"parsed": rec_url.split("\n")[3]})
        except (OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return json_return

    async def get_devices(self):
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

    async def get_products(self):
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

    async def get_actions(self):
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

    async def motion_sensor(self, sensor, fromepoch, toepoch):
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

    async def get_weather(self, weather_url):
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

    async def set_state(self, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        json_return = {}
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) + '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = self.urls["nodes"].format(n_type, n_id)
        try:
            await self.is_file_being_used()
            resp = await self.request("post", url, data=jsc)
            json_return["original"] = resp.status
            json_return["parsed"] = await resp.json(content_type=None)
        except (FileInUse, OSError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}

            await self.error()

        return json_return

    async def set_alarm(self, **kwargs):
        """Set the state of the alarm."""
        json_return = {}
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) + '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = f"{self.urls['alarm']}{self.session.config.home_id}"
        try:
            await self.is_file_being_used()
            resp = await self.request("post", url, data=jsc)
            json_return["original"] = resp.status
            json_return["parsed"] = await resp.json(content_type=None)
        except (FileInUse, OSError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}

            await self.error()

        return json_return

    async def set_action(self, n_id, data):
        """Set the state of a Action."""
        jsc = data
        url = self.urls["actions"] + "/" + n_id
        try:
            await self.is_file_being_used()
            await self.request("put", url, data=jsc)
        except (FileInUse, OSError, RuntimeError, ConnectionError) as e:
            if e.__class__.__name__ == "FileInUse":
                return {"original": "file"}

            await self.error()

        return self.json_return

    async def error(self):
        """An error has occurred interacting with the Hive API."""
        raise web_exceptions.HTTPError

    async def is_file_being_used(self):
        """Check if running in file mode."""
        if self.session.config.file:
            raise FileInUse()

    async def close(self):
        """Close the aiohttp session."""
        if self.websession and not self.websession.closed:
            await self.websession.close()

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        await self.close()
