from rest_framework import serializers
from django.db import models

from cspatients.models import Patient, PatientEntry


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ("patient_id", "name", "age")


class PatientEntrySerializer(serializers.ModelSerializer):
    decision_time = models.DateTimeField()

    class Meta:
        model = PatientEntry
        fields = (
            "patient_id", "operation", "gravpar", "comorbid", "indication",
            "discharge_time", "location", "outstanding_data",
            "delivery_time", "clinician", "urgency", "apgar_1",
            "apgar_5"
            )
