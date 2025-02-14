"""Tests for the session object."""

from tests.common import MockSession


def test_start_session():
    """Test a session can be started."""
    hive = MockSession()
    hive.sync_start_session()

    assert len(hive.sync_start_session()) > 0
