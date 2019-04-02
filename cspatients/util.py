from django.template import loader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import PatientEntry, Patient
from .serializers import PatientSerializer, PatientEntrySerializer

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
        final_dict["patient_id"] = all_dict["patient_id"]
        return final_dict
    else:
        return all_dict


def get_all_active_patient_entries():
    patiententrys = (
        PatientEntry.objects.filter(completion_time__isnull=True)
        .select_related("patient_id")
        .all()
    )
    return sorted(patiententrys, key=lambda x: (x.urgency, x.decision_time))


def get_all_completed_patient_entries():
    return (
        PatientEntry.objects.filter(completion_time__isnull=False)
        .select_related("patient_id")
        .all()
        .order_by("-completion_time")[:10]
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
                {
                    "active": get_all_active_patient_entries(),
                    "completed": get_all_completed_patient_entries(),
                }
            ),
        },
    )


def save_model_changes(changes_dict):
    """
        The function takes in the request.POST object and saves changes in
        models. Returns boolean
    """
    try:
        patiententry = PatientEntry.objects.get(patient_id=changes_dict["patient_id"])
    except PatientEntry.DoesNotExist:
        return None
    patient = patiententry.patient_id
    patientserializer = PatientSerializer(patient, changes_dict, partial=True)
    patiententryserializer = PatientEntrySerializer(
        patiententry, changes_dict, partial=True
    )
    if patientserializer.is_valid():
        patientserializer.save()
    if patiententryserializer.is_valid():
        return patiententryserializer.save()
    else:
        return patiententry


def save_model(data):
    """
        Saves a models. Returns patient object or None.
    """
    patient = PatientSerializer(data=data)
    patiententry = PatientEntrySerializer(data=data)
    if patient.is_valid():
        patient.save()
        if patiententry.is_valid():
            return patiententry.save()
    else:
        return None
