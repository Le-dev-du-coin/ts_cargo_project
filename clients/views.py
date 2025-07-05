from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ts_company.models import Colis

@login_required(login_url='authentication:client_login')
def client_dashboard(request):
    user_colis = Colis.objects.filter(client=request.user)
    colis_en_attente_chine_count = user_colis.filter(status=Colis.Status.EN_ATTENTE_CHINE).count()
    colis_en_transit_count = user_colis.filter(status=Colis.Status.EN_TRANSIT).count()
    colis_arrive_mali_count = user_colis.filter(status=Colis.Status.ARRIVE_MALI).count()
    colis_receptionne_count = user_colis.filter(status=Colis.Status.RECEPTIONNE).count()

    colis_aerien = user_colis.filter(shipping_method__in=[Colis.ShippingMethod.EXPRESS_AERIEN, Colis.ShippingMethod.NORMAL_AERIEN]).order_by('-date_creation')
    colis_maritime = user_colis.filter(shipping_method=Colis.ShippingMethod.MARITIME).order_by('-date_creation')

    # Check for new notifications (e.g., colis arrived in Mali)
    newly_arrived_colis = user_colis.filter(status=Colis.Status.ARRIVE_MALI, notified_client=False)
    for colis in newly_arrived_colis:
        messages.success(request, f"Votre colis {colis.tracking_number} est arrivé au Mali et est prêt à être récupéré !")
        colis.notified_client = True
        colis.save()

    context = {
        'colis_en_attente_chine_count': colis_en_attente_chine_count,
        'colis_en_transit_count': colis_en_transit_count,
        'colis_arrive_mali_count': colis_arrive_mali_count,
        'colis_receptionne_count': colis_receptionne_count,
        'colis_aerien': colis_aerien,
        'colis_maritime': colis_maritime,
    }
    return render(request, 'clients/client_dashboard.html', context)