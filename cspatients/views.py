from django.http import HttpResponse
from django.template import loader
from django.db.models.query import EmptyQuerySet

from .models import Patient
from .serializers import PatientSerializer


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
    template = loader.get_template("cspatients/form.html")
    context = {
        "saved": False,
    }
    if request.method == "POST":
        # Send the Form information
        patient = PatientSerializer(data=request.POST)
        print(request.POST)
        if patient.is_valid():
            patient.save()
            context = {
                "saved": True,
            }

    return HttpResponse(template.render(context, request), status=200)


def event(request):
    # Takes in the information from Rapid Pro
    if request.method == "POST":
        # Save the information
        patient = PatientSerializer(data=request.POST)
        if patient.is_valid():
            patient.save()
            return HttpResponse("", status=201)

    return HttpResponse("", status=400)
