from django.template import loader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import simplejson as json
from datetime import datetime

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
    except json.JSONDecodeError:
        return {}
    final_dict = all_dict
    if context == "entrychanges":
        final_dict[all_dict["change_category"]] = all_dict["new_value"]
        final_dict["patient_id"] = all_dict["patient_id"]
    return final_dict


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


def save_model_changes(post_data):
    """
        The function takes in the request.POST object and saves changes in
        models. Returns boolean
    """

    changes_dict = get_rp_dict(post_data)
    try:
        patiententry = PatientEntry.objects.get(
            patient_id=changes_dict['patient_id']
            )
    except PatientEntry.DoesNotExist:
        return False
    patient = patiententry.patient_id
    patientserializer = PatientSerializer(patient, changes_dict, partial=True)
    patiententryserializer = PatientEntrySerializer(
        patiententry, changes_dict, partial=True
    )
    if patientserializer.is_valid():
        patient.save()
    if patiententryserializer.is_valid():
        patiententry.save()
    return True


def save_model(post_data):
    patient = PatientSerializer(
        data=get_rp_dict(post_data, context="patient")
        )
    patiententry = PatientEntrySerializer(
        data=get_rp_dict(post_data, context="patiententry")
    )
    if patient.is_valid():
        patient.save()
        if patiententry.is_valid():
            patiententry.save()
        return 201
    else:
        return 400


def patient_has_delivered(post_data):

    try:
        patiententry = PatientEntry.objects.get(
            patient_id=get_rp_dict(post_data)['patient_id']
        )
        patiententry.delivery_time = datetime.now()
        send_consumers_table()
        return 200
    except PatientEntry.DoesNotExist:
        return 400
