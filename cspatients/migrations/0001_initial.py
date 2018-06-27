# Generated by Django 2.0.6 on 2018-06-26 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=255)),
                ('age', models.IntegerField(default=20)),
                ('gravidity', models.IntegerField(default=1)),
                ('comorbidity', models.CharField(max_length=255, null=True)),
                ('indication', models.CharField(max_length=255, null=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('urgency', models.IntegerField(default=4)),
                ('location', models.CharField(max_length=255, null=True)),
                ('data', models.CharField(max_length=255, null=True)),
                ('clinician', models.CharField(max_length=255, null=True)),
            ],
            options={
                'ordering': ('urgency', 'time'),
            },
        ),
    ]