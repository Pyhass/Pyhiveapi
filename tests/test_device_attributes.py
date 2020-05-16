from pyhiveapi.device_attributes import Attributes
from pyhiveapi.hive_data import Data
import unittest
import json
import os


def open_file(file):
    path = os.getcwd() + "/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


class Device_Attribute_Tests(unittest.TestCase):
    """Unit tests for the Logger Class."""

    def setUp(self):
        products = open_file("parsed_products.json")
        devices = open_file("parsed_devices.json")
        nodes = open_file("NODES.json")
        mode = open_file("MODE.json")
        battery = open_file("BATTERY.json")
        Data.products = products
        Data.devices = devices
        Data.NODES = nodes
        Data.MODE = mode
        Data.BATTERY = battery

    def tearDown(self):
        Data.products = {}
        Data.devices = {}
        Data.NODES = {"Preheader": {"Header": "HeaderText"}}
        Data.MODE = []
        Data.BATTERY = []

    def test_device_offline(self):
        id_n = "contact-sensor-0000-0000-000000000003"
        end = Attributes.online_offline(Attributes(), id_n)
        print(end)
        self.assertEqual(end, "Offline")

    def test_device_online(self):
        id_n = "contact-sensor-0000-0000-000000000001"
        end = Attributes.online_offline(Attributes(), id_n)
        print(end)
        self.assertEqual(end, "Online")

    def test_device_get_mode(self):
        end = None
        id_n = "light-0000-0000-0000-000000000001"
        end = Attributes.get_mode(Attributes(), id_n)
        print(end)
        self.assertIsNotNone(end)

    def test_device_get_battery(self):
        end = None
        id_n = "contact-sensor-0000-0000-000000000001"
        end = Attributes.battery(Attributes(), id_n)
        print(end)
        self.assertIsNotNone(end)

    def test_device_get_state_attributes(self):
        end = None
        id_n = "motion-sensor-0000-0000-000000000001"
        end = Attributes.state_attributes(Attributes(), id_n)
        print(end)
        self.assertIsNotNone(end)


if __name__ == "__main__":
    unittest.main()
