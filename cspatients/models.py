from django.contrib.auth.models import User
from django.db import models


class Patient(models.Model):
    patient_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    age = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.patient_id, self.name)


class PatientEntry(models.Model):
    patient = models.ForeignKey(
        Patient, related_name="patient_entries", on_delete=models.CASCADE
    )
    operation = models.CharField(max_length=255, default="CS")
    parity = models.IntegerField(default=0)
    gravidity = models.IntegerField(default=1)
    comorbid = models.CharField(max_length=255, null=True)
    indication = models.CharField(max_length=255, null=True)
    decision_time = models.DateTimeField(auto_now_add=True)
    discharge_time = models.DateTimeField(null=True)
    delivery_time = models.DateTimeField(null=True)
    completion_time = models.DateTimeField(null=True)
    urgency = models.IntegerField(default=4)
    location = models.CharField(max_length=255, null=True)
    outstanding_data = models.CharField(max_length=255, null=True)
    clinician = models.CharField(max_length=255, null=True)
    apgar_1 = models.IntegerField(null=True)
    apgar_5 = models.IntegerField(null=True)
    foetus = models.IntegerField(null=True)
    baby_weight_grams = models.IntegerField(null=True)
    nicu = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def gravpar(self):
        return "G{}P{}".format(self.gravidity, self.parity)

    def __str__(self):
        return "{} having {}".format(self.patient, self.operation)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    msisdn = models.CharField("MSISDN(+country code)", max_length=30, blank=True)

    def __str__(self):
        return "{}: {}".format(self.user.username, self.msisdn)
