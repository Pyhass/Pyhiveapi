
![CodeQL](https://github.com/Pyhive/Pyhiveapi/workflows/CodeQL/badge.svg) ![Python Linting](https://github.com/Pyhive/Pyhiveapi/workflows/Python%20package/badge.svg)

# Introduction
This is a library which intefaces with the Hive smart home platform. 
This library is built for to integrate with the Home Assistant platform,
but can be used independently (See examples below.)


## Examples
Below are examples on how to use the library independently.


### Log in - Using Hive Username and Password
Below is an example of how to log in to Hive using your Hive Username and Hive password, using 2FA if needed, to create a pyhiveapi session object.

```Python
from pyhiveapi import Hive, SMS_REQUIRED

session = Hive(username="HiveUserName", password="HivePassword")
login = session.login()

if login.get("ChallengeName") == SMS_REQUIRED:
    code = input("Enter 2FA code: ")
    session.sms_2fa(code, login)

session.startSession()
```


### Use the session object to get devices
Below is an example of how to use the session object to get all devices of each type from `deviceList` and store in a separate list for each device type.

```Python
BinarySensors = session.deviceList["binary_sensor"]
HeatingDevices = session.deviceList["climate"]
Lights = session.deviceList["light"]
Sensors = session.deviceList["sensor"]
Switches = session.deviceList["switch"]
WaterHeaters = session.deviceList["water_heater"]
```


### Use the session object to interact with heating
Below is an example of how to use the session object to interact with all the different heating actions.

```Python
if len(HeatingDevices) >= 1:
    HeatingZone_1 = HeatingDevices[0]
    print("HeatingZone 1 : " + str(HeatingZone_1["hiveName"]))
    print("Get Operation Modes : " + str(session.heating.get_operation_modes()))
    print("Current Mode : " + str(session.heating.get_mode(HeatingZone_1)))
    print("Current State : " + str(session.heating.get_state(HeatingZone_1)))
    print("Current Temperature : " + str(session.heating.current_temperature(HeatingZone_1)))
    print("Target Temperature : " + str(session.heating.target_temperature(HeatingZone_1)))
    print("Min / Max Temperatures : " + str(session.heating.minmax_temperatures(HeatingZone_1)))
    print("Boost On/Off : " + str(session.heating.boost(HeatingZone_1)))
    print("Bost time remaining : " + str(session.heating.get_boost_time(HeatingZone_1)))    
    print("Get Schedule now/next/later : " + str(session.heating.get_schedule_now_next_later(HeatingZone_1)))
    print("Set Mode to SCHEDULE: " + str(session.heating.set_mode(HeatingZone_1, "SCHEDULE")))
    print("Current Operation : " + str(session.heating.current_operation(HeatingZone_1)))
    print("Set Target Temp : " + str(session.heating.set_target_temperature(HeatingZone_1, 15)))
    print("Turn Boost On for 30 minutess at 15c: " + str(session.heating.turn_boost_on(HeatingZone_1, 30, 15)))
    print("Turn off boost : " + str(session.heating.turn_boost_off(HeatingZone_1)))
```


### Use the session object to interact with hotwater
Below is an example of how to use the session object to interact with all the differeht hotwater actions.

```Python
if len(WaterHeaters) >= 1:
    WaterHeater_1 = WaterHeaters[0]
    print("WaterHeater 1 : " + str(WaterHeater_1["hiveName"]))
    print("Get Operation Modes : " + str(session.hotwater.get_operation_modes()))
    print("Current Mode : " + str(session.hotwater.get_mode(WaterHeater_1)))
    print("Get State : " + str(session.hotwater.get_state(WaterHeater_1)))
    print("Get Boost On/Off: " + str(session.hotwater.get_boost(WaterHeater_1)))
    print("Get Boost time remaining : " + str(session.hotwater.get_boost_time(WaterHeater_1)))
    print("Get Schedule now/next/later : " + str(session.hotwater.get_schedule_now_next_later(WaterHeater_1)))
    print("Set Mode to OFF : " + str(session.hotwater.set_mode(WaterHeater_1, "OFF")))
    print("Turn Boost On for 30 minutes : " + str(session.hotwater.turn_boost_on(WaterHeater_1, 30)))
    print("Turn Boost Off : " + str(session.hotwater.turn_boost_off(WaterHeater_1)))
```

### Use the session object to interact with lights
Below is an example of how to use the session object to interact with all the different light actions.

```Python
if len(Lights) >= 1:
    Light_1 = Lights[0]
    print("Light 1 : " + str(Light_1["hiveName"]))
    print("Get State : " + str(session.light.get_state(Light_1)))
    print("Get Brightness : " + str(session.light.get_brightness(Light_1)))
    print("Get min colour temperature : " + str(session.light.get_min_color_temp(Light_1)))
    print("Get max colour temperature : " + str(session.light.get_max_color_temp(Light_1)))
    print("Get colour temperature : " + str(session.light.get_color_temp(Light_1)))
    print("Get colour : " + str(session.light.get_color(Light_1)))
    print("Get colour mode : " + str(session.light.getColourMode(Light_1)))
```


### Log in - Using Tokens
Below is an example how to log in to Hive with 2FA if needed
and get a session token.

```Python
import pyhiveapi as Hive

tokens = {}
auth = Hive.HiveAuth('username', 'password')
session = auth.login()
if session.get("ChallengeName") == Hive.SMS_REQUIRED:
    # Complete SMS 2FA.
    code = input("Enter your 2FA code: ")
    session = auth.sms_2fa(code, session)

if 'AuthenticationResult' in session:
    session = session['AuthenticationResult']
    tokens.update(
        {"token": session["IdToken"]})
    tokens.update(
        {"refreshToken": session["RefreshToken"]})
    tokens.update(
        {"accessToken": session["AccessToken"]})
else:
    raise Hive.NoApiToken
```

### Refresh Tokens
Below is an example how to refresh your session tokens 
after they have expired

```Python
api = Hive.HiveApi()
newTokens = api.refreshTokens(tokens)
if newTokens['original'] == 200:
    tokens.update(
        {"token": newTokens['parsed']["token"]})
    tokens.update(
        {"refreshToken": newTokens['parsed']["refreshToken"]})
    tokens.update(
        {"accessToken": newTokens['parsed']["accessToken"]})
else:
    raise Hive.NoApiToken
```

### Get Hive Data - Using Tokens
Below is an example how to data from the Hive platform 
using the session token acquired from login.

```Python
api = Hive.HiveApi()
data = api.getAllData(tokens["token"])
```
