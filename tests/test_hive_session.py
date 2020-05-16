from pyhiveapi.hive_session import Session
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


class Hive_Session_Tests(unittest.TestCase):
    """Unit tests for the Logger Class."""

    @patch(
        "pyhiveapi.hive_session.Hive.login",
        return_value=open_file("login_sucessful.json"),
    )
    def test_login_sucessfully(self, Session_login_function):
        print("Session ID is {0}".format(Data.sess_id))
        Session.hive_api_logon(Session())
        print("Session ID is {0}".format(Data.sess_id))
        self.assertIsNotNone(Data.sess_id)

    @patch(
        "pyhiveapi.hive_session.Hive.login", return_value=open_file("login_failed.json")
    )
    def test_login_failed(self, Session_login_function):
        print("Session ID is {0}".format(Data.sess_id))
        Session.hive_api_logon(Session())
        print("Session ID is {0}".format(Data.sess_id))
        self.assertIsNone(Data.sess_id)

    @patch(
        "pyhiveapi.hive_session.Hive.login",
        return_value=open_file("login_sucessful.json"),
    )
    def test_token_refresh_required(self, Session_login_function):
        previous = datetime.datetime(2017, 1, 1, 12, 0, 0)
        Data.s_logon_datetime = previous
        Data.sess_id = "Old_Token"
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        Session.hive_api_logon(Session())
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        self.assertNotEqual(previous, Data.s_logon_datetime)

    def test_token_refresh_not_required(self):
        previous_token = "Test_Token"
        Data.sess_id = previous_token
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        Session.hive_api_logon(Session())
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        self.assertEqual(previous_token, Data.sess_id)

    @patch(
        "pyhiveapi.hive_session.Hive.login",
        return_value=open_file("login_sucessful.json"),
    )
    def test_token_refresh_no_session_id(self, Session_login_function):
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        Session.hive_api_logon(Session())
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        self.assertIsNotNone(Data.sess_id)

    @patch(
        "pyhiveapi.hive_session.Hive.login",
        return_value=open_file("login_sucessful.json"),
    )
    def test_token_refresh_using_file(self, Session_login_function):
        previous = datetime.datetime(2017, 1, 1, 12, 0, 0)
        Data.s_logon_datetime = previous
        Data.s_file = True
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        print("File setting is {0}".format(Data.s_file))
        Session.hive_api_logon(Session())
        print("Last logon time - {0}".format(Data.s_logon_datetime))
        print("Session ID is {0}".format(Data.sess_id))
        self.assertEqual(previous, Data.s_logon_datetime)

    def test_minutes_to_time(self):
        minutes = 900
        new = Session.p_minutes_to_time(minutes)
        print("Hours and Minutes is {0}".format(new))
        self.assertNotEqual(minutes, new)

    def test_get_now_next_later(self):
        nnl = None
        schedule = open_file("schedule.json")
        nnl = Session.p_get_schedule_nnl(Session(), schedule)
        print(nnl)
        self.assertIsNotNone(nnl)

    def test_epochtime_to_epoch(self):
        ime = None
        time = "01.01.2019 12:00:00"
        ime = Session.epochtime(time, None, "to_epoch")
        print(ime)

    def test_epochtime_from_epoch(self):
        ime = None
        epoch = str(time.time())
        print(epoch)
        trim = "{:10.10}".format(str(epoch))
        ime = Session.epochtime(trim, "%d-%m-%Y %H:%M:%S", "from_epoch")
        print(ime)
        self.assertIsNotNone(ime)


if __name__ == "__main__":
    unittest.main()
