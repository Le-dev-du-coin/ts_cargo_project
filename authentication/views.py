from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
import random
from datetime import timedelta

User = get_user_model()

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_sms(request, phone_number, otp_code):
    # Placeholder for Orange SMS API integration
    # In a real application, you would call the Orange SMS API here
    print(f"Sending OTP {otp_code} to {phone_number} via Orange SMS")
    messages.info(request, f"OTP {otp_code} sent to {phone_number}") # For testing purposes

def client_login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            if user.role == 'CLIENT':
                # Generate and store OTP
                otp_code = generate_otp()
                user.otp_code = otp_code
                user.otp_created_at = timezone.now()
                user.save()

                # Send OTP (placeholder)
                send_otp_sms(request, user.phone_number, otp_code)

                # Store phone number in session for OTP verification
                request.session['phone_number_for_otp'] = phone_number
                return redirect(reverse('authentication:otp_verify'))
            else:
                messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
                logout(request) # S'assurer que l'utilisateur est déconnecté
                return render(request, 'authentication/client_login.html')
        else:
            messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
    return render(request, 'authentication/client_login.html')

def otp_verify(request):
    phone_number = request.session.get('phone_number_for_otp')
    if not phone_number:
        messages.error(request, "Numéro de téléphone non trouvé. Veuillez vous reconnecter.")
        return redirect(reverse('client_login'))

    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé.")
        return redirect(reverse('client_login'))

    if request.method == 'POST':
        submitted_otp = request.POST.get('otp_code')

        # Check if OTP is valid and not expired (e.g., 5 minutes)
        if user.otp_code == submitted_otp and \
           user.otp_created_at and \
           (timezone.now() - user.otp_created_at) < timedelta(minutes=5):
            
            # Clear OTP fields after successful verification
            user.otp_code = None
            user.otp_created_at = None
            user.save()

            login(request, user)
            messages.success(request, "Connexion réussie !")
            return redirect(reverse('clients:client_dashboard'))
        else:
            messages.error(request, "Code OTP invalide ou expiré.")
    
    return render(request, 'authentication/otp_verify.html', {'phone_number': phone_number})

def register(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Ce numéro de téléphone est déjà enregistré.")
        else:
            user = User.objects.create_user(
                phone_number=phone_number,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='CLIENT'
            )
            messages.success(request, "Votre compte a été créé avec succès. Veuillez vous connecter.")
            return redirect(reverse('client_login'))
    return render(request, 'authentication/register.html')

def password_reset_request(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        try:
            user = User.objects.get(phone_number=phone_number)
            # Generate and store OTP for password reset
            otp_code = generate_otp()
            user.otp_code = otp_code
            user.otp_created_at = timezone.now()
            user.save()

            # Send OTP (placeholder)
            send_otp_sms(request, user.phone_number, otp_code)

            request.session['phone_number_for_reset'] = phone_number
            messages.info(request, "Un code OTP a été envoyé à votre numéro de téléphone.")
            return redirect(reverse('authentication:password_reset_confirm'))
        except User.DoesNotExist:
            messages.error(request, "Aucun utilisateur trouvé avec ce numéro de téléphone.")
    return render(request, 'authentication/password_reset_request.html')

def password_reset_confirm(request):
    phone_number = request.session.get('phone_number_for_reset')
    if not phone_number:
        messages.error(request, "Numéro de téléphone non trouvé pour la réinitialisation.")
        return redirect(reverse('authentication:password_reset_request'))

    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé.")
        return redirect(reverse('authentication:password_reset_request'))

    if request.method == 'POST':
        submitted_otp = request.POST.get('otp_code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif user.otp_code == submitted_otp and \
             user.otp_created_at and \
             (timezone.now() - user.otp_created_at) < timedelta(minutes=5):
            
            user.set_password(new_password)
            user.otp_code = None
            user.otp_created_at = None
            user.save()

            messages.success(request, "Votre mot de passe a été réinitialisé avec succès. Veuillez vous connecter.")
            return redirect(reverse('client_login'))
        else:
            messages.error(request, "Code OTP invalide ou expiré.")
    
    return render(request, 'authentication/password_reset_confirm.html', {'phone_number': phone_number})

def admin_login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            if user.role == 'ADMIN':
                login(request, user)
                messages.success(request, f"Bienvenue, {user.first_name}!")
                return redirect(reverse('ts_company:admin_dashboard'))
            else:
                messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
                logout(request)
                return render(request, 'authentication/admin_login.html')
        else:
            messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
    return render(request, 'authentication/admin_login.html')

def agent_login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            if user.role == 'AGENT_CHINE':
                login(request, user)
                messages.success(request, f"Bienvenue, {user.first_name}!")
                return redirect(reverse('ts_company:china_agent_dashboard'))
            elif user.role == 'AGENT_MALI':
                login(request, user)
                messages.success(request, f"Bienvenue, {user.first_name}!")
                return redirect(reverse('ts_company:mali_agent_dashboard'))
            else:
                messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
                logout(request)
                return render(request, 'authentication/agent_login.html')
        else:
            messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
    return render(request, 'authentication/agent_login.html')

def user_logout(request):
    if request.user.is_authenticated:
        role = request.user.role
        logout(request)
        messages.info(request, "Vous avez été déconnecté.")
        if role == 'ADMIN':
            return redirect(reverse('authentication:admin_login'))
        elif role == 'AGENT_CHINE' or role == 'AGENT_MALI':
            return redirect(reverse('authentication:agent_login'))
        else:
            return redirect(reverse('client_login'))
    return redirect(reverse('client_login'))