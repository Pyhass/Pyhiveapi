from pyhiveapi.weather import Weather
from pyhiveapi.hive_data import Data
import unittest
import json
import os


def open_file(file):
    path = os.getcwd() + "/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


class Weather_Tests(unittest.TestCase):
    """Unit tests for the Logger Class."""

    def setUp(self):
        weather = open_file("preparsed_weather.json")
        Data.w_icon = weather["weather"]["icon"]
        Data.w_description = weather["weather"]["description"]
        Data.w_temperature_unit = weather["weather"]["temperature"]["unit"]
        Data.w_temperature_value = weather["weather"]["temperature"]["value"]
        Data.w_nodeid = "HiveWeather"

    def tearDown(self):
        w_nodeid = ""
        w_icon = ""
        w_description = ""
        w_temperature_unit = ""
        w_temperature_value = 0.00

    def test_get_weather_temperature(self):
        temp = None
        temp = Weather.temperature(Weather())
        self.assertIsNotNone(temp)


if __name__ == "__main__":
    unittest.main()
