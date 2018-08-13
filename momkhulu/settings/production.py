from .base import * # noqa
from .base import env
# PostGres db Setup

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")

SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    "default": env.db(
        var="DATABASE_URL",
        default="postgres://momkhulu:momkhulu@localhost:5432/momkhulu"
    )
}
