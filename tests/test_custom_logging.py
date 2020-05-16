from pyhiveapi.custom_logging import Logger
from pyhiveapi.hive_data import Data
import unittest
import os


class Custom_Logging_Tests(unittest.TestCase):
    """Unit tests for the Logger Class."""

    def setUp(self):
        path = os.path.expanduser("~") + "/.homeassistant/pyhiveapi"
        logfile = os.path.join(path, "log.all")
        writefile = os.path.join(path, "pyhiveapi.log")

        if not os.path.isfile(logfile):
            f = open(logfile, "w+")
            f.close()
        if not os.path.isfile(writefile):
            f = open(writefile, "w+")
            f.close()

        Data.l_o_folder = os.path.expanduser("~") + "/.homeassistant/pyhiveapi"
        Data.l_o_file = Data.l_o_folder + "/pyhiveapi.log"

    def tearDown(self):
        path = os.path.expanduser("~") + "/.homeassistant/pyhiveapi"
        logfile = os.path.join(path, "log.all")
        writefile = os.path.join(path, "pyhiveapi.log")

        if os.path.isfile(logfile):
            os.remove(logfile)
        if os.path.isfile(writefile):
            os.remove(writefile)
        Data.l_values = {}

    def test_checking_logging_enabled(self):
        Logger.check_logging(new_session=True)
        print(Data.l_values)
        self.assertTrue(Data.l_values)

    def test_checking_logging_disabled(self):
        expected = {}
        Data.l_values = {"All": True, "enabled": True}
        path = os.path.expanduser("~") + "/.homeassistant/pyhiveapi"
        logfile = os.path.join(path, "log.all")
        os.remove(logfile)
        Logger.check_logging(new_session=True)
        print(Data.l_values)
        self.assertEqual(Data.l_values, expected)

    def test_writing_a_log_message(self):
        Data.l_values.update({"All": True})
        Data.l_values.update({"enabled": True})
        file = os.path.expanduser("~") + "/.homeassistant/pyhiveapi/pyhiveapi.log"
        message = "This is a unit test message"
        Logger.log("No_ID", "All", message)
        f = open(file, "r")
        file_contents = f.read()
        print(file_contents)
        f.close()
        self.assertIn(message, file_contents)

    def test_error_checking_offline(self):
        Data.l_values.update({"All": True})
        Data.l_values.update({"enabled": True})
        file = os.path.expanduser("~") + "/.homeassistant/pyhiveapi/pyhiveapi.log"
        message = "Device offline could not update entity."
        Logger.error_check(Logger(), "No_ID", "All", "Offline")
        f = open(file, "r")
        file_contents = f.read()
        print(file_contents)
        f.close()
        self.assertIn(message, file_contents)

    def test_error_checking_failed(self):
        Data.l_values.update({"All": True})
        Data.l_values.update({"enabled": True})
        file = os.path.expanduser("~") + "/.homeassistant/pyhiveapi/pyhiveapi.log"
        message = "ERROR - No data found for device."
        Logger.error_check(Logger(), "No_ID", "All", "Failed")
        f = open(file, "r")
        file_contents = f.read()
        print(file_contents)
        f.close()
        self.assertIn(message, file_contents)

    def test_error_checking_failed_api(self):
        Data.l_values.update({"All": True})
        Data.l_values.update({"enabled": True})
        file = os.path.expanduser("~") + "/.homeassistant/pyhiveapi/pyhiveapi.log"
        message = "ERROR - Received"
        Logger.error_check(
            Logger(), "No_ID", "All", "Failed_API", resp="response <400>"
        )
        f = open(file, "r")
        file_contents = f.read()
        print(file_contents)
        f.close()
        self.assertIn(message, file_contents)


if __name__ == "__main__":
    unittest.main()
