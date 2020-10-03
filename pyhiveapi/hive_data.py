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
            "Status": {True: 1, False: 0},
            "Smoke": {True: 1, False: 0},
            "Dog": {True: 1, False: 0},
            "Glass": {True: 1, False: 0},
        },
        "Light": {"ON": True, "OFF": False},
        "Sensor": {"OPEN": True, "CLOSED": False, True: "Online", False: "Offline"},
        "Switch": {"ON": True, "OFF": False},
    }
    HIVE_TYPES = {
        "Hub": ["hub", "sense"],
        "Thermo": ["thermostatui", "trv"],
        "Heating": ["heating", "trvcontrol"],
        "Hotwater": ["hotwater"],
        "Plug": ["activeplug"],
        "Light": ["warmwhitelight", "tuneablelight", "colourtuneablelight"],
        "Sensor": ["motionsensor", "contactsensor"],
    }
    sensor_commands = {
        "SMOKE_CO": "self.hub.hub_smoke(device)",
        "DOG_BARK": "self.hub.hub_dog_bark(device)",
        "GLASS_BREAK": "self.hub.hub_glass(device)",
        "CurrentTemperature": "self.heating.current_temperature(device)",
        "TargetTemperature": "self.heating.target_temperature(device)",
        "Heating_State": "self.heating.get_state(device)",
        "Heating_Mode": "self.heating.get_mode(device)",
        "Heating_Boost": "self.heating.boost(device)",
        "Hotwater_State": "self.hotwater.get_state(device)",
        "Hotwater_Mode": "self.hotwater.get_mode(device)",
        "Hotwater_Boost": "self.hotwater.get_boost(device)",
        "Battery": 'self.attributes.battery(device["device_id"])',
        "Mode": 'self.attributes.get_mode(device["device_id"])',
        "Availability": 'self.online(device)',
        "Connectivity": "self.online(device)",
        "Weather": "self.weather.temperature(device)"}

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
