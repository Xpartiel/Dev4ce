from django.shortcuts import render

from .models import Parque
from .mapas import construir_mapa


def landing(request):
    parques = Parque.objects.filter(activo=True)
    return render(request, "parques/landing.html", {
        "mapa_html": construir_mapa(parques, con_enlaces=False, zoom=10),
        "destacados": parques[:3],   # los 3 que se muestran en "Empieza por estos tres"
    })