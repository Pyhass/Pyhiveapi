"""Tests for HiveHelper covering previously uncovered lines/branches."""

# pylint: disable=protected-access

from unittest.mock import MagicMock

from apyhiveapi.helper.hive_helper import HiveHelper
from apyhiveapi.helper.map import Map


def _make_helper(entity_cache=None, products=None):
    """Build a HiveHelper with a minimally mocked session."""
    session = MagicMock()
    session.entity_cache = entity_cache if entity_cache is not None else {}
    session.data = Map(
        {
            "products": products or {},
            "devices": {},
            "actions": {},
            "user": {},
            "minMax": {},
        }
    )
    return HiveHelper(session)


# ---------------------------------------------------------------------------
# get_device_from_id — branch 133->122 (no match, loop continues then exits)
# ---------------------------------------------------------------------------


class TestGetDeviceFromIdBranch:
    """Covers the branch where no cache entry matches the requested ID."""

    def test_returns_false_when_no_match_in_cache(self):
        """When entity_cache has entries but none match n_id, returns False.

        This exercises the branch where the 'if n_id in (hive_id, device_id)'
        condition is False for every item (133->122 loop-continue then exit).
        """
        from apyhiveapi.helper.hivedataclasses import Device

        other_device = Device(
            hive_id="other-hive-id",
            hive_name="Other",
            hive_type="heating",
            ha_type="climate",
            device_id="other-device-id",
            device_name="Other",
            device_data={},
        )
        helper = _make_helper(entity_cache={"other-key": other_device})
        result = helper.get_device_from_id("nonexistent-id")
        assert result is False

    def test_returns_false_when_cache_is_empty(self):
        """When entity_cache is empty, returns False without entering the loop."""
        helper = _make_helper(entity_cache={})
        assert helper.get_device_from_id("any-id") is False


# ---------------------------------------------------------------------------
# sanitize_payload — list masking (line 329) and non-str/dict/list fallthrough
# ---------------------------------------------------------------------------


class TestSanitizePayload:
    """Covers _mask branches for list values and non-string scalar fallthrough."""

    def test_list_value_under_sensitive_key_is_masked(self):
        """A list value under a sensitive key has each element masked."""
        helper = _make_helper()
        payload = {"token": ["short", "averylongtoken123"]}
        result = helper.sanitize_payload(payload)
        # "short" (<=8 chars) → "***", "averylongtoken123" (>8 chars) → "aver...n123"
        assert result["token"] == ["***", "aver...n123"]

    def test_non_string_non_dict_non_list_under_sensitive_key_passes_through(self):
        """An int/bool/None value under a sensitive key is returned as-is."""
        helper = _make_helper()
        payload = {"token": 42}
        result = helper.sanitize_payload(payload)
        assert result["token"] == 42

    def test_none_under_sensitive_key_passes_through(self):
        """None under a sensitive key is returned unchanged."""
        helper = _make_helper()
        payload = {"token": None}
        result = helper.sanitize_payload(payload)
        assert result["token"] is None

    def test_bool_under_sensitive_key_passes_through(self):
        """A bool under a sensitive key is returned unchanged (not a str/dict/list)."""
        helper = _make_helper()
        payload = {"token": True}
        result = helper.sanitize_payload(payload)
        assert result["token"] is True

    def test_short_string_masked_as_stars(self):
        """A string of 8 characters or fewer is masked as '***'."""
        helper = _make_helper()
        payload = {"password": "abc12345"}  # exactly 8 chars
        result = helper.sanitize_payload(payload)
        assert result["password"] == "***"

    def test_long_string_partially_masked(self):
        """A string longer than 8 characters is partially masked."""
        helper = _make_helper()
        payload = {"password": "supersecretpassword"}
        result = helper.sanitize_payload(payload)
        assert result["password"] == "supe...word"


# ---------------------------------------------------------------------------
# epoch_time — to_epoch must honour the pattern argument
# ---------------------------------------------------------------------------


class TestEpochTimePattern:
    """epoch_time to_epoch must honour the pattern argument."""

    def test_to_epoch_uses_caller_pattern(self):
        """Passing a custom pattern must parse the date string with that pattern."""
        from apyhiveapi.helper.hive_helper import epoch_time

        # ISO date — only parses if the custom pattern is respected
        result = epoch_time("2024-06-15", "%Y-%m-%d", "to_epoch")
        assert isinstance(result, int), "Expected int epoch timestamp"
        assert result > 0

    def test_to_epoch_standard_hive_format_still_works(self):
        """The standard Hive date+time format must still parse correctly."""
        from apyhiveapi.helper.hive_helper import epoch_time

        result = epoch_time("15.06.2024 12:00:00", "%d.%m.%Y %H:%M:%S", "to_epoch")
        assert isinstance(result, int)
        assert result > 0


def _sample_schedule():
    """Minimal 7-day schedule with 3 slots on every day."""
    days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    schedule = {}
    for d in days:
        schedule[d] = [
            {"start": 0, "value": {"status": "ON"}},
            {"start": 480, "value": {"status": "OFF"}},
            {"start": 1200, "value": {"status": "ON"}},
        ]
    return schedule


class TestGetScheduleNnlMutation:
    """get_schedule_nnl must not mutate the input schedule dicts."""

    def test_second_call_returns_same_result_as_first_call(self):
        """Calling get_schedule_nnl twice on the same schedule dict gives consistent results."""
        h = _make_helper()
        schedule = _sample_schedule()

        result1 = h.get_schedule_nnl(schedule)
        result2 = h.get_schedule_nnl(schedule)

        assert result1.get("now", {}).get("value") == result2.get("now", {}).get(
            "value"
        ), "Second call returned different 'now' value — schedule was mutated in-place"

    def test_input_schedule_slots_not_modified(self):
        """Slot dicts in the input schedule must not gain 'Start_DateTime' after the call."""
        h = _make_helper()
        schedule = _sample_schedule()
        monday_slot_before = dict(schedule["monday"][0])

        h.get_schedule_nnl(schedule)

        assert schedule["monday"][0] == monday_slot_before, (
            "get_schedule_nnl mutated the original slot dict"
        )
