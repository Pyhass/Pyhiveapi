"""Sync wrapper for hive."""

from syncer import sync

from ..ahive.hiveasync import HiveAsync


class Hive:
    """Hive class for sync."""

    def __init__(self):
        """Initialise Hive sync."""
        return sync(HiveAsync())
