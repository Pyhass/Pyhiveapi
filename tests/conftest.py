"""Shared pytest fixtures."""

import pytest
from apyhiveapi import Hive


@pytest.fixture
async def file_session():
    """Hive session loaded from the bundled data.json fixture."""
    async with Hive(username="use@file.com", password="") as hive:
        await hive.start_session({})
        yield hive
