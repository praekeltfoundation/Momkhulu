from .base import * # noqa
from .base import env
# PostGres db Setup

DATABASES = {

}

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")
