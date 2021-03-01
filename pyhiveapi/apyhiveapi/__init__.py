"""__init__.py."""
if __name__ == "pyhiveapi":
    from .api.hive_api import HiveApi as API  # noqa: F401
    from .api.hive_auth import HiveAuth as Auth  # noqa: F401
else:
    from .api.hive_async_api import HiveApiAsync as API  # noqa: F401
    from .api.hive_auth_async import HiveAuthAsync as Auth  # noqa: F401

from .helper.const import SMS_REQUIRED  # noqa: F401
from .hive import Hive  # noqa: F401
