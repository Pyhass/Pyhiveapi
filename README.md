
![CodeQL](https://github.com/Pyhive/Pyhiveapi/workflows/CodeQL/badge.svg) ![Python Linting](https://github.com/Pyhive/Pyhiveapi/workflows/Python%20package/badge.svg)

# Introduction
This is a libary which intefaces with the Hive smart home platform. 
This libary is built for to integrate with the Home Assistant platform,
but can be used independantly (See examples below.)


## Examples
Below are examples on how to use the libary independantly.

### Login
Below is an example how to login to Hive with 2FA if needed
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

### Get Hive Data
Below is an example how to data from the Hive platform 
using the session token aquired from login.

```Python
api = Hive.HiveApi()
data = api.getAllData(tokens["token"])
```
