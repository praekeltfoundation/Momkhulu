from rest_framework import serializers

from cspatients.models import Patient, PatientEntry


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        exclude = ("created_at", "updated_at", "id")


class PatientEntrySerializer(serializers.ModelSerializer):
    gravpar = serializers.ReadOnlyField()

    class Meta:
        model = PatientEntry
        exclude = ("created_at", "updated_at", "id", "patient")


class CreateEntrySerializer(serializers.Serializer):
    patient_id = serializers.CharField(max_length=255, required=True)

    def __init__(self, *args, **kwargs):
        super(CreateEntrySerializer, self).__init__(*args, **kwargs)

        self.fields["patient_id"].error_messages["required"] = "Patient ID is required"
