
![CodeQL](https://github.com/Pyhive/Pyhiveapi/workflows/CodeQL/badge.svg) ![Python Linting](https://github.com/Pyhive/Pyhiveapi/workflows/Python%20package/badge.svg)

# Introduction
This is a library which intefaces with the Hive smart home platform. 
This library is built mainly to integrate with the Home Assistant platform,
but it can also be used independently (See examples below.)


## Examples
Below are examples on how to use the library independently.


### Log in - Using Hive Username and Password
Below is an example of how to log in to Hive using your Hive Username and Hive password, using 2FA if needed, to create a pyhiveapi `session` object.

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
Below is an example of how to use the `session` object to get all devices of each type from `deviceList` and store in a separate list for each device type.

```Python
BinarySensors = session.deviceList["binary_sensor"]
HeatingDevices = session.deviceList["climate"]
Lights = session.deviceList["light"]
Sensors = session.deviceList["sensor"]
Switches = session.deviceList["switch"]
WaterHeaters = session.deviceList["water_heater"]
```


### Use the session object to interact with heating
Below is an example of how to use the `session` object to interact with all the different heating actions.

```Python
if len(HeatingDevices) >= 1:
    HeatingZone_1 = HeatingDevices[0]
    print("HeatingZone 1 : " + str(HeatingZone_1["hiveName"]))
    print("Get operation modes : " + str(session.heating.getOperationModes()))
    print("Current mode : " + str(session.heating.getMode(HeatingZone_1)))
    print("Current state : " + str(session.heating.getState(HeatingZone_1)))
    print("Current temperature : " + str(session.heating.currentTemperature(HeatingZone_1)))
    print("Target temperature : " + str(session.heating.targetTemperature(HeatingZone_1)))
    print("Get Min / Max temperatures : " + str(session.heating.minmaxTemperature(HeatingZone_1)))
    print("Get whether boost is currently On/Off : " + str(session.heating.getBoost(HeatingZone_1)))
    print("Boost time remaining : " + str(session.heating.getBoostTime(HeatingZone_1)))    
    print("Get schedule now/next/later : " + str(session.heating.getScheduleNowNextLater(HeatingZone_1)))
    print("Set mode to SCHEDULE: " + str(session.heating.setMode(HeatingZone_1, "SCHEDULE")))
    print("Current operation : " + str(session.heating.currentOperation(HeatingZone_1)))
    print("Set target temperature : " + str(session.heating.setTargetTemperature(HeatingZone_1, 15)))
    print("Turn boost on for 30 minutes at 15c: " + str(session.heating.turnBoostOn(HeatingZone_1, 30, 15)))
    print("Turn boost off : " + str(session.heating.turnBoostOff(HeatingZone_1)))
```


### Use the session object to interact with hotwater
Below is an example of how to use the `session` object to interact with all the different hotwater actions.

```Python
if len(WaterHeaters) >= 1:
    WaterHeater_1 = WaterHeaters[0]
    print("WaterHeater 1 : " + str(WaterHeater_1["hiveName"]))
    print("Get operation modes : " + str(session.hotwater.getOperationModes()))
    print("Current mode : " + str(session.hotwater.getMode(WaterHeater_1)))
    print("Get state : " + str(session.hotwater.getState(WaterHeater_1)))
    print("Get whether boost is currently On/Off: " + str(session.hotwater.getBoost(WaterHeater_1)))
    print("Get boost time remaining : " + str(session.hotwater.getBoostTime(WaterHeater_1)))
    print("Get schedule now/next/later : " + str(session.hotwater.getScheduleNowNextLater(WaterHeater_1)))
    print("Set mode to OFF : " + str(session.hotwater.setMode(WaterHeater_1, "OFF")))
    print("Turn boost on for 30 minutes : " + str(session.hotwater.turnBoostOn(WaterHeater_1, 30)))
    print("Turn boost off : " + str(session.hotwater.turnBoostOff(WaterHeater_1)))
```

### Use the session object to interact with lights
Below is an example of how to use the `session` object to interact with all the different light actions.

```Python
if len(Lights) >= 1:
    Light_1 = Lights[0]
    print("Light 1 : " + str(Light_1["hiveName"]))
    print("Get state : " + str(session.light.getState(Light_1)))
    print("Get brightness : " + str(session.light.getBrightness(Light_1)))
    print("Get min colour temperature : " + str(session.light.getMinColorTemp(Light_1)))
    print("Get max colour temperature : " + str(session.light.getMaxColorTemp(Light_1)))
    print("Get colour temperature : " + str(session.light.getColorTemp(Light_1)))
    print("Get colour : " + str(session.light.getColor(Light_1)))
    print("Get colour mode : " + str(session.light.getColorMode(Light_1)))
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
