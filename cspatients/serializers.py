from rest_framework import serializers

from cspatients.models import Patient, PatientEntry


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = "__all__"


class PatientEntrySerializer(serializers.ModelSerializer):
    decision_time = serializers.DateTimeField()

    class Meta:
        model = PatientEntry
        fields = "__all__"
