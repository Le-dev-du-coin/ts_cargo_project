from django.apps import AppConfig


class ClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clients'

    def ready(self):
        import clients.signals
