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
