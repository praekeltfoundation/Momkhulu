from django.db import models

# Create your models here.


class Patient(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    age = models.IntegerField()
    gravidity = models.CharField()
    comorbidity = models.CharField()
    indication = models.CharField(max=4, min=1)
    time = models.TimeField()
    urgency = models.IntegerField()
    location = models.CharField()
    data = models.CharField()
    clinician = models.CharField()
