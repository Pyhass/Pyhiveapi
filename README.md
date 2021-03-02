
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
Below is an example of how to use the session object to get all devices of each type from `deviceList` and store in a seperate list for each device type.

```Python
BinarySensors = session.deviceList["binary_sensor"]
HeatingDevices = session.deviceList["climate"]
Lights = session.deviceList["light"]
Sensors = session.deviceList["sensor"]
Switches = session.deviceList["switch"]
WaterHeaters = session.deviceList["water_heater"]
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
