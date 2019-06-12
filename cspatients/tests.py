from os import environ

import pytest
import responses
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from mock import patch
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .consumers import ViewConsumer
from .models import Baby, Patient, PatientEntry, Profile
from .util import (
    get_all_active_patient_entries,
    get_rp_dict,
    save_model,
    save_model_changes,
)

# View Tests

SAMPLE_RP_POST_DATA = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Doe", "input": "Jane Doe"},
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "gravpar": {"category": "All Responses", "value": "AAAA", "input": "AAAA"},
        "decision_time": {
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
            "input": "2019-05-12 10:22+00:00",
        },
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_POST_NO_CONSENT_DATA = {
    "results": {
        "name": {
            "category": "All Responses",
            "value": "(No Consent)",
            "input": "(No Consent)",
        },
        "gravidity": {"category": "All Responses", "value": "1", "input": "1"},
        "parity": {"category": "All Responses", "value": "2", "input": "2"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
        "consent": {
            "name": "Consent",
            "category": "no_consent",
            "value": "2",
            "input": "2",
        },
    }
}

SAMPLE_RP_UPDATE_DATA = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Doe", "input": "Jane Doe"},
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "new_value": {
            "category": "All Responses",
            "value": "Nyasha",
            "input": "Nyasha",
        },
        "change_category": {"category": "name", "value": "1", "input": "1"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_POST_DATA_NON_EXISTING = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Moe", "input": "Jane Moe"},
        "patient_id": {"category": "All Responses", "value": "XXXXX", "input": "XXXXX"},
        "change_category": {"category": "name", "value": "A", "input": "A"},
        "new_value": {
            "category": "All Responses",
            "value": "Nyasha",
            "input": "Nyasha",
        },
    }
}

SAMPLE_RP_POST_INVALID_DATA = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Doe", "input": "Jane Moe"},
        "gravpar_invalid": {
            "category": "All Responses",
            "value": "abcdef",
            "input": "abcdef",
        },
    }
}

SAMPLE_RP_UPDATE_INVALID_DATA = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Doe", "input": "Jane Doe"},
        "new_value": {
            "category": "All Responses",
            "value": "Nyasha",
            "input": "Nyasha",
        },
        "change_category": {"category": "name", "value": "1", "input": "1"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_UPDATE_DELIVERY_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "foetus": {"name": "foetus", "category": "All Responses", "value": "2"},
        "baby_number": {
            "name": "baby_number",
            "category": "All Responses",
            "value": "1",
        },
        "delivery_time": {
            "name": "delivery_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "baby_weight_grams": {
            "name": "baby_weight_grams",
            "category": "All Responses",
            "value": "2400",
        },
        "nicu": {"name": "nicu", "category": "Yes", "value": "2"},
        "apgar_1": {"name": "apgar_1", "category": "All Responses", "value": "8"},
        "apgar_5": {"name": "apgar_5", "category": "All Responses", "value": "9"},
        "option": {"category": "Delivery", "value": "3", "input": "3"},
    }
}

SAMPLE_RP_UPDATE_DELIVERY_DATA_MINIMAL = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "foetus": {"name": "foetus", "category": "All Responses", "value": "2"},
        "baby_number": {
            "name": "baby_number",
            "category": "All Responses",
            "value": "1",
        },
        "delivery_time": {
            "name": "delivery_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "option": {"category": "Delivery", "value": "3", "input": "3"},
    }
}

SAMPLE_RP_UPDATE_COMPLETED_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "completion_time": {
            "name": "completion_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "option": {"category": "Completed", "value": "4", "input": "4"},
    }
}

SAMPLE_RP_CHECKLIST_DATA = {"contact": {"urn": "whatsapp:12065550109"}}
SAMPLE_RP_CHECKLIST_DATA_INACTIVE = {"contact": {"urn": "whatsapp:12065550108"}}


class FormTest(TestCase):
    """
        Tests for the form view.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="Itai")
        self.sufficient_data = {
            "patient_id": "XXXXX",
            "name": "Jane Doe",
            "age": 20,
            "clinician": "Dr. Joe",
            "urgency": 3,
        }
        self.insufficient_data = {"name": "Lisa Smith"}

    def test_get_method_when_not_logged_in(self):
        """
            Test GET method to the form view.
            Render template and return 200.
            If you not logged in then the form page must not be
            rendered.
        """
        response = self.client.get(reverse("cspatient_form"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login?next=/form")
        self.assertTemplateNotUsed(
            response=response, template_name="cspatients/form.html"
        )

    def test_get_method_when_logged_in(self):
        """
            Test the GET method when logged in. Must render the form template.
        """
        self.client.force_login(self.user)

        response = self.client.get(reverse("cspatient_form"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response, template_name="cspatients/form.html")

    def test_post_method_with_sufficient_data(self):
        """
            Test the POST method when posted the right information.
        """
        self.client.force_login(self.user)
        response = self.client.post(reverse("cspatient_form"), self.sufficient_data)

        # Check the status code response of the POST
        self.assertEqual(response.status_code, 201)
        jane = Patient.objects.get(patient_id="XXXXX")
        # Check the fields have been saved correctly
        self.assertEqual(jane.name, "Jane Doe")
        self.assertEqual(jane.patient_id, "XXXXX")
        self.assertEqual(jane.age, 20)
        # Check that it renders the form page again
        self.assertTemplateUsed(response=response, template_name="cspatients/form.html")

    def test_post_method_with_insufficient_data(self):
        """
            Test the POST method when given insufficient information
            to save.
        """
        self.client.force_login(self.user)
        response = self.client.post(reverse("cspatient_form"), self.insufficient_data)
        # Check the response code of the post
        self.assertEqual(response.status_code, 400)

        # Check that the template is rendered again
        self.assertTemplateUsed(response=response, template_name="cspatients/form.html")

        # Check that nothing was saved in the database.
        with self.assertRaises(Patient.DoesNotExist):
            Patient.objects.get(name="Lisa Smith")


class ViewTest(TestCase):
    """
        Test the view view method. Pun intended.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="Itai")

    def test_get_view(self):
        """
            1. Test that you only view the page when you are logged in.
        """
        response = self.client.get(reverse("cspatient_view"))
        self.assertTemplateNotUsed(
            response=response, template_name="cspatients/view.html"
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("cspatient_view"))
        self.assertTemplateUsed(response=response, template_name="cspatients/view.html")

    @patch("cspatients.util.get_all_active_patient_entries")
    def test_get_view_filter(self, mock_get_patients):
        """
            Test that request is using the filter
        """
        mock_get_patients.return_value = []

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("cspatient_view"), {"search": "1234", "status": "1"}
        )
        self.assertTemplateUsed(response=response, template_name="cspatients/view.html")

        mock_get_patients.assert_called_with("1234", "1")


class PatientViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="Itai")
        self.client.force_login(self.user)

    def test_view_non_existing_patient_returns_404(self):
        response = self.client.get(
            reverse("cspatient_patient", kwargs={"patient_id": "SHFLFLF"})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(
            response=response, template_name="cspatients/patient.html"
        )
        self.assertInHTML("Sorry. No such patient was found.", str(response.content))

    def test_view_one_existing_patiententry(self):
        jane = Patient.objects.create(name="Jane", patient_id="XXXXXX", age=10)

        PatientEntry.objects.create(
            patient=jane, urgency=2, decision_time=timezone.now()
        )

        response = self.client.get(
            reverse("cspatient_patient", kwargs={"patient_id": jane.patient_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response=response, template_name="cspatients/patient.html"
        )
        self.assertInHTML("Jane", str(response.content))

    def test_view_two_existing_same_patiententries(self):
        jane = Patient.objects.create(name="Jane", patient_id="XXXXXX", age=10)
        PatientEntry.objects.create(
            patient=jane,
            urgency=2,
            decision_time=timezone.now(),
            indication="First Operation",
        )
        PatientEntry.objects.create(
            patient=jane,
            urgency=3,
            decision_time=timezone.now(),
            indication="Second Operation",
        )
        response = self.client.get(
            reverse("cspatient_patient", kwargs={"patient_id": jane.patient_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("Second Operation", str(response.content))


# Util Tests


class ViewAllContextTest(TestCase):
    def setUp(self):
        self.patient_one_data = {
            "name": "Urgency COLD",
            "patient_id": "XXXXX",
            "age": 20,
        }

        self.patient_two_data = {
            "name": "Urgency Immediate",
            "patient_id": "YYYYY",
            "age": 23,
            "urgency": 1,
        }

        self.patient_three_data = {
            "name": "John Completed",
            "patient_id": "111111",
            "age": 20,
        }

        self.patient_four_data = {
            "name": "Urgency Immediate NEW",
            "patient_id": "22222222",
            "age": 23,
            "urgency": 1,
        }

        self.patient_five_data = {
            "name": "Completed OLD",
            "patient_id": "33333333",
            "age": 23,
            "urgency": 1,
        }

    def test_context_when_no_patients(self):
        self.assertFalse(get_all_active_patient_entries())

    @freeze_time("08:00")
    def test_get_all_active_patient_entries(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        entry3, _ = save_model(self.patient_three_data)
        entry4, _ = save_model(self.patient_four_data)
        entry5, _ = save_model(self.patient_five_data)

        entry3.completion_time = timezone.now()
        entry3.save()

        entry4.decision_time = timezone.now() + timezone.timedelta(hours=1)
        entry4.save()

        entry5.completion_time = timezone.now()
        entry5.decision_time = timezone.now() - timezone.timedelta(days=1)
        entry5.save()

        patient_entries = get_all_active_patient_entries()

        # Check that it returns 4 objects
        self.assertEqual(len(patient_entries), 4)

        # Check that the results are sorted by the urgency
        self.assertEqual(patient_entries[0].patient.name, "Urgency Immediate NEW")
        self.assertEqual(patient_entries[1].patient.name, "Urgency Immediate")
        self.assertEqual(patient_entries[2].patient.name, "Urgency COLD")
        self.assertEqual(patient_entries[3].patient.name, "John Completed")

    @freeze_time("04:30")
    def test_get_all_active_patient_entries_before_5_utc(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        entry3, _ = save_model(self.patient_three_data)
        entry4, _ = save_model(self.patient_four_data)
        entry5, _ = save_model(self.patient_five_data)

        entry3.completion_time = timezone.now()
        entry3.save()

        entry4.decision_time = timezone.now() + timezone.timedelta(hours=1)
        entry4.save()

        entry5.completion_time = timezone.now()
        entry5.decision_time = timezone.now() - timezone.timedelta(days=1)
        entry5.save()

        patient_entries = get_all_active_patient_entries()

        # Check that it returns 4 objects
        self.assertEqual(len(patient_entries), 5)

        # Check that the results are sorted by the urgency
        self.assertEqual(patient_entries[0].patient.name, "Urgency Immediate NEW")
        self.assertEqual(patient_entries[1].patient.name, "Urgency Immediate")
        self.assertEqual(patient_entries[2].patient.name, "Urgency COLD")
        self.assertEqual(patient_entries[3].patient.name, "Completed OLD")
        self.assertEqual(patient_entries[4].patient.name, "John Completed")

    def test_get_all_active_patient_entries_filter(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        save_model(self.patient_three_data)

        patient_entries = get_all_active_patient_entries("COLD", "4")

        self.assertEqual(len(patient_entries), 1)
        self.assertEqual(patient_entries[0].patient.name, "Urgency COLD")

    def test_get_all_active_patient_entries_filter_complete(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        entry3, _ = save_model(self.patient_three_data)

        entry3.completion_time = timezone.now()
        entry3.save()

        patient_entries = get_all_active_patient_entries(None, "complete")

        self.assertEqual(len(patient_entries), 1)
        self.assertEqual(patient_entries[0].patient.name, "John Completed")


class SaveModelTest(TestCase):
    def setUp(self):
        self.patient_one_data = {
            "name": "Jane Doe",
            "patient_id": "XXXXX",
            "age": 20,
            "urgency": 1,
        }

    def test_saves_when_given_sufficient_data(self):
        patiententry, errors = save_model(self.patient_one_data)

        # Must return the saved patient entry
        self.assertIsNotNone(patiententry)
        self.assertEqual(errors, [])

        # Check that the save persisted in the database
        self.assertEqual(len(PatientEntry.objects.all()), 1)

    def test_saves_when_given_junk_data(self):
        patiententry, errors = save_model(
            {
                "patient_id": "XXXXX",
                "name": "Mary Mary",
                "age": 23,
                "urgency": 1,
                "response_19": "test",
            }
        )

        # Must return the saved patient entry
        self.assertIsNotNone(patiententry)
        self.assertEqual(errors, [])

        # Check that the save persisted in the database
        self.assertEqual(len(PatientEntry.objects.all()), 1)

    def test_saves_duplicate(self):
        save_model(self.patient_one_data)
        patiententry, errors = save_model(self.patient_one_data)

        # Must not save the second one
        self.assertIsNone(patiententry)
        self.assertEqual(errors, ["Active entry already exists for this patient"])
        # Check that the first save persisted in the database
        self.assertEqual(len(PatientEntry.objects.all()), 1)

    def test_saves_duplicate_completed(self):
        patiententry, errors = save_model(self.patient_one_data)
        patiententry.completion_time = timezone.now()
        patiententry.save()

        patiententry, errors = save_model(self.patient_one_data)

        # Must not save the second one
        self.assertIsNotNone(patiententry)
        self.assertEqual(errors, [])
        # Check that the first save persisted in the database
        self.assertEqual(len(PatientEntry.objects.all()), 2)

    def test_nothing_saved_with_insufficient_data(self):
        patientryentry, errors = save_model(
            {"name": "Mary Mary", "age": 23, "urgency": 1}
        )

        # Must return None
        self.assertIsNone(patientryentry)
        self.assertEqual(errors, ["Patient ID is required"])

        # Check that none of the information is in the database
        with self.assertRaises(Patient.DoesNotExist):
            Patient.objects.get(name="Mary Mary")


class SaveModelChangesTest(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            name="Jane Doe", patient_id="XXXXX", age=20
        )
        self.patient_entry = PatientEntry.objects.create(patient=self.patient)

    def test_saves_data_when_passed_good_dict(self):
        changes_dict = {
            "patient_id": "XXXXX",
            "name": "Jane Moe",
            "gravidity": "1",
            "parity": "1",
        }

        # Check returns PatientEntry
        result, errors = save_model_changes(changes_dict)
        self.assertTrue(isinstance(result, PatientEntry))
        self.assertEqual(errors, [])

        # Check that the name change has persisted.
        self.patient.refresh_from_db()
        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient.name, "Jane Moe")
        self.assertEqual(self.patient_entry.gravpar, "G1P1")
        self.assertEqual(str(self.patient), "XXXXX - Jane Moe")
        self.assertEqual(str(self.patient_entry), "XXXXX - Jane Moe having CS")

    def test_saves_data_multiple_entries(self):
        PatientEntry.objects.create(
            patient=self.patient, completion_time=timezone.now()
        )
        changes_dict = {
            "patient_id": "XXXXX",
            "name": "Jane Moe",
            "gravidity": "2",
            "parity": "2",
        }

        # Check returns PatientEntry
        result, errors = save_model_changes(changes_dict)
        self.assertTrue(isinstance(result, PatientEntry))
        self.assertEqual(errors, [])

        # Check that the name change has persisted.
        self.patient.refresh_from_db()
        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient.name, "Jane Moe")
        self.assertEqual(self.patient_entry.gravpar, "G2P2")

    def test_returns_none_for_patient_dict_with_wrong_patient_id(self):
        changes_dict = {"patient_id": "YXXXX", "name": "Jane Moe"}

        result, errors = save_model_changes(changes_dict)

        # Returns none on bad incorrect patient_id
        self.assertIsNone(result)
        self.assertEqual(errors, ["Patient entry does not exist"])

    def test_does_not_make_changes_when_dict_has_wrong_fields(self):
        changes_dict = {"patient_id": "XXXXX", "names": "Janet Moe", "urgent": "DSHLSD"}

        result, errors = save_model_changes(changes_dict)

        self.assertEqual(errors, [])

        self.patient.refresh_from_db()
        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient_entry, result)


class GetRPDictTest(TestCase):

    """
        Test the get_rp_dict method
        Takes in request.POST method
    """

    def test_get_rp_event_dict(self):
        """
            The Method should be able to extract the name, and patient ID,
            from the Query dict into a dictionary with just name and
            patient_id
        """

        # Extract the dictionary using the get_rp_dict method
        event_dict = get_rp_dict(SAMPLE_RP_POST_DATA)

        # Test that it gets the appropriate keys and values

        self.assertTrue("name" in event_dict)
        self.assertTrue("patient_id" in event_dict)

        # Test that it saves the right methods

        self.assertTrue(event_dict["name"] == "Jane Doe")
        self.assertTrue(event_dict["patient_id"] == "HLFSH")

    def test_get_entrychanges_dict(self):
        """
            The Method when passed a context of entrychanges, must be able
            to pick up the change category and the new value
        """
        # Extract the dictionary using the get_rp_dict method and
        # entrychanges context
        changes_dict = get_rp_dict(SAMPLE_RP_UPDATE_DATA, context="entrychanges")

        # Test that the change category and values are stored well
        self.assertTrue(changes_dict.__contains__("name"))
        self.assertTrue(changes_dict["name"] == "Nyasha")

        # Test that the patient ID is kept well
        self.assertTrue(changes_dict.__contains__("patient_id"))
        self.assertTrue(changes_dict["patient_id"] == "HLFSH")


# API Tests
class AuthenticatedAPITestCase(TestCase):
    def setUp(self):
        super(AuthenticatedAPITestCase, self).setUp()

        self.client = Client()

        # Normal User setup
        self.normalclient = APIClient()
        self.normalusername = "testnormaluser"
        self.normalpassword = "testnormalpass"
        self.normaluser = User.objects.create_user(
            self.normalusername, "testnormaluser@example.com", self.normalpassword
        )
        normaltoken = Token.objects.create(user=self.normaluser)
        self.normaltoken = normaltoken
        self.normalclient.credentials(HTTP_AUTHORIZATION="Token %s" % self.normaltoken)

        Profile.objects.create(**{"user": self.normaluser, "msisdn": "+12065550109"})


class NewPatientAPITestCase(AuthenticatedAPITestCase):
    def test_new_patient_entry_saves_minimum_data(self):
        response = self.normalclient.post(
            reverse("rp_newpatiententry"), SAMPLE_RP_POST_DATA, format="json"
        )
        # Assert a correct response of 201
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["errors"], "")
        self.assertEqual(response.json()["patient_id"], "HLFSH")

        # Check that the Patient, PatientEntry been correctly saved
        self.assertEqual(Patient.objects.get(patient_id="HLFSH").name, "Jane Doe")
        entry = PatientEntry.objects.all().first()
        self.assertEqual(entry.gravpar, "G-P-")
        self.assertEqual(
            entry.decision_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )

    @patch("cspatients.util.get_random_string")
    def test_new_patient_entry_no_consent(self, mock_random):
        mock_random.return_value = "1234567890"

        response = self.normalclient.post(
            reverse("rp_newpatiententry"), SAMPLE_RP_POST_NO_CONSENT_DATA, format="json"
        )

        # Assert a correct response of 201
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["errors"], "")
        patient = Patient.objects.last()
        self.assertEqual(response.json()["patient_id"], f"9{patient.id:07}")

        # Check that the Patient, PatientEntry been correctly saved
        self.assertEqual(patient.name, "(No Consent)")
        self.assertEqual(PatientEntry.objects.all().first().gravpar, "G1P2")

    def test_new_patient_entry_without_auth(self):
        response = self.client.post(
            reverse("rp_newpatiententry"), SAMPLE_RP_POST_DATA, format="json"
        )
        # Assert a correct response of 201
        self.assertEqual(response.status_code, 401)

    def test_new_patient_entry_invalid_data(self):
        response = self.normalclient.post(
            reverse("rp_newpatiententry"), SAMPLE_RP_POST_INVALID_DATA, format="json"
        )
        # Assert a correct response of 400
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"], "Patient ID is required")


class CheckPatientExistsAPITestCase(AuthenticatedAPITestCase):
    @freeze_time("2019-01-01")
    def setUp(self):
        super(CheckPatientExistsAPITestCase, self).setUp()
        self.patient = Patient.objects.create(
            name="Jane Doe", patient_id="HLFSH", age=20
        )
        PatientEntry.objects.create(patient=self.patient)

    def test_patient_exists_found(self):
        response = self.normalclient.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA, format="json"
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "operation": "CS",
                "gravpar": "G-P-",
                "comorbid": None,
                "indication": None,
                "decision_time": "2019-01-01T02:00:00+02:00",
                "gravidity": None,
                "completion_time": None,
                "urgency": 4,
                "location": None,
                "outstanding_data": None,
                "clinician": None,
                "name": "Jane Doe",
                "parity": None,
                "age": 20,
                "foetus": None,
                "patient_id": "HLFSH",
            },
        )

    def test_patient_exists_not_found(self):
        response = self.normalclient.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA_NON_EXISTING, format="json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {})

    def test_patient_exists_multiple_entries(self):
        PatientEntry.objects.create(
            patient=self.patient, completion_time=timezone.now()
        )
        response = self.normalclient.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "operation": "CS",
                "gravpar": "G-P-",
                "comorbid": None,
                "indication": None,
                "decision_time": "2019-01-01T02:00:00+02:00",
                "gravidity": None,
                "completion_time": None,
                "urgency": 4,
                "location": None,
                "outstanding_data": None,
                "clinician": None,
                "name": "Jane Doe",
                "parity": None,
                "age": 20,
                "foetus": None,
                "patient_id": "HLFSH",
            },
        )

    def test_patient_exists_no_auth(self):
        response = self.client.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA, format="json"
        )

        self.assertEqual(response.status_code, 401)


class UpdatePatientEntryAPITestCase(AuthenticatedAPITestCase):
    def setUp(self):
        super(UpdatePatientEntryAPITestCase, self).setUp()
        patient = Patient.objects.create(name="Jane Doe", patient_id="HLFSH", age=20)
        PatientEntry.objects.create(patient=patient)

    def test_update_patient_success(self):
        response = self.normalclient.post(
            reverse("rp_entrychanges"), SAMPLE_RP_UPDATE_DATA, format="json"
        )
        # Test the right response code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["errors"], "")
        self.assertEqual(response.json()["name"], "Nyasha")

        # Test that that the change has been made
        patient = Patient.objects.get(patient_id="HLFSH")
        self.assertTrue(patient.name == "Nyasha")

    def test_update_patient_invalid_data(self):
        response = self.normalclient.post(
            reverse("rp_entrychanges"), SAMPLE_RP_UPDATE_INVALID_DATA, format="json"
        )
        # Test the right response code 400
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"], "Patient ID is required")

    def test_update_patient_not_found(self):
        response = self.normalclient.post(
            reverse("rp_entrychanges"), SAMPLE_RP_POST_DATA_NON_EXISTING, format="json"
        )
        # Test the right response code 400
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"], "Patient entry does not exist")

    def test_patient_exists_no_auth(self):
        response = self.client.post(
            reverse("rp_entrychanges"), SAMPLE_RP_POST_DATA, format="json"
        )

        self.assertEqual(response.status_code, 401)


class EntryStatusUpdateTestCase(AuthenticatedAPITestCase):
    def setUp(self):
        super(EntryStatusUpdateTestCase, self).setUp()
        self.patient = Patient.objects.create(
            name="Jane Doe", patient_id="HLFSH", age=20
        )
        self.patient_entry = PatientEntry.objects.create(patient=self.patient)

    def test_patient_who_exists_delivered(self):

        self.assertEqual(self.patient_entry.entry_babies.count(), 0)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_DELIVERY_DATA,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)

        # Test that the baby records have been created correctly
        self.assertEqual(Baby.objects.count(), 1)

        baby_1 = Baby.objects.get(patiententry=self.patient_entry, baby_number=1)
        self.assertEqual(
            baby_1.delivery_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )
        self.assertEqual(baby_1.apgar_1, 8)
        self.assertEqual(baby_1.apgar_5, 9)
        self.assertEqual(baby_1.baby_weight_grams, 2400)
        self.assertTrue(baby_1.nicu)

    def test_patient_who_exists_delivered_minimal(self):

        self.assertEqual(self.patient_entry.entry_babies.count(), 0)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_DELIVERY_DATA_MINIMAL,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)

        # Test that the baby records have been created correctly
        self.assertEqual(Baby.objects.count(), 1)

        baby_1 = Baby.objects.get(patiententry=self.patient_entry, baby_number=1)
        self.assertEqual(
            baby_1.delivery_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )
        self.assertEqual(baby_1.apgar_1, None)
        self.assertEqual(baby_1.apgar_5, None)
        self.assertEqual(baby_1.baby_weight_grams, None)
        self.assertFalse(baby_1.nicu)

    def test_patient_who_exists_delivered_update(self):
        Baby.objects.create(
            **{
                "patiententry": self.patient_entry,
                "baby_number": 1,
                "apgar_1": 1,
                "apgar_5": 2,
                "baby_weight_grams": 0,
                "delivery_time": timezone.now(),
                "nicu": False,
            }
        )

        self.assertEqual(self.patient_entry.entry_babies.count(), 1)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_DELIVERY_DATA,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)

        # Test that the baby records have been updated correctly
        self.assertEqual(Baby.objects.count(), 1)

        baby_1 = Baby.objects.get(patiententry=self.patient_entry, baby_number=1)
        self.assertEqual(
            baby_1.delivery_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )
        self.assertEqual(baby_1.apgar_1, 8)
        self.assertEqual(baby_1.apgar_5, 9)
        self.assertEqual(baby_1.baby_weight_grams, 2400)
        self.assertTrue(baby_1.nicu)

    def test_patient_who_exists_completed(self):

        self.assertIsNone(self.patient_entry.completion_time)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_COMPLETED_DATA,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)

        # Test that the delivery time has been updated
        self.patient_entry.refresh_from_db()

        self.assertEqual(
            self.patient_entry.completion_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )

    def test_delivery_of_patient_who_does_not_exist(self):

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            data=SAMPLE_RP_POST_DATA_NON_EXISTING,
            format="json",
        )
        # Test returns the right response code
        self.assertEqual(response.status_code, 404)

        # Test that no baby records were created
        self.assertEqual(self.patient_entry.entry_babies.count(), 0)

    def test_delivery_of_patient_multiple_entries(self):
        PatientEntry.objects.create(
            patient=self.patient, completion_time=timezone.now()
        )
        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_DELIVERY_DATA,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_patient_exists_no_auth(self):
        response = self.client.post(
            reverse("rp_entrystatus_update"), SAMPLE_RP_UPDATE_DELIVERY_DATA
        )

        self.assertEqual(response.status_code, 401)


class WhitelistCheckTestCase(AuthenticatedAPITestCase):
    @patch("cspatients.util.force_bytes")
    @patch("cspatients.util.default_token_generator.make_token")
    def test_whitelist_check_exists(self, mock_make_token, mock_bytes):
        mock_make_token.return_value = "fancy-token"
        mock_bytes.return_value = b"1"

        response = self.normalclient.post(
            reverse("rp_whitelist_check"), SAMPLE_RP_CHECKLIST_DATA, format="json"
        )
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(
            result["group_invite_link"], "http://fakewhatsapp/the-group-id"
        )
        self.assertEqual(
            result["reset_password_link"],
            "http://testserver/accounts/reset/MQ/fancy-token/",
        )

        mock_make_token.assert_called_with(self.normaluser)
        mock_bytes.assert_called_with(self.normaluser.pk)

    def test_whitelist_check_not_exists(self):
        response = self.normalclient.post(
            reverse("rp_whitelist_check"),
            SAMPLE_RP_CHECKLIST_DATA_INACTIVE,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        self.assertEqual(response.json(), {})

    def test_whitelist_check_exists_inactive(self):
        new_user = User.objects.create_user(
            "test_user", "testuser@example.com", "1234", is_active=False
        )
        Profile.objects.create(**{"user": new_user, "msisdn": "+12065550108"})

        response = self.normalclient.post(
            reverse("rp_whitelist_check"),
            SAMPLE_RP_CHECKLIST_DATA_INACTIVE,
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {})


class MultiSelectTestCase(AuthenticatedAPITestCase):
    def test_multi_select_valid(self):
        response = self.normalclient.get(
            reverse("rp_multiselect"),
            {"selections": "1, 3,3, ", "options": "test 1|test 2 | test 3"},
        )
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result["valid"], True)
        self.assertEqual(result["value"], "test 1, test 3")

    def test_multi_select_invalid_selection(self):
        response = self.normalclient.get(
            reverse("rp_multiselect"),
            {"selections": "1,5", "options": "test 1|test 2|test 3"},
        )
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result["valid"], False)
        self.assertEqual(result["value"], "")

    def test_multi_select_invalid_character(self):
        response = self.normalclient.get(
            reverse("rp_multiselect"),
            {"selections": "1,a", "options": "test 1|test 2|test 3"},
        )
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result["valid"], False)
        self.assertEqual(result["value"], "")


class PatientListTestCase(AuthenticatedAPITestCase):
    def create_patient_entry(self, patient_id, name, complete=None):
        patient = Patient.objects.create(name=name, patient_id=patient_id, age=20)
        PatientEntry.objects.create(
            patient=patient, completion_time=complete, indication="indic1"
        )

    def test_patient_list_view(self):
        self.create_patient_entry("00000001", "John Doe")
        self.create_patient_entry("00000002", "Mary", timezone.now())
        self.create_patient_entry("00000003", "Test")

        response = self.normalclient.get(reverse("rp_patient_list"))

        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(
            result["patient_list"], "1) John Doe CS indic1 Cold\n2) Test CS indic1 Cold"
        )
        self.assertEqual(result["patient_ids"], "1=00000001|2=00000003")


class PatientSelectTestCase(AuthenticatedAPITestCase):
    def test_patient_select_view(self):

        response = self.normalclient.get(
            reverse("rp_patient_select"),
            {"patient_ids": "1=00000001|2=00000003|3=00000004", "option": "2"},
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(result["patient_id"], "00000003")


class HealthViewTest(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

    def test_health_endpoint(self):
        response = self.api_client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], None)

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], None)

    def test_health_endpoint_with_vars(self):
        environ["MARATHON_APP_ID"] = "marathon-app-id"
        environ["MARATHON_APP_VERSION"] = "marathon-app-version"

        response = self.api_client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], environ["MARATHON_APP_ID"])

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], environ["MARATHON_APP_VERSION"])


class DetailedHealthViewTest(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

    def mock_queue_lookup(self, name="momkhulu", messages=1256, rate=1.25):
        responses.add(
            responses.GET,
            "{}{}".format(settings.RABBITMQ_MANAGEMENT_INTERFACE, name),
            json={
                "messages": messages,
                "messages_details": {"rate": rate},
                "name": name,
            },
            status=200,
            match_querystring=True,
        )

    @responses.activate
    def test_detailed_health_endpoint_not_stuck(self):
        self.mock_queue_lookup()

        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["queues"][0]["stuck"])

    @responses.activate
    def test_detailed_health_endpoint_stuck(self):
        self.mock_queue_lookup(rate=0.0)

        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.json()["queues"][0]["stuck"])

    @override_settings(RABBITMQ_MANAGEMENT_INTERFACE=False)
    def test_detailed_health_endpoint_deactivated(self):
        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["update"], "queues not checked")
        self.assertEqual(response.json()["queues"], [])


class TestModels(TestCase):
    def test_profile(self):
        new_user = User.objects.create_user(
            "test_user", "testuser@example.com", "1234", is_active=False
        )
        profile = Profile.objects.create(**{"user": new_user, "msisdn": "+12065550109"})

        self.assertEqual(str(profile), "test_user: +12065550109")


@pytest.mark.asyncio
async def test_view_consumer():
    communicator = WebsocketCommunicator(ViewConsumer, "/ws/cspatients/viewsocket/")

    connected, subprotocol = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "view", {"type": "view.update", "content": "Testing"}
    )

    response = await communicator.receive_from()
    assert response == "Testing"

    await communicator.disconnect()
