from django.core.management.base import BaseCommand
from django.utils import timezone
from ts_company.models import Colis
from ts_company.utils import send_whatsapp_message
from django.conf import settings

class Command(BaseCommand):
    help = 'Sends WhatsApp notifications for colis that have been marked for notification after lot closure.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting WhatsApp notification sending process...'))

        colis_to_notify = Colis.objects.filter(
            status=Colis.Status.EN_TRANSIT, # Only send for colis in transit
            notification_lot_closed_sent=False # Only send if notification hasn't been sent
        )

        if not colis_to_notify.exists():
            self.stdout.write(self.style.SUCCESS('No colis found requiring WhatsApp notifications.'))
            return

        for colis in colis_to_notify:
            try:
                client_phone_number = colis.client.phone_number
                # Ensure the phone number is in E.164 format (e.g., +22377123456)
                if client_phone_number.startswith('00'):
                    client_phone_number = '+' + client_phone_number[2:]
                elif not client_phone_number.startswith('+'):
                    # Assuming default country code if not present, adjust as needed
                    client_phone_number = '+223' + client_phone_number # Example for Mali
                
                message_body = (
                    f"Votre colis {colis.tracking_number} a été expédié de Chine et est maintenant en transit vers le Mali. "
                    f"Statut actuel: {colis.get_status_display()}. "
                    f"Prix estimé: {colis.estimated_price:.0f} F CFA."
                )
                if colis.image:
                    # Construct absolute URL for the image (assuming MEDIA_URL is configured)
                    # You might need to define SITE_URL in settings.py if not already done
                    # Example: SITE_URL = 'http://127.0.0.1:8000' or your production domain
                    image_url = f"{settings.SITE_URL}{colis.image.url}" 
                    message_body += f" Voir l'image: {image_url}"

                send_whatsapp_message(client_phone_number, message_body)
                colis.notification_lot_closed_sent = True
                colis.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully sent WhatsApp notification for colis {colis.tracking_number}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to send WhatsApp notification for colis {colis.tracking_number}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('WhatsApp notification sending process completed.'))
