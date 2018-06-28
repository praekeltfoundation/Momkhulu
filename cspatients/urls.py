from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="root"),
    path('index', views.index, name="index"),
    path('form', views.form, name="form"),
    path('event', views.event, name='event'),
    path('login', views.log_in, name="log_in"),
    path('logout', views.log_out, name="log_out"),
]
