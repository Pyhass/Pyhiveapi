"""Extended branch-coverage tests for Climate / HiveHeating."""

# pylint: disable=too-few-public-methods
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apyhiveapi.devices.heating import Climate
from apyhiveapi.helper.hivedataclasses import Device, SessionConfig
from apyhiveapi.helper.map import Map

_TODAY = str(datetime.date(datetime.now()))
_CURRENT_TEMP = 19.0
_SCHEDULE_MODE = "SCHEDULE"
_BOOST_MINS = 5
_OFF_MODE = "OFF"


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


class TestGetCurrentTemperature:
    async def test_minmax_today_same_date_updates_min_max(self):
        """When minMax entry exists for today's date, TodayMin/TodayMax are updated."""
        initial_min = _CURRENT_TEMP + 2.0
        initial_max = _CURRENT_TEMP - 2.0
        existing = {
            "TodayMin": initial_min,
            "TodayMax": initial_max,
            "TodayDate": _TODAY,
            "RestartMin": initial_min,
            "RestartMax": initial_max,
        }
        climate = _make_climate(
            products={"heat-1": {"props": {"temperature": _CURRENT_TEMP}}},
            min_max={"heat-1": existing},
        )
        result = await climate.get_current_temperature(_make_device())
        assert result == _CURRENT_TEMP
        entry = climate.session.data.minMax["heat-1"]
        assert entry["TodayMin"] == min(initial_min, _CURRENT_TEMP)
        assert entry["TodayMax"] == max(initial_max, _CURRENT_TEMP)
        assert entry["RestartMin"] == min(initial_min, _CURRENT_TEMP)
        assert entry["RestartMax"] == max(initial_max, _CURRENT_TEMP)

    async def test_minmax_different_date_resets_today(self):
        """When minMax entry exists but TodayDate is stale, today values are reset."""
        existing = {
            "TodayMin": 5.0,
            "TodayMax": 30.0,
            "TodayDate": "2000-01-01",
            "RestartMin": 5.0,
            "RestartMax": 30.0,
        }
        climate = _make_climate(
            products={"heat-1": {"props": {"temperature": _CURRENT_TEMP}}},
            min_max={"heat-1": existing},
        )
        result = await climate.get_current_temperature(_make_device())
        assert result == _CURRENT_TEMP
        entry = climate.session.data.minMax["heat-1"]
        assert entry["TodayMin"] == _CURRENT_TEMP
        assert entry["TodayMax"] == _CURRENT_TEMP
        assert entry["TodayDate"] == _TODAY

    async def test_keyerror_returns_none(self):
        """Missing device.hive_id in products returns None."""
        climate = _make_climate(products={})
        result = await climate.get_current_temperature(_make_device())
        assert result is None


class TestGetTargetTemperature:
    async def test_non_numeric_target_returns_none(self):
        """Non-numeric target temperature string returns None."""
        climate = _make_climate({"heat-1": {"state": {"target": "N/A"}}})
        result = await climate.get_target_temperature(_make_device())
        assert result is None


class TestGetState:
    async def test_current_less_than_target_returns_on(self):
        """When current_temp < target_temp, state resolves to ON."""
        climate = _make_climate(
            {
                "heat-1": {
                    "props": {"temperature": 19.0},
                    "state": {"target": 21.0},
                }
            }
        )
        result = await climate.get_state(_make_device())
        assert result == "ON"

    async def test_current_ge_target_returns_off(self):
        """When current_temp >= target_temp, state resolves to OFF."""
        climate = _make_climate(
            {
                "heat-1": {
                    "props": {"temperature": 21.0},
                    "state": {"target": 19.0},
                }
            }
        )
        result = await climate.get_state(_make_device())
        assert result == "OFF"

    async def test_none_temps_returns_none(self):
        """When temperatures cannot be read, get_state returns None."""
        climate = _make_climate(products={})
        result = await climate.get_state(_make_device())
        assert result is None

    async def test_key_error_in_get_current_temperature_is_caught(self):
        """KeyError from get_current_temperature is caught; get_state returns None."""
        climate = _make_climate(
            {"heat-1": {"state": {"mode": "MANUAL", "target": 20.0}, "props": {}}}
        )
        with patch.object(
            climate, "get_current_temperature", new_callable=AsyncMock
        ) as mock_t:
            mock_t.side_effect = KeyError("missing_key")
            result = await climate.get_state(_make_device())
        assert result is None

    async def test_type_error_in_get_target_temperature_is_caught(self):
        """TypeError from get_target_temperature is caught; get_state returns None."""
        climate = _make_climate(
            {"heat-1": {"state": {"mode": "MANUAL", "target": 20.0}, "props": {}}}
        )
        with patch.object(
            climate, "get_current_temperature", new_callable=AsyncMock
        ) as mock_cur:
            mock_cur.return_value = 19.0
            with patch.object(
                climate, "get_target_temperature", new_callable=AsyncMock
            ) as mock_tgt:
                mock_tgt.side_effect = TypeError("bad type")
                result = await climate.get_state(_make_device())
        assert result is None


class TestGetCurrentOperation:
    async def test_returns_working_state(self):
        """get_current_operation returns the 'working' value from props."""
        climate = _make_climate({"heat-1": {"props": {"working": True}, "state": {}}})
        result = await climate.get_current_operation(_make_device())
        assert result is True


class TestSetBoostOff:
    async def test_not_in_products_returns_false(self):
        """Device hive_id not present in products returns False."""
        climate = _make_climate(products={})
        result = await climate.set_boost_off(_make_device())
        assert result is False

    async def test_previous_off_mode_restored(self):
        """Previous mode OFF sets mode=OFF and target falls back to 7."""
        climate = _make_climate(
            {
                "heat-1": {
                    "type": "heating",
                    "state": {"boost": _BOOST_MINS},
                    "props": {
                        "previous": {
                            "mode": _OFF_MODE,
                            "target": None,
                        }
                    },
                }
            }
        )
        result = await climate.set_boost_off(_make_device())
        assert result is True
        _, kwargs = climate.session.api.set_state.call_args
        assert kwargs.get("mode") == _OFF_MODE
        assert kwargs.get("target") == 7


class TestGetClimate:
    async def test_device_data_not_dict_gets_reset(self):
        """Non-dict device_data is replaced with an empty dict before use."""
        climate = _make_climate(
            products={"heat-1": {"props": {}, "state": {}}},
            devices={"dev-1": {"props": {}, "parent": None}},
        )
        d = _make_device()
        d.device_data = None
        await climate.get_climate(d)
        assert isinstance(d.device_data, dict)

    async def test_offline_device_error_check_called(self):
        """Offline device triggers error_check and status defaults to None values."""
        climate = _make_climate(
            products={"heat-1": {}},
            devices={"dev-1": {}},
        )
        climate.session.attr.online_offline = AsyncMock(return_value=False)
        d = _make_device()
        result = await climate.get_climate(d)
        climate.session.helper.error_check.assert_called_once()
        assert result.status["current_temperature"] is None

    async def test_cache_hit_returns_cached(self):
        """When cached data is available and poll is slow, returns cached device."""
        climate = _make_climate()
        climate.session.should_use_cached_data = MagicMock(return_value=True)
        cached_device = _make_device()
        cached_device.status = {"current_temperature": 20.0}
        climate.session.get_cached_device = MagicMock(return_value=cached_device)
        d = _make_device()
        result = await climate.get_climate(d)
        assert result is cached_device
        climate.session.attr.online_offline.assert_not_called()


class TestGetScheduleNowNextLater:
    async def test_offline_returns_none(self):
        """Offline device returns None regardless of mode."""
        climate = _make_climate(
            {"heat-1": {"state": {"mode": _SCHEDULE_MODE, "schedule": {}}}}
        )
        climate.session.attr.online_offline = AsyncMock(return_value=False)
        result = await climate.get_schedule_now_next_later(_make_device())
        assert result is None


# ---------------------------------------------------------------------------
# get_mode — BOOST path with missing props.previous must not log error
# ---------------------------------------------------------------------------


class TestGetModeBoostMissingPrevious:
    """get_mode BOOST path must use safe access, not bare dict that logs a spurious error."""

    async def test_boost_missing_previous_returns_none_without_error_log(self):
        """When mode=BOOST and props has no previous, get_mode returns None without error log."""
        climate = _make_climate({"heat-1": {"state": {"mode": "BOOST"}, "props": {}}})
        d = _make_device()
        with patch("apyhiveapi.devices.heating._LOGGER") as mock_log:
            result = await climate.get_mode(d)
        assert result is None
        mock_log.error.assert_not_called()

    async def test_boost_with_previous_mode_returns_mapped_value(self):
        """When mode=BOOST and props.previous.mode exists, returns the mapped HA value."""
        from apyhiveapi.helper.const import HIVETOHA

        climate = _make_climate(
            {
                "heat-1": {
                    "state": {"mode": "BOOST"},
                    "props": {"previous": {"mode": "MANUAL"}},
                }
            }
        )
        d = _make_device()
        result = await climate.get_mode(d)
        expected = HIVETOHA["Heating"].get("MANUAL", "MANUAL")
        assert result == expected


# ---------------------------------------------------------------------------
# set_boost_off — must return False when prev_mode is None (not send mode=None to API)
# ---------------------------------------------------------------------------


class TestSetBoostOffNullPrevMode:
    """set_boost_off returns False (not an API call) when prev_mode is None."""

    async def test_set_boost_off_returns_false_when_prev_mode_missing(self):
        """set_boost_off returns False and skips _execute_state_change when prev mode absent."""
        from apyhiveapi.devices.heating import HiveHeating

        class StubHeating(HiveHeating):
            """Concrete stub for testing."""

        h = StubHeating()
        h.session = MagicMock()
        h.session.data.products = {
            "h1": {
                "state": {"mode": "BOOST"},
                "props": {},
            }
        }
        h._execute_state_change = AsyncMock(return_value=True)
        h.get_boost_status = AsyncMock(return_value="ON")

        d = Device(
            hive_id="h1",
            hive_name="T",
            hive_type="heating",
            ha_type="climate",
            device_id="d1",
            device_name="T",
            device_data={"online": True},
            ha_name="Heating",
        )
        result = await h.set_boost_off(d)
        assert result is False
        h._execute_state_change.assert_not_called()
