from django.apps import AppConfig

class SgpiConfig(AppConfig):   
    default_auto_field = "django.db.models.BigAutoField"
    name = "sgpi"

    def ready(self):
        from . import signals  
