from django.template import loader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import simplejson as json

from .models import PatientEntry, Patient

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
            if a_dict['category']['base'] == "All Responses":
                all_dict[a_dict['label']] = a_dict['value']
            else:
                all_dict[a_dict['label']] = a_dict['category']['base']
    except json.JSONDecodeError:
        return {}
    final_dict = {}
    if context == "entrychanges":
        final_dict[all_dict["change_category"]] = all_dict["new_value"]
        final_dict["patient_id"] = all_dict["patient_id"]

    elif context == "patient" or context == "patiententry":
        field = PATIENT_FIELDS if context == "patient" else PATIENTENTRY_FIELDS
        for label in all_dict:
            if label in field:
                final_dict[label] = all_dict[label]
    else:
        final_dict = all_dict
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


def save_model_changes(data):
    """
        The function takes in the request.POST object and creates an all_values
        dictionary with all the intended Patient or PatientEntry changes.

        Returns the status code of the operation.
        200 if changes were made. 400 if the PatientEntry could not be found.

    """

    changes_dict = get_rp_dict(data, "entrychanges")
    try:
        patiententry = PatientEntry.objects.get(
            patient_id=changes_dict['patient_id']
            )
        del changes_dict['patient_id']
        for label in changes_dict:
            if label in PATIENTENTRY_FIELDS:
                patiententry.__dict__[label] = changes_dict[label]
            if label in PATIENT_FIELDS:
                patiententry.__dict__[label] = changes_dict[label]
        return 200
    except PatientEntry.DoesNotExist:
        return 400
    except Patient.DoesNotExist:
        return 400
