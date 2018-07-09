from django.template import loader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from urllib.parse import parse_qs
import simplejson as json

from .models import PatientEntry, Patient

PATIENT_FIELDS = Patient.__dict__.keys()
PATIENTENTRY_FIELDS = PatientEntry.__dict__.keys()


def get_patient_dict(data):
    """
        Take in a rapidpro request body and return a dictionary
        with patient data.
    """
    data = parse_qs(data)[b'values'][0].decode('utf-8')
    patient_dict = {}
    try:
        obj = json.loads(data)
        for a_dict in obj:
            if a_dict['label'] in PATIENT_FIELDS:
                patient_dict[a_dict['label']] = a_dict['value']
        return patient_dict
    except json.JSONDecodeError:
        return patient_dict


def get_patiententry_dict(data):
    """
        Take in a rapidpro request body and return a dictionary
        with patiententry data.
    """
    data = parse_qs(data)[b'values'][0].decode('utf-8')
    patiententry_dict = {}
    try:
        obj = json.loads(data)
        for a_dict in obj:
            if a_dict['label'] in PATIENTENTRY_FIELDS:
                patiententry_dict[a_dict['label']] = a_dict['value']
        return patiententry_dict
    except json.JSONDecodeError:
        return patiententry_dict


def view_all_context():
    try:
        rows = []
        patiententrys = PatientEntry.objects.select_related("patient_id").all()
        for patiententry in patiententrys:
            rows.append(patiententry)
        return sorted(rows, key=lambda x: (x.urgency, x.decision_time))
    except PatientEntry.DoesNotExist:
        return False


def send_consumers_table():
    template = loader.get_template("cspatients/table.html")
    channel_layer = get_channel_layer()
    print(channel_layer)
    print(async_to_sync(channel_layer.group_send)(
        "view",
        {
            "type": "view.update",
            "content":
            template.render({
                "patiententrys": view_all_context()
            })
        }
    ))


def save_model_changes(data):
    """
        The function takes in the request.POST object and creates an all_values
        dictionary with all the intended Patient or PatientEntry changes.

        Returns the status code of the operation.
        200 if changes were made. 400 if the PatientEntry could not be found.

    """
    patient_dict = get_patient_dict(data)
    patiententry_dict = get_patiententry_dict(data)
    try:
        patiententry = PatientEntry.objects.get(
            patient_id=patiententry_dict['patient_id']
        )
        patient = Patient.objects.get(
            patient_id=patient_dict['patient_id']
        )
        for value in patient_dict:
            patient.__dict__[value] = patient_dict[value]
        for value in patiententry_dict:
            patiententry.__dict__[value] = patiententry_dict[value]
        return 200
    except PatientEntry.DoesNotExist:
        return 400
    except Patient.DoesNotExist:
        return 400
