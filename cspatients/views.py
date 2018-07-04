from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .models import Patient
from .serializers import PatientSerializer, PatientEntrySerializer
from .util import get_patient_dict, get_patiententry_dict, view_all_context


def log_in(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/")
    context = {
        "try": False,
    }
    if request.method == "POST":
        context['try'] = True
        password = request.POST['password']
        username = request.POST['username']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next = request.GET.get('next')
            return HttpResponseRedirect(next)
    return render(request, 'cspatients/login.html', context, status=200)


@login_required(login_url="/cspatients/login")
def log_out(request):
    template = loader.get_template('cspatients/logout.html')
    logout(request)
    return HttpResponse(template.render())


@login_required(login_url="/cspatients/login")
def view(request):

    template = loader.get_template('cspatients/view.html')
    context = {
        "patiententrys": view_all_context()
    }
    return HttpResponse(
        template.render(context),
        status=200
        )


@login_required(login_url="/cspatients/login")
def patient(request, patient_id):
    template = loader.get_template("cspatients/patient.html")
    try:
        patient = Patient.objects.get(patient_id=patient_id)
        context = {
            "patient": patient,
        }
        status_code = 200
    except Patient.DoesNotExist:
        context = {
            "patient": False,
        }
        status_code = 400
    return HttpResponse(template.render(context), status=status_code)


@login_required(login_url="/cspatients/login")
def form(request):
    context = {
        "saved": False,
    }
    status_code = 200
    if request.method == "POST":
        status_code = 400
        # Send the Form information
        patient = PatientSerializer(data=request.POST)
        patiententry = PatientEntrySerializer(data=request.POST)
        if patient.is_valid() and patiententry.is_valid():
            patient.save()
            patiententry.save()
            context = {
                "saved": True,
            }
            status_code = 201
    return render(
        request, "cspatients/form.html",
        context=context,
        status=status_code
        )


@csrf_exempt
def rp_event(request):
    """
        RapidPro should use the following url
        /event?secret=momkhulu

    """
    # Takes in the information from Rapid Pro
    status_code = 405
    if request.method == "POST":
        status_code = 400
        if request.GET.get('secret') == "momkhulu":
            patient = PatientSerializer(data=get_patient_dict(request.body))
            patiententry = PatientEntrySerializer(
                data=get_patiententry_dict(request.body)
            )
            if patient.is_valid():
                patient.save()
            if patiententry.is_valid():
                patiententry.save()
                status_code = 201
    return HttpResponse(status=status_code)


@csrf_exempt
def rapidprochange(request):
    return ""


@csrf_exempt
def rapidpro(request):
    return ""
