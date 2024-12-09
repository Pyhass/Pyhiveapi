"""Tests for the switch and plug object."""

from unittest.mock import patch

from tests.common import MockSession


def test_switch_update_switch_online():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]
    device_data = hive_session.switch.get_switch(switch)

    assert device_data != {}


def test_switch_update_switch_offline():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]
    switch["device_data"]["online"] = False
    device_data = hive_session.switch.get_switch(switch)

    assert device_data["hive_id"] in hive_session.session.config.error_list


def test_switch_get_plug_state():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]
    state = hive_session.switch.get_switchState(switch)

    assert state in (True, False)


def test_switch_get_plug_state_with_key_error():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]
    hive_session.session.data.products.pop(switch["hive_id"])
    state = hive_session.switch.get_state(switch)

    assert state is None


def test_switch_get_heat_on_demand_state():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][0]
    state = hive_session.switch.get_switchState(switch)

    assert state in (True, False)


def test_switch_turn_on_successfully():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.set_state",
        return_value={"original": 200, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turn_on(switch)

    assert result is True
    assert len(api_call.mock_calls) == 1


def test_switch_turn_on_unsuccessfully():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.set_state",
        return_value={"original": 401, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turn_on(switch)

    assert result is False
    assert len(api_call.mock_calls) == 1


def test_switch_turn_off_successfully():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.set_state",
        return_value={"original": 200, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turn_off(switch)

    assert result is True
    assert len(api_call.mock_calls) == 1


def test_switch_turn_off_unsuccessfully():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.set_state",
        return_value={"original": 401, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turn_off(switch)

    assert result is False
    assert len(api_call.mock_calls) == 1


def test_switch_heat_on_demand_turn_on_successfully():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][0]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.set_state",
        return_value={"original": 200, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turn_on(switch)

    assert result is True
    assert len(api_call.mock_calls) == 1


def test_switch_heat_on_demand_turn_on_unsuccessfully():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][0]

    with patch(
        "pyhiveapi.api.hive_api.HiveApi.set_state",
        return_value={"original": 401, "parsed": {}},
    ) as api_call:
        result = hive_session.switch.turn_off(switch)

    assert result is False
    assert len(api_call.mock_calls) == 1


def test_plug_get_power_usage():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]
    power_usage = hive_session.switch.get_power_usage(switch)

    assert power_usage is not None


def test_plug_get_power_usage_with_key_error():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()
    hive_session = hive.sync_hive
    switch = hive_session.session.device_list["switch"][1]
    hive_session.session.data.products.pop(switch["hive_id"])
    state = hive_session.switch.get_power_usage(switch)

    assert state is None
