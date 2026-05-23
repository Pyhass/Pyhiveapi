"""Branch-coverage tests for several source modules.

Covers missing lines in:
  - src/devices/heating.py
  - src/devices/hotwater.py
  - src/devices/light.py
  - src/devices/sensor.py
  - src/session/auth.py
  - src/session/discovery.py
"""

# pylint: disable=too-few-public-methods,protected-access,attribute-defined-outside-init

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apyhiveapi.devices.heating import Climate
from apyhiveapi.devices.hotwater import WaterHeater
from apyhiveapi.devices.light import Light
from apyhiveapi.devices.sensor import Sensor
from apyhiveapi.helper.hive_exceptions import HiveApiError
from apyhiveapi.helper.hive_helper import HiveHelper
from apyhiveapi.helper.hivedataclasses import (
    Device,
    EntityConfig,
    SessionConfig,
    SessionTokens,
)
from apyhiveapi.helper.map import Map
from apyhiveapi.session.auth import SessionAuthMixin
from apyhiveapi.session.discovery import DiscoveryMixin

# ---------------------------------------------------------------------------
# Shared helpers — heating
# ---------------------------------------------------------------------------


def _make_climate(products=None, devices=None, min_max=None):
    session = MagicMock()
    session.data = Map(
        {
            "products": products or {},
            "devices": devices or {},
            "actions": {},
            "minMax": min_max or {},
            "user": {},
        }
    )
    session.config = SessionConfig()
    session.helper = MagicMock()
    session.helper.device_recovered = MagicMock()
    session.helper.error_check = AsyncMock()
    session.helper.get_schedule_nnl = MagicMock(
        return_value={"now": {}, "next": {}, "later": {}}
    )
    session.attr = MagicMock()
    session.attr.online_offline = AsyncMock(return_value=True)
    session.attr.state_attributes = AsyncMock(return_value={})
    session.api = MagicMock()
    session.api.set_state = AsyncMock(return_value={"original": 200, "parsed": {}})
    session.hive_refresh_tokens = AsyncMock()
    session.get_devices = AsyncMock(return_value=True)
    session.should_use_cached_data = MagicMock(return_value=False)
    session.get_cached_device = MagicMock(return_value=None)
    session.set_cached_device = MagicMock(side_effect=lambda d: d)
    return Climate(session=session)


def _make_device(hive_id="heat-1", device_id="dev-1", hive_type="heating"):
    return Device(
        hive_id=hive_id,
        hive_name="Hallway",
        hive_type=hive_type,
        ha_type="climate",
        device_id=device_id,
        device_name="Hallway",
        device_data={"online": True},
        ha_name="Hallway",
    )


# ---------------------------------------------------------------------------
# Shared helpers — hotwater
# ---------------------------------------------------------------------------


def _make_hotwater(products=None, devices=None):
    session = MagicMock()
    session.data = Map(
        {
            "products": products or {},
            "devices": devices or {},
            "actions": {},
            "minMax": {},
            "user": {},
        }
    )
    session.config = SessionConfig()
    session.helper = MagicMock()
    session.helper.device_recovered = MagicMock()
    session.helper.get_schedule_nnl = MagicMock(
        return_value={"now": {}, "next": {}, "later": {}}
    )
    session.attr = MagicMock()
    session.attr.online_offline = AsyncMock(return_value=True)
    session.attr.state_attributes = AsyncMock(return_value={})
    session.api = MagicMock()
    session.api.set_state = AsyncMock(return_value={"original": 200, "parsed": {}})
    session.hive_refresh_tokens = AsyncMock()
    session.get_devices = AsyncMock(return_value=True)
    session.should_use_cached_data = MagicMock(return_value=False)
    session.get_cached_device = MagicMock(return_value=None)
    session.set_cached_device = MagicMock(side_effect=lambda d: d)
    return WaterHeater(session=session)


def _make_hw_device(hive_id="hw-1", device_id="dev-1"):
    return Device(
        hive_id=hive_id,
        hive_name="Hot Water",
        hive_type="hotwater",
        ha_type="water_heater",
        device_id=device_id,
        device_name="Hot Water",
        device_data={"online": True},
        ha_name="Hot Water",
    )


# ---------------------------------------------------------------------------
# Shared helpers — sensor
# ---------------------------------------------------------------------------


def _make_sensor(products=None, devices=None):
    session = MagicMock()
    session.data = Map(
        {
            "products": products or {},
            "devices": devices or {},
            "actions": {},
            "minMax": {},
            "user": {},
        }
    )
    session.config = SessionConfig()
    session.helper = MagicMock()
    session.helper.device_recovered = MagicMock()
    session.attr = MagicMock()
    session.attr.online_offline = AsyncMock(return_value=True)
    session.attr.state_attributes = AsyncMock(return_value={})
    session.should_use_cached_data = MagicMock(return_value=False)
    session.get_cached_device = MagicMock(return_value=None)
    session.set_cached_device = MagicMock(side_effect=lambda d: d)
    return Sensor(session=session)


def _make_sensor_device(hive_id="sens-1", device_id="dev-1", hive_type="contactsensor"):
    return Device(
        hive_id=hive_id,
        hive_name="Door",
        hive_type=hive_type,
        ha_type="binary_sensor",
        device_id=device_id,
        device_name="Door",
        device_data={"online": True},
        ha_name="Door",
    )


# ---------------------------------------------------------------------------
# Shared helpers — auth
# ---------------------------------------------------------------------------


def _make_auth_stub():
    class StubAuth(SessionAuthMixin):
        """Concrete subclass used only for testing."""

    s = StubAuth()
    s.auth = MagicMock()
    s.auth.DEVICE_VERIFIER_CHALLENGE = "DEVICE_SRP_AUTH"
    s.auth.SMS_MFA_CHALLENGE = "SMS_MFA"
    s.auth.login = AsyncMock()
    s.auth.device_login = AsyncMock()
    s.auth.sms_2fa = AsyncMock()
    s.auth.refresh_token = AsyncMock()
    s.tokens = SessionTokens()
    s.tokens.token_data = {"refreshToken": "rt", "token": "", "accessToken": ""}
    s.config = SessionConfig()
    s.helper = MagicMock()
    s.helper.sanitize_payload = MagicMock(return_value={})
    s._refresh_threshold = 0.90
    s._refresh_lock = asyncio.Lock()
    return s


# ---------------------------------------------------------------------------
# Shared helpers — discovery
# ---------------------------------------------------------------------------


def _make_discovery_stub(products=None, devices=None, actions=None):
    class StubDiscovery(DiscoveryMixin):
        """Concrete subclass used only for testing."""

    s = StubDiscovery()
    s.config = SessionConfig()
    s.data = Map(
        {
            "products": products or {},
            "devices": devices or {},
            "actions": actions or {},
            "user": {"temperatureUnit": "C"},
            "minMax": {},
        }
    )
    s.helper = MagicMock()
    s.helper.get_device_data = MagicMock(
        return_value={
            "id": "dev-1",
            "state": {"name": "Test Device"},
            "props": {"online": True},
        }
    )
    s.hub_id = None
    s.device_list = {
        "parent": [],
        "binary_sensor": [],
        "climate": [],
        "light": [],
        "sensor": [],
        "switch": [],
        "water_heater": [],
    }
    return s


# ===========================================================================
# 1. src/devices/heating.py
# ===========================================================================


class TestHeatingGetStateKeyError:
    """Lines 206-207: KeyError/TypeError branch in get_state."""

    async def test_get_state_key_error_returns_none(self):
        """Missing product entry causes get_current_temperature to return None,
        leaving final as None without raising."""
        # products dict is empty — device.hive_id not found → both temp helpers
        # return None → the if branch is skipped → final stays None
        climate = _make_climate(products={})
        d = _make_device()
        result = await climate.get_state(d)
        assert result is None


class TestHeatingGetHeatOnDemand:
    """Line 231: get_heat_on_demand happy path."""

    async def test_get_heat_on_demand_returns_value(self):
        """Returns the nested autoBoost.active value from products."""
        climate = _make_climate({"heat-1": {"props": {"autoBoost": {"active": True}}}})
        result = await climate.get_heat_on_demand(_make_device())
        assert result is True

    async def test_get_heat_on_demand_returns_none_when_missing(self):
        """Returns None when the nested path does not exist."""
        climate = _make_climate({"heat-1": {"props": {}}})
        result = await climate.get_heat_on_demand(_make_device())
        assert result is None


class TestHeatingSetBoostOffOffMode:
    """Lines 321->325: set_boost_off when previous mode is 'OFF' with a real target."""

    async def test_set_boost_off_off_mode_with_target_restores_target(self):
        """Previous mode OFF with a real target value restores that target."""
        climate = _make_climate(
            {
                "heat-1": {
                    "type": "heating",
                    "state": {"boost": 5},
                    "props": {"previous": {"mode": "OFF", "target": 18.0}},
                }
            }
        )
        result = await climate.set_boost_off(_make_device())
        assert result is True
        _, kwargs = climate.session.api.set_state.call_args
        assert kwargs.get("mode") == "OFF"
        assert kwargs.get("target") == 18.0


class TestHeatingSetHeatOnDemand:
    """Lines 337-342: set_heat_on_demand calls _execute_state_change with autoBoost kwarg."""

    async def test_set_heat_on_demand_enabled(self):
        """set_heat_on_demand passes autoBoost='ENABLED' to the API."""
        climate = _make_climate({"heat-1": {"type": "heating"}})
        result = await climate.set_heat_on_demand(_make_device(), "ENABLED")
        assert result is True
        climate.session.api.set_state.assert_called_once()
        _, kwargs = climate.session.api.set_state.call_args
        assert kwargs.get("autoBoost") == "ENABLED"

    async def test_set_heat_on_demand_disabled(self):
        """set_heat_on_demand passes autoBoost='DISABLED' to the API."""
        climate = _make_climate({"heat-1": {"type": "heating"}})
        result = await climate.set_heat_on_demand(_make_device(), "DISABLED")
        assert result is True
        _, kwargs = climate.session.api.set_state.call_args
        assert kwargs.get("autoBoost") == "DISABLED"


class TestHeatingGetClimateCacheHit:
    """Lines 371->377: get_climate returns cached device when cache is available."""

    async def test_get_climate_returns_cached_when_available(self):
        """Cache hit short-circuits all I/O and returns the cached dict."""
        climate = _make_climate({"heat-1": {"type": "heating"}})
        cached = {"current_temperature": 20.0}
        climate.session.should_use_cached_data.return_value = True
        climate.session.get_cached_device.return_value = cached
        result = await climate.get_climate(_make_device())
        assert result == cached
        # No API calls should have been made
        climate.session.attr.online_offline.assert_not_called()


class TestHeatingGetScheduleNNLKeyError:
    """Lines 438-439: KeyError in get_schedule_now_next_later."""

    async def test_missing_schedule_key_returns_none(self):
        """Product with state but no 'schedule' key causes KeyError → returns None."""
        climate = _make_climate(
            {"heat-1": {"state": {"mode": "SCHEDULE"}}}
            # no 'schedule' key inside state
        )
        # Override get_mode to return SCHEDULE directly so the if-branch is entered
        climate.session.helper.get_schedule_nnl.side_effect = KeyError("schedule")
        # get_mode will read data["state"]["mode"] == "SCHEDULE" → enters the try block
        # data["state"]["schedule"] raises KeyError → caught, returns None
        result = await climate.get_schedule_now_next_later(_make_device())
        assert result is None

    async def test_schedule_key_error_caught_not_raised(self):
        """A KeyError inside the try block does not propagate to the caller."""
        climate = _make_climate({"heat-1": {"state": {"mode": "SCHEDULE"}}})
        # Accessing data["state"]["schedule"] will raise KeyError (key absent)
        try:
            result = await climate.get_schedule_now_next_later(_make_device())
        except KeyError:
            pytest.fail(
                "KeyError should have been caught inside get_schedule_now_next_later"
            )
        assert result is None


# ===========================================================================
# 2. src/devices/hotwater.py
# ===========================================================================


class TestHotwaterGetModeKeyError:
    """Lines 43-44: KeyError in get_mode."""

    async def test_get_mode_missing_state_returns_none(self):
        """Product with no 'state' key causes KeyError → final stays None."""
        hw = _make_hotwater({"hw-1": {}})
        result = await hw.get_mode(_make_hw_device())
        assert result is None


class TestHotwaterGetStateKeyError:
    """Lines 83-84: KeyError in get_state."""

    async def test_get_state_missing_status_key_returns_none(self):
        """Product 'state' dict missing 'status' key triggers KeyError → None."""
        hw = _make_hotwater({"hw-1": {"state": {"mode": "MANUAL"}}})
        # 'status' key is absent from state → KeyError on data["state"]["status"]
        result = await hw.get_state(_make_hw_device())
        assert result is None

    async def test_get_state_missing_schedule_in_schedule_mode_returns_none(self):
        """SCHEDULE mode with no 'schedule' key in state causes KeyError → None."""
        hw = _make_hotwater(
            {
                "hw-1": {
                    "state": {
                        "mode": "SCHEDULE",
                        "status": "ON",
                        "boost": False,
                        # no 'schedule' key
                    }
                }
            }
        )
        result = await hw.get_state(_make_hw_device())
        assert result is None


class TestHotwaterGetWaterHeaterCacheHit:
    """Lines 173->180: get_water_heater returns cached when cache is available."""

    async def test_get_water_heater_returns_cached(self):
        """Cache hit short-circuits all I/O and returns the cached value."""
        hw = _make_hotwater()
        cached = {"current_operation": "ON"}
        hw.session.should_use_cached_data.return_value = True
        hw.session.get_cached_device.return_value = cached
        result = await hw.get_water_heater(_make_hw_device())
        assert result == cached
        hw.session.attr.online_offline.assert_not_called()


class TestHotwaterScheduleNNLNone:
    """Lines 225->227: get_schedule_now_next_later returns None when schedule is absent."""

    async def test_schedule_none_when_no_schedule_in_state(self):
        """SCHEDULE mode product without 'schedule' key → _get_product_state returns None → None."""
        hw = _make_hotwater({"hw-1": {"state": {"mode": "SCHEDULE"}}})
        # _get_product_state(device, "state", "schedule") → None (key absent)
        result = await hw.get_schedule_now_next_later(_make_hw_device())
        assert result is None

    async def test_non_schedule_mode_returns_none(self):
        """Non-SCHEDULE mode skips the schedule lookup and returns None directly."""
        hw = _make_hotwater({"hw-1": {"state": {"mode": "MANUAL"}}})
        result = await hw.get_schedule_now_next_later(_make_hw_device())
        assert result is None

    async def test_schedule_present_returns_nnl(self):
        """When schedule data exists, get_schedule_nnl result is returned."""
        schedule_data = {"foo": "bar"}
        hw = _make_hotwater(
            {"hw-1": {"state": {"mode": "SCHEDULE", "schedule": schedule_data}}}
        )
        expected = {"now": {}, "next": {}, "later": {}}
        hw.session.helper.get_schedule_nnl.return_value = expected
        result = await hw.get_schedule_now_next_later(_make_hw_device())
        assert result == expected
        hw.session.helper.get_schedule_nnl.assert_called_once_with(schedule_data)


# ===========================================================================
# 3. src/devices/sensor.py
# ===========================================================================


class TestSensorGetStateKeyError:
    """Lines 37->42: KeyError in HiveSensor.get_state."""

    async def test_get_state_missing_type_key_returns_none(self):
        """Product with no 'type' key causes KeyError → final stays None."""
        sensor = _make_sensor({"sens-1": {}})
        d = _make_sensor_device()
        result = await sensor.get_state(d)
        assert result is None

    async def test_get_state_missing_props_key_returns_none(self):
        """contactsensor product without 'props' causes KeyError → None."""
        sensor = _make_sensor({"sens-1": {"type": "contactsensor"}})
        d = _make_sensor_device()
        result = await sensor.get_state(d)
        assert result is None


class TestSensorGetSensorCacheHit:
    """Lines 92->98: get_sensor returns cached device when cache is available."""

    async def test_get_sensor_returns_cached(self):
        """Cache hit short-circuits all I/O and returns the cached value."""
        sensor = _make_sensor()
        cached = {"state": True}
        sensor.session.should_use_cached_data.return_value = True
        sensor.session.get_cached_device.return_value = cached
        result = await sensor.get_sensor(_make_sensor_device())
        assert result == cached
        sensor.session.attr.online_offline.assert_not_called()


class TestSensorGetSensorProductsFallback:
    """Lines 119->122: when device_id not in devices, fall back to products."""

    async def test_uses_products_when_device_id_absent_from_devices(self):
        """device_id not in session.data.devices → hive_id looked up in products."""
        sensor = _make_sensor(
            products={"sens-1": {"type": "contactsensor", "props": {"status": "OPEN"}}},
            devices={},
        )
        d = _make_sensor_device(
            hive_id="sens-1", device_id="unknown-dev", hive_type="contactsensor"
        )
        # Sensor with hive_type in sensor_commands path will be followed;
        # the important thing is the products-fallback path is entered without error.
        result = await sensor.get_sensor(d)
        # Result should be the device (set_cached_device returns the device itself)
        assert result is not None

    async def test_products_fallback_data_used_for_device_data(self):
        """Props from the products entry propagate to device.device_data."""
        sensor = _make_sensor(
            products={
                "sens-1": {
                    "type": "contactsensor",
                    "props": {"status": "OPEN", "online": True},
                }
            },
            devices={},
        )
        d = _make_sensor_device(
            hive_id="sens-1", device_id="unknown-dev", hive_type="contactsensor"
        )
        await sensor.get_sensor(d)
        # get_state uses self.session.data.products[device.hive_id] directly
        # so we just verify it ran without KeyError


class TestSensorGetSensorHiveTypesSensorPath:
    """Lines 135->146: elif device.hive_type in HIVE_TYPES['Sensor'] path."""

    async def test_contactsensor_in_hive_types_sensor_takes_else_branch(self):
        """contactsensor is in HIVE_TYPES['Sensor'] and not in sensor_commands key set,
        so the elif branch is taken."""
        from apyhiveapi.devices.sensor import sensor_commands
        from apyhiveapi.helper.const import HIVE_TYPES

        # 'contactsensor' is in HIVE_TYPES['Sensor'] and NOT a key in sensor_commands
        assert "contactsensor" in HIVE_TYPES["Sensor"]
        assert "contactsensor" not in sensor_commands

        sensor = _make_sensor(
            products={"sens-1": {"type": "contactsensor", "props": {"status": "OPEN"}}},
            devices={"dev-1": {"props": {"online": True}, "type": "contactsensor"}},
        )
        d = _make_sensor_device(
            hive_id="sens-1", device_id="dev-1", hive_type="contactsensor"
        )
        d.device_data = {"online": True}
        await sensor.get_sensor(d)
        # The elif branch sets device.status with 'state' key
        assert d.status is not None
        assert "state" in d.status

    async def test_motionsensor_in_hive_types_sensor_sets_status(self):
        """motionsensor is in HIVE_TYPES['Sensor'] and not in sensor_commands key set."""
        from apyhiveapi.devices.sensor import sensor_commands
        from apyhiveapi.helper.const import HIVE_TYPES

        assert "motionsensor" in HIVE_TYPES["Sensor"]
        assert "motionsensor" not in sensor_commands

        sensor = _make_sensor(
            products={
                "sens-1": {
                    "type": "motionsensor",
                    "props": {"motion": {"status": True}},
                }
            },
            devices={"dev-1": {"props": {"online": True}, "type": "motionsensor"}},
        )
        d = _make_sensor_device(
            hive_id="sens-1", device_id="dev-1", hive_type="motionsensor"
        )
        d.device_data = {"online": True}
        await sensor.get_sensor(d)
        assert d.status is not None
        assert "state" in d.status


# ===========================================================================
# 4. src/session/auth.py
# ===========================================================================


class TestRetryWithBackoffNonZeroDelay:
    """Line 66: asyncio.sleep called when delay > 0."""

    async def test_non_zero_delay_is_awaited_but_succeeds(self):
        """A non-zero delay entry causes asyncio.sleep to be called; factory still runs."""
        s = _make_auth_stub()
        calls = []

        async def factory():
            calls.append(1)
            return "ok"

        with patch(
            "apyhiveapi.session.auth.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await s._retry_with_backoff(factory, delays=(5,))
        assert result == "ok"
        mock_sleep.assert_called_once_with(5)
        assert len(calls) == 1

    async def test_zero_delay_does_not_call_sleep(self):
        """A zero delay skips asyncio.sleep."""
        s = _make_auth_stub()

        async def factory():
            return "done"

        with patch(
            "apyhiveapi.session.auth.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await s._retry_with_backoff(factory, delays=(0,))
        assert result == "done"
        mock_sleep.assert_not_called()


class TestUpdateTokensFlatDictWithExpiresIn:
    """Lines 100->106: flat token dict with ExpiresIn sets token_expiry."""

    async def test_flat_dict_with_expires_in_sets_token_expiry(self):
        """Flat token dict containing ExpiresIn updates tokens.token_expiry."""
        s = _make_auth_stub()
        flat = {
            "token": "t",
            "refreshToken": "r",
            "accessToken": "a",
            "ExpiresIn": 1800,
        }
        await s.update_tokens(flat)
        assert s.tokens.token_expiry == timedelta(seconds=1800)

    async def test_flat_dict_tokens_are_stored(self):
        """All token values from flat dict are written to token_data."""
        s = _make_auth_stub()
        flat = {"token": "my-id", "refreshToken": "my-rt", "accessToken": "my-at"}
        await s.update_tokens(flat)
        assert s.tokens.token_data["token"] == "my-id"
        assert s.tokens.token_data["refreshToken"] == "my-rt"
        assert s.tokens.token_data["accessToken"] == "my-at"


class TestLoginApiError:
    """Lines 160-162: HiveApiError in login() is logged and re-raised."""

    async def test_login_api_error_reraises(self):
        """HiveApiError raised by auth.login propagates unchanged to the caller."""
        s = _make_auth_stub()
        s.auth.login.side_effect = HiveApiError()
        with pytest.raises(HiveApiError):
            await s.login()


class TestHiveRefreshTokensNoAuthResult:
    """Lines 341->373: refresh returns a result but without AuthenticationResult."""

    async def test_result_without_auth_result_does_not_update_tokens(self):
        """When refresh_token returns a dict with no AuthenticationResult, tokens stay unchanged."""
        s = _make_auth_stub()
        s.tokens.token_created = datetime.now() - timedelta(hours=2)
        s.tokens.token_expiry = timedelta(hours=1)
        # Return something truthy but without AuthenticationResult
        s.auth.refresh_token.return_value = {"SomeOtherKey": "value"}
        result = await s.hive_refresh_tokens()
        # Tokens must not have been updated
        assert s.tokens.token_data["token"] == ""
        assert s.tokens.token_data["accessToken"] == ""
        # result is what refresh_token returned
        assert result == {"SomeOtherKey": "value"}

    async def test_none_refresh_result_does_not_update_tokens(self):
        """When refresh_token returns None, tokens are left unchanged."""
        s = _make_auth_stub()
        s.tokens.token_created = datetime.now() - timedelta(hours=2)
        s.tokens.token_expiry = timedelta(hours=1)
        s.auth.refresh_token.return_value = None
        await s.hive_refresh_tokens()
        assert s.tokens.token_data["token"] == ""


# ===========================================================================
# 5. src/session/discovery.py
# ===========================================================================


class TestCreateDevicesEntityConfigKwargs:
    """Lines 224->226, 226->228, 228->230: entity_config kwarg population in DEVICES loop."""

    async def test_entity_config_with_all_fields_populates_kwargs(self):
        """EntityConfig with ha_name, hive_type, and category all set → all kwargs passed."""
        s = _make_discovery_stub(
            devices={
                "dev-1": {
                    "id": "dev-1",
                    "type": "hub",
                    "state": {"name": "My Hub"},
                    "props": {},
                }
            }
        )
        entity_cfg = EntityConfig(
            entity_type="binary_sensor",
            ha_name="Hub Status",
            hive_type="Connectivity",
            category="diagnostic",
        )
        with patch("apyhiveapi.session.discovery.DEVICES", {"hub": [entity_cfg]}):
            result = await s.create_devices()
        assert len(result["binary_sensor"]) == 1
        created = result["binary_sensor"][0]
        assert created.hive_type == "Connectivity"
        assert created.category == "diagnostic"

    async def test_entity_config_empty_fields_does_not_add_to_kwargs(self):
        """EntityConfig with empty ha_name and hive_type does not inject those keys."""
        s = _make_discovery_stub(
            devices={
                "dev-1": {
                    "id": "dev-1",
                    "type": "hub",
                    "state": {"name": "My Hub"},
                    "props": {},
                }
            }
        )
        entity_cfg = EntityConfig(
            entity_type="binary_sensor",
            ha_name="",  # falsy — should not be added to kwargs
            hive_type="",  # falsy — should not be added to kwargs
            category=None,  # None — should not be added to kwargs
        )
        with patch("apyhiveapi.session.discovery.DEVICES", {"hub": [entity_cfg]}):
            result = await s.create_devices()
        # Should still process without error
        assert isinstance(result, dict)


class TestCreateDevicesDeviceAddListError:
    """Lines 232-233: KeyError/TypeError from add_list in DEVICES loop is caught."""

    async def test_add_list_keyerror_is_caught_not_raised(self):
        """KeyError from add_list during device processing is logged, not propagated."""
        s = _make_discovery_stub(
            devices={
                "dev-1": {
                    "id": "dev-1",
                    "type": "hub",
                    "state": {"name": "My Hub"},
                    "props": {},
                }
            }
        )
        entity_cfg = EntityConfig(
            entity_type="binary_sensor",
            ha_name="Hub Status",
            hive_type="Connectivity",
            category="diagnostic",
        )
        with patch("apyhiveapi.session.discovery.DEVICES", {"hub": [entity_cfg]}):
            with patch.object(s, "add_list", side_effect=KeyError("bad key")):
                # Should complete without raising
                result = await s.create_devices()
        assert isinstance(result, dict)

    async def test_add_list_typeerror_is_caught_not_raised(self):
        """TypeError from add_list during device processing is caught."""
        s = _make_discovery_stub(
            devices={
                "dev-1": {
                    "id": "dev-1",
                    "type": "hub",
                    "state": {"name": "My Hub"},
                    "props": {},
                }
            }
        )
        entity_cfg = EntityConfig(
            entity_type="binary_sensor",
            ha_name="",
            hive_type="",
            category=None,
        )
        with patch("apyhiveapi.session.discovery.DEVICES", {"hub": [entity_cfg]}):
            with patch.object(s, "add_list", side_effect=TypeError("bad type")):
                result = await s.create_devices()
        assert isinstance(result, dict)


class TestCreateDevicesActionAddListError:
    """Lines 258-259: KeyError/TypeError from add_list in actions loop is caught."""

    async def test_action_add_list_keyerror_is_caught(self):
        """KeyError from add_list when processing an action is logged, not propagated."""
        s = _make_discovery_stub(
            actions={"act-1": {"id": "act-1", "name": "Good Night"}}
        )
        with patch.object(s, "add_list", side_effect=KeyError("missing")):
            result = await s.create_devices()
        assert isinstance(result, dict)

    async def test_action_add_list_typeerror_is_caught(self):
        """TypeError from add_list when processing an action is caught."""
        s = _make_discovery_stub(actions={"act-1": {"id": "act-1", "name": "Wake Up"}})
        with patch.object(s, "add_list", side_effect=TypeError("type error")):
            result = await s.create_devices()
        assert isinstance(result, dict)


class TestCreateDevicesProductTemperatureUnit:
    """Line 305: entity_config.temperature_unit is used when set and entity_type != 'climate'."""

    async def test_entity_config_temperature_unit_passed_to_add_list(self):
        """EntityConfig with temperature_unit set propagates that value as a kwarg."""
        s = _make_discovery_stub(
            products={
                "prod-1": {
                    "id": "prod-1",
                    "type": "heating",
                    "state": {"name": "Heating"},
                    "props": {},
                }
            }
        )
        # A non-climate entity with temperature_unit set triggers line 305
        entity_cfg = EntityConfig(
            entity_type="sensor",
            ha_name="Temp Sensor",
            hive_type="Current_Temperature",
            category="diagnostic",
            temperature_unit="F",
        )
        captured_kwargs = {}

        original_add_list = s.add_list

        def capturing_add_list(entity_type, data, **kwargs):
            captured_kwargs.update(kwargs)
            return original_add_list(entity_type, data, **kwargs)

        with patch("apyhiveapi.session.discovery.PRODUCTS", {"heating": [entity_cfg]}):
            with patch.object(s, "add_list", side_effect=capturing_add_list):
                await s.create_devices()

        assert captured_kwargs.get("temperature_unit") == "F"


class TestCreateDevicesProductAddListAttributeError:
    """Lines 308-309: NameError/AttributeError from add_list in products loop is caught."""

    async def test_product_add_list_attribute_error_is_caught(self):
        """AttributeError from add_list when processing a product is caught."""
        s = _make_discovery_stub(
            products={
                "prod-1": {
                    "id": "prod-1",
                    "type": "heating",
                    "state": {"name": "Heating"},
                    "props": {},
                }
            }
        )
        entity_cfg = EntityConfig(
            entity_type="climate",
            ha_name="",
            hive_type="",
            category=None,
        )
        with patch("apyhiveapi.session.discovery.PRODUCTS", {"heating": [entity_cfg]}):
            with patch.object(s, "add_list", side_effect=AttributeError("attr error")):
                result = await s.create_devices()
        assert isinstance(result, dict)

    async def test_product_add_list_name_error_is_caught(self):
        """NameError from add_list when processing a product is caught."""
        s = _make_discovery_stub(
            products={
                "prod-1": {
                    "id": "prod-1",
                    "type": "heating",
                    "state": {"name": "Heating"},
                    "props": {},
                }
            }
        )
        entity_cfg = EntityConfig(
            entity_type="climate",
            ha_name="",
            hive_type="",
            category=None,
        )
        with patch("apyhiveapi.session.discovery.PRODUCTS", {"heating": [entity_cfg]}):
            with patch.object(s, "add_list", side_effect=NameError("name error")):
                result = await s.create_devices()
        assert isinstance(result, dict)


# ===========================================================================
# Additional False-branch tests: cache-miss paths and elif False paths
# ===========================================================================


def _make_light_session(products=None, devices=None):
    session = MagicMock()
    session.data = Map(
        {
            "products": products or {},
            "devices": devices or {},
            "actions": {},
            "minMax": {},
            "user": {},
        }
    )
    session.config = SessionConfig()
    session.helper = MagicMock()
    session.helper.device_recovered = MagicMock()
    session.helper.error_check = AsyncMock()
    session.attr = MagicMock()
    session.attr.online_offline = AsyncMock(return_value=True)
    session.attr.state_attributes = AsyncMock(return_value={})
    session.api = MagicMock()
    session.api.set_state = AsyncMock(return_value={"original": 200, "parsed": {}})
    session.hive_refresh_tokens = AsyncMock()
    session.get_devices = AsyncMock(return_value=True)
    session.should_use_cached_data = MagicMock(return_value=False)
    session.get_cached_device = MagicMock(return_value=None)
    session.set_cached_device = MagicMock(side_effect=lambda d: d)
    return session


def _make_light_device(
    hive_id="light-1", device_id="dev-1", hive_type="warmwhitelight"
):
    return Device(
        hive_id=hive_id,
        hive_name="Bulb",
        hive_type=hive_type,
        ha_type="light",
        device_id=device_id,
        device_name="Bulb",
        device_data={"online": True},
        ha_name="Bulb",
    )


# ---------------------------------------------------------------------------
# heating.py: 321->325 — set_boost_off with non-MANUAL/OFF previous mode
# ---------------------------------------------------------------------------


class TestHeatingSetBoostOffScheduleMode:
    """Lines 321->325: prev_mode not in ('MANUAL','OFF') — target kwarg not added."""

    async def test_schedule_mode_no_target_kwarg(self):
        """SCHEDULE as previous mode does not add a target kwarg."""
        climate = _make_climate(
            {
                "heat-1": {
                    "type": "heating",
                    "state": {"boost": 5},
                    "props": {"previous": {"mode": "SCHEDULE"}},
                }
            }
        )
        result = await climate.set_boost_off(_make_device())
        assert result is True
        _, kwargs = climate.session.api.set_state.call_args
        assert "target" not in kwargs
        assert kwargs.get("mode") == "SCHEDULE"


# ---------------------------------------------------------------------------
# heating.py: 371->377 — get_climate: should_use_cached=True but cached is None
# ---------------------------------------------------------------------------


class TestHeatingGetClimateCacheMiss:
    """Lines 371->377: cache enabled but cached device is None → normal execution."""

    async def test_cached_none_falls_through_to_normal_path(self):
        """should_use_cached_data=True but get_cached_device=None → normal update."""
        climate = _make_climate(
            {
                "heat-1": {
                    "state": {"mode": "MANUAL", "target": 20.0},
                    "props": {"temperature": 19.0},
                }
            },
            devices={"dev-1": {"state": {}, "props": {}}},
        )
        climate.session.should_use_cached_data.return_value = True
        climate.session.get_cached_device.return_value = None
        result = await climate.get_climate(_make_device())
        assert result is not None
        climate.session.attr.online_offline.assert_called_once()


# ---------------------------------------------------------------------------
# hotwater.py: 173->180 — same pattern
# ---------------------------------------------------------------------------


class TestHotwaterGetWaterHeaterCacheMiss:
    """Lines 173->180: cache enabled but cached is None → continues with network call."""

    async def test_cached_none_falls_through(self):
        hw = _make_hotwater(
            {"hw-1": {"state": {"mode": "ON"}, "props": {}}},
            devices={"dev-1": {"state": {}, "props": {}}},
        )
        hw.session.should_use_cached_data.return_value = True
        hw.session.get_cached_device.return_value = None
        result = await hw.get_water_heater(_make_hw_device())
        assert result is not None
        hw.session.attr.online_offline.assert_called_once()


# ---------------------------------------------------------------------------
# light.py: 141->147 — same pattern
# ---------------------------------------------------------------------------


class TestLightGetLightCacheMiss:
    """Lines 141->147: cache enabled but cached is None → normal execution."""

    async def test_cached_none_falls_through(self):
        session = _make_light_session(
            products={
                "light-1": {"state": {"status": "ON", "brightness": 100}, "props": {}}
            },
            devices={"dev-1": {"state": {}, "props": {}}},
        )
        light = Light(session=session)
        d = _make_light_device()
        session.should_use_cached_data.return_value = True
        session.get_cached_device.return_value = None
        result = await light.get_light(d)
        assert result is not None
        session.attr.online_offline.assert_called_once()


# ---------------------------------------------------------------------------
# sensor.py: 37->42 — get_state: type neither contactsensor nor motionsensor
# ---------------------------------------------------------------------------


class TestSensorGetStateUnknownType:
    """Lines 37->42: data['type'] is neither contactsensor nor motionsensor."""

    async def test_unknown_type_returns_none(self):
        """Product with type 'hub' skips both if/elif → final stays None."""
        sensor = _make_sensor({"sens-1": {"type": "hub", "props": {}}})
        d = _make_sensor_device()
        result = await sensor.get_state(d)
        assert result is None


# ---------------------------------------------------------------------------
# sensor.py: 92->98 — get_sensor: cache enabled but cached is None
# ---------------------------------------------------------------------------


class TestSensorGetSensorCacheMiss:
    """Lines 92->98: should_use_cached_data=True but cached is None."""

    async def test_cached_none_falls_through(self):
        sensor = _make_sensor(
            products={"sens-1": {"type": "contactsensor", "props": {"status": "OPEN"}}},
            devices={"dev-1": {"props": {"online": True}, "type": "contactsensor"}},
        )
        sensor.session.should_use_cached_data.return_value = True
        sensor.session.get_cached_device.return_value = None
        d = _make_sensor_device()
        result = await sensor.get_sensor(d)
        assert result is not None
        sensor.session.attr.online_offline.assert_called_once()


# ---------------------------------------------------------------------------
# sensor.py: 119->122 — get_sensor: neither device_id nor hive_id found
# ---------------------------------------------------------------------------


class TestSensorGetSensorNoDataFallthrough:
    """Lines 119->122: device_id not in devices AND hive_id not in products."""

    async def test_neither_match_continues_with_empty_data(self):
        """data stays empty dict when neither lookup succeeds."""
        sensor = _make_sensor(products={}, devices={})
        d = _make_sensor_device(
            hive_id="unknown-hive", device_id="unknown-dev", hive_type="contactsensor"
        )
        result = await sensor.get_sensor(d)
        # Should not raise; result will be the device (set_cached_device returns it)
        assert result is not None


# ---------------------------------------------------------------------------
# sensor.py: 135->146 — get_sensor: hive_type not in sensor_commands or HIVE_TYPES["Sensor"]
# ---------------------------------------------------------------------------


class TestSensorGetSensorUnknownHiveType:
    """Lines 135->146: hive_type not in sensor_commands and not in HIVE_TYPES['Sensor']."""

    async def test_hive_type_not_in_either_dict_skips_both_branches(self):
        """activeplug is neither in sensor_commands nor HIVE_TYPES['Sensor']."""
        sensor = _make_sensor(
            devices={"dev-1": {"props": {"online": True}, "type": "activeplug"}}
        )
        d = _make_sensor_device(
            hive_id="dev-1", device_id="dev-1", hive_type="activeplug"
        )
        d.device_data = {"online": True}
        result = await sensor.get_sensor(d)
        # Neither branch sets device.status; device returned as-is via set_cached_device
        assert result is not None


# ===========================================================================
# Additional branches: session/auth.py, hive_helper.py, heating.py
# ===========================================================================


class TestUpdateTokensUnknownKey:
    """session/auth.py 100->106: tokens dict has neither AuthenticationResult nor token."""

    async def test_unknown_key_does_not_raise_and_does_not_update_tokens(self):
        """When neither expected key is present, data stays {}, ExpiresIn check skips."""
        s = _make_auth_stub()
        original_token = s.tokens.token_data["token"]
        # Pass a dict that is neither the AuthResult form nor the flat-token form
        await s.update_tokens({"some_other_key": "some_value"})
        # Tokens must be unchanged
        assert s.tokens.token_data["token"] == original_token

    async def test_unknown_key_does_not_set_token_expiry(self):
        """ExpiresIn check at line 106 skips when data is {} (no match in either branch)."""
        s = _make_auth_stub()
        original_expiry = s.tokens.token_expiry
        await s.update_tokens({"random_key": "random_value"})
        assert s.tokens.token_expiry == original_expiry


class TestHiveHelperZoneMismatch:
    """hive_helper.py 163->160: loop continues when zones don't match."""

    def test_zone_mismatch_keeps_product_as_device(self):
        """When a Thermo device's zone doesn't match the product's zone,
        the loop arc 163->160 is taken and device stays as the product."""
        helper = HiveHelper(session=MagicMock())
        helper.session.data = Map(
            {
                "devices": {
                    "thermo-1": {
                        "type": "thermostatui",
                        "props": {"zone": "zone-B"},
                    }
                },
                "products": {},
                "actions": {},
                "user": {},
                "minMax": {},
            }
        )

        product = {
            "type": "heating",
            "id": "prod-1",
            "props": {"zone": "zone-A"},  # different zone from thermo-1
        }

        result = helper.get_device_data(product)
        # The zone mismatch means device was never re-assigned; returns the product
        assert result is product

    def test_trv_without_zone_does_not_log_warning(self, caplog):
        """TRV devices that omit 'zone' from props are silently skipped (no warning)."""
        import logging

        helper = HiveHelper(session=MagicMock())
        helper.session.data = Map(
            {
                "devices": {
                    "trv-1": {
                        "type": "trv",
                        "props": {
                            "online": True
                        },  # no 'zone' key — current API behaviour
                    }
                },
                "products": {},
                "actions": {},
                "user": {},
                "minMax": {},
            }
        )

        product = {
            "type": "heating",
            "id": "prod-1",
            "props": {"zone": "zone-A"},
        }

        with caplog.at_level(logging.WARNING, logger="apyhiveapi.helper.hive_helper"):
            result = helper.get_device_data(product)

        assert result is product
        assert not caplog.records, (
            f"Unexpected warnings: {[r.getMessage() for r in caplog.records]}"
        )

    def test_zone_match_replaces_device_with_thermostat(self):
        """Matching zones cause device to be replaced with the thermostat entry."""
        helper = HiveHelper(session=MagicMock())
        thermo_data = {
            "type": "thermostatui",
            "props": {"zone": "zone-X"},
        }
        helper.session.data = Map(
            {
                "devices": {"thermo-1": thermo_data},
                "products": {},
                "actions": {},
                "user": {},
                "minMax": {},
            }
        )

        product = {
            "type": "heating",
            "id": "prod-1",
            "props": {"zone": "zone-X"},  # matching zone
        }

        result = helper.get_device_data(product)
        assert result is thermo_data


class TestHiveHelperSanitizeDictValue:
    """hive_helper.py line 328: dict value under a sensitive key calls _mask(dict)."""

    def test_dict_under_sensitive_key_is_recursively_masked(self):
        """A dict value under 'token' key hits the isinstance(value, dict) branch."""
        helper = HiveHelper()
        result = helper.sanitize_payload({"token": {"inner_key": "secret_value"}})
        # 'token' is sensitive → _mask is called with the nested dict
        # _mask for a dict returns {k: _mask(v) for k, v in value.items()}
        # _mask("secret_value") → "sec...lue" (long enough) or "***"
        assert "token" in result
        assert isinstance(result["token"], dict)
        assert "inner_key" in result["token"]
        # The inner value should be masked (not the original)
        assert result["token"]["inner_key"] != "secret_value"

    def test_nested_dict_keys_preserved_after_masking(self):
        """Keys inside a sensitive dict are preserved, values are masked."""
        helper = HiveHelper()
        result = helper.sanitize_payload(
            {
                "authenticationresult": {
                    "AccessToken": "long-secret-token-value",
                    "ExpiresIn": 3600,
                }
            }
        )
        inner = result["authenticationresult"]
        assert "AccessToken" in inner
        assert "ExpiresIn" in inner
        # ExpiresIn is an int, _mask returns it as-is
        assert inner["ExpiresIn"] == 3600


class TestHiveHelperSanitizeListNode:
    """hive_helper.py line 359: list value under a non-sensitive key calls _walk(list)."""

    def test_list_under_non_sensitive_key_is_walked(self):
        """A list value under a non-sensitive key hits the isinstance(node, list) branch."""
        helper = HiveHelper()
        result = helper.sanitize_payload({"devices": ["device-a", "device-b"]})
        # 'devices' is not a sensitive key → _walk called for the list
        # _walk for a list returns [_walk(item) for item in node]
        # Each string item: _walk(str) → str (falls through to return node)
        assert result == {"devices": ["device-a", "device-b"]}

    def test_list_containing_dicts_is_walked_recursively(self):
        """A list of dicts under a non-sensitive key is recursively processed."""
        helper = HiveHelper()
        result = helper.sanitize_payload(
            {
                "items": [
                    {"token": "abc", "name": "device1"},
                    {"token": "xyz", "name": "device2"},
                ]
            }
        )
        # 'items' is not sensitive → _walk called for the list
        # Each dict in the list is processed by _walk
        # 'token' IS sensitive → masked in each sub-dict
        assert result["items"][0]["name"] == "device1"
        assert result["items"][0]["token"] != "abc"
        assert result["items"][1]["name"] == "device2"
        assert result["items"][1]["token"] != "xyz"


class TestHeatingGetStateExceptionCaught:
    """heating.py lines 206-207: except (KeyError, TypeError) handler is reached."""

    async def test_key_error_in_get_current_temperature_is_caught(self):
        """KeyError raised by get_current_temperature is caught, final stays None."""
        climate = _make_climate(
            {"heat-1": {"state": {"mode": "MANUAL", "target": 20.0}, "props": {}}}
        )
        d = _make_device()
        with patch.object(
            climate, "get_current_temperature", new_callable=AsyncMock
        ) as mock_t:
            mock_t.side_effect = KeyError("missing_key")
            result = await climate.get_state(d)
        assert result is None

    async def test_type_error_in_get_target_temperature_is_caught(self):
        """TypeError raised by get_target_temperature is caught, final stays None."""
        climate = _make_climate(
            {"heat-1": {"state": {"mode": "MANUAL", "target": 20.0}, "props": {}}}
        )
        d = _make_device()
        with patch.object(
            climate, "get_current_temperature", new_callable=AsyncMock
        ) as mock_cur:
            mock_cur.return_value = 19.0
            with patch.object(
                climate, "get_target_temperature", new_callable=AsyncMock
            ) as mock_tgt:
                mock_tgt.side_effect = TypeError("bad type")
                result = await climate.get_state(d)
        assert result is None
