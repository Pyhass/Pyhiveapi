"""Hive Data Module."""
import datetime


class Data:
    """Hive Data"""

    NODE_INTERVAL_DEFAULT = 120
    WEATHER_INTERVAL_DEFAULT = 600

    # API Data
    products = {}
    devices = {}
    actions = {}
    user = {}
    NODES = {"Preheader": {"Header": "HeaderText"}}
    MODE = []
    BATTERY = []
    HIVETOHA = {
        "Attribute": {True: "Online", False: "Offline"},
        "Boost": {None: "OFF", False: "OFF"},
        "Heating": {False: "OFF"},
        "Hotwater": {"MANUAL": "ON", None: "OFF", False: "OFF"},
        "Hub": {
            "Status": {True: "Online", False: "Offline"},
            "Smoke": {True: "Alarm Detected", False: "Clear"},
            "Dog": {True: "Barking Detected", False: "Clear"},
            "Glass": {True: "Noise Detected", False: "Clear"},
        },
        "Light": {"ON": True, "OFF": False},
        "Sensor": {"OPEN": True, "CLOSED": False},
        "Switch": {"ON": True, "OFF": False},
    }
    HIVE_TYPES = {
        "Hub": ["hub", "sense"],
        "Thermo": ["thermostatui", "nathermostat"],
        "Heating": ["heating", "trvcontrol", "nathermostat"],
        "Hotwater": ["hotwater"],
        "Plug": ["activeplug"],
        "Light": ["warmwhitelight", "tuneablelight", "colourtuneablelight"],
        "Sensor": ["motionsensor", "contactsensor"],
    }

    # Session Data
    sess_id = None
    s_token = False
    s_logon_datetime = datetime.datetime.now()
    s_username = ""
    s_password = ""
    s_interval_seconds = NODE_INTERVAL_DEFAULT
    s_last_update = datetime.datetime(2017, 1, 1, 12, 0, 0)
    s_file = False

    # Weather data
    w_last_update = datetime.datetime(2017, 1, 1, 12, 0, 0)
    w_nodeid = ""
    w_icon = ""
    w_description = ""
    w_interval_seconds = WEATHER_INTERVAL_DEFAULT
    w_temperature_unit = ""
    w_temperature_value = 0.00

    # Platform data
    p_minmax = {}

    # Logging data
    l_o_folder = ""
    l_o_file = ""
    l_files = {
        "All": "log.all",
        "Action": "log.aciton",
        "Attribute": "log.attribute",
        "API": "log.api",
        "API_CORE": "log.api_core",
        "ERROR": "log.error",
        "Extra": "log.extra",
        "Heating": "log.heating",
        "Hotwater": "log.hotwater",
        "Light": "log.light",
        "Sensor": "log.sensor",
        "Session": "log.session",
        "Switch": "log.switch",
    }
    l_values = {}
