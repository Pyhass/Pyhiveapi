"""Hive API Module."""

import json
import logging

import requests
import urllib3
from pyquery import PyQuery

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)


class HiveApi:
    """Hive API Code."""

    def __init__(self, hive_session=None, token=None):
        """Hive API initialisation."""
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
        self.timeout = 5
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }
        self.session = hive_session
        self.token = token
        self.headers = {
            "content-type": "application/json",
            "Accept": "*/*",
            "authorization": "",
        }

    def request(self, http_method, url, jsc=None):
        """Make API request."""
        _LOGGER.debug("request - Making %s request to: %s", http_method, url)
        if jsc:
            _LOGGER.debug("request - Request payload: %s", jsc)

        if self.session is not None:
            self.headers["authorization"] = self.session.tokens.token_data["token"]
        else:
            self.headers["authorization"] = self.token

        _LOGGER.debug(
            "request - Request headers: %s",
            {k: v for k, v in self.headers.items() if k.lower() != "authorization"},
        )

        try:
            if http_method == "GET":
                return requests.get(
                    url=url, headers=self.headers, data=jsc, timeout=self.timeout
                )
            if http_method == "POST":
                return requests.post(
                    url=url, headers=self.headers, data=jsc, timeout=self.timeout
                )
            raise ValueError(f"Unsupported request type: {http_method}")
        except Exception as e:
            _LOGGER.error("Request failed: %s", e)
            raise

    def get_login_info(self):
        """Get login properties to make the login request."""
        _LOGGER.debug(
            "get_login_info - Fetching login info from: %s", self.urls["properties"]
        )
        url = self.urls["properties"]
        try:
            data = requests.get(url=url, verify=False, timeout=self.timeout)
            _LOGGER.debug(
                "get_login_info - Login info response status: %s", data.status_code
            )
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
            _LOGGER.debug("get_login_info - Login info extracted successfully")
            return login_data
        except (
            OSError,
            RuntimeError,
            ZeroDivisionError,
            json.JSONDecodeError,
            KeyError,
        ) as e:
            _LOGGER.error("Failed to get login info: %s", str(e))
            self.error()
            return None

    def get_all(self):
        """Build and query all endpoint."""
        _LOGGER.debug("get_all - Fetching all devices/products/actions from Hive API")
        json_return = {}
        url = self.urls["base"] + self.urls["all"]
        try:
            info = self.request("GET", url)
            if info is not None:
                json_return.update({"original": info.status_code})
                json_return.update({"parsed": info.json()})
                _LOGGER.debug(
                    "get_all - All data fetch successful, status: %s", info.status_code
                )
            else:
                _LOGGER.error("Failed to get response from all endpoint")
        except (OSError, RuntimeError, ZeroDivisionError, json.JSONDecodeError) as e:
            _LOGGER.error("Failed to fetch all data: %s", str(e))
            self.error()

        return json_return

    def get_devices(self):
        """Call the get devices endpoint."""
        url = self.urls["base"] + self.urls["devices"]
        try:
            response = self.request("GET", url)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_products(self):
        """Call the get products endpoint."""
        url = self.urls["base"] + self.urls["products"]
        try:
            response = self.request("GET", url)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_actions(self):
        """Call the get actions endpoint."""
        url = self.urls["base"] + self.urls["actions"]
        try:
            response = self.request("GET", url)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def motion_sensor(self, sensor, fromepoch, toepoch):
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
            response = self.request("GET", url)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_weather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        t_url = self.urls["weather"] + weather_url
        url = t_url.replace(" ", "%20")
        try:
            response = self.request("GET", url)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError, ConnectionError):
            self.error()

        return self.json_return

    def set_state(self, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        _LOGGER.debug(
            "set_state - Setting state for device %s (type: %s): %s",
            n_id,
            n_type,
            kwargs,
        )
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": "' + str(t) + '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = self.urls["base"] + self.urls["nodes"].format(n_type, n_id)

        try:
            response = self.request("POST", url, jsc)
            if response is not None:
                self.json_return.update({"original": response.status_code})
                self.json_return.update({"parsed": response.json()})
                _LOGGER.debug(
                    "set_state - State set successfully for %s, status: %s",
                    n_id,
                    response.status_code,
                )
            else:
                _LOGGER.error("Failed to set state for %s - no response", n_id)
        except (
            OSError,
            RuntimeError,
            ZeroDivisionError,
            ConnectionError,
            json.JSONDecodeError,
        ) as e:
            _LOGGER.error("Failed to set state for %s: %s", n_id, str(e))
            self.error()

        return self.json_return

    def set_action(self, n_id, data):
        """Set the state of a Action."""
        jsc = data
        url = self.urls["base"] + self.urls["actions"] + "/" + n_id
        try:
            response = self.request("POST", url, jsc)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError, ConnectionError):
            self.error()

        return self.json_return

    def error(self):
        """An error has occurred interacting with the Hive API."""
        _LOGGER.error("API error occurred - returning error response")
        self.json_return.update({"original": "Error making API call"})
        self.json_return.update({"parsed": "Error making API call"})


class UnknownConfig(Exception):
    """Unknown API config."""
