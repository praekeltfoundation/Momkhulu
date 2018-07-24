from .base import * # noqa
import environ

DEBUG = False

BASE_DIR = environ.Path(__file__) - 2

# PostGres db Setup

DATABASES = {

}
