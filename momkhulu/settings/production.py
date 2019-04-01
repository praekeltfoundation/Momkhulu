from .base import *  # noqa
from .base import env

SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")

# PostGres db Setup
DATABASES = {
    "default": env.db(default="postgres://momkhulu:momkhulu@localhost:5432/momkhulu")
}
