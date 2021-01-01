"""Hive API Module."""
import json

import requests
import urllib3
from pyquery import PyQuery

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HiveApi:
    """Hive API Code."""

    def __init__(self):
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

    def refreshTokens(self, tokens):
        """Get new session tokens"""
        url = self.urls["refresh"]
        jsc = (
            "{"
            + ",".join(
                (
                    '"' + str(i) + '": ' '"' + str(t) + '" '
                    for i, t in tokens.items()
                )
            )
            + "}"
        )
        try:
            response = requests.post(
                url=url, headers=self.headers, data=jsc, timeout=self.timeout
            )
            self.json_return.update({"original": response.status_code})
            self.json_return.update({"parsed": response.json()})
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

        return self.json_return

    def getLoginInfo(self):
        """Get login properties to make the login request."""
        url = self.urls["properties"]
        try:
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
            loginData.update(
                {"CLIID": json_data["HiveSSOPublicCognitoClientId"]}
            )
            loginData.update({"REGION": json_data["HiveSSOPoolId"]})
            return loginData
        except (IOError, RuntimeError, ZeroDivisionError):
            self.error()

    def getAllData(self, session_id):
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

    def getDevices(self, session_id):
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
                (
                    '"' + str(i) + '": ' '"' + str(t) + '" '
                    for i, t in kwargs.items()
                )
            )
            + "}"
        )

        url = self.urls["base"] + self.urls["nodes"].format(n_type, n_id)

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
