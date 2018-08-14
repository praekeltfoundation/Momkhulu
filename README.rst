====
momkhulu
====

This is a hospital resource allocation tool. Provides an API which can be
used with RapidPro. Uses WebSockets for real-time page updates.

####
Getting started on local
####

To set up the environment:

    $ virtualenv env
    $ . env/bin/activate
    $ pip install -r requirements/dev.txt
    $ pip install -e

To start up channels redis::

    $ sudo docker run -p 6379:6379 -d redis:2.8

Migrate the database::

    $ python3 manage.py migrate

Run the server::

    $ python3 manage.py runserver

You can now go access the site on 127.0.0.1/cspatients/

----
Docker Compose
----

To use Docker Compose create a ``.env`` file in the root directory with the following values::

    CHANNEL_LAYERS_PORT=6379
    ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    SECRET_KEY=foobar

Make sure the docker daemon is running::

    $ docker --version

Run the following::

    $ docker-compose build
    $ docker-compose up

The application should
