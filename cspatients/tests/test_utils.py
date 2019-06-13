from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from cspatients.models import PatientEntry
from cspatients.util import (
    get_all_active_patient_entries,
    get_rp_dict,
    save_model,
    save_model_changes,
)

from .constants import SAMPLE_RP_POST_DATA, SAMPLE_RP_UPDATE_DATA


class ViewAllContextTest(TestCase):
    def setUp(self):
        self.patient_one_data = {"surname": "Urgency COLD", "age": 20}

        self.patient_two_data = {
            "surname": "Urgency Immediate",
            "age": 23,
            "urgency": 1,
        }

        self.patient_three_data = {"surname": "John Completed", "age": 20}

        self.patient_four_data = {
            "surname": "Urgency Immediate NEW",
            "age": 23,
            "urgency": 1,
        }

        self.patient_five_data = {"surname": "Completed OLD", "age": 23, "urgency": 1}

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
        self.assertEqual(patient_entries[0].surname, "Urgency Immediate NEW")
        self.assertEqual(patient_entries[1].surname, "Urgency Immediate")
        self.assertEqual(patient_entries[2].surname, "Urgency COLD")
        self.assertEqual(patient_entries[3].surname, "John Completed")

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
        self.assertEqual(patient_entries[0].surname, "Urgency Immediate NEW")
        self.assertEqual(patient_entries[1].surname, "Urgency Immediate")
        self.assertEqual(patient_entries[2].surname, "Urgency COLD")
        self.assertEqual(patient_entries[3].surname, "Completed OLD")
        self.assertEqual(patient_entries[4].surname, "John Completed")

    def test_get_all_active_patient_entries_filter(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        save_model(self.patient_three_data)

        patient_entries = get_all_active_patient_entries("COLD", "4")

        self.assertEqual(len(patient_entries), 1)
        self.assertEqual(patient_entries[0].surname, "Urgency COLD")

    def test_get_all_active_patient_entries_filter_complete(self):
        save_model(self.patient_one_data)
        save_model(self.patient_two_data)
        entry3, _ = save_model(self.patient_three_data)

        entry3.completion_time = timezone.now()
        entry3.save()

        patient_entries = get_all_active_patient_entries(None, "complete")

        self.assertEqual(len(patient_entries), 1)
        self.assertEqual(patient_entries[0].surname, "John Completed")


class SaveModelTest(TestCase):
    def setUp(self):
        self.patient_one_data = {"surname": "Jane Doe", "age": 20, "urgency": 1}

    def test_saves_when_given_sufficient_data(self):
        patiententry, errors = save_model(self.patient_one_data)

        # Must return the saved patient entry
        self.assertEqual(errors, [])
        self.assertIsNotNone(patiententry)

        # Check that the save persisted in the database
        self.assertEqual(len(PatientEntry.objects.all()), 1)

    def test_saves_when_given_junk_data(self):
        patiententry, errors = save_model(
            {"surname": "Mary Mary", "age": 23, "urgency": 1, "response_19": "test"}
        )

        # Must return the saved patient entry
        self.assertIsNotNone(patiententry)
        self.assertEqual(errors, [])

        # Check that the save persisted in the database
        self.assertEqual(len(PatientEntry.objects.all()), 1)

    def test_nothing_saved_with_insufficient_data(self):
        patientryentry, errors = save_model({"age": 23, "urgency": 1})

        # Must return None
        self.assertIsNone(patientryentry)
        self.assertEqual(errors, ["Surname is required"])

        # Check that none of the information is in the database
        self.assertEqual(len(PatientEntry.objects.all()), 0)


class SaveModelChangesTest(TestCase):
    def setUp(self):
        self.patient_entry = PatientEntry.objects.create(surname="Doe", age=20)

    def test_saves_data_when_passed_good_dict(self):
        changes_dict = {
            "patient_id": str(self.patient_entry.id),
            "surname": "Moe",
            "gravidity": "1",
            "parity": "1",
        }

        # Check returns PatientEntry
        result, errors = save_model_changes(changes_dict)
        self.assertEqual(errors, [])
        self.assertTrue(isinstance(result, PatientEntry))

        # Check that the changes persisted.
        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient_entry.surname, "Moe")
        self.assertEqual(self.patient_entry.gravpar, "G1P1")
        self.assertEqual(str(self.patient_entry), "Moe having CS")

    def test_returns_none_for_patient_dict_with_wrong_patient_id(self):
        changes_dict = {"patient_id": "999", "surname": "Moe"}

        result, errors = save_model_changes(changes_dict)

        # Returns none on bad incorrect patient_id
        self.assertIsNone(result)
        self.assertEqual(errors, ["Patient entry does not exist"])

    def test_does_not_make_changes_when_dict_has_wrong_fields(self):
        changes_dict = {
            "patient_id": str(self.patient_entry.id),
            "surname": "Moe",
            "urgent": "DSHLSD",
        }

        result, errors = save_model_changes(changes_dict)

        self.assertEqual(errors, [])

        self.patient_entry.refresh_from_db()
        self.assertEqual(self.patient_entry.urgency, result.urgency)


class GetRPDictTest(TestCase):

    """
        Test the get_rp_dict method
        Takes in request.POST method
    """

    def test_get_rp_event_dict(self):
        """
            The Method should be able to extract the surname, and patient ID,
            from the Query dict into a dictionary with just name and
            patient_id
        """
        SAMPLE_RP_POST_DATA["results"]["patient_id"] = {
            "category": "All Responses",
            "value": "123",
            "input": "123",
        }
        event_dict = get_rp_dict(SAMPLE_RP_POST_DATA)

        self.assertEqual(event_dict["surname"], "Doe")
        self.assertEqual(event_dict["patient_id"], "123")

    def test_get_entrychanges_dict(self):
        """
            The Method when passed a context of entrychanges, must be able
            to pick up the change category and the new value
        """
        changes_dict = get_rp_dict(SAMPLE_RP_UPDATE_DATA, context="entrychanges")

        self.assertEqual(changes_dict["surname"], "Nyasha")
        self.assertEqual(changes_dict["patient_id"], "1")
