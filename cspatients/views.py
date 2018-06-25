from django.http import HttpResponse
from django.template import loader
from django.db.models.query import EmptyQuerySet
from django.shortcuts import render, redirect

from .models import Patient
from .forms import PatientLogForm


def index(request):

    patients_list = Patient.objects.all()
    if isinstance(patients_list, EmptyQuerySet):
        patients_list = False
    template = loader.get_template('cspatients/index.html')
    context = {
        'patients_list': patients_list
    }
    return HttpResponse(template.render(context, request))


def form(request):
    return render(request, "cspatients/form.html")


def submit(request):
    if request.method == "POST":
        form = PatientLogForm(request.POST)
        if form.is_valid():
            return render(request, "cspatients/index.html")
    return redirect("form")
