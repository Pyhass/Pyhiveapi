"""Tests for session polling behaviour."""

# pylint: disable=protected-access
from unittest.mock import AsyncMock

import pytest

from apyhiveapi import Hive


def test_hub_smoke():
    """Placeholder smoke test."""
    assert True


@pytest.mark.asyncio
async def test_force_update_polls_when_idle():
    """forceUpdate() calls _pollDevices and returns its result when no poll is running."""
    hive = Hive(username="test@example.com", password="pass")
    hive._pollDevices = AsyncMock(return_value=True)

    result = await hive.forceUpdate()

    assert result is True
    hive._pollDevices.assert_called_once()


@pytest.mark.asyncio
async def test_force_update_skips_when_locked():
    """forceUpdate() returns False without polling when the update lock is already held."""
    hive = Hive(username="test@example.com", password="pass")
    hive._pollDevices = AsyncMock(return_value=True)

    async with hive.updateLock:
        result = await hive.forceUpdate()

    assert result is False
    hive._pollDevices.assert_not_called()
