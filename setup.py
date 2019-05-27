import codecs
import os
from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))


def read(*args):
    with codecs.open(os.path.join(HERE, *args), "rb", "utf-8") as f:
        return f.read()


def get_requirements():
    return read("requirements.txt").split("\n")


setup(
    name="momkhulu",
    version="0.0.3",
    description="Hospital Resource Allocation Tool",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    keywords="real-time hospital-updates whatsapp rapidpro channels",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Healthcare Industry"
        "Intended Audience :: Science/Research"
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
    ],
    author="Praekelt.org",
    author_email="dev@praekelt.org",
    url="https://github.com/praekeltfoundation/momkhulu",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "celery==3.1.26post2",
        "daphne==2.2",
        "channels==2.1.7",
        "channels-redis==2.3.3",
        "Django>=2.1.7,<2.2",
        "django-celery==3.2.2",
        "django-environ==0.4.5",
        "djangorestframework>=3.9.1,<4",
        "environ==1.0",
        "simplejson==3.16.0",
        "psycopg2==2.7.1",
        "raven==6.9.0",
        "requests==2.21.0",
    ],
    entry_points={},
)
