FROM praekeltfoundation/django-bootstrap:py3.6

COPY . /app
COPY entrypoint.sh /scripts/django-entrypoint.sh
COPY nginx.conf /etc/nginx/conf.d/django.conf
RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE "momkhulu.settings.production"
RUN SECRET_KEY=placeholder ALLOWED_HOSTS=placeholder python manage.py collectstatic --noinput
CMD ["momkhulu.wsgi:application"]
