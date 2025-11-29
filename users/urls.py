from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('registerHome/', views.registerHomeView, name="registerHome"),
    path('studentRegister/', views.studentRegisterView, name="studentRegister"),
    path('studentSuccessfulRegister/', views.studentSuccessfulRegisterView, name="studentSuccessfulRegister"),
    path('landlordRegister/', views.landlordRegisterView, name="landlordRegister"),
    path('landlordSuccessfulRegister/', views.landlordSuccessfulRegisterView),
    path('login/', views.loginView, name="login"),
    path('logout/', views.logoutView, name="logout"),
    path('passwordReset/', views.ResetPasswordView.as_view(), name="passwordReset"),
    path('passwordResetConfirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='passwordResetConfirm'),
    path('passwordResetComplete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/passwordResetComplete.html'), name='passwordResetComplete'),
    path('deactivateAccount/', views.deactivateAccountView, name="deactivateAccount"),
    path('deleteAccount/', views.deleteAccountView, name="deleteAccount"),
    path('activate/<uidb64>/<token>/', views.activateUserView, name='activate'),
    path('successfulEmailActivation/', views.successfulEmailActivationView, name="successfulEmailActivation"),
    path('unSuccessfulEmailActivation/', views.unSuccessfulEmailActivationView, name="unSuccessfulEmailActivation"),
]
