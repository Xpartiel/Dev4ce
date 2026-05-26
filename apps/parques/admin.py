from django.contrib.gis import admin
from .models import Parque, DisponibilidadParque

@admin.register(Parque)
class ParqueAdmin(admin.GISModelAdmin):
    list_display = ("nombre", "direccion", "capacidad_max_camping", "capacidad_max_cabania")
    search_fields = ("nombre", "direccion")

admin.site.register(DisponibilidadParque)
