from .base import *  # noqa
from .base import env

# PostGres db Setup

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": env.db(default="postgres://momkhulu:momkhulu@localhost:5432/momkhulu")
}
