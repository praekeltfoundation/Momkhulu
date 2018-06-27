from rest_framework import serializers
from cspatients.models import Patient

# Model Tests 


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ("patient_id", "name", "age", "gravidity", "comorbidity",
                  "indication", "time", "urgency", "location", "data",
                  "date", "clinician")

# End Point Tests


