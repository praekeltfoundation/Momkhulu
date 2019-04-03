from .base import *  # noqa
from .base import env

SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")

# Configure Sentry Logging
INSTALLED_APPS += ("raven.contrib.django.raven_compat",)
RAVEN_DSN = env.str("RAVEN_DSN", "")
RAVEN_CONFIG = {"dsn": RAVEN_DSN} if RAVEN_DSN else {}
