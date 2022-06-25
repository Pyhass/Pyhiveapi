"""Tests for the switch and plug object."""

from unittest.mock import patch

from tests.common import MockSession


def test_switch_turn_on_success():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.deviceList["switch"][1]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.setState",
        return_value={"original": 200, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turnOn(switch)

    assert result is True
    assert len(api_call.mock_calls) == 1
