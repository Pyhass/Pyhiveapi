"""Extended branch-coverage tests for WaterHeater / HiveHotwater."""

# pylint: disable=too-few-public-methods
from unittest.mock import AsyncMock, MagicMock

from apyhiveapi.devices.hotwater import WaterHeater
from apyhiveapi.helper.hivedataclasses import Device, SessionConfig
from apyhiveapi.helper.map import Map

_SCHEDULE_MODE = "SCHEDULE"
_ON_MODE = "ON"
_OFF_MODE = "OFF"
_BOOST_MODE = "BOOST"
_BOOST_MINS = 30


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
    session.helper.error_check = AsyncMock()
    session.helper.get_schedule_nnl = MagicMock(
        return_value={"now": {"value": {"status": _ON_MODE}}, "next": {}, "later": {}}
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


def _make_device(hive_id="hw-1", device_id="dev-1"):
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


class TestGetMode:
    async def test_boost_mode_reads_previous(self):
        """BOOST state resolves to the previous mode stored in props."""
        hw = _make_hotwater(
            {
                "hw-1": {
                    "state": {"mode": _BOOST_MODE},
                    "props": {"previous": {"mode": _ON_MODE}},
                }
            }
        )
        result = await hw.get_mode(_make_device())
        assert result == _ON_MODE


class TestGetState:
    async def test_schedule_mode_boost_off_reads_schedule(self):
        """SCHEDULE mode with boost OFF reads state from schedule nnl."""
        hw = _make_hotwater(
            {
                "hw-1": {
                    "state": {
                        "mode": _SCHEDULE_MODE,
                        "status": _OFF_MODE,
                        "boost": False,
                        "schedule": {},
                    }
                }
            }
        )
        result = await hw.get_state(_make_device())
        assert result is not None

    async def test_non_schedule_state_mapped(self):
        """Direct ON mode/status maps through HIVETOHA without schedule lookup."""
        hw = _make_hotwater(
            {
                "hw-1": {
                    "state": {
                        "mode": _ON_MODE,
                        "status": _ON_MODE,
                        "schedule": {},
                    }
                }
            }
        )
        result = await hw.get_state(_make_device())
        assert result is not None


class TestGetWaterHeater:
    async def test_cache_hit_returns_cached(self):
        """Cached device is returned immediately when poll is slow/busy."""
        hw = _make_hotwater()
        hw.session.should_use_cached_data = MagicMock(return_value=True)
        cached_device = _make_device()
        cached_device.status = {"current_operation": _SCHEDULE_MODE}
        hw.session.get_cached_device = MagicMock(return_value=cached_device)
        d = _make_device()
        result = await hw.get_water_heater(d)
        assert result is cached_device
        hw.session.attr.online_offline.assert_not_called()

    async def test_device_data_not_dict_gets_reset(self):
        """Non-dict device_data is replaced with an empty dict before use."""
        hw = _make_hotwater(
            products={"hw-1": {"state": {"mode": _SCHEDULE_MODE}}},
            devices={"dev-1": {"props": {}, "parent": None}},
        )
        d = _make_device()
        d.device_data = None
        await hw.get_water_heater(d)
        assert isinstance(d.device_data, dict)

    async def test_offline_device_calls_error_check(self):
        """Offline device triggers error_check and status defaults to None."""
        hw = _make_hotwater(
            products={"hw-1": {}},
            devices={"dev-1": {}},
        )
        hw.session.attr.online_offline = AsyncMock(return_value=False)
        d = _make_device()
        result = await hw.get_water_heater(d)
        hw.session.helper.error_check.assert_called_once()
        assert result.status["current_operation"] is None


class TestGetScheduleNowNextLater:
    async def test_schedule_mode_returns_nnl(self):
        """SCHEDULE mode with schedule data returns now/next/later dict."""
        hw = _make_hotwater(
            {"hw-1": {"state": {"mode": _SCHEDULE_MODE, "schedule": {"data": []}}}}
        )
        result = await hw.get_schedule_now_next_later(_make_device())
        assert result is not None
        assert "now" in result

    async def test_non_schedule_mode_returns_none(self):
        """Non-SCHEDULE mode returns None."""
        hw = _make_hotwater({"hw-1": {"state": {"mode": _ON_MODE}}})
        result = await hw.get_schedule_now_next_later(_make_device())
        assert result is None
