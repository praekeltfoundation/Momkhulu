# Generated by Django 2.1.7 on 2019-06-03 08:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("cspatients", "0011_add_patiententry_urgency_choices")]

    operations = [
        migrations.RemoveField(model_name="patiententry", name="apgar_1"),
        migrations.RemoveField(model_name="patiententry", name="apgar_5"),
        migrations.RemoveField(model_name="patiententry", name="baby_weight_grams"),
        migrations.RemoveField(model_name="patiententry", name="delivery_time"),
        migrations.RemoveField(model_name="patiententry", name="nicu"),
    ]
