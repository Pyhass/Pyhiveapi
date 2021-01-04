"""Hive Data Module."""
import datetime


class Data:
    """Hive Data"""

    # API Data
    products = {}
    devices = {}
    actions = {}
    user = {}
    ha_devices = {}
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
        "Sensor": {
            "OPEN": True,
            "CLOSED": False,
            True: "Online",
            False: "Offline",
        },
        "Switch": {"ON": True, "OFF": False},
    }
    HIVE_TYPES = {
        "Hub": ["hub", "sense"],
        "Thermo": ["thermostatui", "trv"],
        "Heating": ["heating", "trvcontrol"],
        "Hotwater": ["hotwater"],
        "Light": ["warmwhitelight", "tuneablelight", "colourtuneablelight"],
        "Sensor": ["motionsensor", "contactsensor"],
        "Switch": ["activeplug"],
    }
    sensor_commands = {
        "SMOKE_CO": "Hub.hub_smoke(Hub(), device)",
        "DOG_BARK": "Hub.hub_dog_bark(Hub(), device)",
        "GLASS_BREAK": "Hub.hub_glass(Hub(), device)",
        "CurrentTemperature": "Heating.current_temperature(Heating(), device)",
        "TargetTemperature": "Heating.target_temperature(Heating(), device)",
        "Heating_State": "Heating.get_state(Heating(), device)",
        "Heating_Mode": "Heating.get_mode(Heating(), device)",
        "Heating_Boost": "Heating.boost(Heating(), device)",
        "Hotwater_State": "Hotwater.get_state(Hotwater(), device)",
        "Hotwater_Mode": "Hotwater.get_mode(Hotwater(), device)",
        "Hotwater_Boost": "Hotwater.get_boost(Hotwater(), device)",
        "Battery": 'self.attr.battery(device["device_id"])',
        "Mode": 'self.attr.get_mode(device["device_id"])',
        "Availability": "self.online(device)",
        "Connectivity": "self.online(device)",
    }

    # Session Data
    tokens = {}
    tokenCreated = datetime.datetime.now() - datetime.timedelta(seconds=4000)
    tokenExpiry = datetime.timedelta(seconds=1800)
    lastUpdate = datetime.datetime.now()
    intervalSeconds = datetime.timedelta(seconds=120)
    sensors = False
    file = False
    errorList = {}
    HttpCount = 0
    haWebsession = None
    loginData = {}

    # Platform data
    minMax = {}

    # Debugging data
    debugOutFolder = ""
    debugOutFile = ""
    debugEnabled = False
    debugList = []
