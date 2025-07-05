from twilio.rest import Client
from django.conf import settings

def send_whatsapp_message(to_number, message_body):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=to_number
        )
        print(f"Message WhatsApp envoyé avec succès à {to_number}: {message.sid}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi du message WhatsApp à {to_number}: {e}")
        return False