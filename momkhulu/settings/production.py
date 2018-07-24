from .base import * # noqa
from .base import env
# PostGres db Setup

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS", "").split(",")

SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    "default": env.db(
        var="DATABASE_URL",
        default="postgres://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}".format(
            **{
                "USER": env.str("DB_USER", "momkhulu"),
                "PASSWORD": env.str("DB_PASSWORD", "momkhulu"),
                "HOST": env.str("DB_HOST", "localhost"),
                "PORT": env.str("DB_PORT", ""),
                "NAME": env.str("DB_NAME", "momkhulu"),
            }
        ),
    )
}

RAPIDPRO_API_KEY = env.str("RAPIDPRO_API_KEY")
