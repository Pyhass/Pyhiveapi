"""Hive API Module."""

import asyncio
import json
import logging
import time

import requests
from aiohttp import ClientResponse, ClientSession, ClientTimeout, web_exceptions
from pyquery import PyQuery

from ..helper.const import HTTP_FORBIDDEN, HTTP_OK, HTTP_UNAUTHORIZED
from ..helper.hive_exceptions import FileInUse, HiveApiError, HiveAuthError, NoApiToken

_LOGGER = logging.getLogger(__name__)


class HiveApiAsync:
    """Hive API Code."""

    def __init__(self, hive_session=None, websession: ClientSession | None = None):
        """Hive API initialisation."""
        self.base_url = "https://beekeeper.hivehome.com/1.0"
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": f"{self.base_url}/cognito/login",
            "refresh": f"{self.base_url}/cognito/refresh-token",
            "holiday_mode": f"{self.base_url}/holiday-mode",
            "all": f"{self.base_url}/nodes/all?products=true&devices=true&actions=true",
            "devices": f"{self.base_url}/devices",
            "products": f"{self.base_url}/products",
            "actions": f"{self.base_url}/actions",
            "nodes": f"{self.base_url}/nodes/{{0}}/{{1}}",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "weather": "https://weather.prod.bgchprod.info/weather",
        }
        self.timeout = 5
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }
        self.session = hive_session
        self.websession = ClientSession() if websession is None else websession

    async def request(self, method: str, url: str, **kwargs) -> ClientResponse:
        """Make a request."""
        _LOGGER.debug("API %s request to %s", method.upper(), url)
        data = kwargs.get("data", None)

        headers = {
            "content-type": "application/json",
            "Accept": "*/*",
            "User-Agent": "Hive/12.04.0 iOS/18.3.1 Apple",
        }
        try:
            headers["Authorization"] = self.session.tokens.token_data["token"]
        except KeyError as exc:
            if "sso" in url:
                pass
            else:
                raise NoApiToken from exc

        auth_token = headers.get("Authorization", "")
        _LOGGER.debug(
            "Using token (len=%d, tail=…%s)",
            len(auth_token),
            auth_token[-4:] if len(auth_token) >= 4 else auth_token,  # noqa: PLR2004
        )

        timeout = ClientTimeout(total=self.timeout)
        req_start = time.monotonic()
        async with self.websession.request(
            method, url, headers=headers, data=data, timeout=timeout
        ) as resp:
            resp_body = await resp.text()
            req_duration = time.monotonic() - req_start
            _LOGGER.debug(
                "API %s %s completed in %.2fs — HTTP %s",
                method.upper(),
                url,
                req_duration,
                resp.status,
            )
            if str(resp.status).startswith("20"):
                return resp

        if resp.status in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
            _LOGGER.error(
                "Hive token rejected calling %s - HTTP %s — response: %s",
                url,
                resp.status,
                resp_body[:200],
            )
            raise HiveAuthError(
                f"Token expired or forbidden calling {url} — HTTP {resp.status}"
            )
        if url is not None and resp.status is not None:
            _LOGGER.error(
                "Something has gone wrong calling %s - HTTP status is - %s — response: %s",
                url,
                resp.status,
                resp_body[:200],
            )

        raise HiveApiError

    def get_login_info(self):
        """Get login properties to make the login request."""
        url = "https://sso.hivehome.com/"

        data = requests.get(url=url, timeout=self.timeout)
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

    async def refresh_tokens(self):
        """Refresh tokens - DEPRECATED NOW BY AWS TOKEN MANAGEMENT."""
        url = self.urls["refresh"]
        tokens = self.session.tokens.token_data if self.session is not None else {}
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": "' + str(t) + '" ' for i, t in tokens.items())
            )
            + "}"
        )
        try:
            await self.request("post", url, data=jsc)

            if self.json_return["original"] == HTTP_OK:
                info = self.json_return["parsed"]
                if "token" in info:
                    await self.session.update_tokens(info)
                    # pylint: disable-next=invalid-sequence-index
                    self.base_url = info["platform"]["endpoint"]
                return True
        except (ConnectionError, OSError, RuntimeError, ZeroDivisionError):
            await self.error()

        return self.json_return

    async def get_all(self):
        """Build and query all endpoint."""
        json_return = {}
        url = self.urls["all"]
        try:
            resp = await self.request("get", url)
            json_return.update({"original": resp.status})
            json_return.update({"parsed": await resp.json(content_type=None)})
        except asyncio.TimeoutError:
            _LOGGER.warning("Hive API request timed out fetching all nodes.")
            raise
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
            self.base_url
            + "/products"
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
        _LOGGER.debug("set_state - Setting state for %s/%s: %s", n_type, n_id, kwargs)
        json_return = {}
        jsc = json.dumps(kwargs)

        url = self.urls["nodes"].format(n_type, n_id)
        try:
            await self.is_file_being_used()
            resp = await self.request("post", url, data=jsc)
            json_return["original"] = resp.status
            json_return["parsed"] = await resp.json(content_type=None)
        except FileInUse:
            return {"original": "file"}
        except (OSError, RuntimeError, ConnectionError):
            await self.error()

        return json_return

    async def set_action(self, n_id, data):
        """Set the state of a Action."""
        _LOGGER.debug("Setting action %s", n_id)
        json_return = {}
        jsc = data
        url = self.urls["actions"] + "/" + n_id
        try:
            await self.is_file_being_used()
            resp = await self.request("put", url, data=jsc)
            json_return["original"] = resp.status
            json_return["parsed"] = await resp.json(content_type=None)
        except FileInUse:
            return {"original": "file"}
        except (OSError, RuntimeError, ConnectionError):
            await self.error()

        return json_return

    async def error(self):
        """An error has occurred interacting with the Hive API."""
        _LOGGER.error("HTTP error occurred during Hive API interaction.")
        raise web_exceptions.HTTPError

    async def is_file_being_used(self):
        """Check if running in file mode."""
        if self.session.config.file:
            raise FileInUse()
