from rest_framework import serializers
from cspatients.models import Patient, PatientEntry


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ("patient_id", "name", "age")


class PatientEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = PatientEntry
        fields = (
            "patient_id", "operation", "gravpar", "comorbid", "indication",
            "discharge_time", "decision_time", "location", "outstanding_data",
            "delivery_time", "clinician", "urgency", "apgar_1",
            "apgar_5"
            )
