from django.apps import AppConfig

class ReservacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reservaciones"
    verbose_name = "Reservaciones"

    def ready(self):
        from . import signals  # noqa: registra el Observer
