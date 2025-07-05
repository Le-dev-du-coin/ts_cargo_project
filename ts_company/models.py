from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

def get_upload_path(instance, filename):
    return f'colis_images/{instance.tracking_number}/{filename}'

class Lot(models.Model):
    class Status(models.TextChoices):
        OUVERT = 'OUVERT', 'Ouvert'
        FERME = 'FERME', 'Fermé/Expédié'

    numero_lot = models.CharField(max_length=50, unique=True)
    agent_createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='lots_crees')
    date_creation = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OUVERT)
    date_expedition = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero_lot:
            today_str = timezone.now().strftime("%Y-%m-%d")
            # Find the highest sequential number for today's date
            last_lot_today = Lot.objects.filter(numero_lot__startswith=f"LOT-{today_str}").order_by('-numero_lot').first()
            if last_lot_today:
                try:
                    last_seq_num = int(last_lot_today.numero_lot.split('-')[-1])
                except (ValueError, IndexError):
                    last_seq_num = 0
            else:
                last_seq_num = 0
            self.numero_lot = f"LOT-{today_str}-{last_seq_num + 1:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_lot

class ShippingPrice(models.Model):
    class Method(models.TextChoices):
        EXPRESS_AERIEN = 'EXPRESS_AERIEN', 'Vol Express (Aérien)'
        NORMAL_AERIEN = 'NORMAL_AERIEN', 'Vol Normal (Aérien)'
        MARITIME = 'MARITIME', 'Bateau (Maritime)'

    class UnitType(models.TextChoices):
        KG = 'KG', 'Kilogramme'
        M3 = 'M3', 'Mètre Cube'

    method = models.CharField(max_length=20, choices=Method.choices, unique=True)
    price_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Prix par unité (Kg ou M³) en F CFA")
    unit_type = models.CharField(max_length=2, choices=UnitType.choices, default=UnitType.KG)
    min_charge_weight = models.DecimalField(max_digits=10, decimal_places=2, default=1.0, help_text="Poids/Volume minimum pour le calcul à l'unité")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_method_display()} - {self.price_unit} F CFA/{self.get_unit_type_display()}"

class Colis(models.Model):
    class Status(models.TextChoices):
        EN_ATTENTE_CHINE = 'EN_ATTENTE_CHINE', 'En attente en Chine'
        EN_TRANSIT = 'EN_TRANSIT', 'En transit'
        ARRIVE_MALI = 'ARRIVE_MALI', 'Arrivé au Mali'
        RECEPTIONNE = 'RECEPTIONNE', 'Réceptionné'

    class ShippingMethod(models.TextChoices):
        EXPRESS_AERIEN = 'EXPRESS_AERIEN', 'Vol Express (Aérien)'
        NORMAL_AERIEN = 'NORMAL_AERIEN', 'Vol Normal (Aérien)'
        MARITIME = 'MARITIME', 'Bateau (Maritime)'

    tracking_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='colis')
    description = models.TextField(blank=True)
    poids = models.DecimalField(max_digits=10, decimal_places=2, help_text="Poids en kg")
    longueur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Longueur en cm")
    largeur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Largeur en cm")
    hauteur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Hauteur en cm")
    image = models.ImageField(upload_to=get_upload_path, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EN_ATTENTE_CHINE)
    shipping_method = models.CharField(max_length=20, choices=ShippingMethod.choices)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Prix estimé en F CFA")
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name='colis')
    date_creation = models.DateTimeField(default=timezone.now)
    date_arrivee = models.DateTimeField(blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True, help_text="Adresse de livraison spécifique pour ce colis")
    notification_lot_closed_sent = models.BooleanField(default=False)
    notified_client = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            # Generate a unique tracking number
            last_colis = Colis.objects.all().order_by('id').last()
            if last_colis:
                last_id = last_colis.id
            else:
                last_id = 0
            self.tracking_number = f'TSC{timezone.now().strftime("%y%m%d")}{last_id + 1:04d}'

        # Calculate estimated price
        try:
            shipping_price_obj = ShippingPrice.objects.get(method=self.shipping_method)
            
            if shipping_price_obj.unit_type == ShippingPrice.UnitType.KG:
                # Logic for KG based pricing
                if self.poids >= shipping_price_obj.min_charge_weight:
                    self.estimated_price = self.poids * shipping_price_obj.price_unit
                else:
                    if self.poids > 0:
                        self.estimated_price = shipping_price_obj.price_unit / self.poids
                    else:
                        self.estimated_price = 0
            elif shipping_price_obj.unit_type == ShippingPrice.UnitType.M3:
                # Logic for M3 based pricing (volume in cubic meters)
                # Convert cm to meters: (longueur/100) * (largeur/100) * (hauteur/100)
                volume_m3 = (self.longueur / 100) * (self.largeur / 100) * (self.hauteur / 100)
                if volume_m3 >= shipping_price_obj.min_charge_weight:
                    self.estimated_price = volume_m3 * shipping_price_obj.price_unit
                else:
                    if volume_m3 > 0:
                        self.estimated_price = shipping_price_obj.price_unit / volume_m3
                    else:
                        self.estimated_price = 0

        except ShippingPrice.DoesNotExist:
            self.estimated_price = None # Or set a default/error value
            # Log this error in a real application

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Colis {self.tracking_number} pour {self.client.phone_number}'
