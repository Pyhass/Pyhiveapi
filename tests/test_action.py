import os
import time
import json
import datetime
import unittest
from unittest.mock import Mock, patch
from pyhiveapi.hive_data import Data
from pyhiveapi.action import Action


def open_file(file):
    path = os.getcwd() + "/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


class Action_Tests(unittest.TestCase):
    """Unit tests for the  Actiion Class."""

    def setUp(self):
        actions = open_file("parsed_actions.json")
        nodes = open_file("NODES.json")
        Data.actions = actions
        Data.NODES = nodes

    def tearDown(self):
        Data.actions = {}
        Data.NODES = {"Preheader": {"Header": "HeaderText"}}

    def test_action_is_off(self):
        id_n = "action2-0000-0000-0000-000000000002"
        end = Action.get_state(Action(), id_n)
        print(end)
        self.assertEqual(end, False)

    def test_action_is_on(self):
        id_n = "action1-0000-0000-0000-000000000001"
        end = Action.get_state(Action(), id_n)
        print(end)
        self.assertEqual(end, True)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_action",
        return_value=open_file("set_state_sucessful.json"),
    )
    def test_turn_action_on(self, Check_login, Get_nodes, Set_state):
        id_n = "action2-0000-0000-0000-000000000002"
        Action.turn_on(Action(), id_n)
        print(Data.actions[id_n]["enabled"])
        self.assertEqual(Data.actions[id_n]["enabled"], True)

    @patch("pyhiveapi.hive_session.Session.hive_api_logon", return_value=None)
    @patch("pyhiveapi.hive_session.Session.hive_api_get_nodes", return_value=None)
    @patch(
        "pyhiveapi.hive_api.Hive.set_action",
        return_value=open_file("set_state_sucessful.json"),
    )
    def test_turn_action_off(self, Check_login, Get_nodes, Set_state):
        id_n = "action1-0000-0000-0000-000000000001"
        Action.turn_off(Action(), id_n)
        print(Data.actions[id_n]["enabled"])
        self.assertEqual(Data.actions[id_n]["enabled"], False)


if __name__ == "__main__":
    unittest.main()
