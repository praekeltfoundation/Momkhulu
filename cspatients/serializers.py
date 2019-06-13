from rest_framework import serializers

from cspatients.models import PatientEntry


class PatientEntrySerializer(serializers.ModelSerializer):
    gravpar = serializers.ReadOnlyField()

    class Meta:
        model = PatientEntry
        exclude = ("created_at", "updated_at", "id")

    def __init__(self, *args, **kwargs):
        super(PatientEntrySerializer, self).__init__(*args, **kwargs)

        self.fields["surname"].error_messages["required"] = "Surname is required"


class UpdateEntrySerializer(serializers.Serializer):
    patient_id = serializers.CharField(max_length=255, required=True)

    def __init__(self, *args, **kwargs):
        super(UpdateEntrySerializer, self).__init__(*args, **kwargs)

        self.fields["patient_id"].error_messages["required"] = "Patient ID is required"
