from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .forms import UserCreationForm, ColisForm, ColisUpdateStatusForm, LotForm, UserEditForm
from .models import ShippingPrice, Colis, Lot
from .utils import send_whatsapp_message # Import the utility function
from django.db.models import Sum, Count, Q

User = get_user_model()

@login_required(login_url='authentication:admin_login')
def admin_dashboard(request):
    # Statistiques sur les colis
    total_colis = Colis.objects.count()
    colis_en_attente_chine = Colis.objects.filter(status=Colis.Status.EN_ATTENTE_CHINE).count()
    colis_en_transit = Colis.objects.filter(status=Colis.Status.EN_TRANSIT).count()
    colis_arrive_mali = Colis.objects.filter(status=Colis.Status.ARRIVE_MALI).count()

    # Calcul des montants
    total_amount = Colis.objects.aggregate(total=Sum('estimated_price'))['total'] or 0
    amount_en_attente_chine = Colis.objects.filter(status=Colis.Status.EN_ATTENTE_CHINE).aggregate(total=Sum('estimated_price'))['total'] or 0
    amount_en_transit = Colis.objects.filter(status=Colis.Status.EN_TRANSIT).aggregate(total=Sum('estimated_price'))['total'] or 0
    amount_arrive_mali = Colis.objects.filter(status=Colis.Status.ARRIVE_MALI).aggregate(total=Sum('estimated_price'))['total'] or 0

    # Statistiques sur les utilisateurs
    total_agents = User.objects.filter(role__in=[User.Role.AGENT_CHINE, User.Role.AGENT_MALI]).count()
    total_clients = User.objects.filter(role=User.Role.CLIENT).count()
    
    # Récupérer les utilisateurs pour la liste
    users = User.objects.all()

    context = {
        'total_colis': total_colis,
        'colis_en_attente_chine': colis_en_attente_chine,
        'colis_en_transit': colis_en_transit,
        'colis_arrive_mali': colis_arrive_mali,
        'total_amount': total_amount,
        'amount_en_attente_chine': amount_en_attente_chine,
        'amount_en_transit': amount_en_transit,
        'amount_arrive_mali': amount_arrive_mali,
        'total_agents': total_agents,
        'total_clients': total_clients,
        'users': users
    }
    return render(request, 'ts_company/admin_dashboard.html', context)

@login_required(login_url='authentication:agent_login')
def china_agent_dashboard(request):
    if request.user.role != User.Role.AGENT_CHINE:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')
    colis_enregistres = Colis.objects.filter(client__role='CLIENT').order_by('-date_creation') # Filtrer les colis enregistrés par l'agent Chine
    lots_ouverts = Lot.objects.filter(agent_createur=request.user, status=Lot.Status.OUVERT).order_by('-date_creation')
    context = {
        'colis_enregistres': colis_enregistres,
        'lots_ouverts': lots_ouverts
    }
    return render(request, 'ts_company/china_agent_dashboard.html', context)

@login_required(login_url='authentication:agent_login')
def mali_agent_dashboard(request):
    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')
    lots_en_attente = []
    all_lots = Lot.objects.filter(status=Lot.Status.FERME).order_by('-date_expedition')

    for lot in all_lots:
        total_colis_in_lot = Colis.objects.filter(lot=lot).count()
        colis_arrive_mali_in_lot = Colis.objects.filter(lot=lot, status=Colis.Status.ARRIVE_MALI).count()
        colis_receptionne_in_lot = Colis.objects.filter(lot=lot, status=Colis.Status.RECEPTIONNE).count()

        # Only include lots that are not fully received
        if total_colis_in_lot > colis_receptionne_in_lot:
            lots_en_attente.append({
                'lot': lot,
                'total_colis': total_colis_in_lot,
                'colis_arrive_mali': colis_arrive_mali_in_lot,
                'colis_receptionne': colis_receptionne_in_lot,
                'status_display': 'En Transit' if colis_arrive_mali_in_lot == 0 else 'Partiellement Arrivé'
            })

    context = {
        'lots_en_attente': lots_en_attente
    }
    return render(request, 'ts_company/mali_agent_dashboard.html', context)

from django.http import JsonResponse
from clients.models import ClientProfile

@login_required
def get_client_address(request, client_id):
    try:
        client_profile = ClientProfile.objects.get(user__id=client_id)
        address = f"{client_profile.address_line1 or ''}\n{client_profile.address_line2 or ''}\n{client_profile.city or ''}, {client_profile.country or ''}".strip()
        return JsonResponse({'address': address})
    except ClientProfile.DoesNotExist:
        return JsonResponse({'address': ''})

@login_required
def search_clients(request):
    query = request.GET.get('q', '')
    clients = []
    try:
        if query:
            # Search by phone number, first name, or last name
            users = User.objects.filter(
                Q(role=User.Role.CLIENT) &
                (Q(phone_number__icontains=query) |
                 Q(first_name__icontains=query) |
                 Q(last_name__icontains=query))
            )[:10] # Limit to 10 suggestions
            for user in users:
                clients.append({
                    'id': user.id,
                    'phone_number': user.phone_number,
                    'full_name': f"{user.first_name} {user.last_name}".strip()
                })
        return JsonResponse({'clients': clients})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='authentication:admin_login')
def create_user(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Check if it's an AJAX request
                return JsonResponse({'success': True, 'message': "L'utilisateur a été créé avec succès."}, status=200)
            messages.success(request, "L'utilisateur a été créé avec succès.")
            return redirect(reverse('ts_company:manage_users')) # Rediriger vers la gestion des utilisateurs
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Check if it's an AJAX request
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = UserCreationForm()
    return render(request, 'ts_company/create_user.html', {'form': form})

@login_required(login_url='authentication:agent_login')
def register_colis(request, lot_pk=None):
    if request.user.role != 'AGENT_CHINE':
        messages.error(request, "Vous n'avez pas la permission d'enregistrer des colis.")
        return redirect(reverse('ts_company:china_agent_dashboard'))

    lot_instance = None
    if lot_pk:
        lot_instance = get_object_or_404(Lot, pk=lot_pk, agent_createur=request.user, status=Lot.Status.OUVERT)

    if request.method == 'POST':
        form = ColisForm(request.POST, request.FILES, user=request.user, lot_instance=lot_instance)
        if form.is_valid():
            colis = form.save(commit=False)
            if lot_instance:
                colis.lot = lot_instance
            # If delivery_address is provided in the form, use it. Otherwise, try to get from client profile.
            if not colis.delivery_address and colis.client and hasattr(colis.client, 'client_profile'):
                client_profile = colis.client.client_profile
                if client_profile.address_line1:
                    colis.delivery_address = f"{client_profile.address_line1}\n{client_profile.address_line2 or ''}\n{client_profile.city or ''}, {client_profile.country or ''}".strip()
            colis.save()

            # Send WhatsApp notification
            client_phone_number = colis.client.phone_number
            # Ensure the phone number is in E.164 format (e.g., +22377123456)
            # You might need to add logic to format the number if it's not already in E.164
            # For example, if numbers are stored as 00223..., convert to +223...
            if client_phone_number.startswith('00'):
                client_phone_number = '+' + client_phone_number[2:]
            elif not client_phone_number.startswith('+'):
                # Assuming default country code if not present, adjust as needed
                client_phone_number = '+223' + client_phone_number # Example for Mali

            message_body = f"Votre colis {colis.tracking_number} a été enregistré en Chine. Statut: {colis.get_status_display()} et le prix estimé est de {colis.estimated_price:.0f} F CFA."
            if colis.image:
                # Construct absolute URL for the image
                image_url = request.build_absolute_uri(colis.image.url)
                message_body += f" Voir l'image: {image_url}"
            
            send_whatsapp_message(client_phone_number, message_body)

            messages.success(request, f"Colis {colis.tracking_number} enregistré avec succès.")
            if lot_instance:
                return redirect(reverse('ts_company:lot_detail', kwargs={'pk': lot_instance.pk}))
            else:
                return redirect(reverse('ts_company:china_agent_dashboard'))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ColisForm(user=request.user, lot_instance=lot_instance)
    return render(request, 'ts_company/register_colis.html', {'form': form, 'lot_instance': lot_instance})

@login_required(login_url='authentication:admin_login')
def manage_shipping_prices(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    if request.method == 'POST':
        try:
            for key, value in request.POST.items():
                if key.startswith('price_unit_'):
                    pk = key.replace('price_unit_', '')
                    price_obj = ShippingPrice.objects.get(pk=pk)
                    new_price_unit = float(value)
                    if new_price_unit < 0:
                        return JsonResponse({'success': False, 'message': "Le prix par unité ne peut pas être négatif."}, status=400)
                    price_obj.price_unit = new_price_unit
                    price_obj.save()
                elif key.startswith('min_charge_weight_'):
                    pk = key.replace('min_charge_weight_', '')
                    price_obj = ShippingPrice.objects.get(pk=pk)
                    new_min_charge_weight = float(value)
                    if new_min_charge_weight < 0:
                        return JsonResponse({'success': False, 'message': "La charge minimale ne peut pas être négative."}, status=400)
                    price_obj.min_charge_weight = new_min_charge_weight
                    price_obj.save()
            return JsonResponse({'success': True, 'message': "Les prix ont été mis à jour avec succès."}, status=200)
        except ValueError:
            return JsonResponse({'success': False, 'message': "Valeur invalide fournie."}, status=400)
        except ShippingPrice.DoesNotExist:
            return JsonResponse({'success': False, 'message': "Méthode d'expédition non trouvée."}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Une erreur inattendue est survenue: {str(e)}"}, status=500)

    shipping_prices = ShippingPrice.objects.all()
    context = {
        'shipping_prices': shipping_prices
    }
    return render(request, 'ts_company/manage_shipping_prices.html', context)

@login_required(login_url='authentication:agent_login')
def update_colis_status(request, pk):
    colis = get_object_or_404(Colis, pk=pk)

    if request.user.role != 'AGENT_MALI':
        messages.error(request, "Vous n'avez pas la permission de mettre à jour le statut des colis.")
        return redirect(reverse('ts_company:mali_agent_dashboard'))

    if request.method == 'POST':
        form = ColisUpdateStatusForm(request.POST, instance=colis)
        if form.is_valid():
            colis = form.save(commit=False)
            if colis.status == Colis.Status.ARRIVE_MALI:
                colis.date_arrivee = timezone.now()
            colis.save()
            messages.success(request, f"Statut du colis {colis.tracking_number} mis à jour avec succès.")
            return redirect(reverse('ts_company:mali_agent_dashboard'))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ColisUpdateStatusForm(instance=colis)
    
    context = {
        'form': form,
        'colis': colis
    }
    return render(request, 'ts_company/update_colis_status.html', context)

@login_required(login_url='authentication:agent_login')
def create_lot(request):
    if request.user.role != 'AGENT_CHINE':
        messages.error(request, "Vous n'avez pas la permission de créer un lot.")
        return redirect(reverse('ts_company:china_agent_dashboard'))

    if request.method == 'POST':
        form = LotForm(request.POST)
        if form.is_valid():
            lot = form.save(commit=False)
            lot.agent_createur = request.user
            lot.save()
            messages.success(request, f"Lot {lot.numero_lot} créé avec succès.")
            return redirect(reverse('ts_company:china_agent_dashboard')) # Rediriger vers la liste des lots ou le dashboard
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = LotForm()
    return render(request, 'ts_company/create_lot.html', {'form': form})

@login_required(login_url='authentication:agent_login')
def lot_detail(request, pk):
    lot = get_object_or_404(Lot, pk=pk)
    colis_in_lot = Colis.objects.filter(lot=lot)

    if request.user.role != 'AGENT_CHINE':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:china_agent_dashboard'))

    # Handle ColisForm submission within lot_detail
    if request.method == 'POST':
        form = ColisForm(request.POST, request.FILES, initial={'agent_createur': request.user, 'lot': lot}, lot_instance=lot)
        if form.is_valid():
            colis = form.save(commit=False)
            colis.lot = lot # Ensure colis is linked to this lot
            colis.save()
            messages.success(request, f"Colis {colis.tracking_number} enregistré dans le lot {lot.numero_lot} avec succès.")
            return redirect(reverse('ts_company:lot_detail', kwargs={'pk': lot.pk}))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ColisForm(initial={'agent_createur': request.user, 'lot': lot}, lot_instance=lot)

    context = {
        'lot': lot,
        'colis_in_lot': colis_in_lot,
        'form': form
    }
    return render(request, 'ts_company/lot_detail.html', context)

@login_required(login_url='authentication:admin_login')
def edit_user(request, pk):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'utilisateur {user.phone_number} a été mis à jour avec succès.")
            return redirect(reverse('ts_company:manage_users'))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = UserEditForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user # Renamed to avoid conflict with 'user' in template context
    }
    return render(request, 'ts_company/edit_user.html', context)

@login_required(login_url='authentication:admin_login')
def delete_user(request, pk):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"L'utilisateur {user.phone_number} a été supprimé avec succès.")
        return redirect(reverse('ts_company:manage_users'))
    
    context = {
        'user_obj': user
    }
    return render(request, 'ts_company/delete_user_confirm.html', context)



@login_required(login_url='authentication:agent_login')
def edit_lot(request, pk):
    if request.user.role != 'AGENT_CHINE':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:china_agent_dashboard'))

    lot = get_object_or_404(Lot, pk=pk)

    if request.method == 'POST':
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le lot {lot.numero_lot} a été mis à jour avec succès.")
            return redirect(reverse('ts_company:china_agent_dashboard')) # Rediriger vers le dashboard agent chine
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = LotForm(instance=lot)
    
    context = {
        'form': form,
        'lot': lot
    }
    return render(request, 'ts_company/edit_lot.html', context)

@login_required(login_url='authentication:agent_login')
def close_lot(request, pk):
    if request.user.role != 'AGENT_CHINE':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:china_agent_dashboard'))

    lot = get_object_or_404(Lot, pk=pk)

    if request.method == 'POST':
        lot.status = Lot.Status.FERME
        lot.date_expedition = timezone.now()
        lot.save()
        # Update status of all colis in the lot to EN_TRANSIT and mark for notification
        Colis.objects.filter(lot=lot).update(status=Colis.Status.EN_TRANSIT, notification_lot_closed_sent=False)
        messages.success(request, f"Le lot {lot.numero_lot} a été fermé et expédié avec succès. Les notifications WhatsApp seront envoyées sous peu.")
        return redirect(reverse('ts_company:china_agent_dashboard'))
    
    context = {
        'lot': lot
    }
    return render(request, 'ts_company/close_lot_confirm.html', context)

@login_required(login_url='authentication:admin_login')
def lot_admin_detail(request, pk):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    lot = get_object_or_404(Lot, pk=pk)
    colis_in_lot = Colis.objects.filter(lot=lot)

    context = {
        'lot': lot,
        'colis_in_lot': colis_in_lot
    }
    return render(request, 'ts_company/lot_admin_detail.html', context)

@login_required(login_url='authentication:admin_login')
def delete_lot(request, pk):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    lot = get_object_or_404(Lot, pk=pk)
    if request.method == 'POST':
        lot.delete()
        messages.success(request, f"Le lot {lot.numero_lot} a été supprimé avec succès.")
        return redirect(reverse('ts_company:manage_lots'))
    
    context = {
        'lot': lot
    }
    return render(request, 'ts_company/delete_lot_confirm.html', context)

@login_required(login_url='authentication:admin_login')
def inventory(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    colis = Colis.objects.all().order_by('-date_creation')
    context = {
        'colis': colis
    }
    return render(request, 'ts_company/inventory.html', context)

@login_required(login_url='authentication:admin_login')
def manage_lots(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    lots = Lot.objects.all().order_by('-date_creation')
    context = {
        'lots': lots
    }
    return render(request, 'ts_company/manage_lots.html', context)

@login_required(login_url='authentication:admin_login')
def manage_users(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse('ts_company:admin_dashboard'))

    users = User.objects.all().order_by('date_joined')
    creation_form = UserCreationForm() # Instancier le formulaire de création d'utilisateur
    context = {
        'users': users,
        'creation_form': creation_form # Passer le formulaire au contexte
    }
    return render(request, 'ts_company/manage_users.html', context)

@login_required(login_url='authentication:agent_login')
def mali_manage_lots(request):
    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')

    lots = Lot.objects.filter(status=Lot.Status.FERME).order_by('date_expedition') # Lots fermés, triés par date d'expédition
    context = {
        'lots': lots
    }
    return render(request, 'ts_company/mali_manage_lots.html', context)

@login_required(login_url='authentication:agent_login')
def update_lot_status_mali(request, pk):
    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')

    lot = get_object_or_404(Lot, pk=pk)

    if request.method == 'POST':
        # Mettre à jour le statut de tous les colis du lot à ARRIVE_MALI
        Colis.objects.filter(lot=lot).update(status=Colis.Status.ARRIVE_MALI, date_arrivee=timezone.now())
        messages.success(request, f"Tous les colis du lot {lot.numero_lot} ont été marqués comme 'Arrivé au Mali'.")
        return redirect(reverse('ts_company:mali_manage_lots'))
    
    context = {
        'lot': lot
    }
    return render(request, 'ts_company/update_lot_status_mali_confirm.html', context)

@login_required(login_url='authentication:agent_login')
def mali_inventory(request):
    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')

    colis = Colis.objects.filter(status__in=[Colis.Status.ARRIVE_MALI, Colis.Status.RECEPTIONNE]).order_by('-date_arrivee')
    context = {
        'colis': colis
    }
    return render(request, 'ts_company/mali_inventory.html', context)

@login_required(login_url='authentication:agent_login')
def lot_detail_mali(request, pk):
    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')

    lot = get_object_or_404(Lot, pk=pk)
    colis_in_lot = Colis.objects.filter(lot=lot).order_by('tracking_number')

    context = {
        'lot': lot,
        'colis_in_lot': colis_in_lot
    }
    return render(request, 'ts_company/lot_detail_mali.html', context)

@login_required(login_url='authentication:agent_login')
def update_colis_receptionne(request, pk):
    colis = get_object_or_404(Colis, pk=pk)

    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Vous n'avez pas la permission de mettre à jour le statut des colis.")
        return redirect(reverse('ts_company:mali_agent_dashboard'))

    if request.method == 'POST':
        colis.status = Colis.Status.RECEPTIONNE
        colis.save()
        messages.success(request, f"Colis {colis.tracking_number} marqué comme 'Réceptionné' avec succès.")
        return redirect(reverse('ts_company:mali_inventory'))
    
    context = {
        'colis': colis
    }
    return render(request, 'ts_company/update_colis_receptionne_confirm.html', context)

@login_required(login_url='authentication:agent_login')
def lot_inventory_mali(request):
    if request.user.role != User.Role.AGENT_MALI:
        messages.error(request, "Accès non autorisé.")
        return redirect('authentication:login')

    lots = Lot.objects.all().order_by('-date_creation')
    inventory_data = []

    for lot in lots:
        total_colis = Colis.objects.filter(lot=lot).count()
        colis_receptionnes = Colis.objects.filter(lot=lot, status=Colis.Status.RECEPTIONNE).count()
        
        inventory_data.append({
            'lot': lot,
            'total_colis': total_colis,
            'colis_receptionnes': colis_receptionnes,
            'all_received': total_colis > 0 and total_colis == colis_receptionnes
        })

    context = {
        'inventory_data': inventory_data
    }
    return render(request, 'ts_company/lot_inventory_mali.html', context)