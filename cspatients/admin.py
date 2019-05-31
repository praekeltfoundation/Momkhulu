from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Patient, PatientEntry, Profile


class PatientEntryAdmin(admin.TabularInline):
    model = PatientEntry


class PatientAdmin(admin.ModelAdmin):
    model = Patient
    inlines = [PatientEntryAdmin]


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.register(Patient, PatientAdmin)
admin.site.register(PatientEntry)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
