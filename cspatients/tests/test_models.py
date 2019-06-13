from django.contrib.auth.models import User
from django.test import TestCase

from cspatients.models import Profile


class TestModels(TestCase):
    def test_profile(self):
        new_user = User.objects.create_user(
            "test_user", "testuser@example.com", "1234", is_active=False
        )
        profile = Profile.objects.create(**{"user": new_user, "msisdn": "+12065550109"})

        self.assertEqual(str(profile), "test_user: +12065550109")
