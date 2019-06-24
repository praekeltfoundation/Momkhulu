from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import PatientEntry
from .serializers import PatientEntrySerializer, UpdateEntrySerializer


def get_rp_dict(data, context=None):
    """
    Get a label and value dictionary from the request POST
    """
    all_dict = {}

    for key, item in data["results"].items():
        """
        All Responses is a category base for responses that are free text
        and not options. If not all All Responses, the label must take
        the value of the chosen category base.
        """
        if item["category"] == "All Responses":
            all_dict[key] = item["value"]
        else:
            all_dict[key] = item["category"]

    if context == "entrychanges":
        final_dict = {}
        final_dict[all_dict["change_category"]] = all_dict["new_value"]
        if "patient_id" in all_dict:
            final_dict["patient_id"] = all_dict["patient_id"]
        return final_dict
    else:
        return all_dict


def get_all_active_patient_entries(search=None, status=None):
    # At 7am SAST(5am UTC) we hide all completed patients from the previous day
    last_date = timezone.now().date()
    if timezone.now().hour < 5:
        last_date = timezone.now().date() - timezone.timedelta(days=1)

    patiententrys = PatientEntry.objects.filter(operation_cancelled=False).filter(
        Q(completion_time__isnull=True)
        | Q(completion_time__isnull=False, decision_time__gte=last_date)
    )

    if search:
        patiententrys = patiententrys.filter(surname__icontains=search)

    if status:
        if status == "complete":
            patiententrys = patiententrys.filter(completion_time__isnull=False)
        else:
            patiententrys = patiententrys.filter(
                urgency=status, completion_time__isnull=True
            )

    # latest most urgent on the top, completed at the bottom
    sorted_entries = sorted(
        patiententrys, key=lambda x: (x.decision_time), reverse=True
    )
    return sorted(
        sorted_entries, key=lambda x: (x.completion_time is not None, x.urgency)
    )


def send_consumers_table():
    """
        Method to send a rendered templated through to the
        view channel in the ViewConsumer.
    """
    template = loader.get_template("cspatients/table.html")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "view",
        {
            "type": "view.update",
            "content": template.render(
                {"patient_entries": get_all_active_patient_entries()}
            ),
        },
    )


def save_model_changes(data):
    """
        The function takes in the request.POST object and saves changes in the
        PatientEntry model. Returns object and errors
    """
    serializer = UpdateEntrySerializer(data=data)
    if not serializer.is_valid():
        return None, get_errors_from_serializer(serializer.errors)

    entry_data = get_patient_entry_data(data)

    try:
        patiententry = PatientEntry.objects.get(id=data["patient_id"])
    except PatientEntry.DoesNotExist:
        return None, ["Patient entry does not exist"]

    patiententry.__dict__.update(entry_data)
    patiententry.save()

    return patiententry, []


def save_model(data):
    """
        Saves model. Returns PatientEntry object.
    """
    serializer = PatientEntrySerializer(data=data)
    if not serializer.is_valid():
        return None, get_errors_from_serializer(serializer.errors)

    entry_data = get_patient_entry_data(data)

    return PatientEntry.objects.create(**entry_data), []


def get_errors_from_serializer(serializer_errors):
    """
    Extracts the errors from the serializer errors into a list of strings.
    """
    errors = []
    for key, details in serializer_errors.items():
        for error in details:
            errors.append(str(error))
    return errors


def get_patient_entry_data(data):
    """
    Removes all the unwanted keys from the data and updates the surname for
    patients without consent
    """
    entry_data = {}

    patient_entry_fields = [f.name for f in PatientEntry._meta.get_fields()]

    for key, value in data.items():
        if key in patient_entry_fields:
            entry_data[key] = value

    if "No Consent" in entry_data.get("surname", ""):
        clinician = entry_data.get("clinician", "")
        entry_data["surname"] = f"Pt of {clinician}"

    return entry_data


def generate_password_reset_url(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    path = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    return request.build_absolute_uri(path)


def clean_and_split_string(text, separator=","):
    return [x.strip() for x in text.strip().split(separator) if x]


def can_convert_string_to_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def serialise_patient_entry(patient_entry):
    patient_entry_serializer = PatientEntrySerializer(patient_entry)
    return patient_entry_serializer.data


def build_new_patient_message(patient_data, url):
    patient_data["momkhulu_url"] = url
    message_template = (
        "Patient Ms. {surname} has been added to the Momkhulu Triage Board.\n\n"
        "*Patient Details:*\n"
        "Operation: {operation}\n"
        "Location: {location}\n"
        "Indications: {indication}\n"
        "Urgency: {urgency}\n"
        "Decision time: {decision_time}\n\n"
        "You can now view her entry here: {momkhulu_url}"
    )
    return message_template.format(**patient_data)
