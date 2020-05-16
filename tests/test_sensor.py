from pyhiveapi.sensor import Sensor
from pyhiveapi.hive_data import Data
import unittest
import json
import os


def open_file(file):
    path = os.getcwd() + "/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


class Sensor_Tests(unittest.TestCase):
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

    def test_contact_sensor_closed(self):
        id_n = "contact-sensor-0000-0000-000000000001"
        end = Sensor.get_state(Sensor(), id_n)
        print(end)
        self.assertEqual(end, False)

    def test_contact_sensor_open(self):
        id_n = "contact-sensor-0000-0000-000000000002"
        end = Sensor.get_state(Sensor(), id_n)
        print(end)
        self.assertEqual(end, True)

    def test_motion_sensor_non_detected(self):
        id_n = "motion-sensor-0000-0000-000000000001"
        end = Sensor.get_state(Sensor(), id_n)
        print(end)
        self.assertEqual(end, False)

    def test_motion_sensor_detected(self):
        id_n = "motion-sensor-0000-0000-000000000001"
        Data.products[id_n]["props"]["motion"]["status"] = True
        end = Sensor.get_state(Sensor(), id_n)
        print(end)
        self.assertEqual(end, True)


if __name__ == "__main__":
    unittest.main()
