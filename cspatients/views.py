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
    status_code = 200
    if request.method == "POST":
        # Send the Form information
        patient = PatientSerializer(data=request.POST)
        print(request.POST)
        if patient.is_valid():
            patient.save()
            context = {
                "saved": True,
            }
            status_code = 201
        status_code = 405
    return HttpResponse(template.render(context, request), status=status_code)


def event(request):
    # Takes in the information from Rapid Pro
    status_code = 405
    if request.method == "POST":
        # Save the information
        patient = PatientSerializer(data=request.POST)
        if patient.is_valid():
            patient.save()
            status_code = 201
        status_code = 400
    else:
        HttpResponse("", status=status_code)

