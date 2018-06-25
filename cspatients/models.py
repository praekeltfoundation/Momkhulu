from django.db import models

# Create your models here.


class Patient(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    age = models.IntegerField()
    gravidity = models.CharField(max_length=200)
    comorbidity = models.CharField(max_length=200)
    indication = models.CharField(max_length=200)
    time = models.DateTimeField(auto_now_add=True)
    urgency = models.IntegerField()
    location = models.CharField(max_length=200)
    data = models.CharField(max_length=200)
    clinician = models.CharField(max_length=200)

    class Meta:
        ordering = ('urgency', 'time')
