"""Hive API Module."""
import requests
from .custom_logging import Logger


class Hive:
    """Hive API Code."""

    def __init__(self):
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
            "authorization": "None",
        }
        self.timeout = 10
        self.json_return = {
            "original": "No response to Hive API request",
            "parsed": "No response to Hive API request",
        }

    def login(self, username, password):
        """Login to the Hive API."""
        try:
            j = '{{"username": "{0}", "password": "{1}"}}'.format(
                username, password)
            response = requests.post(
                url=self.urls["login"],
                headers=self.headers,
                data=j,
                timeout=self.timeout,
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def check_token(self, token):
        """Get a long lived token"""
        self.headers.update({"authorization": "Bearer " + token})
        self.headers.update({"X-Omnia-Client": "swagger"})
        self.headers.update({"X-MQTT-Client-ID": "swagger_MQTT_client"})
        self.headers.update(
            {"Accept": "application/vnd.alertme.zoo-6.6.0+json"})
        try:
            response = requests.get(
                url=self.urls["long_lived"],
                headers=self.headers,
                data=None,
                timeout=self.timeout,
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def create_token(self, token):
        """Get a long lived token"""
        self.headers.update({"authorization": "Bearer " + token})
        self.headers.update({"X-Omnia-Client": "swagger"})
        self.headers.update({"X-MQTT-Client-ID": "swagger_MQTT_client"})
        self.headers.update(
            {"Accept": "application/vnd.alertme.zoo-6.6.0+json"})
        try:
            j = '{ "accessTokens": [ { "description": "HA access token" } ] }'
            response = requests.post(
                url=self.urls["long_lived"],
                headers=self.headers,
                data=j,
                timeout=self.timeout,
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def remove_token(self, token, token_id):
        """Get a long lived token"""
        self.headers.update({"X-Omnia-Access-Token": token})
        self.headers.update({"X-Omnia-Client": "swagger"})
        self.headers.update({"X-MQTT-Client-ID": "swagger_MQTT_client"})
        self.headers.update(
            {"Accept": "application/vnd.alertme.zoo-6.6.0+json"})
        try:
            response = requests.delete(
                url=self.urls["long_lived"] + "/" + token_id,
                headers=self.headers,
                data=None,
                timeout=self.timeout,
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (ConnectionError, IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_all(self, session_id):
        """Build and query all endpoint."""
        self.headers.update({"authorization": session_id})
        url = self.urls["base"] + self.urls["all"]
        try:
            jsc = None
            response = requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_devices(self, session_id):
        """Call the get devices endpoint."""
        self.headers.update({"authorization": session_id})
        url = self.urls["base"] + self.urls["devices"]
        try:
            jsc = None
            response = requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_products(self, session_id):
        """Call the get products endpoint."""
        self.headers.update({"authorization": session_id})
        url = self.urls["base"] + self.urls["products"]
        try:
            jsc = None
            response = requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_actions(self, session_id):
        """Call the get actions endpoint."""
        self.headers.update({"authorization": session_id})
        url = self.urls["base"] + self.urls["actions"]
        try:
            jsc = None
            response = requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def motion_sensor(self, session_id, sensor, fromepoch, toepoch):
        """Call a way to get motion sensor info."""
        self.headers.update({"authorization": session_id})
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
            jsc = None
            response = requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def get_weather(self, weather_url):
        """Call endpoint to get local weather from Hive API."""
        t_url = self.urls["weather"] + weather_url
        url = t_url.replace(" ", "%20")
        try:
            jsc = None
            response = requests.get(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            self.error()

        return self.json_return

    def set_state(self, session_id, n_type, n_id, **kwargs):
        """Set the state of a Device."""
        self.headers.update({"authorization": session_id})
        jsc = (
            "{"
            + ",".join(
                ('"' + str(i) + '": ' '"' + str(t) +
                 '" ' for i, t in kwargs.items())
            )
            + "}"
        )

        url = self.urls["base"] + self.urls["nodes"].format(n_type, n_id)

        self.log.log(
            n_id,
            "api_core",
            "Headers >\n{0}\nURL >\n{1}\n"
            + "Payload\n{2}\n".format(self.headers, url, jsc),
        )
        try:
            response = requests.post(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            self.error()

        return self.json_return

    def set_action(self, session_id, n_id, data):
        """Set the state of a Action."""
        self.headers.update({"authorization": session_id})
        jsc = data
        url = self.urls["base"] + self.urls["actions"] + "/" + n_id
        self.log.log(
            n_id,
            "api_core",
            "Headers >\n{0}\nURL >\n{1}\n"
            + "Payload\n{2}\n".format(self.headers, url, jsc),
        )
        try:
            response = requests.put(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError, ConnectionError):
            self.error()

        return self.json_return

    def error(self):
        """An error has occured iteracting wth the Hive API."""
        self.json_return.update({"original": "Error making API call"})
        self.json_return.update({"parsed": "Error making API call"})
        self.log.log("API_ERROR", "ERROR", "Error attempting API call")
