"""Tests for SensorCompatMixin and ActionCompatMixin aliases (coverage gap fill)."""

# pylint: disable=too-few-public-methods

from unittest.mock import AsyncMock

from apyhiveapi.helper.compat_aliases import ActionCompatMixin, SensorCompatMixin
from apyhiveapi.helper.hivedataclasses import Device


def _make_device(hive_type="action", ha_type="switch"):
    return Device(
        hive_id="h1",
        hive_name="Test",
        hive_type=hive_type,
        ha_type=ha_type,
        device_id="d1",
        device_name="Test",
        device_data={},
    )


# ---------------------------------------------------------------------------
# SensorCompatMixin
# ---------------------------------------------------------------------------


class TestSensorCompatMixin:
    """CamelCase alias smoke tests for SensorCompatMixin."""

    async def test_get_sensor_delegates(self):
        """getSensor delegates to get_sensor and returns its result."""

        class Stub(SensorCompatMixin):
            """Stub with mocked get_sensor."""

            get_sensor = AsyncMock(return_value="sensor_result")

        s = Stub()
        d = _make_device(hive_type="motionsensor", ha_type="binary_sensor")
        result = await s.getSensor(d)
        s.get_sensor.assert_called_once_with(d)
        assert result == "sensor_result"


# ---------------------------------------------------------------------------
# ActionCompatMixin
# ---------------------------------------------------------------------------


class TestActionCompatMixin:
    """CamelCase alias smoke tests for ActionCompatMixin."""

    async def test_get_action_delegates(self):
        """getAction delegates to get_action and returns its result."""

        class Stub(ActionCompatMixin):
            """Stub with mocked get_action."""

            get_action = AsyncMock(return_value="action_result")

        s = Stub()
        d = _make_device()
        result = await s.getAction(d)
        s.get_action.assert_called_once_with(d)
        assert result == "action_result"

    async def test_set_status_on_delegates(self):
        """setStatusOn delegates to set_status_on and returns its result."""

        class Stub(ActionCompatMixin):
            """Stub with mocked set_status_on."""

            set_status_on = AsyncMock(return_value=True)

        s = Stub()
        d = _make_device()
        result = await s.setStatusOn(d)
        s.set_status_on.assert_called_once_with(d)
        assert result is True

    async def test_set_status_off_delegates(self):
        """setStatusOff delegates to set_status_off and returns its result."""

        class Stub(ActionCompatMixin):
            """Stub with mocked set_status_off."""

            set_status_off = AsyncMock(return_value=True)

        s = Stub()
        d = _make_device()
        result = await s.setStatusOff(d)
        s.set_status_off.assert_called_once_with(d)
        assert result is True
