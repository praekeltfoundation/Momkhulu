from rest_framework import serializers
from django.db import models
from cspatients.models import Patient, PatientEntry


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = "__all__"


class PatientEntrySerializer(serializers.ModelSerializer):
    decision_time = models.DateTimeField()

    class Meta:
        model = PatientEntry
        fields = "__all__"


class CreateEntrySerializer(serializers.Serializer):
    patient_id = serializers.CharField(max_length=255, required=True)

    def __init__(self, *args, **kwargs):
        super(CreateEntrySerializer, self).__init__(*args, **kwargs)

        self.fields["patient_id"].error_messages["required"] = "Patient ID is required"
        self.fields["patient_id"].error_messages["null"] = "Patient ID is required"
