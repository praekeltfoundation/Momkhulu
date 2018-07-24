from .base import * # noqa
import environ

DEBUG = False

root = environ.Path(__file__) - 2
BASE_DIR = root()

# PostGres db Setup

DATABASES = {

}
