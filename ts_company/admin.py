from django.contrib import admin
from .models import Lot, Colis, ShippingPrice

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ('numero_lot', 'agent_createur', 'date_creation', 'status')
    list_filter = ('status', 'date_creation')
    search_fields = ('numero_lot', 'agent_createur__phone_number')

@admin.register(Colis)
class ColisAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'client', 'poids', 'shipping_method', 'estimated_price', 'status', 'date_creation')
    list_filter = ('status', 'shipping_method', 'date_creation')
    search_fields = ('tracking_number', 'client__phone_number', 'description')
    readonly_fields = ('tracking_number', 'estimated_price') # estimated_price is calculated

@admin.register(ShippingPrice)
class ShippingPriceAdmin(admin.ModelAdmin):
    list_display = ('method', 'price_unit', 'min_charge_weight', 'last_updated')
    list_editable = ('price_unit', 'min_charge_weight')