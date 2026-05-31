from django import forms
from .models import Parque

class ParqueForm(forms.ModelForm):
    class Meta:
        model = Parque
        fields = [
            "nombre",
            "slug",
            "estado",
            "descripcion",
            "direccion",
            "horario",
            "servicios",
            "latitud",
            "longitud",
            #"capacidad_total",
            "capacidad_max_cabana",
            "capacidad_max_camping",
            "tiene_cabanas",
            "precio_cabana",
            "precio_camping",
            "activo",
        ]