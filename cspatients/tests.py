from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User

from .models import Patient
# View Tests


class LoginTest(TestCase):

    """
        Tests for the log_in view.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="Itai", password="itai")

    def test_get_login_page(self):
        """
            Test using get method on login view will render the login page
            if you aren't logged in and will redirect when logged in.
        """
        get_response = self.client.get("/cspatients/login")
        # Must render the log in page
        self.assertTemplateUsed(
            get_response,
            template_name="cspatients/login.html"
            )
        self.client.force_login(self.user)
        get_response_logged = self.client.get("/cspatients/login")
        # Must not show you the login page
        self.assertTemplateNotUsed(
            get_response_logged,
            template_name="cspatients/login.html"
            )
        # Must redirect to the root of the cspatients app
        self.assertRedirects(get_response_logged, "/cspatients/")

    def test_good_login(self):
        """
            Test the posting credintials to login
        """
        self.client.logout()
        response = self.client.post("/cspatients/login", {
            "username": "Itai",
            "password": "itai",
        })
        # The user must now be logged in
        self.assertTrue(self.user.is_authenticated)
        # The login should redirect to the root of the cspatients app
        self.assertRedirects(response, "/cspatients/")

    def test_bad_login(self):

        """
            Test trying to login in with the wrong details.
        """
        self.client.logout()
        # The user must not be authenticated

        response = self.client.post("/cspatients/login", {
            "username": "Itai",
            "password": "badpassword",
        })

        # The returned status code must be 401
        self.assertEquals(response.status_code, 401)
        # Must render the login in page again
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/login.html",
        )


class LogoutTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="Itai")

    def test_logout_when_logged_in(self):
        """
            Test the logout view. Must log out the user if logged in
        """
        self.client.force_login(self.user)
        response = self.client.get("/cspatients/logout")
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/logout.html"
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_when_not_logged_in(self):
        response = self.client.get("/cspatients/logout")
        self.assertTemplateNotUsed(
            response=response,
            template_name="cspatients/logout.html"
        )
        self.assertEqual(response.status_code, 302)


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
        self.insufficient_data = {
            "name": "Lisa Smith",
        }

    def test_get_method_not_logged_in(self):
        """
            Test GET method to the form view.
            Render template and return 200.
            If you not logged in then the form page must not be
            rendered.
        """
        response = self.client.get('/cspatients/form')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, "/cspatients/login?next=/cspatients/form"
            )
        self.assertTemplateNotUsed(
            response=response,
            template_name="cspatients/form.html"
            )

    def test_get_method_logged_in(self):
        """
            Test the GET method when logged in. Must render the form template.
        """
        self.client.force_login(self.user)
        response = self.client.get('/cspatients/form')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response=response, template_name="cspatients/form.html"
            )

    def test_sufficient_post_method(self):
        """
            Test the POST method when posted the right information.
        """
        self.client.force_login(self.user)
        response = self.client.post(
            '/cspatients/form', self.sufficient_data)

        # Check the status code response of the POST
        self.assertEqual(response.status_code, 201)
        jane = Patient.objects.get(patient_id="XXXXX")
        # Check the fields have been saved correctly
        self.assertEqual(jane.name, "Jane Doe")
        self.assertEqual(jane.patient_id, "XXXXX")
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
        self.client.force_login(self.user)
        response = self.client.post(
            '/cspatients/form', self.insufficient_data)
        # Check the response code of the post
        self.assertEqual(response.status_code, 400)

        # Check that the template is rendered again
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/form.html"
            )

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
        response = self.client.get("/cspatients/view")
        self.assertTemplateNotUsed(
            response=response,
            template_name="cspatients/view.html"
        )
        self.client.force_login(self.user)
        response = self.client.get("/cspatients/view")
        self.assertTemplateUsed(
            response=response,
            template_name="cspatients/view.html"
        )
