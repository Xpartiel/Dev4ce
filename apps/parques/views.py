from django.shortcuts import render
from django.db.models import Sum

from .models import Parque
from .mapas import construir_mapa


def landing(request):
    parques = Parque.objects.filter(activo=True)

    totals = parques.aggregate(
        cabanas=Sum('capacidad_max_cabana'),
        camping=Sum('capacidad_max_camping'),
    )
    total_espacios = (totals['cabanas'] or 0) + (totals['camping'] or 0)

    return render(request, "parques/landing.html", {
        "mapa_html": construir_mapa(parques, con_enlaces=False, zoom=10),
        "destacados": parques[:3],
        "total_parques": parques.count(),
        "total_espacios": total_espacios,
        "noches_festival": 38,  # 26 jun – 2 ago 2026 inclusive
    })