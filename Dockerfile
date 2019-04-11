FROM praekeltfoundation/django-bootstrap:py3.6

COPY . /app
COPY entrypoint.sh /scripts/django-entrypoint.sh
COPY nginx.conf /etc/nginx/conf.d/django.conf

RUN apt-get -qq update && apt-get -qqy install build-essential python3-dev
RUN pip install --no-cache-dir -e .

RUN apt-get remove --purge -y build-essential python3-dev

ENV DJANGO_SETTINGS_MODULE "momkhulu.settings.production"
RUN SECRET_KEY=placeholder ./manage.py collectstatic --noinput
CMD ["momkhulu.wsgi:application"]
