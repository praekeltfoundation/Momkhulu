from django.conf.urls import url

from .consumers import ViewConsumer

websocket_urlpatterns = [
    url("ws/cspatients/viewsocket/", ViewConsumer),
]
