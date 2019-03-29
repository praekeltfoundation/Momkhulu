from .base import *  # noqa
from .base import env
from .base import BASE_DIR

import os

DEBUG = True

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="sqlite:///{}".format(os.path.join(BASE_DIR, "db.sqlite3")),
    )
}

ENV_HOSTS = [host for host in env.str("ALLOWED_HOSTS", "").split(",") if host]
ALLOWED_HOSTS = ENV_HOSTS + ["localhost", ".localhost", "127.0.0.1", "0.0.0.0"]
