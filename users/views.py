from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm, StudentCreationForm, LandlordCreationForm

def registerHomeView(request):
    return render(request, 'users/registerHome.html')

def landlordRegisterView(request):
    if request.method == "POST":
        form = LandlordCreationForm(request.POST, request.FILES)    
        if form.is_valid():
            user = form.save()
            #login(request, user) #In case we want the user to log in immediately and automatically after registering 
            return redirect("users/landlordSuccesfulRegister.html")
    else:
        form = LandlordCreationForm()
    return render(request, 'users/landlordRegister.html', {"form" : form})

def studentRegisterView(request):
    if request.method == "POST":
        form = StudentCreationForm(request.POST)    
        if form.is_valid():
            user = form.save()
            #login(request, user) #In case we want the user to log in immediately and automatically after registering 
            return redirect("/")
    else:
        form = StudentCreationForm()
    return render(request, 'users/studentRegister.html', {"form" : form})

def loginView(request):
    if request.method == "POST":
        form = AuthenticationForm(data = request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if "next" in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect("/")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {"form" : form})

def logoutView(request):
    if request.method == "POST":
        logout(request)
        return redirect("/")