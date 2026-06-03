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
            "capacidad_max_cabana",
            "capacidad_max_camping",
            "tiene_cabanas",
            "precio_cabana",
            "precio_camping",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "admin-input"}),
            "slug": forms.TextInput(attrs={"class": "admin-input"}),
            "estado": forms.TextInput(attrs={"class": "admin-input"}),

            "descripcion": forms.Textarea(
                attrs={
                    "class": "admin-textarea",
                    "rows": 4,
                }
            ),

            "direccion": forms.TextInput(attrs={"class": "admin-input"}),
            "horario": forms.TextInput(attrs={"class": "admin-input"}),

            "servicios": forms.Textarea(
                attrs={
                    "class": "admin-textarea",
                    "rows": 4,
                }
            ),

            "latitud": forms.NumberInput(attrs={"class": "admin-input"}),
            "longitud": forms.NumberInput(attrs={"class": "admin-input"}),

            "capacidad_max_cabana": forms.NumberInput(
                attrs={"class": "admin-input"}
            ),

            "capacidad_max_camping": forms.NumberInput(
                attrs={"class": "admin-input"}
            ),

            "precio_cabana": forms.NumberInput(
                attrs={"class": "admin-input"}
            ),

            "precio_camping": forms.NumberInput(
                attrs={"class": "admin-input"}
            ),

            "tiene_cabañas": forms.CheckboxInput(
                attrs={"class": "admin-checkbox"}
            ),

            "activo": forms.CheckboxInput(
                attrs={"class": "admin-checkbox"}
            ),
        }