# Generated by Django 2.1.7 on 2019-06-11 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cspatients", "0016_patiententry_update_gravpar")]

    operations = [
        migrations.AlterField(
            model_name="baby", name="apgar_1", field=models.IntegerField(null=True)
        ),
        migrations.AlterField(
            model_name="baby", name="apgar_5", field=models.IntegerField(null=True)
        ),
        migrations.AlterField(
            model_name="baby",
            name="baby_weight_grams",
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="baby", name="nicu", field=models.BooleanField(null=True)
        ),
    ]
