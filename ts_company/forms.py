from django import forms
from django.contrib.auth import get_user_model
from .models import Colis, Lot

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    role = forms.ChoiceField(choices=User.Role.choices, label="Rôle", initial=User.Role.CLIENT)
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")

    class Meta:
        model = User
        fields = ('phone_number', 'first_name', 'last_name', 'role', 'password')
        labels = {
            'phone_number': "Numéro de téléphone",
            'first_name': "Prénom",
            'last_name': "Nom",
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = self.cleaned_data['role'] # Set role based on form selection
        if commit:
            user.save()
        return user

class ColisForm(forms.ModelForm):
    class Meta:
        model = Colis
        fields = ('client', 'description', 'poids', 'longueur', 'largeur', 'hauteur', 'image', 'shipping_method', 'lot', 'delivery_address') # Added delivery_address field
        labels = {
            'shipping_method': 'Méthode d\'expédition',
            'delivery_address': 'Adresse de livraison',
        }
        widgets = {
            'client': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'description': forms.Textarea(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'rows': 3}),
            'poids': forms.NumberInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'longueur': forms.NumberInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'largeur': forms.NumberInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'hauteur': forms.NumberInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'image': forms.FileInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'shipping_method': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'lot': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'delivery_address': forms.Textarea(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        lot_instance = kwargs.pop('lot_instance', None) # Pop lot_instance from kwargs
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = User.objects.filter(role=User.Role.CLIENT)
        
        if lot_instance:
            self.fields['lot'].initial = lot_instance
            self.fields['lot'].widget.attrs['disabled'] = 'disabled'
            self.fields['lot'].required = False # Not required if disabled
        else:
            # Filter lots by agent and status for regular ColisForm
            if user:
                self.fields['lot'].queryset = Lot.objects.filter(agent_createur=user, status=Lot.Status.OUVERT)
            else:
                self.fields['lot'].queryset = Lot.objects.none()

        # Pre-fill delivery_address if client is selected and has a profile
        if 'client' in self.initial and self.initial['client']:
            client_user = self.initial['client']
            if hasattr(client_user, 'client_profile') and client_user.client_profile.address_line1:
                self.fields['delivery_address'].initial = f"{client_user.client_profile.address_line1}\n{client_user.client_profile.address_line2 or ''}\n{client_user.client_profile.city or ''}, {client_user.client_profile.country or ''}".strip()


    def clean(self):
        cleaned_data = super().clean()
        shipping_method = cleaned_data.get('shipping_method')
        longueur = cleaned_data.get('longueur')
        largeur = cleaned_data.get('largeur')
        hauteur = cleaned_data.get('hauteur')

        if shipping_method == Colis.ShippingMethod.MARITIME:
            if not all([longueur, largeur, hauteur]):
                self.add_error(None, "Pour l'expédition maritime, la longueur, la largeur et la hauteur sont requises.")
        else:
            # Clear dimensions if not maritime to avoid saving irrelevant data
            cleaned_data['longueur'] = None
            cleaned_data['largeur'] = None
            cleaned_data['hauteur'] = None
        return cleaned_data

class ColisUpdateStatusForm(forms.ModelForm):
    class Meta:
        model = Colis
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict status choices for Mali agent
        self.fields['status'].choices = [
            (Colis.Status.ARRIVE_MALI, 'Arrivé au Mali'),
            (Colis.Status.RECEPTIONNE, 'Réceptionné'),
        ]

class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict status choices for Lot creation
        self.fields['status'].choices = [
            (Lot.Status.OUVERT, 'Ouvert'),
            (Lot.Status.FERME, 'Fermé/Expédié'),
        ]

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'role', 'is_active')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'role': forms.Select(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded'}),
        }