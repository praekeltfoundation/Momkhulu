from .base import * # noqa

import os
import environ

DEBUG = True

root = environ.Path(__file__) - 2
BASE_DIR = root()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
