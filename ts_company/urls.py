from django.urls import path
from . import views

app_name = 'ts_company'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    path('agent/china/dashboard/', views.china_agent_dashboard, name='china_agent_dashboard'),
    path('agent/mali/dashboard/', views.mali_agent_dashboard, name='mali_agent_dashboard'),
    path('agent/chine/colis/register/', views.register_colis, name='register_colis'),
    path('agent/chine/colis/register/<int:lot_pk>/', views.register_colis, name='register_colis_in_lot'),
    path('prices/manage/', views.manage_shipping_prices, name='manage_shipping_prices'),
    path('colis/<int:pk>/update-status/', views.update_colis_status, name='update_colis_status'),
    path('agent/chine/lot/create/', views.create_lot, name='create_lot'),
    path('agent/chine/lot/<int:pk>/', views.lot_detail, name='lot_detail'),
    path('agent/chine/lot/<int:pk>/edit/', views.edit_lot, name='edit_lot'),
    path('agent/chine/lot/<int:pk>/close/', views.close_lot, name='close_lot'),
    path('lot/<int:pk>/admin-detail/', views.lot_admin_detail, name='lot_admin_detail'),
    path('lot/<int:pk>/delete/', views.delete_lot, name='delete_lot'),
    path('lots/manage/', views.manage_lots, name='manage_lots'), # Pour l'administrateur
    path('inventory/', views.inventory, name='inventory'), # Pour l'administrateur
    
    path('agent/mali/lots/manage/', views.mali_manage_lots, name='mali_manage_lots'),
    path('agent/mali/lot/<int:pk>/update-status/', views.update_lot_status_mali, name='update_lot_status_mali'),
    path('agent/mali/inventory/', views.mali_inventory, name='mali_inventory'),
    path('agent/mali/colis/<int:pk>/receptionne/', views.update_colis_receptionne, name='update_colis_receptionne'),
    path('agent/mali/lot/<int:pk>/detail/', views.lot_detail_mali, name='lot_detail_mali'),
    path('agent/mali/lot/inventory/', views.lot_inventory_mali, name='lot_inventory_mali'),
    path('users/manage/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('api/get_client_address/<int:client_id>/', views.get_client_address, name='get_client_address'),
    path('api/search_clients/', views.search_clients, name='search_clients'),
]
