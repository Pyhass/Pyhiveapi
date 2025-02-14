import pytest
from unittest.mock import AsyncMock, MagicMock
from src.apyhiveapi.plug import Switch
from tests.common import MockSession

@pytest.fixture
async def session():
    session = MockSession()
    hive = await session.async_start_session()
    return hive


@pytest.mark.asyncio
async def test_session_initialised(session):
    assert session is not None

@pytest.mark.asyncio
async def test_get_switch_happy_path(session):
    device = {"device_id": "123", "device_data": {"online": True}, "hive_type": "activeplug"}
    session.attr.online_offline = AsyncMock(return_value=True)
    session.helper.device_recovered = MagicMock()
    session.data.devices = {"123": {"props": "props_data", "parent": "parent_data"}}
    session.attr.state_attributes = AsyncMock(return_value={"attr": "value"})
    session.switch.get_switch_state = AsyncMock(return_value="on")
    session.switch.get_power_usage = AsyncMock(return_value="100W")

    result = await session.switch.get_switch(device)

    assert result["status"]["state"] == "on"
    assert result["status"]["power_usage"] == "100W"
    assert result["attributes"] == {"attr": "value"}

@pytest.mark.asyncio
async def test_get_switch_unhappy_path(switch):
    device = {"device_id": "123", "device_data": {"online": False}, "hive_type": "activeplug"}
    switch.session.attr.online_offline = AsyncMock(return_value=False)
    switch.session.log.error_check = AsyncMock()

    result = await switch.get_switch(device)

    assert result == device

@pytest.mark.asyncio
async def test_turn_on_happy_path(switch):
    device = {"hive_type": "activeplug"}
    switch.set_status_on = AsyncMock(return_value="on")

    result = await switch.turn_on(device)

    assert result == "on"

@pytest.mark.asyncio
async def test_turn_off_happy_path(switch):
    device = {"hive_type": "activeplug"}
    switch.set_status_off = AsyncMock(return_value="off")

    result = await switch.turn_off(device)

    assert result == "off"

@pytest.mark.asyncio
async def test_turn_on_unhappy_path(switch):
    device = {"hive_type": "Heating_Heat_On_Demand"}
    switch.session.heating.set_heat_on_demand = AsyncMock(return_value="ENABLED")

    result = await switch.turn_on(device)

    assert result == "ENABLED"

@pytest.mark.asyncio
async def test_turn_off_unhappy_path(switch):
    device = {"hive_type": "Heating_Heat_On_Demand"}
    switch.session.heating.set_heat_on_demand = AsyncMock(return_value="DISABLED")

    result = await switch.turn_off(device)

    assert result == "DISABLED"