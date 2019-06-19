from os import environ

import responses
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

from cspatients.models import Baby, PatientEntry, Profile

from .constants import (
    SAMPLE_RP_CHECKLIST_DATA,
    SAMPLE_RP_CHECKLIST_DATA_INACTIVE,
    SAMPLE_RP_POST_DATA,
    SAMPLE_RP_POST_DATA_NON_EXISTING,
    SAMPLE_RP_POST_INVALID_DATA,
    SAMPLE_RP_POST_NO_CONSENT_DATA,
    SAMPLE_RP_UPDATE_BAD_OPTION_DATA,
    SAMPLE_RP_UPDATE_CANCELLED_DATA,
    SAMPLE_RP_UPDATE_COMPLETED_DATA,
    SAMPLE_RP_UPDATE_DATA,
    SAMPLE_RP_UPDATE_DELIVERY_DATA,
    SAMPLE_RP_UPDATE_DELIVERY_DATA_MINIMAL,
    SAMPLE_RP_UPDATE_INVALID_DATA,
)


class FormTest(TestCase):
    """
        Tests for the form view.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="Itai")
        self.sufficient_data = {
            "surname": "Jane Doe",
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
        jane = PatientEntry.objects.first()
        # Check the fields have been saved correctly
        self.assertEqual(jane.surname, "Jane Doe")
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
        self.assertEqual(PatientEntry.objects.count(), 0)


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
            reverse("cspatient_patient", kwargs={"patient_id": "123"})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(
            response=response, template_name="cspatients/patient.html"
        )
        self.assertInHTML("Sorry. No such patient was found.", str(response.content))

    def test_view_one_existing_patiententry(self):
        jane = PatientEntry.objects.create(
            surname="Jane", age=10, urgency=2, decision_time=timezone.now()
        )

        response = self.client.get(
            reverse("cspatient_patient", kwargs={"patient_id": jane.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response=response, template_name="cspatients/patient.html"
        )
        self.assertInHTML("Jane", str(response.content))


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

        # Check that the PatientEntry been correctly saved

        entry = PatientEntry.objects.all().first()
        self.assertEqual(entry.surname, "Doe")
        self.assertEqual(entry.gravpar, "G-P-")
        self.assertEqual(
            entry.decision_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )

    def test_new_patient_entry_no_consent(self):
        response = self.normalclient.post(
            reverse("rp_newpatiententry"), SAMPLE_RP_POST_NO_CONSENT_DATA, format="json"
        )

        # Assert a correct response of 201
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["errors"], "")
        entry = PatientEntry.objects.all().first()

        # Check that the PatientEntry been correctly saved
        self.assertEqual(entry.surname, "Pt of Dr Test")
        self.assertEqual(entry.gravpar, "G1P2")

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
        self.assertEqual(response.json()["errors"], "Surname is required")


class CheckPatientExistsAPITestCase(AuthenticatedAPITestCase):
    @freeze_time("2019-01-01")
    def setUp(self):
        super(CheckPatientExistsAPITestCase, self).setUp()
        self.patient_entry = PatientEntry.objects.create(surname="Jane Doe", age=20)

    def test_patient_exists_found(self):
        SAMPLE_RP_POST_DATA["results"]["patient_id"] = {
            "category": "All Responses",
            "value": str(self.patient_entry.id),
            "input": str(self.patient_entry.id),
        }
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
                "surname": "Jane Doe",
                "parity": None,
                "age": 20,
                "foetus": None,
                "operation_cancelled": False,
            },
        )

    def test_patient_exists_not_found(self):
        response = self.normalclient.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA_NON_EXISTING, format="json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {})

    def test_patient_exists_no_auth(self):
        response = self.client.post(
            reverse("rp_patientexits"), SAMPLE_RP_POST_DATA, format="json"
        )

        self.assertEqual(response.status_code, 401)


class UpdatePatientEntryAPITestCase(AuthenticatedAPITestCase):
    def setUp(self):
        super(UpdatePatientEntryAPITestCase, self).setUp()
        self.patiententry = PatientEntry.objects.create(surname="Doe", age=20)

    def test_update_patient_success(self):
        SAMPLE_RP_UPDATE_DATA["results"]["patient_id"]["value"] = str(
            self.patiententry.id
        )
        SAMPLE_RP_UPDATE_DATA["results"]["patient_id"]["input"] = str(
            self.patiententry.id
        )

        response = self.normalclient.post(
            reverse("rp_entrychanges"), SAMPLE_RP_UPDATE_DATA, format="json"
        )

        # Test the right response code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["errors"], "")
        self.assertEqual(response.json()["surname"], "Nyasha")

        # Test that that the change has been made
        self.patiententry.refresh_from_db()
        self.assertTrue(self.patiententry.surname == "Nyasha")

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
        self.patient_entry = PatientEntry.objects.create(surname="Jane Doe", age=20)

    def test_patient_who_exists_delivered(self):
        SAMPLE_RP_UPDATE_DELIVERY_DATA["results"]["patient_id"]["value"] = str(
            self.patient_entry.id
        )
        SAMPLE_RP_UPDATE_DELIVERY_DATA["results"]["patient_id"]["input"] = str(
            self.patient_entry.id
        )

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

        baby_1 = Baby.objects.get(patiententry=self.patient_entry, baby_number=2)
        self.assertEqual(
            baby_1.delivery_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )
        self.assertEqual(baby_1.apgar_1, 8)
        self.assertEqual(baby_1.apgar_5, 9)
        self.assertEqual(baby_1.baby_weight_grams, 2400)
        self.assertTrue(baby_1.nicu)

        self.patient_entry.refresh_from_db()
        self.assertIsNotNone(self.patient_entry.completion_time)

    def test_patient_who_exists_delivered_minimal(self):
        SAMPLE_RP_UPDATE_DELIVERY_DATA_MINIMAL["results"]["patient_id"]["value"] = str(
            self.patient_entry.id
        )
        SAMPLE_RP_UPDATE_DELIVERY_DATA_MINIMAL["results"]["patient_id"]["input"] = str(
            self.patient_entry.id
        )
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
        SAMPLE_RP_UPDATE_DELIVERY_DATA["results"]["patient_id"]["value"] = str(
            self.patient_entry.id
        )
        SAMPLE_RP_UPDATE_DELIVERY_DATA["results"]["patient_id"]["input"] = str(
            self.patient_entry.id
        )

        Baby.objects.create(
            **{
                "patiententry": self.patient_entry,
                "baby_number": 2,
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

        baby_1 = Baby.objects.get(patiententry=self.patient_entry, baby_number=2)
        self.assertEqual(
            baby_1.delivery_time,
            timezone.datetime(2019, 5, 12, 10, 22, tzinfo=timezone.utc),
        )
        self.assertEqual(baby_1.apgar_1, 8)
        self.assertEqual(baby_1.apgar_5, 9)
        self.assertEqual(baby_1.baby_weight_grams, 2400)
        self.assertTrue(baby_1.nicu)

    def test_patient_who_exists_completed(self):
        SAMPLE_RP_UPDATE_COMPLETED_DATA["results"]["patient_id"]["value"] = str(
            self.patient_entry.id
        )
        SAMPLE_RP_UPDATE_COMPLETED_DATA["results"]["patient_id"]["input"] = str(
            self.patient_entry.id
        )

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

    def test_patient_who_exists_cancelled(self):
        SAMPLE_RP_UPDATE_CANCELLED_DATA["results"]["patient_id"]["value"] = str(
            self.patient_entry.id
        )
        SAMPLE_RP_UPDATE_CANCELLED_DATA["results"]["patient_id"]["input"] = str(
            self.patient_entry.id
        )

        self.assertFalse(self.patient_entry.operation_cancelled)

        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_CANCELLED_DATA,
            format="json",
        )

        # Test returns the right response code
        self.assertEqual(response.status_code, 200)
        self.patient_entry.refresh_from_db()
        self.assertTrue(self.patient_entry.operation_cancelled)

    def test_patient_status_update_bad_option(self):
        SAMPLE_RP_UPDATE_BAD_OPTION_DATA["results"]["patient_id"]["value"] = str(
            self.patient_entry.id
        )
        SAMPLE_RP_UPDATE_BAD_OPTION_DATA["results"]["patient_id"]["input"] = str(
            self.patient_entry.id
        )
        response = self.normalclient.post(
            reverse("rp_entrystatus_update"),
            SAMPLE_RP_UPDATE_BAD_OPTION_DATA,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

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
    def create_patient_entry(self, surname, complete=None, urgency=4):
        return PatientEntry.objects.create(
            surname=surname,
            age=20,
            completion_time=complete,
            indication="indic1",
            urgency=urgency,
        )

    def test_patient_list_view(self):
        entry1 = self.create_patient_entry("John Doe", urgency=1)
        self.create_patient_entry("Mary", timezone.now())
        entry3 = self.create_patient_entry("Test")

        response = self.normalclient.get(reverse("rp_patient_list"))

        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(
            result["patient_list_1"],
            "1) John Doe CS indic1 Red\n2) Test CS indic1 Green",
        )
        self.assertEqual(result["patient_ids"], f"1={entry1.id}|2={entry3.id}")
        self.assertEqual(result["list_count"], 1)

    def test_patient_list_view_multiple_lists(self):
        for i in range(0, 33):
            self.create_patient_entry(f"John Doe {i}")

        response = self.normalclient.get(reverse("rp_patient_list"))

        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertTrue("1) John Doe 0 CS indic1 Green" in result["patient_list_1"])
        self.assertTrue("12) John Doe 11 CS indic1 Green" in result["patient_list_2"])
        self.assertTrue("23) John Doe 22 CS indic1 Green" in result["patient_list_3"])
        self.assertTrue("32) John Doe 31 CS indic1 Green" in result["patient_list_4"])
        self.assertFalse("patient_list_5" in result)

        self.assertEqual(result["list_count"], 4)


class PatientSelectTestCase(AuthenticatedAPITestCase):
    def test_patient_select_view(self):

        response = self.normalclient.get(
            reverse("rp_patient_select"),
            {"patient_ids": "1=00000001|2=00000003|3=00000004", "option": "2"},
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(result["patient_id"], "00000003")

    def test_patient_select_view_invalid(self):

        response = self.normalclient.get(
            reverse("rp_patient_select"),
            {"patient_ids": "1=00000001|2=00000003|3=00000004", "option": "4"},
        )

        self.assertEqual(response.status_code, 404)


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
