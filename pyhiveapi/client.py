"""Define a client to interact with the Hive APIs."""
import logging
from typing import Optional

from aiohttp import ClientSession
from .hive_async_api import HiveAsync

_LOGGER = logging.getLogger(__name__)

DEFAULT_API_VERSION = 1


class Client:  # pylint: disable=too-few-public-methods
    """Define the client."""

    def __init__(self, session: Optional[ClientSession] = None,):
        """Initialize."""
        client = HiveAsync(session)
