"""Tests for the hub object."""

import pytest

from tests.common import MockSession


@pytest.mark.asyncio
async def test_hub_get_smoke_status_detected():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    smoke_sensor = hive_session.session.device_list["binary_sensor"][1]
    hive_session.session.data.products[smoke_sensor["hiveID"]]["props"]["sensors"][
        "SMOKE_CO"
    ]["active"] = True
    state = await hive_session.hub.get_smoke_status(smoke_sensor)

    assert state == 1


@pytest.mark.asyncio
async def test_hub_get_smoke_status_not_detected():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    smoke_sensor = hive_session.session.device_list["binary_sensor"][1]

    state = await hive_session.hub.get_smoke_status(smoke_sensor)

    assert state == 0


@pytest.mark.asyncio
async def test_hub_get_smoke_status_with_key_error():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    smoke_sensor = hive_session.session.device_list["binary_sensor"][1]
    hive_session.session.data.products.pop(smoke_sensor["hiveID"])
    state = await hive_session.hub.get_smoke_status(smoke_sensor)

    assert state is None


@pytest.mark.asyncio
async def test_hub_get_glass_break_detected():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    glass_sensor = hive_session.session.device_list["binary_sensor"][0]
    state = await hive_session.hub.get_glass_break_status(glass_sensor)

    assert state == 1


@pytest.mark.asyncio
async def test_hub_get_glass_break_not_detected():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    glass_sensor = hive_session.session.device_list["binary_sensor"][1]
    hive_session.session.data.products[glass_sensor["hiveID"]]["props"]["sensors"][
        "GLASS_BREAK"
    ]["active"] = False
    state = await hive_session.hub.get_glass_break_status(glass_sensor)

    assert state == 0


@pytest.mark.asyncio
async def test_hub_get_glass_break_detection_with_key_error():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    glass_sensor = hive_session.session.device_list["binary_sensor"][0]
    hive_session.session.data.products.pop(glass_sensor["hiveID"])
    state = await hive_session.hub.get_glass_break_status(glass_sensor)

    assert state is None


@pytest.mark.asyncio
async def test_hub_get_dog_bark_detected():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    dog_sensor = hive_session.session.device_list["binary_sensor"][2]
    hive_session.session.data.products[dog_sensor["hiveID"]]["props"]["sensors"][
        "DOG_BARK"
    ]["active"] = True
    state = await hive_session.hub.get_dog_bark_status(dog_sensor)

    assert state == 1


@pytest.mark.asyncio
async def test_hub_get_dog_bark_not_detected():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    dog_sensor = hive_session.session.device_list["binary_sensor"][2]
    state = await hive_session.hub.get_dog_bark_status(dog_sensor)

    assert state == 0


@pytest.mark.asyncio
async def test_hub_get_dog_bark_detection_status_with_key_error():
    """Test a session can be started."""
    hive = MockSession()
    await hive.async_start_session()
    hive_session = hive.async_hive
    dog_sensor = hive_session.session.device_list["binary_sensor"][2]
    hive_session.session.data.products.pop(dog_sensor["hiveID"])
    state = await hive_session.hub.get_dog_bark_status(dog_sensor)

    assert state is None
