import unittest

from django.test import TestCase
from django.test import Client

from .models import Patient

# Model Tests


class PatientTestCase(TestCase):
    def setUp(self):
        Patient.objects.create(patient_id="XKT6484", name="Jane Doe",
                               age=33, gravidity=1, parity=0,
                               comorbidity="Pneumonia Diabeties",
                               indication="Extreme pain", urgency=1,
                               location="Ward 56", clinician="Dr Peter Drew")

    def test_Patient_str(self):
        jane = Patient.objects.get(patient_id="XKT6484")
        self.AssertEqual(jane.__str__(), "Jane Doe")


# View Tests


class EventTest(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def test_request_methods(self):
        get_response = self.client.get('/event')
        # POST with minimal vital information
        post_response = self.client.post('/event', {
            "patient_id": "XXXXX",
            "name": "Jane Doe",
            "age": 20
        })
        # POST with incompelete vital information 
        post_response2 = self.client.post('/event', {
            "name": "Lisa Smith",
        })
        self.assertEquals(get_response.status_code, 405)
        self.assertEquals(post_response.status_code, 201)
        self.assertEquals(post_response2.status_code, 400)


class FormTest(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_method(self):
        response = self.client.get('/form')
        self.assertEqual(response.status_code, 200)

    def post_get_method(self):
        response = self.client.post("/form", {
            "name": "Jane Doe",
            "patient_id": "XXXXXX",
            "age": 20,
            "location": "Ward 56",
            "urgency": 2,
            "parity": 1,
            "indication": " Severe Pain",
            "clinician": "Dr Peter Drew",
        })

        # Check the status code response of the POST
        self.assertEquals(response.status_code, 201)
        jane = Patient.objects.get(patient_id="XXXXXX")
        # Check the fields have been saved correctly
        self.assertEquals(jane.name, "Jane Doe")
        self.assertEquals(jane.patient_id, "XXXXXX")
        self.assertEquals(jane.age, 20)
        self.assertEquals(jane.location, "Ward 56")
        self.assertEquals(jane.urgency, 2)
        self.assertEquals(jane.parity, 1)
        self.assertEquals(jane.clinician, "Dr Peter Drew")
