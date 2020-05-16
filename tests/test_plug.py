from pyhiveapi.plug import Plug
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


class Plug_Tests(unittest.TestCase):
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

    def test_get_state(self):
        id_n = "plug-0000-0000-0000-000000000001"
        end = Plug.get_state(Plug(), id_n)
        print(end)
        self.assertIsNotNone(end)

    def test_get_power_usage(self):
        id_n = "plug-0000-0000-0000-000000000001"
        end = Plug.get_power_usage(Plug(), id_n)
        print(end)
        self.assertIsNotNone(end)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_state",
        return_value=open_file("set_state_sucessful.json"),
    )
    def test_turn_on_sucessful(self, Check_login, Get_nodes, Set_state):
        end = None
        id_n = "plug-0000-0000-0000-000000000001"
        end = Plug.turn_on(Plug(), id_n)
        print(end)
        self.assertTrue(end)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_state",
        return_value=open_file("set_state_failed.json"),
    )
    def test_turn_on_failed(self, Check_login, Get_nodes, Set_state):
        end = None
        id_n = "plug-0000-0000-0000-000000000001"
        end = Plug.turn_on(Plug(), id_n)
        print(end)
        self.assertFalse(end)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_state",
        return_value=open_file("set_state_sucessful.json"),
    )
    def test_turn_off_sucessful(self, Check_login, Get_nodes, Set_state):
        end = None
        id_n = "plug-0000-0000-0000-000000000001"
        end = Plug.turn_off(Plug(), id_n)
        print(end)
        self.assertTrue(end)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_state",
        return_value=open_file("set_state_failed.json"),
    )
    def test_turn_off_failed(self, Check_login, Get_nodes, Set_state):
        end = None
        id_n = "plug-0000-0000-0000-000000000001"
        end = Plug.turn_off(Plug(), id_n)
        print(end)
        self.assertFalse(end)


if __name__ == "__main__":
    unittest.main()
