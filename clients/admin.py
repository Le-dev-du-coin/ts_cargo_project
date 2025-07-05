from django.contrib import admin
from .models import ClientProfile

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line1', 'city', 'country')
    search_fields = ('user__phone_number', 'user__first_name', 'user__last_name', 'city', 'country')