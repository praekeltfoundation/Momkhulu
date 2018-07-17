from django.template import loader
from django.db.models.query import EmptyQuerySet

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import simplejson as json

from .models import PatientEntry, Patient
from .serializers import PatientSerializer, PatientEntrySerializer

PATIENT_FIELDS = Patient.__dict__.keys()
PATIENTENTRY_FIELDS = PatientEntry.__dict__.keys()


def get_rp_dict(data, context=None):
    """
        Get a label and value dictionary from the request POST
    """
    data = data['values']
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return {}
    all_dict = {}
    for a_dict in obj:
        """
        All Responses is a category base for responses that are free text
        and not options. If not all All Responses, the label must take
        the value of the chosen category base.
        """
        if a_dict['category']['base'] == "All Responses":
            all_dict[a_dict['label']] = a_dict['value']
        else:
            all_dict[a_dict['label']] = a_dict['category']['base']

    if context == "entrychanges":
        final_dict = {}
        final_dict[all_dict["change_category"]] = all_dict["new_value"]
        final_dict["patient_id"] = all_dict["patient_id"]
        return final_dict
    else:
        return all_dict


def view_all_context():
    rows = []
    patiententrys = PatientEntry.objects.select_related("patient_id").all()
    if isinstance(patiententrys, EmptyQuerySet):
        return False
    for patiententry in patiententrys:
        rows.append(patiententry)
    return sorted(rows, key=lambda x: (x.urgency, x.decision_time))


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
            "content":
            template.render({
                "patiententrys": view_all_context()
            })
        }
    )


def save_model_changes(changes_dict):
    """
        The function takes in the request.POST object and saves changes in
        models. Returns boolean
    """
    try:
        patiententry = PatientEntry.objects.get(
            patient_id=changes_dict['patient_id']
            )
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
    patient = PatientSerializer(
        data=data
        )
    patiententry = PatientEntrySerializer(
        data=data
    )
    if patient.is_valid():
        patient.save()
        if patiententry.is_valid():
            return patiententry.save()
    else:
        return None
