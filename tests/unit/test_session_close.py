"""Tests for HiveSession.close() covering both branches of the websession guard."""

from unittest.mock import AsyncMock, MagicMock

from apyhiveapi.session import HiveSession


class TestHiveSessionClose:
    """Branch coverage for HiveSession.close() (line 79)."""

    async def test_close_calls_websession_close_when_not_already_closed(self):
        """close() calls websession.close() when websession is open (closed=False).

        Covers the True branch of 'if not self.api.websession.closed'.
        """
        session = object.__new__(HiveSession)
        session.api = MagicMock()
        session.api.websession.closed = False
        session.api.websession.close = AsyncMock()

        await session.close()

        session.api.websession.close.assert_called_once()

    async def test_close_skips_websession_close_when_already_closed(self):
        """close() does NOT call websession.close() when websession is already closed.

        Covers branch 79->exit: the 'if not closed' condition is False, so the
        body is skipped entirely.
        """
        session = object.__new__(HiveSession)
        session.api = MagicMock()
        session.api.websession.closed = True
        session.api.websession.close = AsyncMock()

        await session.close()

        session.api.websession.close.assert_not_called()
