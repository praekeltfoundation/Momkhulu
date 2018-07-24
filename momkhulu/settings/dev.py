from .base import * # noqa

import os
import environ

DEBUG = True

BASE_DIR = environ.Path(__file__) - 2

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
