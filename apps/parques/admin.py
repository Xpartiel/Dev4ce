from django.contrib import admin
from .models import Parque


@admin.register(Parque)
class ParqueAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "estado",
        "capacidad_total",
        "precio_cabana",
        "precio_camping",
        "activo",
    )

    list_filter = ("estado", "activo")

    search_fields = ("nombre", "estado", "slug")