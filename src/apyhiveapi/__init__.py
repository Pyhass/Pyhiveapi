"""__init__.py."""

import os

from .helper.const import SMS_REQUIRED  # noqa: F401
from .hive import Hive  # noqa: F401

if __name__ == "pyhiveapi":
    from .api.hive_api import HiveApi as API  # noqa: F401
    from .api.hive_auth import HiveAuth as Auth  # noqa: F401

    PATH = os.path.dirname(os.path.realpath(__file__)) + "/test_data/"
    PATH = PATH.replace("/pyhiveapi/", "/apyhiveapi/")
else:
    from .api.hive_async_api import HiveApiAsync as API  # noqa: F401
    from .api.hive_auth_async import HiveAuthAsync as Auth  # noqa: F401

    PATH = os.path.dirname(os.path.realpath(__file__)) + "/test_data/"

# noqa: F401
