import os

from .base import *  # noqa
from .base import env

DEBUG = True

SECRET_KEY = os.environ.get("SECRET_KEY", "REPLACEME")

ENV_HOSTS = [host for host in env.str("ALLOWED_HOSTS", "").split(",") if host]
ALLOWED_HOSTS = ENV_HOSTS + ["localhost", ".localhost", "127.0.0.1", "0.0.0.0"]

CELERY_EAGER_PROPAGATES_EXCEPTIONS = False  # To test error handling
CELERY_ALWAYS_EAGER = True
BROKER_BACKEND = "memory"
CELERY_RESULT_BACKEND = "djcelery.backends.database:DatabaseBackend"

RABBITMQ_MANAGEMENT_INTERFACE = "http://user:pass@rabbitmq:15672/api/queues//my_vhost/"
MOMKHULU_GROUP_INVITE_LINK = "http://fakewhatsapp/the-group-id"
MOMKHULU_WA_GROUP_ID = "the-group-id"
RAPIDPRO_CHANNEL_URL = (
    "https://myrp.com/c/wa/11111111-1111-1111-1111-111111111111/receive"
)

TURN_TOKEN = env.str("TURN_TOKEN", "123456")
TURN_URL = env.str("TURN_URL", "https://fakewhatsapp/")
