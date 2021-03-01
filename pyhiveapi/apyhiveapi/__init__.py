"""__init__.py."""
from .helper.const import SMS_REQUIRED  # noqa: F401

if __name__ == "pyhiveapi.__init__":
    from .api.hive_api import HiveApi as API  # noqa: F401
    from .api.hive_auth import HiveAuth as Auth  # noqa: F401
    from .hive import HiveAsync  # noqa: F401
elif __name__ == "apyhiveapi.__init__":
    from .api.hive_async_api import HiveApiAsync as API  # noqa: F401
    from .api.hive_auth_async import HiveAuthAsync as Auth  # noqa: F401
    from .hive import HiveAsync  # noqa: F401
