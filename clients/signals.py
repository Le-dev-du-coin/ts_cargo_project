from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import ClientProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_client_profile(sender, instance, created, **kwargs):
    if instance.role == 'CLIENT':
        if created:
            ClientProfile.objects.create(user=instance)
        instance.client_profile.save()
