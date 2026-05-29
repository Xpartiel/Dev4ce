from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date
from .models import DisponibilidadParque
from apps.parques.models import Parque
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
    total_reservaciones = Reservacion.objects.count()

    ingresos = sum(
        reservacion.total
        for reservacion in Reservacion.objects.all()
    )

    total_parques = Parque.objects.count()

    cancelaciones = Reservacion.objects.filter(
        estado="cancelada"
    ).count()

    reservaciones_recientes = Reservacion.objects.select_related(
        "parque"
    )[:5]

    return render(request, "reservaciones/admin_dashboard.html", {

        "total_reservaciones": total_reservaciones,
        "ingresos": ingresos,
        "total_parques": total_parques,
        "cancelaciones": cancelaciones,
        "reservaciones_recientes": reservaciones_recientes,

    })

@user_passes_test(solo_admin, login_url="login")
def admin_parques(request):
    parques = Parque.objects.all()

    return render(request, "reservaciones/admin_parques.html", {
        "parques": parques
    })


@user_passes_test(solo_admin, login_url="login")
def admin_reservaciones(request):
    reservaciones = Reservacion.objects.select_related(
        "parque",
        "usuario"
    ).all()

    return render(request, "reservaciones/admin_reservaciones.html", {
        "reservaciones": reservaciones
    })


@user_passes_test(solo_admin, login_url="login")
def admin_calendario(request):

    disponibilidades = DisponibilidadParque.objects.select_related(
        "parque"
    ).all()

    dias_calendario = []

    for disponibilidad in disponibilidades:

        estado_css = {
            "libre": "free",
            "pocos": "few",
            "agotado": "full",
            "mantenimiento": "maintenance",
        }.get(disponibilidad.estado, "free")

        dias_calendario.append({
            "numero": disponibilidad.fecha.day,
            "estado": estado_css,
            "texto": f"{disponibilidad.capacidad_disponible} disponibles",
        })

    return render(request, "reservaciones/admin_calendario.html", {
        "dias_calendario": dias_calendario
    })


@user_passes_test(solo_admin, login_url="login")
def admin_reportes(request):
    return render(request, "reservaciones/admin_reportes.html")