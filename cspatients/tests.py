import unittest

from django.test import TestCase, Client
from django.test.testcases import SimpleTestCase

from .models import Patient

# Model Tests
"""
Do not test Django functionality. Assume she does it perfectly
Assert template used
Find a key phrase expected to be in the template
Assert contains
Hypothesis

"""


# View Tests


class RPEventTest(SimpleTestCase):

    def setUp(self):
        self.client = Client()

    def test_request_methods(self):
        get_response = self.client.get('/rpevent')
        # POST with minimal vital information
        post_response = self.client.post('/rpevent', {
            "patient_id": "XXXXX",
            "name": "Jane Doe",
            "age": 20
        })

        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(post_response.status_code, 201)

    def test_serializing(self):
        """
            Test the serialization into database
        """
        post_response1 = self.client.post('/rpevent', {
            "patient_id": "XXXXX",
            "name": "Jane Doe",
            "age": 20,
        })
        # POST with incompelete vital information
        post_response2 = self.client.post('/rpevent', {
            "name": "Lisa Smith",
        })

        self.assertEqual(post_response1.status_code, 201)
        self.assertEqual(post_response2.status_code, 400)
        try:
            Patient.objects.get(patient_id="XXXXX")


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
        self.assertEqual(response.status_code, 201)
        jane = Patient.objects.get(patient_id="XXXXXX")
        # Check the fields have been saved correctly
        self.assertEqual(jane.name, "Jane Doe")
        self.assertEqual(jane.patient_id, "XXXXXX")
        self.assertEqual(jane.age, 20)
        self.assertEqual(jane.location, "Ward 56")
        self.assertEqual(jane.urgency, 2)
        self.assertEqual(jane.parity, 1)
        self.assertEqual(jane.clinician, "Dr Peter Drew")
