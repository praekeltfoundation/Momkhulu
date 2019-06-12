from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Patient(models.Model):
    patient_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    age = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.patient_id, self.name)


class PatientEntry(models.Model):
    ELECTIVE = 5
    COLD = 4
    HOT_YELLOW = 3
    HOT_ORANGE = 2
    IMMEDIATE = 1

    URGENCY_CHOICES = (
        (ELECTIVE, "Elective"),
        (COLD, "Cold"),
        (HOT_YELLOW, "Hot"),
        (HOT_ORANGE, "Hot"),
        (IMMEDIATE, "Immediate"),
    )

    URGENCY_COLORS = {1: "❤", 2: "🧡", 3: "💛", 4: "💚", 5: "💙"}

    patient = models.ForeignKey(
        Patient, related_name="patient_entries", on_delete=models.CASCADE
    )
    operation = models.CharField(max_length=255, default="CS")
    parity = models.IntegerField(null=True)
    gravidity = models.IntegerField(null=True)
    comorbid = models.CharField(max_length=255, null=True)
    indication = models.CharField(max_length=255, null=True)
    decision_time = models.DateTimeField(default=timezone.now)
    completion_time = models.DateTimeField(null=True)
    urgency = models.IntegerField(default=4, choices=URGENCY_CHOICES)
    location = models.CharField(max_length=255, null=True)
    outstanding_data = models.CharField(max_length=255, null=True)
    clinician = models.CharField(max_length=255, null=True)
    foetus = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def gravpar(self):
        gravidity = "-"
        parity = "-"
        if self.gravidity is not None:
            gravidity = self.gravidity
        if self.parity is not None:
            parity = self.parity
        return "G{}P{}".format(gravidity, parity)

    def get_urgency_color(self):
        return self.URGENCY_COLORS[self.urgency]

    def __str__(self):
        return "{} having {}".format(self.patient, self.operation)


class Baby(models.Model):
    patiententry = models.ForeignKey(
        PatientEntry, related_name="entry_babies", on_delete=models.CASCADE
    )
    baby_number = models.IntegerField()
    delivery_time = models.DateTimeField()
    apgar_1 = models.IntegerField(null=True)
    apgar_5 = models.IntegerField(null=True)
    baby_weight_grams = models.IntegerField(null=True)
    nicu = models.BooleanField(null=True)

    class Meta:
        unique_together = ("patiententry", "baby_number")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    msisdn = models.CharField("MSISDN(+country code)", max_length=30, blank=True)

    def __str__(self):
        return "{}: {}".format(self.user.username, self.msisdn)
