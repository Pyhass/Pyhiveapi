"""Test the helper method for writing tests."""
# pylint: skip-file

from dataclasses import dataclass

from apyhiveapi import Hive as HiveAsync

from pyhiveapi import Hive as HiveSync

USERNAME = "use@file.com"
PASSWORD = "Test12345"
TEMP_CONFIG = {
    "username": USERNAME,
    "password": PASSWORD,
    "options": {"scan_interval": 120},
}


@dataclass
class MockConfig:
    """Mock config for tests."""

    username: str
    password: str
    device_data: dict
    tokens: dict
    options: dict


@dataclass
class MockDevice:
    """Mock config for tests."""

    username: str
    password: str
    device_data: dict
    tokens: dict
    options: dict


class MockSession:
    """Mock Session for tests."""

    def __init__(self):
        """Initialize the Mock Session."""
        self.async_hive = None
        self.sync_hive = None

    def sync_start_session(self):
        """Start a sync session."""
        self.sync_hive = HiveSync(username=USERNAME, password=PASSWORD)
        return self.sync_hive.startSession(TEMP_CONFIG)

    async def async_start_session(self):
        """Start a async session."""
        self.async_hive = HiveAsync(username=USERNAME, password=PASSWORD)
        return await self.async_hive.startSession(TEMP_CONFIG)
