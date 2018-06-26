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
    return HttpResponse(template.render(context, request), status=200)


def form(request):
    template = loader.get_template("cspatients/index.html")
    if request.method == "POST":
        # Send the Form information
        form = PatientLogForm(request.POST)
        if form.is_valid():

            context = {
                "saved": True,
            }    
    elif request.method == "GET":
        # Get the Form

        context = {
            "saved": False,
        }
    return HttpResponse(template.render(context, request), status=200)


def event(request):
    # Takes in the information from Rapid Pro
    if request.method == "POST":
        # Save the information
        return HttpResponse("", status=200)
    return HttpResponse("", status=400)
