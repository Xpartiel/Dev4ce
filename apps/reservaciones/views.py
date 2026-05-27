from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_cliente(request):
    return render(request, "reservaciones/dashboard_cliente.html")

@login_required
def mapa_cliente(request):
    return render(request, "reservaciones/mapa_cliente.html")

@login_required
def detalle_parque(request, parque_id):

    parque = {
        "id": parque_id,
        "nombre": "Santuario El Rosario",
        "estado": "Michoacán",
        "descripcion": "Un santuario rodeado de bosque, ideal para vivir una experiencia nocturna entre luciérnagas.",
        "precio": 850,
        "disponibles": 47,
        "servicios": [
            "Cabañas",
            "Camping",
            "Senderos guiados",
            "Estacionamiento",
            "Baños",
            "Zona de alimentos",
        ],
    }

    return render(request, "reservaciones/detalle_parque.html", {
        "parque": parque
    })