import pytest
import responses

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from .consumers import ViewConsumer
from .models import Patient, PatientEntry
from .util import (
    get_all_active_patient_entries,
    get_all_completed_patient_entries,
    save_model,
    save_model_changes,
    get_rp_dict,
)


# View Tests

SAMPLE_RP_POST_DATA = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Doe", "input": "Jane Doe"},
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "gravpar": {"category": "All Responses", "value": "AAAA", "input": "AAAA"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
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
        "option": {"category": "Delivery", "value": "3", "input": "3"},
    }
}

SAMPLE_RP_UPDATE_COMPLETED_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "option": {"category": "Completed", "value": "4", "input": "4"},
    }
}


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
        self.patient_one_data = {"name": "Jane Doe", "patient_id": "XXXXX", "age": 20}

        self.patient_two_data = {
            "name": "Mary Mary",
            "patient_id": "YYYYY",
            "age": 23,
            "urgency": 1,
        }

        self.patient_three_data = {"name": "John", "patient_id": "111111", "age": 20}

    def test_context_when_no_patients(self):
        self.assertFalse(get_all_active_patient_entries())
        self.assertFalse(get_all_completed_patient_entries())

    def test_get_all_active_patient_entries(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        entry3, _ = save_model(self.patient_three_data)

        entry3.completion_time = timezone.now()
        entry3.save()

        patient_entries = get_all_active_patient_entries()

        # Check that it returns two objects
        self.assertEqual(len(patient_entries), 2)

        # Check that the results are sorted by the urgency
        self.assertEqual(patient_entries[0].patient.name, "Mary Mary")
        self.assertEqual(patient_entries[1].patient.name, "Jane Doe")

    def test_get_all_completed_patient_entries(self):
        entry1, _ = save_model(self.patient_one_data)
        entry2, _ = save_model(self.patient_two_data)
        save_model(self.patient_three_data)

        entry1.completion_time = timezone.now()
        entry1.save()

        entry2.completion_time = timezone.now()
        entry2.save()

        patient_entries = get_all_completed_patient_entries()

        # Check that it returns two objects
        self.assertEqual(len(patient_entries), 2)

        # Check that the results are sorted by the urgency
        self.assertEqual(patient_entries[0].patient.name, "Mary Mary")
        self.assertEqual(patient_entries[1].patient.name, "Jane Doe")


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
        self.patient_entry = PatientEntry.objects.create(
            patient=self.patient, gravpar="AAAA"
        )

    def test_saves_data_when_passed_good_dict(self):
        changes_dict = {"patient_id": "XXXXX", "name": "Jane Moe", "gravpar": "BBBB"}

        # Check returns PatientEntry
        result, errors = save_model_changes(changes_dict)
        self.assertTrue(isinstance(result, PatientEntry))
        self.assertEqual(errors, [])

        # Check that the name change has persisted.
        self.patient.refresh_from_db()
        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient.name, "Jane Moe")
        self.assertEqual(self.patient_entry.gravpar, "BBBB")

    def test_saves_data_multiple_entries(self):
        PatientEntry.objects.create(
            patient=self.patient, completion_time=timezone.now()
        )
        changes_dict = {"patient_id": "XXXXX", "name": "Jane Moe", "gravpar": "BBBB"}

        # Check returns PatientEntry
        result, errors = save_model_changes(changes_dict)
        self.assertTrue(isinstance(result, PatientEntry))
        self.assertEqual(errors, [])

        # Check that the name change has persisted.
        self.patient.refresh_from_db()
        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient.name, "Jane Moe")
        self.assertEqual(self.patient_entry.gravpar, "BBBB")

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


class NewPatientAPITestCase(AuthenticatedAPITestCase):
    def test_new_patient_entry_saves_minimum_data(self):
        response = self.normalclient.post(
            reverse("rp_newpatiententry"), SAMPLE_RP_POST_DATA, format="json"
        )
        # Assert a correct response of 201
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["errors"], "")

        # Check that the Patient, PatientEntry been correctly saved
        self.assertEqual(Patient.objects.get(patient_id="HLFSH").name, "Jane Doe")
        self.assertEqual(PatientEntry.objects.all().first().gravpar, "AAAA")

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

    def test_patient_exists_not_found(self):
        response = self.normalclient.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA_NON_EXISTING, format="json"
        )

        self.assertEqual(response.status_code, 404)

    def test_patient_exists_multiple_entries(self):
        PatientEntry.objects.create(
            patient=self.patient, completion_time=timezone.now()
        )
        response = self.normalclient.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA, format="json"
        )

        self.assertEqual(response.status_code, 200)

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

        self.assertIsNone(self.patient_entry.delivery_time)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_DELIVERY_DATA,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)

        # Test that the delivery time has been updated
        self.patient_entry.refresh_from_db()
        self.assertIsNotNone(self.patient_entry.delivery_time)

    def test_patient_who_exists_completed(self):

        self.assertIsNone(self.patient_entry.delivery_time)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_COMPLETED_DATA,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)

        # Test that the delivery time has been updated
        self.patient_entry.refresh_from_db()
        self.assertIsNotNone(self.patient_entry.completion_time)

    def test_delivery_of_patient_who_does_not_exist(self):

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            data=SAMPLE_RP_POST_DATA_NON_EXISTING,
            format="json",
        )
        # Test returns the right response code
        self.assertEqual(response.status_code, 404)

        # Test that the delivery time has not been updated
        self.assertIsNone(self.patient_entry.delivery_time)

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
