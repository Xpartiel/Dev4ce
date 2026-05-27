from django.contrib import admin
from .models import DisponibilidadParque, Reservacion


@admin.register(DisponibilidadParque)
class DisponibilidadParqueAdmin(admin.ModelAdmin):
    list_display = (
        "parque",
        "fecha",
        "capacidad_disponible",
        "estado",
    )

    list_filter = ("estado", "fecha", "parque")

    search_fields = ("parque__nombre",)


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display = (
        "folio",
        "usuario",
        "parque",
        "checkin",
        "checkout",
        "huespedes",
        "tipo_hospedaje",
        "total",
        "estado",
    )

    list_filter = ("estado", "tipo_hospedaje", "parque")

    search_fields = (
        "folio",
        "usuario__email",
        "usuario__username",
        "parque__nombre",
    )