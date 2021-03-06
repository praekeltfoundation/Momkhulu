# Generated by Django 2.1.7 on 2019-04-03 10:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cspatients", "0004_patiententry_completion_time")]

    operations = [
        migrations.RemoveField(model_name="patiententry", name="patient_id"),
        migrations.AddField(
            model_name="patiententry",
            name="patient",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="patient_entries",
                to="cspatients.Patient",
            ),
            preserve_default=False,
        ),
    ]
