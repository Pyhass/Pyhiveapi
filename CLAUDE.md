# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt -r requirements_test.txt

# Run all linters (via pre-commit)
pre-commit run --all-files

# Run tests
pytest tests/

# Run a single test
pytest tests/test_hub.py::test_hub_smoke

# Generate the sync (pyhiveapi) package from async source
python setup.py build_py

# Individual linters
black src/
flake8 src/
pylint src/
isort src/
bandit --configfile=tests/bandit.yaml src/
```

Direct commits to `master` are blocked by pre-commit hook.

## Architecture

The library exposes two packages from the same source:
- **`apyhiveapi`** — async package (the actual source in `src/`)
- **`pyhiveapi`** — sync package (auto-generated from `src/` during `setup.py build_py` using `unasync`)

Never edit generated sync files — edit the async source in `src/` only.

### Entry Point

`src/hive.py` — `Hive` class is the public API. It inherits `HiveSession` and composes all device modules:

```python
from apyhiveapi import Hive
hive = Hive(username="user@example.com", password="pass")
await hive.startSession(config)
```

### Core Modules

- **`src/session.py` (`HiveSession`)** — session lifecycle: login, token refresh (at 90% of lifetime), polling (`updateData`), and device discovery (`startSession` → `createDevices`). Handles AWS Cognito SRP auth flow including device login and SMS 2FA.
- **`src/api/hive_async_api.py` (`HiveApiAsync`)** — all async HTTP calls to `beekeeper.hivehome.com` and camera endpoints
- **`src/api/hive_auth_async.py` (`HiveAuthAsync`)** — AWS Cognito SRP authentication; device registration/login
- **`src/__init__.py`** — selects sync vs async implementations based on module name (`pyhiveapi` → sync, otherwise → async)

### Device Modules (all in `src/`)

Each device type (`action.py`, `alarm.py`, `camera.py`, `heating.py`, `hotwater.py`, `hub.py`, `light.py`, `plug.py`, `sensor.py`) follows the same pattern: receives the session as `self.session`, reads from `self.session.data`, and calls `self.session.api.*` to set state.

### Device Discovery (`createDevices`)

`PRODUCTS` and `DEVICES` dicts in `src/helper/const.py` map Hive product/device types to `addList(...)` calls (stored as strings and `eval`'d during `createDevices`). This is how the session builds `deviceList` for Home Assistant entity creation.

### Helpers

- `src/helper/const.py` — `HIVE_TYPES`, `PRODUCTS`, `DEVICES`, `HIVETOHA` mappings, HTTP constants
- `src/helper/hive_exceptions.py` — all custom exceptions (`HiveReauthRequired`, `HiveAuthError`, etc.)
- `src/helper/map.py` — `Map` class: dict wrapper allowing attribute-style access (`session.config.homeID`)
- `src/data/*.json` — fixture files for offline/file-based testing

### File-Based Testing

Set `username="use@file.com"` to make the session load data from `src/data/*.json` instead of calling the API. Used for development without live credentials.

### Token Refresh Strategy

Tokens refresh proactively at 90% of their lifetime (`_refreshThreshold = 0.90`). On `HiveRefreshTokenExpired` or `HiveFailedToRefreshTokens`, the session falls back to `_retryLogin` (3 attempts with backoff). A `HiveReauthRequired` exception propagates up when user interaction is needed (SMS 2FA).
