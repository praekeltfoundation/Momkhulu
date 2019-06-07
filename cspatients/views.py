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

from cspatients import util

from .models import Baby, PatientEntry, Profile
from .tasks import post_patient_update


@login_required()
def view(request):
    template = loader.get_template("cspatients/view.html")
    search = None
    status = None
    if "search" in request.GET and request.GET["search"]:
        search = request.GET["search"]

    if "status" in request.GET and request.GET.get("status", "0") != "0":
        status = request.GET["status"]

    context = {
        "patient_entries": util.get_all_active_patient_entries(search, status),
        "search": search or "",
        "status": status or "0",
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
        entry, errors = util.save_model(request.POST)
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
        patient_data = {}
        status_code = status.HTTP_201_CREATED

        patient_entry, errors = util.save_model(util.get_rp_dict(request.data))
        if patient_entry:
            patient_data = util.serialise_patient_entry(patient_entry)

            post_patient_update.delay()
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        patient_data["errors"] = ", ".join(errors)

        return JsonResponse(patient_data, status=status_code)


class CheckPatientExistsView(APIView):
    def post(self, request):
        patient_data = {}
        return_status = status.HTTP_200_OK

        try:
            patient_id = util.get_rp_dict(request.data)["patient_id"]
            patient_entry = PatientEntry.objects.get(
                patient__patient_id=patient_id, completion_time__isnull=True
            )

            patient_data = util.serialise_patient_entry(patient_entry)
        except PatientEntry.DoesNotExist:
            return_status = status.HTTP_404_NOT_FOUND

        return JsonResponse(patient_data, status=return_status)


class UpdatePatientEntryView(APIView):
    def post(self, request):
        patient_data = {}
        status_code = status.HTTP_200_OK

        changes_dict = util.get_rp_dict(request.data, context="entrychanges")
        patient_entry, errors = util.save_model_changes(changes_dict)
        if patient_entry:
            patient_data = util.serialise_patient_entry(patient_entry)

            post_patient_update.delay()
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        patient_data["errors"] = ", ".join(errors)

        return JsonResponse(patient_data, status=status_code)


class EntryStatusUpdateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = util.get_rp_dict(request.data)
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
        data = {}
        return_status = status.HTTP_200_OK

        try:
            msisdn = request.data["contact"]["urn"].split(":")[1]
            profile = Profile.objects.get(msisdn__contains=msisdn, user__is_active=True)

            data["reset_password_link"] = util.generate_password_reset_url(
                request, profile.user
            )
            data["group_invite_link"] = settings.MOMKHULU_GROUP_INVITE_LINK
        except Profile.DoesNotExist:
            return_status = status.HTTP_404_NOT_FOUND

        return Response(data, status=return_status)


class MultiSelectView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        valid = True
        selected_items = []

        selections = util.clean_and_split_string(request.GET.get("selections", ""))
        options = util.clean_and_split_string(request.GET.get("options", ""))

        for item in selections:
            if not util.can_convert_string_to_int(item):
                valid = False
            elif int(item) > len(options):
                valid = False

        if valid:
            for item in selections:
                option = options[int(item) - 1]
                if option not in selected_items:
                    selected_items.append(option)

        return Response(
            {"valid": valid, "value": ", ".join(selected_items)},
            status=status.HTTP_200_OK,
        )


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
