from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('registerHome/', views.registerHomeView),
    path('studentRegister/', views.studentRegisterView),
    path('studentSuccessfulRegister/', views.studentSuccessfulRegisterView),
    path('landlordRegister/', views.landlordRegisterView),
    path('landlordSuccessfulRegister/', views.landlordSuccessfulRegisterView),
    path('login/', views.loginView, name="login"),
    path('logout/', views.logoutView, name="logout"),
    path('passwordReset/', views.ResetPasswordView.as_view(), name="passwordReset"),
    path('passwordResetConfirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/passwordResetConfirm.html'), name='passwordResetConfirm'),
    path('passwordResetComplete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/passwordResetComplete.html'), name='passwordResetComplete'),
    re_path(r'^activateUser/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activateUser, name="activate"),
]
