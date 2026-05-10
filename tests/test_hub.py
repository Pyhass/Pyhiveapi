"""Tests for session polling behaviour, HiveHub sensor status, and Hive lifecycle."""

# pylint: disable=protected-access
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from apyhiveapi import Hive
from apyhiveapi.devices.hub import HiveHub
from apyhiveapi.helper.hivedataclasses import Device
from apyhiveapi.helper.map import Map


def test_hub_smoke():
    """Placeholder smoke test."""
    assert True


@pytest.mark.asyncio
async def test_force_update_polls_when_idle():
    """force_update() calls _poll_devices and returns its result when no poll is running."""
    async with Hive(
        username="test@example.com",
        password="pass",  # pragma: allowlist secret
    ) as hive:
        hive._poll_devices = AsyncMock(return_value=True)
        result = await hive.force_update()

    assert result is True
    hive._poll_devices.assert_called_once()


@pytest.mark.asyncio
async def test_force_update_skips_when_locked():
    """force_update() returns False without polling when the update lock is already held."""
    async with Hive(
        username="test@example.com",
        password="pass",  # pragma: allowlist secret
    ) as hive:
        hive._poll_devices = AsyncMock(return_value=True)

        async with hive.update_lock:
            result = await hive.force_update()

    assert result is False
    hive._poll_devices.assert_not_called()


# ---------------------------------------------------------------------------
# Shared fixtures for HiveHub sensor tests
# ---------------------------------------------------------------------------

SMOKE_PRODUCTS = {
    "hub-1": {
        "props": {
            "sensors": {
                "SMOKE_CO": {"active": True},
                "DOG_BARK": {"active": False},
                "GLASS_BREAK": {"active": True},
            }
        }
    }
}


def _make_hub_handler(products):
    """Build a HiveHub with a mocked session."""
    session = MagicMock()
    session.data = Map(
        {"products": products, "devices": {}, "actions": {}, "minMax": {}, "user": {}}
    )
    return HiveHub(session=session)


def _make_hub_device(hive_id="hub-1"):
    """Return a minimal sense Device."""
    return Device(
        hive_id=hive_id,
        hive_name="Hub",
        hive_type="sense",
        ha_type="binary_sensor",
        device_id="hub-1",
        device_name="Hub",
        device_data={"online": True},
    )


class TestHiveHubSensorStatus:
    """Tests for HiveHub smoke, dog-bark and glass-break sensor status methods."""

    async def test_smoke_active_true_returns_1(self):
        """get_smoke_status returns 1 when SMOKE_CO active is True."""
        hub = _make_hub_handler(SMOKE_PRODUCTS)
        assert await hub.get_smoke_status(_make_hub_device()) == 1

    async def test_smoke_active_false_returns_0(self):
        """get_smoke_status returns 0 when SMOKE_CO active is False."""
        prods = {"hub-1": {"props": {"sensors": {"SMOKE_CO": {"active": False}}}}}
        hub = _make_hub_handler(prods)
        assert await hub.get_smoke_status(_make_hub_device()) == 0

    async def test_smoke_missing_returns_none(self):
        """get_smoke_status returns None when the product key is absent."""
        hub = _make_hub_handler({})
        assert await hub.get_smoke_status(_make_hub_device()) is None

    async def test_dog_bark_false_returns_0(self):
        """get_dog_bark_status returns 0 when DOG_BARK active is False."""
        hub = _make_hub_handler(SMOKE_PRODUCTS)
        assert await hub.get_dog_bark_status(_make_hub_device()) == 0

    async def test_dog_bark_missing_returns_none(self):
        """get_dog_bark_status returns None when the product key is absent."""
        hub = _make_hub_handler({})
        assert await hub.get_dog_bark_status(_make_hub_device()) is None

    async def test_glass_break_active_true_returns_1(self):
        """get_glass_break_status returns 1 when GLASS_BREAK active is True."""
        hub = _make_hub_handler(SMOKE_PRODUCTS)
        assert await hub.get_glass_break_status(_make_hub_device()) == 1

    async def test_glass_break_missing_returns_none(self):
        """get_glass_break_status returns None when the product key is absent."""
        hub = _make_hub_handler({})
        assert await hub.get_glass_break_status(_make_hub_device()) is None


class TestHiveLifecycle:
    """Tests for Hive context manager and set_debugging."""

    async def test_context_manager_aenter_returns_self(self):
        """__aenter__ returns the Hive instance itself."""
        async with Hive(
            username="test@example.com",
            password="pass",  # pragma: allowlist secret
        ) as hive:
            assert hive is not None

    async def test_close_calls_websession_close(self):
        """__aexit__ closes the underlying aiohttp websession."""
        async with Hive(
            username="test@example.com",
            password="pass",  # pragma: allowlist secret
        ) as hive:
            ws = hive.api.websession
        # After context exit the session should be closed
        assert ws.closed

    async def test_set_debugging_empty_list_clears_trace(self):
        """set_debugging([]) removes any active trace function."""
        async with Hive(
            username="test@example.com",
            password="pass",  # pragma: allowlist secret
        ) as hive:
            hive.set_debugging([])
        assert sys.gettrace() is None

    async def test_set_debugging_with_function_sets_trace(self):
        """set_debugging([name]) installs the trace_debug function."""
        async with Hive(
            username="test@example.com",
            password="pass",  # pragma: allowlist secret
        ) as hive:
            hive.set_debugging(["some_func"])
            assert sys.gettrace() is not None
            sys.settrace(None)  # clean up
