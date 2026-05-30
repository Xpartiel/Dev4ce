from django import forms
from .models import Reservacion

class ReservacionForm(forms.ModelForm):

    class Meta:
        model = Reservacion

        fields = [
            "usuario",
            "parque",
            "folio",
            "checkin",
            "checkout",
            "huespedes",
            "tipo_hospedaje",
            "total",
            "estado",
            "comentarios",
        ]