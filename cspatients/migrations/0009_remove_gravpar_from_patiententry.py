# Generated by Django 2.1.7 on 2019-05-29 15:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("cspatients", "0008_add_patient_entry_fields")]

    operations = [migrations.RemoveField(model_name="patiententry", name="gravpar")]
