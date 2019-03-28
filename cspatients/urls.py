from django.urls import path

from . import views

urlpatterns = [
    path("", views.view, name="root"),
    path("view", views.view, name="view"),
    path("form", views.form, name="form"),
    path("login", views.log_in, name="log_in"),
    path("logout", views.log_out, name="log_out"),
    path("patient/<str:patient_id>", views.patient, name="patient"),
    path(
        "api/rpnewpatiententry",
        views.NewPatientEntryView.as_view(),
        name="rp_newpatiententry",
    ),
    path(
        "api/rppatientexists",
        views.CheckPatientExistsView.as_view(),
        name="rp_patientexits",
    ),
    path(
        "api/rpentrychanges",
        views.UpdatePatientEntryView.as_view(),
        name="rp_entrychanges",
    ),
    path(
        "api/rpentrydelivered",
        views.EntryDeliveredView.as_view(),
        name="rp_entrydelivered",
    ),
]
