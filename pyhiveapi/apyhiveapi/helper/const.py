"""Constants for Pyhiveapi."""
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
    "SMOKE_CO": "self.session.hub.getSmokeStatus(device)",
    "DOG_BARK": "self.session.hub.getDogBarkStatus(device)",
    "GLASS_BREAK": "self.session.hub.getGlassBreakStatus(device)",
    "Camera_Temp": "self.session.camera.getCameraTemperature(device)",
    "Heating_Current_Temperature": "self.session.heating.getCurrentTemperature(device)",
    "Heating_Target_Temperature": "self.session.heating.getTargetTemperature(device)",
    "Heating_State": "self.session.heating.getState(device)",
    "Heating_Mode": "self.session.heating.getMode(device)",
    "Heating_Boost": "self.session.heating.getBoostStatus(device)",
    "Hotwater_State": "self.session.hotwater.getState(device)",
    "Hotwater_Mode": "self.session.hotwater.getMode(device)",
    "Hotwater_Boost": "self.session.hotwater.getBoost(device)",
    "Battery": 'self.session.attr.getBattery(device["device_id"])',
    "Mode": 'self.session.attr.getMode(device["hiveID"])',
    "Availability": "self.online(device)",
    "Connectivity": "self.online(device)",
    "Power": "self.session.switch.getPowerUsage(device)",
}

PRODUCTS = {
    "sense": [
        'addList("binary_sensor", p, haName="Glass Detection", hiveType="GLASS_BREAK")',
        'addList("binary_sensor", p, haName="Smoke Detection", hiveType="SMOKE_CO")',
        'addList("binary_sensor", p, haName="Dog Bark Detection", hiveType="DOG_BARK")',
    ],
    "heating": [
        'addList("climate", p, temperatureunit=self.data["user"]["temperatureUnit"])',
        'addList("switch", p, haName=" Heat on Demand", hiveType="Heating_Heat_On_Demand", category="config")',
        'addList("sensor", p, haName=" Current Temperature", hiveType="Heating_Current_Temperature", category="diagnostic")',
        'addList("sensor", p, haName=" Target Temperature", hiveType="Heating_Target_Temperature", category="diagnostic")',
        'addList("sensor", p, haName=" State", hiveType="Heating_State", category="diagnostic")',
        'addList("sensor", p, haName=" Mode", hiveType="Heating_Mode", category="diagnostic")',
        'addList("sensor", p, haName=" Boost", hiveType="Heating_Boost", category="diagnostic")',
    ],
    "trvcontrol": [
        'addList("climate", p, temperatureunit=self.data["user"]["temperatureUnit"])',
        'addList("sensor", p, haName=" Current Temperature", hiveType="Heating_Current_Temperature", category="diagnostic")',
        'addList("sensor", p, haName=" Target Temperature", hiveType="Heating_Target_Temperature", category="diagnostic")',
        'addList("sensor", p, haName=" State", hiveType="Heating_State", category="diagnostic")',
        'addList("sensor", p, haName=" Mode", hiveType="Heating_Mode", category="diagnostic")',
        'addList("sensor", p, haName=" Boost", hiveType="Heating_Boost", category="diagnostic")',
    ],
    "hotwater": [
        'addList("water_heater", p,)',
        'addList("sensor", p, haName="Hotwater State", hiveType="Hotwater_State", category="diagnostic")',
        'addList("sensor", p, haName="Hotwater Mode", hiveType="Hotwater_Mode", category="diagnostic")',
        'addList("sensor", p, haName="Hotwater Boost", hiveType="Hotwater_Boost", category="diagnostic")',
    ],
    "activeplug": [
        'addList("switch", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", category="diagnostic")',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", category="diagnostic")',
        'addList("sensor", p, haName=" Power", hiveType="Power", category="diagnostic")',
    ],
    "warmwhitelight": [
        'addList("light", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", category="diagnostic")',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
    "tuneablelight": [
        'addList("light", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", category="diagnostic")',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
    "colourtuneablelight": [
        'addList("light", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", category="diagnostic")',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
    #    "hivecamera": [
    #        'addList("camera", p)',
    #        'addList("sensor", p, haName=" Mode", hiveType="Mode", category="diagnostic")',
    #        'addList("sensor", p, haName=" Availability", hiveType="Availability", category="diagnostic")',
    #        'addList("sensor", p, haName=" Temperature", hiveType="Camera_Temp", category="diagnostic")',
    #    ],
    "motionsensor": [
        'addList("binary_sensor", p)',
    ],
    "contactsensor": ['addList("binary_sensor", p)'],
}

DEVICES = {
    "contactsensor": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery", category="diagnostic")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
    "hub": [
        'addList("binary_sensor", d, haName="Hive Hub Status", hiveType="Connectivity", category="diagnostic")',
    ],
    "motionsensor": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery", category="diagnostic")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
    "sense": [
        'addList("binary_sensor", d, haName="Hive Hub Status", hiveType="Connectivity")',
    ],
    "siren": ['addList("alarm_control_panel", d)'],
    "thermostatui": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery", category="diagnostic")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
    "trv": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery", category="diagnostic")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", category="diagnostic")',
    ],
}

ACTIONS = (
    'addList("switch", a, hiveName=a["name"], haName=a["name"], hiveType="action")'
)
