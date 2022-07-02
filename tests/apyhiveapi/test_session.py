"""Tests for the session object."""

import pytest

from tests.common import MockSession


@pytest.mark.asyncio
async def test_start_session():
    """Test a session can be started."""
    hive = MockSession()
    device_list = await hive.async_start_session()

    assert len(device_list) > 0
