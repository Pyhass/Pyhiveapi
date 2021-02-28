"""Constants for Pyhiveapi."""
PACKAGE_NAME = "Pyhiveapi"
PACKAGE_DIR = "/pyhiveapi/"
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
    "Battery": 'self.session.attr.battery(device["device_id"])',
    "Mode": 'self.session.attr.get_mode(device["hiveID"])',
    "Availability": "self.online(device)",
    "Connectivity": "self.online(device)",
}
