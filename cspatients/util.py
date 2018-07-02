from urllib.parse import parse_qs
import simplejson as json


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
            patient_dict[a_dict['label']] = a_dict['value']
        return patient_dict
    except json.JSONDecodeError:
        return patient_dict
