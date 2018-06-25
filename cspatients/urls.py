from django.urls import path

from . import views

urlpatterns = [
    path('index', views.index, name="index"),
    path('form', views.form, name="form"),
    path('', views.submit, name='submit'),
]
