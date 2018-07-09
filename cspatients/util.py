from django.template import loader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from urllib.parse import parse_qs
import simplejson as json

from .models import PatientEntry


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
            if a_dict['label'] in ("patient_id", "name", "age"):
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
    fields = (
            "patient_id", "operation", "gravpar", "comorbid", "indication",
            "discharge_time", "decision_time", "location", "outstanding_data",
            "delivery_time", "clinician", "urgency", "apgar_1",
            "apgar_5"
        )
    try:
        obj = json.loads(data)
        for a_dict in obj:
            if a_dict['label'] in fields:
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
