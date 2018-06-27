from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.db.models.query import EmptyQuerySet
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from .models import Patient
from .serializers import PatientSerializer


def log_in(request):
    context = {
        'try': False
    }
    template = loader.get_template('cspatients/login.html')
    if request.method == "POST":
        context['try'] = True
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(user)
            next = request.GET.get('next')
            return HttpResponseRedirect(next)
        else:
            context['success'] = False
    return HttpResponse(template.render(context, request), status=200)


@login_required(login_url="/login")
def log_out(request):
    template = loader.get_template('cspatients/logout.html')
    logout(request)
    return HttpResponse(template.render())


@login_required(login_url="/login")
def index(request):

    patients_list = Patient.objects.all()
    if isinstance(patients_list, EmptyQuerySet):
        patients_list = False
    template = loader.get_template('cspatients/index.html')
    context = {
        'patients_list': patients_list
    }
    return HttpResponse(template.render(context, request), status=200)


@login_required(login_url="/login")
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
