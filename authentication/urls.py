from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('admin/login/', views.admin_login, name='admin_login'),
    path('agent/login/', views.agent_login, name='agent_login'),
    path('otp/verify/', views.otp_verify, name='otp_verify'),
    path('register/', views.register, name='register'),
    path('password-reset/request/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('logout/', views.user_logout, name='logout'),
]