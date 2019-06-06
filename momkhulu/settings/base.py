import os

import djcelery
import environ
from kombu import Exchange, Queue

root = environ.Path(__file__) - 3
BASE_DIR = root()
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "cspatients",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "djcelery",
    "rest_framework",
    "rest_framework.authtoken",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "momkhulu.urls"

LOGIN_URL = "/accounts/login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "momkhulu.wsgi.application"

# Channels Settings

ASGI_APPLICATION = "momkhulu.routing.application"

REDIS_URL = env.str(
    "REDIS_URL",
    "redis://{}:{}".format(
        env.str("CHANNEL_LAYERS_HOST", "127.0.0.1"),
        env.int("CHANNEL_LAYERS_PORT", 6379),
    ),
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# Database
DATABASES = {"default": env.db(default="postgres://postgres@localhost:5432/momkhulu")}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Johannesburg"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# REST Framework conf defaults
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# Celery configuration options
CELERY_RESULT_BACKEND = "djcelery.backends.database:DatabaseBackend"
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

BROKER_URL = env.str("BROKER_URL", "redis://localhost:6379/0")

CELERY_DEFAULT_QUEUE = "momkhulu"
CELERY_QUEUES = (Queue("momkhulu", Exchange("momkhulu"), routing_key="momkhulu"),)

CELERY_ALWAYS_EAGER = False

# Tell Celery where to find the tasks
CELERY_IMPORTS = ("cspatients.tasks",)

CELERY_CREATE_MISSING_QUEUES = True
CELERY_ROUTES = {"celery.backend_cleanup": {"queue": "mediumpriority"}}

CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

djcelery.setup_loader()

RABBITMQ_MANAGEMENT_INTERFACE = env.str("RABBITMQ_MANAGEMENT_INTERFACE", "")

MOMKHULU_GROUP_INVITE_LINK = env.str("MOMKHULU_GROUP_INVITE_LINK", "REPLACEME")
