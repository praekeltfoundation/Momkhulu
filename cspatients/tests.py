from django.test import Client
from django.test.testcases import SimpleTestCase
from django.contrib.auth.models import UserManager

from .models import Patient, PatientEntry

# Model Tests
"""
Do not test Django functionality. Assume she does it perfectly
Assert template used
Find a key phrase expected to be in the template
Assert contains
Hypothesis

"""


# View Tests

class LoginTest(SimpleTestCase):

    """
        Tests for the log_in view.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserManager.create_user("Itai")

    def test_get_login_page(self):
        """
            Test using get method on login view will render the login page
            if you aren't logged in and will redirect somewhere else if
            you are logged in.
        """
        get_response = self.client.get("/login")
        self.assertTemplateUsed(
            get_response,
            template_name="cspatients/login.html"
            )
        self.client.force_login(self.user)
        get_response_logged = self.client.get("/login")
        self.assertTemplateNotUsed(
            get_response_logged,
            template_name="cspatients/login.html"
            )


class RPEventTest(SimpleTestCase):

    def setUp(self):
        self.client = Client()
        self.allow_database_queries = True

    def test_request_methods(self):
        """
            Test for the method used with the rpevent view.
            Using GET method should return 405
            Using POST method with right parameters should return 201
        """
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
            Test the serialization into database.
            Inadequate data should return status 400.
            Adequate data should return status 201.

            Minimum adequate data is:
            1. patient_id
            2. name
            3. age

            After successful serialization, the data should persist
            in the database.
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
        with self.assertRaises(Patient.DoesNotExist):
            Patient.objects.get(name="Lisa Smith")
        self.assertEqual(
            Patient.objects.get(name="Jane Doe")[0].patient_id == "XXXXX"
            )
        self.assertFalse(
            PatientEntry.objects.all(), PatientEntry.objects.none()
            )


class LogoutTest(SimpleTestCase):

    def setUp(self):
        self.client = Client()
        self.user = UserManager.create_user("Itai")

    def test_logout(self):
        """
            Test the logout view. Must log out the user if logged in
            or redirect them to the login page if they aren't logged in.
        """
        response = self.client.get("/logout")
        self.assertTemplateNotUsed(
            response=response,
            template_name="cspatients/logout.html"
        )
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/login.html"
        )
        self.client.force_login(self.user)
        response = self.client.get("/logout")
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/logout.html"
        )
        self.assertTemplateNotUsed(
            response=response,
            template_name="cspatients/login.html"
        )


class FormTest(SimpleTestCase):
    """
        Tests for the form view.
    """

    def setUp(self):
        self.client = Client()
        self.allow_database_queries = True
        self.user = UserManager.create_user("Itai")

    def test_get_method(self):
        """
            Test GET method to the form view.
            Render template and return 200.
            If you not logged in then the form page must not be
            rendered.
        """
        response = self.client.get('/form')
        self.assertTemplateNotUsed(
            response=response,
            template="cspatients/form.html"
            )
        self.client.force_login(self.user)
        response = self.client.get('/form')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response=response, template="cspatients/form.html"
            )

    def test_sufficient_post_method(self):
        """
            Test the POST method when posted the right information.
        """
        response = self.client.post("/form", {
            "name": "Jane Doe",
            "patient_id": "XXXXX",
            "age": 20,
            "location": "Ward 56",
            "urgency": 2,
            "parity": 1,
            "indication": "Severe Pain",
            "clinician": "Dr Peter Drew",
        })

        # Check the status code response of the POST
        self.assertEqual(response.status_code, 201)
        jane = Patient.objects.get(patient_id="XXXXXX")[0]
        # Check the fields have been saved correctly
        self.assertEqual(jane.name, "Jane Doe")
        self.assertEqual(jane.patient_id, "XXXXXX")
        self.assertEqual(jane.age, 20)
        # Check that it renders the form page again
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/form.html"
            )

    def test_insufficient_post_method(self):
        """
            Test the POST method when given insufficient information
            to save.
        """
        response = self.client.post("/form", {
            "name": "Jane Doe",
            "patient_id": "XXXXX",
            "location": "Ward 56",
            "urgency": 2,
            "parity": 1,
            "indication": "Severe Pain",
            "clinician": "Dr Peter Drew",
        })
        # Check the response code of the post
        self.assertEqual(response.status_code, 405)

        # Check that the template is rendered again
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/form.html"
            )

        # Check that nothing was saved in the database.
        with self.assertRaises(Patient.DoesNotExit):
            Patient.objects.get(name="Jane Doe")

        with self.assertRaises(PatientEntry.DoesNotExist):
            PatientEntry.objects.get(patient_id="XXXXX")


class ViewTest(SimpleTestCase):
    """
        Test the view view method. Pun intended.
    """
    def setUp(self):
        self.client = Client()
        self.client.user = UserManager.create_user("Itai")

    def test_get_view(self):
        """
            1. Test that you only view the page when you are logged in.
        """
        response = self.client.get("/view")
        self.assertTemplateNotUsed(
            response=response,
            template_name="cspatients/view.html"
        )
        self.client.force_login(self.user)
        response = self.client.get("/view")
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/view.html"
        )
