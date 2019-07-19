from os import environ

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cspatients import util

from .models import Baby, PatientEntry, Profile
from .tasks import post_patient_update, send_rapidpro_event, send_wa_group_message


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
    context = {"user": request.user}
    status_code = status.HTTP_200_OK

    try:
        patiententry = PatientEntry.objects.prefetch_related("entry_babies").get(
            id=patient_id
        )
        context["patiententry"] = patiententry
    except PatientEntry.DoesNotExist:
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
            patient_entry.refresh_from_db()
            patient_data = util.serialise_patient_entry(patient_entry)

            message = util.build_new_patient_message(
                patient_data, request.build_absolute_uri("/")
            )

            send_wa_group_message.delay(message)
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
            patient_entry = PatientEntry.objects.get(id=patient_id)

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
            patient_entry.refresh_from_db()
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
            patiententry = PatientEntry.objects.get(id=data["patient_id"])

            if data["option"] == "Delivery":
                patiententry.foetus = data["foetus"]
                patiententry.starvation_hours = data.get("starvation_hours")

                if data["baby_number"] == data["foetus"]:
                    patiententry.completion_time = timezone.now()

                default_data = {
                    "apgar_1": data.get("apgar_1"),
                    "apgar_5": data.get("apgar_5"),
                    "baby_weight_grams": data.get("baby_weight_grams"),
                    "delivery_time": data["delivery_time"],
                }

                if "nicu" in data:
                    default_data["nicu"] = data["nicu"] == "Yes"

                _, _ = Baby.objects.update_or_create(
                    patiententry=patiententry,
                    baby_number=data["baby_number"],
                    defaults=default_data,
                )

            elif data["option"] == "Completed":
                patiententry.completion_time = data["completion_time"]
            elif data["option"] == "NonDelivery":
                patiententry.anesthetic_time = data["anesthetic_time"]
                patiententry.completion_time = timezone.now()
                patiententry.starvation_hours = data.get("starvation_hours")
            elif data["option"] == "ChangeOrCancel":
                patiententry.operation_cancelled = True
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

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
        options = util.clean_and_split_string(
            request.GET.get("options", ""), separator="|"
        )

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


class ActivePatientListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        entries = PatientEntry.objects.filter(
            completion_time__isnull=True, operation_cancelled=False
        )

        ids = []
        patient_data = []
        for count, entry in enumerate(entries, start=1):
            patient_data.append(
                f"{count}) {entry.surname} {entry.operation} {entry.indication} {entry.get_urgency_color()}"
            )
            ids.append(f"{count}={entry.id}")

        data = {"patient_ids": "|".join(ids)}

        list_size = settings.PATIENT_LIST_SIZE
        list_number = 0
        while len(patient_data) > 0:
            list_number += 1
            data[f"patient_list_{list_number}"] = "\n".join(patient_data[0:list_size])
            patient_data = patient_data[list_size:]

        data["list_count"] = list_number

        return Response(data, status=status.HTTP_200_OK)


class PatientSelectView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        id_string = request.GET.get("patient_ids", "")
        option = request.GET.get("option", "")

        patient_ids = dict(item.split("=") for item in id_string.split("|"))

        return Response(
            {"patient_id": patient_ids.get(option, "-1")}, status=status.HTTP_200_OK
        )


class WhatsAppEventListener(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):

        payload = {"messages": [], "events": []}

        for type in ("messages", "events"):
            if type in request.data:
                for item in request.data[type]:
                    if "group_id" not in item:
                        payload[type].append(item)

        payload["contacts"] = request.data.get("contacts", [])

        if len(payload["messages"]) == 0 and len(payload["events"]) == 0:
            return Response(status=status.HTTP_200_OK)

        send_rapidpro_event.delay(payload)

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
