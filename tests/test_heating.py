from pyhiveapi.heating import Heating
from pyhiveapi.hive_data import Data
from unittest.mock import Mock, patch
import unittest
import datetime
import json
import time
import os


def open_file(file):
    path = os.getcwd() + "/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


class Heating_Tests(unittest.TestCase):
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

    def test_get_min_temp(self):
        temp = None
        temp = Heating.min_temperature()
        print(temp)
        self.assertIsNotNone(temp)

    def test_get_max_temp(self):
        temp = None
        temp = Heating.max_temperature()
        print(temp)
        self.assertIsNotNone(temp)

    def test_get_current_temp(self):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        end = Heating.current_temperature(Heating(), id_n)
        print(end)
        print(Data.p_minmax)
        self.assertIsNotNone(end)
        self.assertNotEqual(Data.p_minmax, {})

    def test_get_minmax_temp(self):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        Data.p_minmax = {
            "heating-0000-0000-0000-000000000001": {
                "TodayMin": 19.79,
                "TodayMax": 19.79,
                "TodayDate": "2019-04-07",
                "RestartMin": 10.01,
                "RestartMax": 25.05,
            }
        }
        end = Heating.minmax_temperatures(Heating(), id_n)
        print(end)
        self.assertIsNotNone(end)

    #    def test_get_mode(self):

    def test_get_state(self):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        end = Heating.get_state(Heating(), id_n)
        print(end)
        self.assertIsNotNone(end)

    def test_get_boost_on(self):
        id_n = "heating-0000-0000-0000-000000000001"
        end = Heating.get_boost(Heating(), id_n)
        print(end)
        self.assertEqual("ON", end)

    def test_get_boost_off(self):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        data = Data.products[id_n]
        data["state"]["boost"] = None
        end = Heating.get_boost(Heating(), id_n)
        print(end)
        self.assertEqual("OFF", end)

    def test_get_boost_time(self):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        end = Heating.get_boost_time(Heating(), id_n)
        print(end)
        self.assertGreater(end, 0)

    def test_get_operation_modes(self):
        end = None
        end = Heating.get_operation_modes()
        print(end)
        self.assertIsNotNone(end)

    def test_get_schedule_now_next_later(self):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        data = Data.products[id_n]
        data["state"]["mode"] = "SCHEDULE"
        end = Heating.get_schedule_now_next_later(Heating(), id_n)
        print(end)
        self.assertIsNotNone(end)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_state",
        return_value=open_file("set_state_sucessful.json"),
    )
    def test_set_target_temperature_sucessful(self, Check_login, Get_nodes, Set_state):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        end = Heating.set_target_temperature(Heating(), id_n, 32)
        print(end)
        self.assertTrue(end)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_state",
        return_value=open_file("set_state_failed.json"),
    )
    def test_set_target_temperature_failed(self, Check_login, Get_nodes, Set_state):
        end = None
        id_n = "heating-0000-0000-0000-000000000001"
        end = Heating.set_target_temperature(Heating(), id_n, 32)
        print(end)
        self.assertFalse(end)


#    def test_set_mode(self):

#    def test_turn_boost_on(self):

#    def test_turn_boost_off(self):


if __name__ == "__main__":
    unittest.main()
