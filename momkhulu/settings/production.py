from .base import * # noqa
from .base import env
# PostGres db Setup

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")

SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    "default": env.db(
        default="postgres://postgres@db:5432/postgres"
    )
}
