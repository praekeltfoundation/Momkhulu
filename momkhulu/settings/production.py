from .base import * # noqa
import os

DEBUG = False

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# PostGres db Setup

DATABASES = {

}
