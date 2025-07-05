from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
]