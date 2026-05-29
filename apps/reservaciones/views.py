from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date

from .models import Reservacion

# Criterio único de "reservación activa" (RF-08.1).
# Lo reutilizaremos en el dashboard para mantener consistencia.
ESTADOS_ACTIVOS = ("pendiente", "confirmada")
FESTIVAL_INICIO = date(2026, 6, 14)

@login_required
def dashboard_cliente(request):
    activas = (
        Reservacion.objects
        .filter(usuario=request.user, estado__in=ESTADOS_ACTIVOS)
        .select_related("parque")
        .order_by("checkin")
    )

    dias_para_festival = (FESTIVAL_INICIO - date.today()).days

    return render(request, "reservaciones/dashboard_cliente.html", {
        "proximas": activas[:2],          # solo las 2 más cercanas
        "total_activas": activas.count(),
        "dias_para_festival": dias_para_festival,
    })

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

@login_required
def reservar_paso_1(request, parque_id):
    return render(request, "reservaciones/reservar_paso_1.html", {
        "parque_id": parque_id
    })


@login_required
def reservar_paso_2(request, parque_id):
    return render(request, "reservaciones/reservar_paso_2.html", {
        "parque_id": parque_id
    })


@login_required
def reservar_paso_3(request, parque_id):
    return render(request, "reservaciones/reservar_paso_3.html", {
        "parque_id": parque_id
    })


@login_required
def reservacion_confirmada(request):
    return render(request, "reservaciones/reservacion_confirmada.html")

@login_required
def mis_reservaciones(request):
    reservaciones = (
        Reservacion.objects
        .filter(usuario=request.user, estado__in=ESTADOS_ACTIVOS)
        .select_related("parque")
        .order_by("checkin")
    )
    return render(request, "reservaciones/mis_reservaciones.html", {
        "reservaciones": reservaciones,
    })


@login_required
def detalle_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("parque"),
        id=reservacion_id,
        usuario=request.user,
    )
    return render(request, "reservaciones/detalle_reservacion.html", {
        "reservacion": reservacion,
    })

@login_required
def mi_perfil(request):
    total_reservaciones = Reservacion.objects.filter(usuario=request.user).count()
    return render(request, "reservaciones/mi_perfil.html", {
        "total_reservaciones": total_reservaciones,
    })

def solo_admin(user):
    return user.is_authenticated and getattr(user, "tipoAdministrador", False)

@user_passes_test(solo_admin, login_url="login")
def admin_dashboard(request):
    return render(request, "reservaciones/admin_dashboard.html")

@user_passes_test(solo_admin, login_url="login")
def admin_parques(request):
    return render(request, "reservaciones/admin_parques.html")


@user_passes_test(solo_admin, login_url="login")
def admin_reservaciones(request):
    return render(request, "reservaciones/admin_reservaciones.html")


@user_passes_test(solo_admin, login_url="login")
def admin_calendario(request):

    dias_calendario = []

    for i in range(1, 29):

        if i in [2, 9, 16, 23]:
            estado = "maintenance"
            texto = "mantenimiento"

        elif i in [4, 14, 24, 27]:
            estado = "full"
            texto = "120/120"

        elif i in [3, 13, 19, 26]:
            estado = "few"
            texto = "102/120"

        else:
            estado = "free"
            texto = "48/120"

        dias_calendario.append({
            "numero": i,
            "estado": estado,
            "texto": texto,
        })

    return render(request, "reservaciones/admin_calendario.html", {
        "dias_calendario": dias_calendario
    })


@user_passes_test(solo_admin, login_url="login")
def admin_reportes(request):
    return render(request, "reservaciones/admin_reportes.html")