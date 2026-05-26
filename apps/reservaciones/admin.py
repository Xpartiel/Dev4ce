from django.contrib import admin
from .models import Reservacion

@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display  = ("folio", "perfil", "parque", "fecha_inicio", "fecha_fin", "estado")
    list_filter   = ("estado", "tipo_visita", "parque")
    search_fields = ("folio", "perfil__email")
    readonly_fields = ("folio", "fecha_registro")
