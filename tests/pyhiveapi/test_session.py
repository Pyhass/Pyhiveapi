"""Tests for the session object."""

from tests.common import MockSession


def test_start_session():
    """Test a session can be started."""
    hive = MockSession()
    device_list = hive.sync_start_session()

    assert len(device_list) > 0
