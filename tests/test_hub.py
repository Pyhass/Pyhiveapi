from pyhiveapi.hub import Hub
from pyhiveapi.hive_data import Data
import unittest
import json
import os


def open_file(file):
    path = os.getcwd() + "/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


class Hub_Tests(unittest.TestCase):
    """Unit tests for the Logger Class."""

    def setUp(self):
        products = open_file("parsed_products.json")
        devices = open_file("parsed_devices.json")
        nodes = open_file("NODES.json")
        Data.products = products
        Data.devices = devices
        Data.NODES = nodes

    def tearDown(self):
        Data.products = {}
        Data.devices = {}

    def test_hub_status_hub_online(self):
        id_n = "parent-0000-0000-0000-000000000001"
        end = Hub.hub_status(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Online")

    def test_hub_status_hub_offline(self):
        id_n = "parent-0000-0000-0000-000000000001"
        Data.devices[id_n]["props"]["online"] = "Offline"
        end = Hub.hub_status(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Offline")

    def test_hub_smoke_alarm_detected(self):
        id_n = "hub-0000-0000-0000-000000000001"
        Data.products[id_n]["props"]["sensors"]["SMOKE_CO"]["active"] = True
        end = Hub.hub_smoke(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Alarm Detected")

    def test_hub_smoke_alarm_not_detected(self):
        id_n = "hub-0000-0000-0000-000000000001"
        end = Hub.hub_smoke(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Clear")

    def test_hub_dog_bark_detected(self):
        id_n = "hub-0000-0000-0000-000000000001"
        Data.products[id_n]["props"]["sensors"]["DOG_BARK"]["active"] = True
        end = Hub.hub_dog_bark(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Barking Detected")

    def test_hub_dog_bark_not_detected(self):
        id_n = "hub-0000-0000-0000-000000000001"
        end = Hub.hub_dog_bark(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Clear")

    def test_hub_glass_breaking_detected(self):
        id_n = "hub-0000-0000-0000-000000000001"
        Data.products[id_n]["props"]["sensors"]["GLASS_BREAK"]["active"] = True
        end = Hub.hub_glass(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Noise Detected")

    def test_hub_glass_not_breaking(self):
        id_n = "hub-0000-0000-0000-000000000001"
        end = Hub.hub_glass(Hub(), id_n)
        print(end)
        self.assertEqual(end, "Clear")


if __name__ == "__main__":
    unittest.main()
