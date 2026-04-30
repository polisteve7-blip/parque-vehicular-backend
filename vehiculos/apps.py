from django.apps import AppConfig


class VehiculosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vehiculos'

    def ready(self):
        import vehiculos.signals
# vehiculos/apps.py
from django.apps import AppConfig

class VehiculosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vehiculos'
    
    def ready(self):
        import vehiculos.signals