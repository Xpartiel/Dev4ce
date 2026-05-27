from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_cliente(request):
    return render(request, "reservaciones/dashboard_cliente.html")

@login_required
def mapa_cliente(request):
    return render(request, "reservaciones/mapa_cliente.html")