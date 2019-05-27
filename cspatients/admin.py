from django.contrib import admin

from .models import Patient, PatientEntry


class PatientEntryAdmin(admin.TabularInline):
    model = PatientEntry


class PatientAdmin(admin.ModelAdmin):
    model = Patient
    inlines = [PatientEntryAdmin]


admin.site.register(Patient, PatientAdmin)
admin.site.register(PatientEntry)
