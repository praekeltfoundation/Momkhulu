FROM praekeltfoundation/django-bootstrap:py3.6

COPY . /app
RUN pip install --no-cache-dir -e .

ENV DJANGO_SETTINGS_MODULE "momkhulu.settings.production"
RUN SECRET_KEY=placeholder ./manage.py collectstatic --noinput
CMD ["momkhulu.wsgi:application"]
