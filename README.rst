momkhulu
=============================
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black


.. image:: https://codecov.io/gh/praekeltfoundation/momkhulu/branch/develop/graph/badge.svg
  :target: https://codecov.io/gh/praekeltfoundation/momkhulu


This is a hospital resource allocation tool. Provides an API which can be
used with RapidPro. Uses WebSockets for real-time page updates.


Getting started on local
--------------------------

To set up the environment::

    $ git clone git@github.com:praekeltfoundation/momkhulu.git
    $ cd momkhulu
    $ virtualenv env
    $ source env/bin/activate
    $ pip install -e .
    $ pip install -r requirements-dev.txt
    $ pre-commit install

To start up channels redis::

    $ sudo docker run -p 6379:6379 -d redis:2.8

Migrate the database::

    $ ./manage.py migrate

Run the server::

    $ ./manage.py runserver

You can now go access the site on 127.0.0.1/cspatients/
