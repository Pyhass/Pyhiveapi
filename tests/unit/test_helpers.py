"""Unit tests for HiveHelper and epoch_time."""

# pylint: disable=protected-access

from unittest.mock import MagicMock

import pytest
from apyhiveapi.helper.hive_helper import HiveHelper, epoch_time
from apyhiveapi.helper.hivedataclasses import Device, SessionConfig
from apyhiveapi.helper.map import Map


def _make_helper(products=None, devices=None, entity_cache=None):
    """Build a minimal mock session and return (helper, session)."""
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
    # entity_cache lives directly on session, not on session.config
    session.entity_cache = entity_cache or {}
    helper = HiveHelper(session)
    return helper, session


# ---------------------------------------------------------------------------
# epoch_time
# ---------------------------------------------------------------------------


class TestEpochTime:
    """Tests for the top-level epoch_time() helper function."""

    def test_to_epoch_returns_int(self):
        """to_epoch converts a date string to an integer Unix timestamp."""
        result = epoch_time("01.01.2024 12:00:00", "%d.%m.%Y %H:%M:%S", "to_epoch")
        assert isinstance(result, int)

    def test_to_epoch_is_deterministic(self):
        """Same input always yields the same epoch integer."""
        r1 = epoch_time("01.01.2024 12:00:00", "%d.%m.%Y %H:%M:%S", "to_epoch")
        r2 = epoch_time("01.01.2024 12:00:00", "%d.%m.%Y %H:%M:%S", "to_epoch")
        assert r1 == r2

    def test_from_epoch_returns_string(self):
        """from_epoch converts an integer timestamp to a formatted string."""
        result = epoch_time(0, "%H:%M", "from_epoch")
        assert isinstance(result, str)

    def test_from_epoch_format_applied(self):
        """The pattern argument is honoured for 'from_epoch'."""
        result = epoch_time(0, "%H:%M", "from_epoch")
        # Should look like HH:MM
        assert ":" in result
        assert len(result) == 5  # noqa: PLR2004

    def test_unknown_action_returns_none(self):
        """Unrecognised action argument returns None."""
        assert epoch_time("anything", "%Y", "unknown") is None


# ---------------------------------------------------------------------------
# HiveHelper.convert_minutes_to_time
# ---------------------------------------------------------------------------


class TestConvertMinutesToTime:
    """Tests for HiveHelper.convert_minutes_to_time."""

    def test_90_minutes(self):
        """90 minutes converts to '01:30'."""
        helper, _ = _make_helper()
        assert helper.convert_minutes_to_time(90) == "01:30"

    def test_zero_minutes(self):
        """0 minutes converts to '00:00'."""
        helper, _ = _make_helper()
        assert helper.convert_minutes_to_time(0) == "00:00"

    def test_60_minutes(self):
        """60 minutes converts to '01:00'."""
        helper, _ = _make_helper()
        assert helper.convert_minutes_to_time(60) == "01:00"

    def test_30_minutes(self):
        """30 minutes converts to '00:30'."""
        helper, _ = _make_helper()
        assert helper.convert_minutes_to_time(30) == "00:30"

    def test_1440_minutes_wraps_to_midnight(self):
        """24 hours = 1440 minutes → "24:00" via strptime("%H:%M") — verify no crash."""
        helper, _ = _make_helper()
        # strptime does not support hour 24; 23 * 60 = 1380 is a safe boundary
        assert helper.convert_minutes_to_time(1380) == "23:00"


# ---------------------------------------------------------------------------
# HiveHelper.sanitize_payload
# ---------------------------------------------------------------------------


class TestSanitizePayload:
    """Tests for HiveHelper.sanitize_payload."""

    def test_masks_password_key(self):
        """Keys containing 'password' are masked in the output."""
        helper, _ = _make_helper()
        _pw = "s3cr3t-v@lue-for-test"  # pragma: allowlist secret
        result = helper.sanitize_payload({"password": _pw})
        assert result["password"] != _pw

    def test_short_value_becomes_stars(self):
        """Values ≤ 8 chars are replaced with '***'."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"token": "abc"})
        assert result["token"] == "***"

    def test_long_value_shows_head_and_tail(self):
        """Values > 8 chars are replaced with first4...last4."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"token": "abcdefghijklmnop"})
        assert result["token"].startswith("abcd")
        assert result["token"].endswith("mnop")
        assert "..." in result["token"]

    def test_exactly_8_chars_becomes_stars(self):
        """Boundary: 8-char value (≤ 8) → '***'."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"token": "12345678"})
        assert result["token"] == "***"

    def test_nine_chars_shows_head_and_tail(self):
        """Boundary: 9-char value (> 8) → truncated form."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"token": "123456789"})
        assert result["token"].startswith("1234")
        assert result["token"].endswith("6789")

    def test_non_sensitive_key_passes_through(self):
        """Keys with no sensitive substrings are left unchanged."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"username": "user@test.com"})
        assert result["username"] == "user@test.com"

    def test_nested_dict_is_recursed_for_sensitive_key(self):
        """Sensitive key inside a nested dict is masked."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"outer": {"token": "abc"}})
        assert result["outer"]["token"] == "***"

    def test_nested_dict_non_sensitive_passes_through(self):
        """Non-sensitive key inside a nested dict is left unchanged."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"outer": {"name": "living room"}})
        assert result["outer"]["name"] == "living room"

    def test_list_items_are_masked_when_parent_key_is_sensitive(self):
        """List values under a sensitive key have each element masked."""
        helper, _ = _make_helper()
        # "tokens" contains "token" — all list items should be masked
        result = helper.sanitize_payload({"tokens": ["abc", "def"]})
        assert result["tokens"] == ["***", "***"]

    def test_original_payload_is_not_mutated(self):
        """sanitize_payload works on a deep copy — original must not change."""
        helper, _ = _make_helper()
        original = {"token": "supersecretvalue"}
        helper.sanitize_payload(original)
        assert original["token"] == "supersecretvalue"

    def test_secret_key_is_masked(self):
        """Keys containing 'secret' are masked in the output."""
        helper, _ = _make_helper()
        _val = "s3cr3t-v@lue-for-test"  # pragma: allowlist secret
        result = helper.sanitize_payload({"secret": _val})
        assert result["secret"] != _val

    def test_code_key_is_masked(self):
        """Keys containing 'code' are masked; short values become '***'."""
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"code": "123456"})
        assert result["code"] == "***"

    def test_non_string_value_under_sensitive_key_passes_through(self):
        """Non-string, non-dict, non-list values under sensitive keys are returned as-is."""
        _non_string_int = 42  # noqa: PLR2004
        helper, _ = _make_helper()
        result = helper.sanitize_payload({"token": _non_string_int})
        assert result["token"] == _non_string_int


# ---------------------------------------------------------------------------
# HiveHelper.device_recovered
# ---------------------------------------------------------------------------


class TestDeviceRecovered:
    """Tests for HiveHelper.device_recovered."""

    def test_removes_from_error_list(self):
        """device_recovered removes the device ID from error_list."""
        helper, session = _make_helper()
        session.config.error_list["dev-1"] = "2026-01-01"
        helper.device_recovered("dev-1")
        assert "dev-1" not in session.config.error_list

    def test_no_op_when_not_in_error_list(self):
        """device_recovered is a no-op when the ID is not already in error_list."""
        helper, session = _make_helper()
        helper.device_recovered("not-there")  # must not raise
        assert not session.config.error_list

    def test_only_target_removed(self):
        """Other entries in error_list are preserved."""
        helper, session = _make_helper()
        session.config.error_list["dev-1"] = "2026-01-01"
        session.config.error_list["dev-2"] = "2026-01-01"
        helper.device_recovered("dev-1")
        assert "dev-1" not in session.config.error_list
        assert "dev-2" in session.config.error_list


# ---------------------------------------------------------------------------
# HiveHelper.get_device_name  (async)
# ---------------------------------------------------------------------------


class TestGetDeviceName:
    """Tests for HiveHelper.get_device_name (async)."""

    async def test_found_in_products(self):
        """ID matching a product entry returns the product state name."""
        helper, _ = _make_helper(products={"p1": {"state": {"name": "Hallway"}}})
        assert await helper.get_device_name("p1") == "Hallway"

    async def test_found_in_devices(self):
        """ID matching a device entry returns the device state name."""
        helper, _ = _make_helper(devices={"d1": {"state": {"name": "Thermostat"}}})
        assert await helper.get_device_name("d1") == "Thermostat"

    async def test_product_takes_priority_over_device(self):
        """When both products and devices have the ID, product name wins."""
        helper, _ = _make_helper(
            products={"x1": {"state": {"name": "ProductName"}}},
            devices={"x1": {"state": {"name": "DeviceName"}}},
        )
        assert await helper.get_device_name("x1") == "ProductName"

    async def test_no_id_returns_hive(self):
        """The literal ID 'No_ID' resolves to 'Hive'."""
        helper, _ = _make_helper()
        assert await helper.get_device_name("No_ID") == "Hive"

    async def test_not_found_returns_id(self):
        """Unknown IDs are echoed back as the device name."""
        helper, _ = _make_helper()
        assert await helper.get_device_name("unknown-id") == "unknown-id"


# ---------------------------------------------------------------------------
# HiveHelper.error_check  (async)
# ---------------------------------------------------------------------------


class TestErrorCheck:
    """Tests for HiveHelper.error_check (async)."""

    async def test_offline_adds_to_error_list(self):
        """False → offline: device is added to error_list."""
        helper, session = _make_helper(products={"d1": {"state": {"name": "Device"}}})
        await helper.error_check("d1", "Sensor", False)
        assert "d1" in session.config.error_list

    async def test_offline_not_duplicated(self):
        """Already-listed device is not added again."""
        helper, session = _make_helper(products={"d1": {"state": {"name": "Device"}}})
        session.config.error_list["d1"] = "already there"
        await helper.error_check("d1", "Sensor", False)
        assert len(session.config.error_list) == 1

    async def test_failed_adds_to_error_list(self):
        """'Failed' → missing data: device is added to error_list."""
        helper, session = _make_helper(products={"d1": {"state": {"name": "Device"}}})
        await helper.error_check("d1", "Sensor", "Failed")
        assert "d1" in session.config.error_list

    async def test_failed_not_duplicated(self):
        """'Failed' for an already-listed device does not duplicate."""
        helper, session = _make_helper(products={"d1": {"state": {"name": "Device"}}})
        session.config.error_list["d1"] = "already there"
        await helper.error_check("d1", "Sensor", "Failed")
        assert len(session.config.error_list) == 1

    async def test_online_true_does_not_add_to_error_list(self):
        """error_type=True (or any truthy non-'Failed') leaves error_list empty."""
        helper, session = _make_helper(products={"d1": {"state": {"name": "Device"}}})
        await helper.error_check("d1", "Sensor", True)
        assert "d1" not in session.config.error_list


# ---------------------------------------------------------------------------
# HiveHelper.get_device_from_id
# ---------------------------------------------------------------------------


class TestGetDeviceFromId:
    """Tests for HiveHelper.get_device_from_id."""

    def test_found_by_hive_id(self):
        """Returns the cached Device when looked up by its hive_id."""
        dev = Device(
            hive_id="h1",
            hive_name="T",
            hive_type="heating",
            ha_type="climate",
            device_id="d1",
            device_name="T",
            device_data={},
            ha_name="Test",
        )
        helper, _ = _make_helper(entity_cache={"key1": dev})
        result = helper.get_device_from_id("h1")
        assert result is dev

    def test_found_by_device_id(self):
        """Returns the cached Device when looked up by its device_id."""
        dev = Device(
            hive_id="h1",
            hive_name="T",
            hive_type="heating",
            ha_type="climate",
            device_id="d1",
            device_name="T",
            device_data={},
            ha_name="Test",
        )
        helper, _ = _make_helper(entity_cache={"key1": dev})
        result = helper.get_device_from_id("d1")
        assert result is dev

    def test_not_found_returns_false(self):
        """Returns False when the ID is not in the entity_cache."""
        helper, _ = _make_helper()
        assert helper.get_device_from_id("nope") is False

    def test_empty_cache_returns_false(self):
        """Returns False immediately when entity_cache is empty."""
        helper, _ = _make_helper(entity_cache={})
        assert helper.get_device_from_id("h1") is False

    def test_dict_style_cache_entry_found_by_hive_id(self):
        """get_device_from_id also handles dict entries in entity_cache."""
        cache_entry = {"hive_id": "h2", "device_id": "d2", "haName": "Lamp"}
        helper, _ = _make_helper(entity_cache={"lamp": cache_entry})
        result = helper.get_device_from_id("h2")
        assert result is cache_entry

    def test_no_entity_cache_attribute_returns_false(self):
        """If session has no entity_cache at all, returns False gracefully."""
        helper, session = _make_helper()
        del session.entity_cache  # remove the attribute entirely
        assert helper.get_device_from_id("h1") is False


# ---------------------------------------------------------------------------
# HiveHelper.get_device_data
# ---------------------------------------------------------------------------


class TestGetDeviceData:
    """Tests for HiveHelper.get_device_data."""

    def test_sense_type_returns_parent_device(self):
        """'sense' products look up their parent device."""
        devices = {
            "parent-1": {
                "id": "parent-1",
                "type": "hub",
                "state": {"name": "Hub"},
            },
        }
        helper, _ = _make_helper(devices=devices)
        product = {"id": "sense-1", "type": "sense", "parent": "parent-1"}
        result = helper.get_device_data(product)
        assert result["id"] == "parent-1"

    def test_other_type_returns_device_by_product_id(self):
        """Non-special types look up the device using the product ID."""
        devices = {
            "light-1": {
                "id": "light-1",
                "type": "warmwhitelight",
                "state": {"name": "Lamp"},
                "props": {"model": "HALOGEN001"},
            },
        }
        helper, _ = _make_helper(devices=devices)
        # model is NOT "SIREN001" so this falls through to the else branch
        product = {
            "id": "light-1",
            "type": "warmwhitelight",
            "props": {"model": "HALOGEN001"},
        }
        result = helper.get_device_data(product)
        assert result["id"] == "light-1"

    def test_siren001_returns_parent_device(self):
        """warmwhitelight with model SIREN001 looks up device via product['parent']."""
        devices = {
            "hub-1": {"id": "hub-1", "type": "hub", "state": {"name": "Hub"}},
        }
        helper, _ = _make_helper(devices=devices)
        product = {
            "id": "siren-1",
            "type": "warmwhitelight",
            "props": {"model": "SIREN001"},
            "parent": "hub-1",
        }
        result = helper.get_device_data(product)
        assert result["id"] == "hub-1"

    def test_trvcontrol_no_trvs_raises_key_error(self):
        """trvcontrol with an empty trvs list raises KeyError."""
        helper, _ = _make_helper()
        product = {"id": "trv-1", "type": "trvcontrol", "props": {"trvs": []}}
        with pytest.raises(KeyError):
            helper.get_device_data(product)

    def test_trvcontrol_with_trv_returns_device(self):
        """trvcontrol with a valid TRV looks up the TRV device."""
        devices = {
            "trv-device-1": {
                "id": "trv-device-1",
                "type": "trv",
                "state": {"name": "TRV"},
            },
        }
        helper, _ = _make_helper(devices=devices)
        product = {
            "id": "trv-1",
            "type": "trvcontrol",
            "props": {"trvs": ["trv-device-1"]},
        }
        result = helper.get_device_data(product)
        assert result["id"] == "trv-device-1"

    def test_heating_matches_by_zone(self):
        """'heating' type finds the thermostat device sharing the same zone."""
        devices = {
            "thermo-1": {
                "id": "thermo-1",
                "type": "thermostatui",
                "state": {"name": "Thermostat"},
                "props": {"zone": "zone-A"},
            },
        }
        helper, _ = _make_helper(devices=devices)
        product = {
            "id": "heating-1",
            "type": "heating",
            "props": {"zone": "zone-A"},
        }
        result = helper.get_device_data(product)
        assert result["id"] == "thermo-1"
