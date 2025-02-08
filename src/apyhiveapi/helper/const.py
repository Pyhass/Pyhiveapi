# pylint: skip-file
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
    "smoke_co": "self.session.hub.get_smoke_status(device)",
    "dog_bark": "self.session.hub.get_dog_bark_status(device)",
    "glass_break": "self.session.hub.get_glass_break_status(device)",
    "camera_temp": "self.session.camera.get_camera_temperature(device)",
    "current_temperature": "self.session.heating.get_current_temperature(device)",
    "heating_current_temperature": "self.session.heating.get_current_temperature(device)",
    "heating_target_temperature": "self.session.heating.get_target_temperature(device)",
    "heating_state": "self.session.heating.get_state(device)",
    "heating_mode": "self.session.heating.get_mode(device)",
    "heating_boost": "self.session.heating.get_boost_status(device)",
    "hotwater_state": "self.session.hotwater.get_state(device)",
    "hotwater_mode": "self.session.hotwater.get_mode(device)",
    "hotwater_boost": "self.session.hotwater.get_boost(device)",
    "battery": 'self.session.attr.get_battery(device["device_id"])',
    "mode": 'self.session.attr.get_mode(device["hive_id"])',
    "availability": "self.online(device)",
    "connectivity": "self.online(device)",
    "power": "self.session.switch.get_power_usage(device)",
}

PRODUCTS = {
    "sense": [
        'add_list("binary_sensor", p, ha_name="Glass Detection", hive_type="GLASS_BREAK")',
        'add_list("binary_sensor", p, ha_name="Smoke Detection", hive_type="SMOKE_CO")',
        'add_list("binary_sensor", p, ha_name="Dog Bark Detection", hive_type="DOG_BARK")',
    ],
    "heating": [
        'add_list("climate", p, temperature_unit=self.data["user"]["temperature_unit"])',
        'add_list("switch", p, ha_name=" Heat on Demand", hive_type="heating_heat_on_demand", category="config")',
        'add_list("sensor", p, ha_name=" Current Temperature", hive_type="heating_current_temperature", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Target Temperature", hive_type="heating_target_temperature", category="diagnostic")',
        'add_list("sensor", p, ha_name=" State", hive_type="heating_state", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Mode", hive_type="heating_mode", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Boost", hive_type="heating_boost", category="diagnostic")',
    ],
    "trvcontrol": [
        'add_list("climate", p, temperature_unit=self.data["user"]["temperature_unit"])',
        'add_list("sensor", p, ha_name=" Current Temperature", hive_type="heating_current_temperature", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Target Temperature", hive_type="heating_target_temperature", category="diagnostic")',
        'add_list("sensor", p, ha_name=" State", hive_type="heating_state", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Mode", hive_type="heating_mode", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Boost", hive_type="heating_boost", category="diagnostic")',
    ],
    "hotwater": [
        'add_list("water_heater", p,)',
        'add_list("sensor", p, ha_name="Hotwater State", hive_type="hotwater_state", category="diagnostic")',
        'add_list("sensor", p, ha_name="Hotwater Mode", hive_type="hotwater_mode", category="diagnostic")',
        'add_list("sensor", p, ha_name="Hotwater Boost", hive_type="hotwater_boost", category="diagnostic")',
    ],
    "activeplug": [
        'add_list("switch", p)',
        'add_list("sensor", p, ha_name=" Mode", hive_type="mode", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Availability", hive_type="availability", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Power", hive_type="power", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Energy", hive_type="energy", category="diagnostic")',
    ],
    "warmwhitelight": [
        'add_list("light", p)',
        'add_list("sensor", p, ha_name=" Mode", hive_type="mode", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
    "tuneablelight": [
        'add_list("light", p)',
        'add_list("sensor", p, ha_name=" Mode", hive_type="mode", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
    "colourtuneablelight": [
        'add_list("light", p)',
        'add_list("sensor", p, ha_name=" Mode", hive_type="mode", category="diagnostic")',
        'add_list("sensor", p, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
    #    "hivecamera": [
    #        'add_list("camera", p)',
    #        'add_list("sensor", p, ha_name=" Mode", hive_type="mode", category="diagnostic")',
    #        'add_list("sensor", p, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    #        'add_list("sensor", p, ha_name=" Temperature", hive_type="camera_temp", category="diagnostic")',
    #    ],
    "motionsensor": [
        'add_list("binary_sensor", p)',
        'add_list("sensor", p, ha_name=" Current Temperature", hive_type="current_temperature", category="diagnostic")',
    ],
    "contactsensor": ['add_list("binary_sensor", p)'],
}

DEVICES = {
    "contactsensor": [
        'add_list("sensor", d, ha_name=" Battery Level", hive_type="battery", category="diagnostic")',
        'add_list("sensor", d, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
    "hub": [
        'add_list("binary_sensor", d, ha_name="Hive Hub Status", hive_type="connectivity", category="diagnostic")',
    ],
    "motionsensor": [
        'add_list("sensor", d, ha_name=" Battery Level", hive_type="battery", category="diagnostic")',
        'add_list("sensor", d, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
    "sense": [
        'add_list("binary_sensor", d, ha_name="Hive Hub Status", hive_type="connectivity")',
    ],
    "siren": ['add_list("alarm_control_panel", d)'],
    "thermostatui": [
        'add_list("sensor", d, ha_name=" Battery Level", hive_type="battery", category="diagnostic")',
        'add_list("sensor", d, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
    "trv": [
        'add_list("sensor", d, ha_name=" Battery Level", hive_type="battery", category="diagnostic")',
        'add_list("sensor", d, ha_name=" Availability", hive_type="availability", category="diagnostic")',
    ],
}

ACTIONS = (
    'add_list("switch", a, hive_name=a["name"], ha_name=a["name"], hive_type="action")'
)