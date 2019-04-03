from .base import *  # noqa
from .base import env

import os

DEBUG = True

SECRET_KEY = os.environ.get("SECRET_KEY", "REPLACEME")

ENV_HOSTS = [host for host in env.str("ALLOWED_HOSTS", "").split(",") if host]
ALLOWED_HOSTS = ENV_HOSTS + ["localhost", ".localhost", "127.0.0.1", "0.0.0.0"]
