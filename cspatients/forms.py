from django import forms


class PatientLogForm(forms.Form):
    name = forms.CharField(label="name", max_length=200)
    id = forms.IntegerField(label="patient_id")
    age = forms.IntegerField(label="patient_age")
    urgency = forms.IntegerField(label="patient_urgency")
    indication = forms.CharField(label='patient_notes', max_length=200)
    clinician = forms.CharField(label='patient_clinician', max_length=200)
