from rest_framework import serializers
from cspatients.models import Patient


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ("id", "name", "age", "gravidity", "comorbidity",
                  "indication", "time", "urgency", "location", "data",
                  "clinician")
