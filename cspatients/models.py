from django.db import models


class Patient(models.Model):
    patient_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    age = models.IntegerField(default=20)
    gravidity = models.IntegerField(default=1)
    parity = models.IntegerField(default=0)
    comorbidity = models.CharField(max_length=255, null=True)
    indication = models.CharField(max_length=255, null=True)
    time = models.TimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)
    urgency = models.IntegerField(default=4)
    location = models.CharField(max_length=255, null=True)
    data = models.CharField(max_length=255, null=True)
    clinician = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ('urgency', 'time')

    def __str__(self):
        return self.name
