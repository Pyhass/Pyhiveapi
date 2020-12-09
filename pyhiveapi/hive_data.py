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
        "Sensor": {"OPEN": True, "CLOSED": False, True: "Online", False: "Offline"},
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
        "Connectivity": "self.online(device)"}

    # Session Data
    s_tokens = {}
    s_token_update = datetime.datetime.now()
    s_last_update = datetime.datetime.now()
    s_interval_seconds = datetime.timedelta(seconds=120)
    s_entity_update_flag = False
    s_sensors = False
    s_file = False
    s_error_list = {}
    s_token_expiry = datetime.timedelta(seconds=3450)

    # Platform data
    p_minmax = {}

    # Debugging data
    d_o_folder = ""
    d_o_file = ""
    d_enabled = False
    d_list = []
