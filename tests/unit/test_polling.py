"""Unit tests for PollingMixin cache and rate-limit helpers."""

# pylint: disable=protected-access,attribute-defined-outside-init,too-few-public-methods

import asyncio

from apyhiveapi.helper.hivedataclasses import Device
from apyhiveapi.session.polling import PollingMixin


def _make_device(ha_type="climate", hive_id="h1", hive_type="heating"):
    return Device(
        hive_id=hive_id,
        hive_name="T",
        hive_type=hive_type,
        ha_type=ha_type,
        device_id="d1",
        device_name="T",
        device_data={"online": True},
    )


def _make_polling():
    class StubPolling(PollingMixin):
        """Minimal concrete stub for testing PollingMixin."""

    p = StubPolling()
    p.entity_cache = {}
    p.update_lock = asyncio.Lock()
    p._update_task = None
    p._last_poll_slow = False
    p._slow_poll_threshold = 3
    return p


# ---------------------------------------------------------------------------
# _entity_cache_key
# ---------------------------------------------------------------------------


class TestEntityCacheKey:
    """Tests for PollingMixin._entity_cache_key."""

    def test_key_format(self):
        """Cache key is 'ha_type|hive_id|hive_type'."""
        p = _make_polling()
        d = _make_device(ha_type="climate", hive_id="h1", hive_type="heating")
        assert p._entity_cache_key(d) == "climate|h1|heating"

    def test_key_is_stable(self):
        """The same device always produces the same key."""
        p = _make_polling()
        d = _make_device()
        assert p._entity_cache_key(d) == p._entity_cache_key(d)

    def test_different_devices_produce_different_keys(self):
        """Two devices with different hive_ids produce distinct keys."""
        p = _make_polling()
        d1 = _make_device(hive_id="h1")
        d2 = _make_device(hive_id="h2")
        assert p._entity_cache_key(d1) != p._entity_cache_key(d2)

    def test_ha_type_included_in_key(self):
        """ha_type is part of the key — different ha_types yield different keys."""
        p = _make_polling()
        d1 = _make_device(ha_type="climate", hive_id="h1", hive_type="heating")
        d2 = _make_device(ha_type="sensor", hive_id="h1", hive_type="heating")
        assert p._entity_cache_key(d1) != p._entity_cache_key(d2)

    def test_key_is_string(self):
        """_entity_cache_key always returns a string."""
        p = _make_polling()
        d = _make_device()
        assert isinstance(p._entity_cache_key(d), str)

    def test_static_method_callable_on_class(self):
        """_entity_cache_key is a staticmethod — callable without an instance."""
        d = _make_device()
        assert PollingMixin._entity_cache_key(d) == "climate|h1|heating"


# ---------------------------------------------------------------------------
# Cache round-trip: set_cached_device / get_cached_device
# ---------------------------------------------------------------------------


class TestCacheRoundTrip:
    """Tests for PollingMixin.set_cached_device / get_cached_device."""

    def test_set_then_get_returns_device(self):
        """set then get returns the exact same device object."""
        p = _make_polling()
        d = _make_device()
        p.set_cached_device(d)
        assert p.get_cached_device(d) is d

    def test_get_unknown_returns_none(self):
        """get_cached_device returns None for a device not yet cached."""
        p = _make_polling()
        d = _make_device()
        assert p.get_cached_device(d) is None

    def test_set_returns_device(self):
        """set_cached_device returns the device it stores."""
        p = _make_polling()
        d = _make_device()
        assert p.set_cached_device(d) is d

    def test_overwrite_replaces_entry(self):
        """A second set_cached_device for the same key replaces the prior entry."""
        p = _make_polling()
        d1 = _make_device(hive_id="h1")
        d2 = _make_device(hive_id="h1")
        p.set_cached_device(d1)
        p.set_cached_device(d2)
        assert p.get_cached_device(d2) is d2

    def test_different_devices_cached_independently(self):
        """Distinct devices occupy separate cache slots."""
        p = _make_polling()
        d1 = _make_device(hive_id="h1")
        d2 = _make_device(hive_id="h2")
        p.set_cached_device(d1)
        p.set_cached_device(d2)
        assert p.get_cached_device(d1) is d1
        assert p.get_cached_device(d2) is d2

    def test_cache_populated_after_set(self):
        """entity_cache dict contains the key after set_cached_device."""
        p = _make_polling()
        d = _make_device()
        p.set_cached_device(d)
        key = p._entity_cache_key(d)
        assert key in p.entity_cache


# ---------------------------------------------------------------------------
# should_use_cached_data
# ---------------------------------------------------------------------------


class TestShouldUseCachedData:
    """Tests for PollingMixin.should_use_cached_data."""

    def test_last_poll_slow_returns_true(self):
        """True when _last_poll_slow is set."""
        p = _make_polling()
        p._last_poll_slow = True
        assert p.should_use_cached_data() is True

    def test_not_locked_not_slow_returns_false(self):
        """False when not slow and lock is not held."""
        p = _make_polling()
        assert p.should_use_cached_data() is False

    async def test_lock_held_without_update_task_returns_true(self):
        """True when update_lock is held and _update_task is None."""
        p = _make_polling()
        await p.update_lock.acquire()
        p._update_task = None
        result = p.should_use_cached_data()
        p.update_lock.release()
        assert result is True

    async def test_slow_poll_overrides_unlocked_state(self):
        """_last_poll_slow=True returns True even when lock is free."""
        p = _make_polling()
        p._last_poll_slow = True
        assert p.should_use_cached_data() is True

    async def test_lock_held_by_update_task_itself_returns_false(self):
        """False when update_lock is locked *and* current task is _update_task."""
        p = _make_polling()

        async def _hold_lock():
            async with p.update_lock:
                p._update_task = asyncio.current_task()
                return p.should_use_cached_data()

        result = await _hold_lock()
        assert result is False
