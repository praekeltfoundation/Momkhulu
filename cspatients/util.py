from django.template import loader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from urllib.parse import parse_qs
import simplejson as json

from .models import PatientEntry

PATIENT_FIELDS = ("patient_id", "name", "age")
PATIENTENTRY_FIELDS = (
    "patient_id", "operation", "gravpar", "comorbid", "indication",
    "discharge_time", "decision_time", "location", "outstanding_data",
    "delivery_time", "clinician", "urgency", "apgar_1",
    "apgar_5"
)


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
    all_values = get_patient_dict(data).update(get_patiententry_dict(data))
    try:
        current_patiententry = PatientEntry.objects.get(
            patient_id=all_values['patient_id']
        )
        if all_values.contains("name"):
            current_patiententry.patient_id.name = all_values["name"]
        if all_values.contains("age"):
            current_patiententry.patient_id.age = all_values["age"]
        if all_values.contains("operation"):
            current_patiententry.operation = all_values["operation"]
        if all_values.contains("gravpar"):
            current_patiententry.gravpar = all_values["gravpar"]
        if all_values.contains("comorbid"):
            current_patiententry.comorbid = all_values["comorbid"]
        if all_values.contains("indication"):
            current_patiententry.indication = all_values["indication"]
        if all_values.contains("decision_time"):
            current_patiententry.decision_time = all_values["decision_time"]
        if all_values.contains("discharge_time"):
            current_patiententry.discharge_time = all_values["discharge_time"]
        if all_values.contains("delivery_time"):
            current_patiententry.delivery_time = all_values["delivery_time"]
        if all_values.contains("urgency"):
            current_patiententry.urgency = all_values["urgency"]
        if all_values.contains("location"):
            current_patiententry.location = all_values["location"]
        if all_values.contains("outstanding_data"):
            current_patiententry.outstanding_data = all_values["outstanding_data"]
        if all_values.contains("clinician"):
            current_patiententry.clinician = all_values["clinician"]
        if all_values.contains("apgar_1"):
            current_patiententry.apgar_1 = all_values["apgar_1"]
        if all_values.contains("apgar_5"):
            current_patiententry.apgar_5 = all_values["apgar_5"]

        return 200
    except PatientEntry.DoesNotExist:
        return 400
