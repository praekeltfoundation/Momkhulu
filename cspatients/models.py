from django.db import models

# Create your models here.


class Patient(models.Model):
    patient_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    age = models.IntegerField(default=20)
    gravidity = models.IntegerField(default=1)
    comorbidity = models.CharField(max_length=255, null=True)
    indication = models.CharField(max_length=255, null=True)
    time = models.DateTimeField(auto_now_add=True)
    urgency = models.IntegerField(default=4)
    location = models.CharField(max_length=255, null=True)
    data = models.CharField(max_length=255, null=True)
    clinician = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ('urgency', 'time')

    def __str__(self):
        return self.patient_id
