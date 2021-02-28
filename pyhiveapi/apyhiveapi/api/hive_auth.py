"""Sync version of hive auth."""

import asyncio

from .hive_auth_async import HiveAuthAsync


class HiveAuth:
    """Sync wrapper for hive auth."""

    def __init__(self, username, password, pool_region=None, client_secret=None):
        """Initialise hive auth sync."""
        self.auth = HiveAuthAsync(username, password, pool_region, client_secret)
        self.loop = asyncio.get_event_loop()

    def login(self):
        """Login into a Hive account."""
        result = self.loop.run_until_complete(self.auth.login())
        return result

    def sms_2fa(self, entered_code, challenge_parameters):
        """Complete 2FA auth."""
        result = self.loop.run_until_complete(
            self.auth.sms_2fa(entered_code, challenge_parameters)
        )
        return result
