from django.urls import path

from . import views

urlpatterns = [
    path('', views.view, name="root"),
    path('view', views.view, name="view"),
    path('form', views.form, name="form"),
    path('rpevent', views.rp_event, name='rp_event'),
    path('login', views.log_in, name="log_in"),
    path('logout', views.log_out, name="log_out"),
    path('patient/<int:patient_id>', views.patient, name="patient"),
]
