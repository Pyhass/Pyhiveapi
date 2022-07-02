"""Tests for the switch and plug object."""

from unittest.mock import patch

import pytest

from tests.common import MockSession


@pytest.mark.asyncio
async def test_switch_update_switch():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][1]
    device_data = await hive_session.switch.getSwitch(switch)

    assert device_data != {}


@pytest.mark.asyncio
async def test_switch_get_plug_state():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][1]
    state = await hive_session.switch.getSwitchState(switch)

    assert state in (True, False)


@pytest.mark.asyncio
async def test_switch_get_plug_state_with_key_error():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][1]
    hive_session.session.data.products.pop(switch["hiveID"])
    state = await hive_session.switch.getState(switch)

    assert state is None


@pytest.mark.asyncio
async def test_switch_get_heat_on_demand_state():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][0]
    state = await hive_session.switch.getSwitchState(switch)

    assert state in (True, False)


@pytest.mark.asyncio
async def test_switch_turn_on_successfully():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][1]

    with patch(
        "apyhiveapi.api.hive_async_api.HiveApiAsync.setState",
        return_value={"original": 200, "parsed": {}},
    ) as api_call:
        result = await hive_session.switch.turnOn(switch)

    assert result is True
    assert len(api_call.mock_calls) == 1


@pytest.mark.asyncio
async def test_switch_turn_off_unsuccessfully():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][1]

    with patch(
        "apyhiveapi.api.hive_async_api.HiveApiAsync.setState",
        return_value={"original": 401, "parsed": {}},
    ) as api_call:
        result = await hive_session.switch.turnOff(switch)

    assert result is False
    assert len(api_call.mock_calls) == 1


@pytest.mark.asyncio
async def test_switch_heat_on_demand_turn_on_successfully():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][0]

    with patch(
        "apyhiveapi.api.hive_async_api.HiveApiAsync.setState",
        return_value={"original": 200, "parsed": {}},
    ) as api_call:
        result = await hive_session.switch.turnOn(switch)

    assert result is True
    assert len(api_call.mock_calls) == 1


@pytest.mark.asyncio
async def test_switch_heat_on_demand_turn_on_unsuccessfully():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][0]

    with patch(
        "apyhiveapi.api.hive_async_api.HiveApiAsync.setState",
        return_value={"original": 401, "parsed": {}},
    ) as api_call:
        result = await hive_session.switch.turnOff(switch)

    assert result is False
    assert len(api_call.mock_calls) == 1


@pytest.mark.asyncio
async def test_plug_get_power_usage():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    switch = hive_session.session.device_list["switch"][1]
    power_usage = await hive_session.switch.getPowerUsage(switch)

    assert power_usage is not None
