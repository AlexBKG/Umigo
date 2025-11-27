from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.models import Group
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required

from users.models import User, Student

from .tokens import account_activation_token
from .forms import CustomUserCreationForm, LandlordCreationForm

def registerHomeView(request):
    return render(request, 'users/registerHome.html')

def landlordRegisterView(request):
    if request.method == "POST":
        user_form = CustomUserCreationForm(request.POST)
        landlord_profile_form = LandlordCreationForm(request.POST, request.FILES)  
        if user_form.is_valid() and landlord_profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active = False
            user.save()

            landlord_profile = landlord_profile_form.save(commit=False)
            landlord_profile.user = user
            landlord_profile.save()

            current_site = get_current_site(request)
            mail_subject = 'Activa tu cuenta Umigo'
            message = render_to_string('users/activateLandlordEmail.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = user_form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            
            return redirect("/users/landlordSuccessfulRegister")
    else:
        user_form = CustomUserCreationForm()
        landlord_profile_form = LandlordCreationForm()
    return render(request, 'users/landlordRegister.html', {"user_form" : user_form, "landlord_profile_form" : landlord_profile_form})

def landlordSuccessfulRegisterView(request):
    return render(request, 'users/landlordSuccessfulRegister.html')

def studentRegisterView(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)    
        if form.is_valid():
            newStudent = form.save()
            
            newStudent.is_active = False
            Student.objects.create(user = newStudent)
            students_group, created = Group.objects.get_or_create(name = 'Students')
            newStudent.groups.add(students_group)

            newStudent.save()

            current_site = get_current_site(request)
            mail_subject = 'Activa tu cuenta Umigo'
            message = render_to_string('users/activateStudentEmail.html', {
                'user': newStudent,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(newStudent.pk)),
                'token':account_activation_token.make_token(newStudent),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return redirect("/users/studentSuccessfulRegister")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/studentRegister.html', {"form" : form})

def studentSuccessfulRegisterView(request):
    return render(request, 'users/studentSuccessfulRegister.html')

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
    
@login_required 
def deactivateAccountView(request):
    if request.method == "POST":
        user_pk = request.user.pk
        logout(request)
        user = get_user_model()
        user.objects.filter(pk=user_pk).update(is_active=False)
    return redirect("/")

@login_required 
def deleteAccountView(request):
    if request.method == "POST":
        user_pk = request.user.pk
        logout(request)
        user = get_user_model()
        user.objects.filter(pk=user_pk).delete()
    return redirect("/")
    
class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/passwordReset.html'
    email_template_name = 'users/passwordResetEmail.html'
    subject_template_name = 'users/passwordResetSubject.txt'
    success_message = "Te hemos mandado un correo con instrucciones para reiniciar tu contraseña." \
                      "Si existe una cuenta con el correo que ingresaste, deberías recibir el correo dentro de poco." \
                      "Si no recibes un correo, por favor asegúrate que has ingresado el correo con el que te registraste, y revisa tu carpeta de spam"
    success_url = '/'

def activateUserView(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()        
        return redirect("/users/successfulEmailActivation")
    else:
        return redirect("/users/unSuccessfulEmailActivation")