from os import environ

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Baby, PatientEntry, Profile
from .serializers import PatientEntrySerializer, PatientSerializer
from .tasks import post_patient_update
from .util import (
    get_all_active_patient_entries,
    get_rp_dict,
    save_model,
    save_model_changes,
)


@login_required()
def view(request):
    template = loader.get_template("cspatients/view.html")
    search = None
    if "search" in request.GET and request.GET["search"]:
        search = request.GET["search"]

    context = {
        "patient_entries": get_all_active_patient_entries(search),
        "user": request.user,
    }
    return HttpResponse(template.render(context), status=200)


@login_required()
def patient(request, patient_id):
    template = loader.get_template("cspatients/patient.html")
    patiententry = (
        PatientEntry.objects.prefetch_related("entry_babies", "patient")
        .filter(patient__patient_id=patient_id)
        .order_by("-created_at")
        .first()
    )

    context = {"patiententry": patiententry, "user": request.user}
    if patiententry:
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_404_NOT_FOUND
    return HttpResponse(template.render(context), status=status_code)


@login_required()
def form(request):
    errors = []
    status_code = status.HTTP_200_OK
    if request.method == "POST":
        entry, errors = save_model(request.POST)
        if entry:
            status_code = status.HTTP_201_CREATED
            post_patient_update.delay()
        else:
            status_code = status.HTTP_400_BAD_REQUEST
    return render(
        request,
        "cspatients/form.html",
        context={"errors": errors, "user": request.user},
        status=status_code,
    )


# API VIEWS
class NewPatientEntryView(APIView):
    def post(self, request):
        entry, errors = save_model(get_rp_dict(request.data))
        if entry:
            post_patient_update.delay()
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        return JsonResponse({"errors": ", ".join(errors)}, status=status_code)


class CheckPatientExistsView(APIView):
    def post(self, request):
        patient_data = {}
        return_status = status.HTTP_200_OK

        try:
            patient_id = get_rp_dict(request.data)["patient_id"]
            patient_entry = PatientEntry.objects.get(
                patient__patient_id=patient_id, completion_time__isnull=True
            )

            patient_entry_serializer = PatientEntrySerializer(patient_entry)
            patient_serializer = PatientSerializer(patient_entry.patient)

            patient_data = patient_entry_serializer.data
            patient_data.update(patient_serializer.data)
        except PatientEntry.DoesNotExist:
            return_status = status.HTTP_404_NOT_FOUND

        return JsonResponse(patient_data, status=return_status)


class UpdatePatientEntryView(APIView):
    def post(self, request):
        changes_dict = get_rp_dict(request.data, context="entrychanges")
        entry, errors = save_model_changes(changes_dict)
        if entry:
            status_code = status.HTTP_200_OK

            post_patient_update.delay()
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        return JsonResponse({"errors": ", ".join(errors)}, status=status_code)


class EntryStatusUpdateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = get_rp_dict(request.data)
        try:
            patiententry = PatientEntry.objects.get(
                patient__patient_id=data["patient_id"], completion_time__isnull=True
            )

            if data["option"] == "Delivery":
                patiententry.foetus = data["foetus"]

                _, _ = Baby.objects.update_or_create(
                    patiententry=patiententry,
                    baby_number=data["baby_number"],
                    defaults={
                        "apgar_1": data["apgar_1"],
                        "apgar_5": data["apgar_5"],
                        "baby_weight_grams": data["baby_weight_grams"],
                        "delivery_time": data["delivery_time"],
                        "nicu": data["nicu"] == "Yes",
                    },
                )

            elif data["option"] == "Completed":
                patiententry.completion_time = data["completion_time"]

            patiententry.save()
            post_patient_update.delay()
        except PatientEntry.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_200_OK)


class WhitelistCheckView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            msisdn = request.data["contact"]["urn"].split(":")[1]
            Profile.objects.get(msisdn__contains=msisdn, user__is_active=True)
        except Profile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_200_OK)


def health(request):
    app_id = environ.get("MARATHON_APP_ID", None)
    ver = environ.get("MARATHON_APP_VERSION", None)
    return JsonResponse({"id": app_id, "version": ver})


def detailed_health(request):
    queues = []
    stuck = False

    if settings.RABBITMQ_MANAGEMENT_INTERFACE:
        message = "queues ok"
        for queue in settings.CELERY_QUEUES:
            queue_results = requests.get(
                "{}{}".format(settings.RABBITMQ_MANAGEMENT_INTERFACE, queue.name)
            ).json()

            details = {
                "name": queue_results["name"],
                "stuck": False,
                "messages": queue_results.get("messages"),
                "rate": queue_results["messages_details"]["rate"],
            }
            if details["messages"] > 0 and details["rate"] == 0:
                stuck = True
                details["stuck"] = True

            queues.append(details)
    else:
        message = "queues not checked"

    status_code = status.HTTP_200_OK
    if stuck:
        message = "queues stuck"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JsonResponse({"update": message, "queues": queues}, status=status_code)
