"""Hive API Module."""

import json
from typing import Any, Dict, Optional

from pyquery import PyQuery
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HiveApi:
    """Hive API Code."""

    def __init__(self, hive_session=None, websession=None, token=None):
        """Hive API initialisation."""
        self.camera_base_url = "prod.hcam.bgchtest.info"
        self.urls = {
            "properties": "https://sso.hivehome.com/",
            "login": "https://beekeeper.hivehome.com/1.0/cognito/login",
            "refresh": "https://beekeeper.hivehome.com/1.0/cognito/refresh-token",
            "long_lived": "https://api.prod.bgchprod.info/omnia/accessTokens",
            "base": "https://beekeeper-uk.hivehome.com/1.0",
            "weather": "https://weather.prod.bgchprod.info/weather",
            "holiday_mode": "/holiday-mode",
            "all": "/nodes/all?products=true&devices=true&actions=true",
            "alarm": "/security-lite?homeId=",
            "cameraImages": f"https://event-history-service.{self.camera_base_url}" \
                "/v1/events/cameras?latest=true&cameraId={{0}}",
            "cameraRecordings": f"https://event-history-service.{self.camera_base_url}" \
                "/v1/playlist/cameras/{{0}}/events/{{1}}.m3u8",
            "devices": "/devices",
            "products": "/products",
            "actions": "/actions",
            "nodes": "/nodes/{0}/{1}",
        }
        self.timeout = 10
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }
        self.session = hive_session
        self.token = token
        self.headers = {}
        self.websession = websession

    def request(self, request_type, url, jsc=None, camera=False):
        """Make API request."""
        if self.session is not None:
            if camera:
                self.headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.session.tokens.token_data['token']}",
                    "x-jwt-token": self.session.tokens.token_data["token"],
                }
            else:
                self.headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "authorization": self.session.tokens.token_data["token"],
                }
        else:
            if camera:
                self.headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.token}",
                    "x-jwt-token": self.token,
                }
            else:
                self.headers = {
                    "content-type": "application/json",
                    "Accept": "*/*",
                    "authorization": self.token,
                }

        if request_type == "GET":
            return requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
        if request_type == "POST":
            return requests.post(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )

        return None

    def refresh_tokens(self, tokens: Dict[str, str] = None) -> Dict[str, Any]:
        """Get new session tokens - DEPRECATED NOW BY AWS TOKEN MANAGEMENT."""
        url = self.urls["refresh"]
        if self.session is not None:
            tokens = self.session.tokens.token_data
        jsc = json.dumps({str(i): str(t) for i, t in tokens.items()})
        try:
            info = self.request("POST", url, jsc)
            data = info.json()
            if "token" in data and self.session:
                self.session.update_tokens(data)
                self.urls.update({"base": data["platform"]["endpoint"]})
                self.urls.update({"camera": data["platform"]["cameraPlatform"]})
            self.json_return.update({"original": info.status_code})
            self.json_return.update({"parsed": info.json()})
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_login_info(self) -> Dict[str, str]:
        """Get login properties to make the login request."""
        url = self.urls["properties"]
        try:
            data = requests.get(url=url, verify=False, timeout=self.timeout)
            html = PyQuery(data.content)
            json_data = json.loads(
                f'{{"{html("script:first").text().replace(",", ", ").replace(
                    "=", ":").replace("window.", "")}"}}'
            )

            login_data = {}
            login_data.update({"UPID": json_data["HiveSSOPoolId"]})
            login_data.update({"CLIID": json_data["HiveSSOPublicCognitoClientId"]})
            login_data.update({"REGION": json_data["HiveSSOPoolId"]})
            return login_data
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()
            return {}

    def get_all(self) -> Dict[str, Any]:
        """Build and query all endpoint."""
        json_return: Dict[str, Any] = {}
        url = self.urls["base"] + self.urls["all"]
        try:
            info = self.request("GET", url)
            json_return["original"] = info.status_code
            json_return["parsed"] = info.json()
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return json_return

    def get_alarm(self, home_id: Optional[str] = None) -> Dict[str, Any]:
        """Build and query alarm endpoint."""
        if self.session is not None:
            home_id = self.session.config.home_id
        url = self.urls["base"] + self.urls["alarm"] + home_id
        json_return: Dict[str, Any] = {}
        try:
            info = self.request("GET", url)
            json_return["original"] = info.status_code
            json_return["parsed"] = info.json()
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return json_return

    def get_camera_image(
        self, device: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build and query camera endpoint."""
        json_return: Dict[str, Any] = {}
        url = self.urls["cameraImages"].format(device["props"]["hardwareIdentifier"])
        try:
            info = self.request("GET", url, camera=True)
            json_return.update({"original": info.status_code})
            json_return.update({"parsed": info.json()})
        except (OSError, RuntimeError, ZeroDivisionError):
            self.error()

        return json_return

    def get_camera_recording(
        self, device: Optional[Dict[str, Any]] = None, event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build and query camera endpoint."""
        json_return: Dict[str, Any] = {}
        url = self.urls["camera_recordings"].format(
            device["props"]["hardwareIdentifier"], event_id
        )
        try:
            info = self.request("GET", url, camera=True)
            json_return.update({"original": info.status_code})
            json_return.update({"parsed": info.text.split("\n")[3]})
        except (OSError, RuntimeError, ZeroDivisionError):
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
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) + '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = self.urls["base"] + self.urls["nodes"].format(n_type, n_id)

        try:
            response = self.request("POST", url, jsc)
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (OSError, RuntimeError, ZeroDivisionError, ConnectionError):
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
        self.json_return.update({"original": "Error making API call"})
        self.json_return.update({"parsed": "Error making API call"})


class UnknownConfig(Exception):
    """Unknown API config."""
