"""Constants for Pyhiveapi."""
# pylint: skip-file
SYNC_PACKAGE_NAME = "pyhiveapi"
SYNC_PACKAGE_DIR = "/pyhiveapi/"
ASYNC_PACKAGE_NAME = "apyhiveapi"
ASYNC_PACKAGE_DIR = "/apyhiveapi/"
SMS_REQUIRED = "SMS_MFA"


# HTTP return codes.
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_MOVED_PERMANENTLY = 301
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503


HIVETOHA = {
    "Alarm": {"home": "armed_home", "away": "armed_away", "asleep": "armed_night"},
    "Attribute": {True: "Online", False: "Offline"},
    "Boost": {None: "OFF", False: "OFF"},
    "Heating": {False: "OFF", "ENABLED": True, "DISABLED": False},
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
    "SMOKE_CO": "self.session.hub.get_smoke_status(device)",
    "DOG_BARK": "self.session.hub.get_dog_bark_status(device)",
    "GLASS_BREAK": "self.session.hub.get_glass_break_status(device)",
    "Camera_Temp": "self.session.camera.get_camera_temperature(device)",
    "Current_Temperature": "self.session.heating.get_current_temperature(device)",
    "Heating_Current_Temperature": "self.session.heating.get_current_temperature(device)",
    "Heating_Target_Temperature": "self.session.heating.get_target_temperature(device)",
    "Heating_State": "self.session.heating.get_state(device)",
    "Heating_Mode": "self.session.heating.get_mode(device)",
    "Heating_Boost": "self.session.heating.get_boost_status(device)",
    "Hotwater_State": "self.session.hotwater.get_state(device)",
    "Hotwater_Mode": "self.session.hotwater.get_mode(device)",
    "Hotwater_Boost": "self.session.hotwater.get_boost(device)",
    "Battery": 'self.session.attr.get_battery(device["device_id"])',
    "Mode": 'self.session.attr.get_mode(device["hive_id"])',
    "Availability": "self.online(device)",
    "Connectivity": "self.online(device)",
    "Power": "self.session.switch.get_power_usage(device)",
}

PRODUCTS = {
    "sense": [
        'addList("binary_sensor", p, ha_name="Glass Detection", hive_type="GLASS_BREAK")',
        'addList("binary_sensor", p, ha_name="Smoke Detection", hive_type="SMOKE_CO")',
        'addList("binary_sensor", p, ha_name="Dog Bark Detection", hive_type="DOG_BARK")',
    ],
    "heating": [
        'addList("climate", p, temperatureunit=self.data["user"]["temperatureUnit"])',
        'addList("switch", p, ha_name=" Heat on Demand", hive_type="Heating_Heat_On_Demand", category="config")',
        'addList("sensor", p, ha_name=" Current Temperature", hive_type="Heating_Current_Temperature", category="diagnostic")',
        'addList("sensor", p, ha_name=" Target Temperature", hive_type="Heating_Target_Temperature", category="diagnostic")',
        'addList("sensor", p, ha_name=" State", hive_type="Heating_State", category="diagnostic")',
        'addList("sensor", p, ha_name=" Mode", hive_type="Heating_Mode", category="diagnostic")',
        'addList("sensor", p, ha_name=" Boost", hive_type="Heating_Boost", category="diagnostic")',
    ],
    "trvcontrol": [
        'addList("climate", p, temperatureunit=self.data["user"]["temperatureUnit"])',
        'addList("sensor", p, ha_name=" Current Temperature", hive_type="Heating_Current_Temperature", category="diagnostic")',
        'addList("sensor", p, ha_name=" Target Temperature", hive_type="Heating_Target_Temperature", category="diagnostic")',
        'addList("sensor", p, ha_name=" State", hive_type="Heating_State", category="diagnostic")',
        'addList("sensor", p, ha_name=" Mode", hive_type="Heating_Mode", category="diagnostic")',
        'addList("sensor", p, ha_name=" Boost", hive_type="Heating_Boost", category="diagnostic")',
    ],
    "hotwater": [
        'addList("water_heater", p,)',
        'addList("sensor", p, ha_name="Hot Water State", hive_type="Hotwater_State", category="diagnostic")',
        'addList("sensor", p, ha_name="Hot Water Mode", hive_type="Hotwater_Mode", category="diagnostic")',
        'addList("sensor", p, ha_name="Hot Water Boost", hive_type="Hotwater_Boost", category="diagnostic")',
    ],
    "activeplug": [
        'addList("switch", p)',
        'addList("sensor", p, ha_name=" Mode", hive_type="Mode", category="diagnostic")',
        'addList("sensor", p, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
        'addList("sensor", p, ha_name=" Power", hive_type="Power", category="diagnostic")',
    ],
    "warmwhitelight": [
        'addList("light", p)',
        'addList("sensor", p, ha_name=" Mode", hive_type="Mode", category="diagnostic")',
        'addList("sensor", p, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
    "tuneablelight": [
        'addList("light", p)',
        'addList("sensor", p, ha_name=" Mode", hive_type="Mode", category="diagnostic")',
        'addList("sensor", p, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
    "colourtuneablelight": [
        'addList("light", p)',
        'addList("sensor", p, ha_name=" Mode", hive_type="Mode", category="diagnostic")',
        'addList("sensor", p, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
    #    "hivecamera": [
    #        'addList("camera", p)',
    #        'addList("sensor", p, ha_name=" Mode", hive_type="Mode", category="diagnostic")',
    #        'addList("sensor", p, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    #        'addList("sensor", p, ha_name=" Temperature", hive_type="Camera_Temp", category="diagnostic")',
    #    ],
    "motionsensor": [
        'addList("binary_sensor", p)',
        'addList("sensor", p, ha_name=" Current Temperature", hive_type="Current_Temperature", category="diagnostic")',
    ],
    "contactsensor": ['addList("binary_sensor", p)'],
}

DEVICES = {
    "contactsensor": [
        'addList("sensor", d, ha_name=" Battery Level", hive_type="Battery", category="diagnostic")',
        'addList("sensor", d, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
    "hub": [
        'addList("binary_sensor", d, ha_name="Hive Hub Status", hive_type="Connectivity", category="diagnostic")',
    ],
    "motionsensor": [
        'addList("sensor", d, ha_name=" Battery Level", hive_type="Battery", category="diagnostic")',
        'addList("sensor", d, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
    "sense": [
        'addList("binary_sensor", d, ha_name="Hive Hub Status", hive_type="Connectivity")',
    ],
    "siren": ['addList("alarm_control_panel", d)'],
    "thermostatui": [
        'addList("sensor", d, ha_name=" Battery Level", hive_type="Battery", category="diagnostic")',
        'addList("sensor", d, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
    "trv": [
        'addList("sensor", d, ha_name=" Battery Level", hive_type="Battery", category="diagnostic")',
        'addList("sensor", d, ha_name=" Availability", hive_type="Availability", category="diagnostic")',
    ],
}

ACTIONS = (
    'addList("switch", a, hive_name=a["name"], ha_name=a["name"], hive_type="action")'
)
