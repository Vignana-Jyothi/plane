from django.apps import AppConfig

class VJStartupsConfig(AppConfig):
    name = "plane.vj_startups"
    verbose_name = "VJ Startups"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        pass
