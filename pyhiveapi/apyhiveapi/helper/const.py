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
    "SMOKE_CO": "self.session.hub.hubSmoke(device)",
    "DOG_BARK": "self.session.hub.hubDogBark(device)",
    "GLASS_BREAK": "self.session.hub.hubGlass(device)",
    "CurrentTemperature": "self.session.heating.currentTemperature(device)",
    "TargetTemperature": "self.session.heating.targetTemperature(device)",
    "Heating_State": "self.session.heating.getState(device)",
    "Heating_Mode": "self.session.heating.getMode(device)",
    "Heating_Boost": "self.session.heating.getBoost(device)",
    "Hotwater_State": "self.session.hotwater.getState(device)",
    "Hotwater_Mode": "self.session.hotwater.getMode(device)",
    "Hotwater_Boost": "self.session.hotwater.getBoost(device)",
    "Battery": 'self.session.attr.getBattery(device["device_id"])',
    "Mode": 'self.session.attr.getMode(device["hiveID"])',
    "Availability": "self.online(device)",
    "Connectivity": "self.online(device)",
}

PRODUCTS = {
    "sense": [
        'addList("binary_sensor", p, haName="Glass Detection", hiveType="GLASS_BREAK")',
        'addList("binary_sensor", p, haName="Smoke Detection", hiveType="SMOKE_CO")',
        'addList("binary_sensor", p, haName="Dog Bark Detection", hiveType="DOG_BARK")',
    ],
    "heating": [
        'addList("climate", p, temperatureunit=self.data["user"]["temperatureUnit"])',
        'addList("sensor", p, haName=" Current Temperature", hiveType="CurrentTemperature", custom=True)',
        'addList("sensor", p, haName=" Target Temperature", hiveType="TargetTemperature", custom=True)',
        'addList("sensor", p, haName=" State", hiveType="Heating_State", custom=True)',
        'addList("sensor", p, haName=" Mode", hiveType="Heating_Mode", custom=True)',
        'addList("sensor", p, haName=" Boost", hiveType="Heating_Boost", custom=True)',
    ],
    "trvcontrol": [
        'addList("climate", p, temperatureunit=self.data["user"]["temperatureUnit"])',
        'addList("sensor", p, haName=" Current Temperature", hiveType="CurrentTemperature", custom=True)',
        'addList("sensor", p, haName=" Target Temperature", hiveType="TargetTemperature", custom=True)',
        'addList("sensor", p, haName=" State", hiveType="Heating_State", custom=True)',
        'addList("sensor", p, haName=" Mode", hiveType="Heating_Mode", custom=True)',
        'addList("sensor", p, haName=" Boost", hiveType="Heating_Boost", custom=True)',
    ],
    "hotwater": [
        'addList("water_heater", p,)',
        'addList("sensor", p, haName="Hotwater State", hiveType="Hotwater_State", custom=True)',
        'addList("sensor", p, haName="Hotwater Mode", hiveType="Hotwater_Mode", custom=True)',
        'addList("sensor", p, haName="Hotwater Boost", hiveType="Hotwater_Boost", custom=True)',
    ],
    "activeplug": [
        'addList("switch", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", custom=True)',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "warmwhitelight": [
        'addList("light", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", custom=True)',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "tuneablelight": [
        'addList("light", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", custom=True)',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "colourtuneablelight": [
        'addList("light", p)',
        'addList("sensor", p, haName=" Mode", hiveType="Mode", custom=True)',
        'addList("sensor", p, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "motionsensor": ['addList("binary_sensor", p)'],
    "contactsensor": ['addList("binary_sensor", p)'],
}

DEVICES = {
    "thermostatui": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "trv": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "motionsensor": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "contactsensor": [
        'addList("sensor", d, haName=" Battery Level", hiveType="Battery")',
        'addList("sensor", d, haName=" Availability", hiveType="Availability", custom=True)',
    ],
    "sense": [
        'addList("binary_sensor", d, haName="Hive Hub Status", hiveType="Connectivity")',
    ],
    "hub": [
        'addList("binary_sensor", d, haName="Hive Hub Status", hiveType="Connectivity")',
    ],
}

ACTIONS = (
    'addList("switch", a, hiveName=a["name"], haName=a["name"], hiveType="action")'
)
