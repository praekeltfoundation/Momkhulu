from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template import loader

from .models import Patient, PatientEntry
from .serializers import CreateEntrySerializer

PATIENT_FIELDS = Patient.__dict__.keys()
PATIENTENTRY_FIELDS = PatientEntry.__dict__.keys()


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


def get_all_active_patient_entries():
    patiententrys = PatientEntry.objects.select_related("patient").all()
    sorted_entries = sorted(
        patiententrys, key=lambda x: (x.urgency, x.decision_time), reverse=True
    )
    return sorted(sorted_entries, key=lambda x: (x.completion_time is not None))


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
        The function takes in the request.POST object and saves changes in
        models. Returns boolean
    """
    serializer = CreateEntrySerializer(data=data)
    if not serializer.is_valid():
        return None, get_errors_from_serializer(serializer.errors)

    patient_data, entry_data = split_patient_and_entry_data(data)

    try:
        patiententry = PatientEntry.objects.get(
            patient__patient_id=data["patient_id"], completion_time__isnull=True
        )
    except PatientEntry.DoesNotExist:
        return None, ["Patient entry does not exist"]
    patient = patiententry.patient
    entry_data["patient"] = patient

    patient.__dict__.update(patient_data)
    patient.save()
    patiententry.__dict__.update(entry_data)
    patiententry.save()

    return patiententry, []


def save_model(data):
    """
        Saves a models. Returns patient object.
    """
    serializer = CreateEntrySerializer(data=data)
    if not serializer.is_valid():
        return None, get_errors_from_serializer(serializer.errors)

    patient_data, entry_data = split_patient_and_entry_data(data)

    patient, created = Patient.objects.update_or_create(
        patient_id=patient_data["patient_id"], defaults=patient_data
    )

    # check if we already have a active entry
    if PatientEntry.objects.filter(
        patient=patient, completion_time__isnull=True
    ).exists():
        return None, ["Active entry already exists for this patient"]

    entry_data["patient"] = patient
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


def split_patient_and_entry_data(data):
    """
    Splits the data from a RapidPro POST request into patient and patient entry
    related fields.
    """
    patient_data = {}
    entry_data = {}

    patient_fields = [f.name for f in Patient._meta.get_fields()]
    patient_entry_fields = [f.name for f in PatientEntry._meta.get_fields()]

    for key, value in data.items():
        if key in patient_fields:
            patient_data[key] = value
        elif key in patient_entry_fields:
            entry_data[key] = value

    return patient_data, entry_data
