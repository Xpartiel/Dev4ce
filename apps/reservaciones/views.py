from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from datetime import date, timedelta
import uuid
import folium
from django.urls import reverse
from django.template.loader import render_to_string
from apps.parques.forms import ParqueForm
from .forms import ReservacionForm
from .models import DisponibilidadParque, Reservacion
from apps.parques.models import Parque
from apps.parques.mapas import construir_mapa

ESTADOS_ACTIVOS = ("pendiente", "confirmada")
FESTIVAL_INICIO = date(2026, 6, 14)


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
        "proximas": activas[:2],
        "total_activas": activas.count(),
        "dias_para_festival": dias_para_festival,
        "sugeridos": Parque.objects.filter(activo=True)[:3],
    })

@login_required
def mapa_cliente(request):
    parques = Parque.objects.filter(activo=True)
    return render(request, "reservaciones/mapa_cliente.html", {
        "mapa_html": construir_mapa(parques, con_enlaces=True),
        "parques": parques,
    })

@login_required
def detalle_parque(request, parque_id):
    parque = get_object_or_404(Parque, pk=parque_id, activo=True)
    return render(request, "reservaciones/detalle_parque.html", {
        "parque": parque,
    })

@login_required
def reservar_paso_1(request, parque_id):
    parque = get_object_or_404(Parque, pk=parque_id, activo=True)

    if request.method == "GET" and request.GET.get("checkin"):
        # Guardar seleccion en la sesionn para usarla en el paso 3
        request.session["reserva"] = {
            "parque_id": parque_id,
            "checkin": request.GET.get("checkin"),
            "checkout": request.GET.get("checkout"),
            "tipo": request.GET.get("tipo", "camping"),
            "huespedes": int(request.GET.get("huespedes", 1)),
        }
        return redirect("reservar_paso_2", parque_id=parque_id)

    return render(request, "reservaciones/reservar_paso_1.html", {
        "parque": parque,
        "parque_id": parque_id,
    })


@login_required
def reservar_paso_2(request, parque_id):
    return render(request, "reservaciones/reservar_paso_2.html", {
        "parque_id": parque_id
    })


@login_required
def reservar_paso_3(request, parque_id):
    parque = get_object_or_404(Parque, pk=parque_id, activo=True)
    reserva = request.session.get("reserva", {})
    
    # Si no hay datos de reserva en la sesion, redirigimos al paso 1
    if not reserva or reserva.get("parque_id") != parque_id:
        return redirect("reservar_paso_1", parque_id=parque_id)
    
    checkin = date.fromisoformat(reserva["checkin"])
    checkout = date.fromisoformat(reserva["checkout"])
    tipo = reserva["tipo"]
    huespedes = reserva["huespedes"]


    # POST: Valida cupo fecha por fecha, crea reservacion, descuenta disponibilidad, envia correo de confirmacion y redirige 
    if request.method == "POST":
        # 1. Validamos disponibilidad y revisamos cada dia de la estadia
        dias = (checkout - checkin).days
        fechas = [checkin + timedelta(days=i) for i in range(dias)]

        sin_cupo = []
        for fecha in fechas:
            disponibilidad = DisponibilidadParque.objects.filter(
                parque = parque, fecha = fecha
                ).first()
            if disponibilidad and disponibilidad.capacidad_disponible < huespedes:
                sin_cupo.append(fecha)

        if sin_cupo: 
            return render(request, "reservaciones/reservar_paso_3.html", {
                "parque": parque,
                "parque_id": parque_id,
                "checkin": checkin,
                "checkout": checkout,
                "tipo": tipo,
                "huespedes": huespedes,
                "error": f"No hay cupo para {huespedes} huéspedes en las fechas: {', '.join(str(d) for d in sin_cupo)}"
            })
        
        # 2. Calculamos el precio

        precio_noche = parque.precio_cabana if tipo == "cabana" else parque.precio_camping
        total = precio_noche * dias

        # 3. Creamos la reservacion
        
        folio = f"LUZ-{date.today().year}-{uuid.uuid4().hex[:5].upper()}"
        reservacion = Reservacion.objects.create(
            usuario = request.user,
            parque = parque,
            checkin = checkin,
            checkout = checkout,
            huespedes = huespedes,
            tipo_hospedaje = tipo,
            total = total,
            estado = "confirmada",
            comentarios = request.POST.get("comentarios", ""),
        )

        # 4. Reducimos la disponibilidad de cada dia

        for fecha in fechas:
            disponibilidad, _ = DisponibilidadParque.objects.get_or_create(
                parque = parque,
                fecha = fecha, 
                defaults={"capacidad_disponible": parque.capacidad_max_cabana 
                          if tipo == "cabana" else parque.capacidad_max_camping},
            )
            disponibilidad.capacidad_disponible = max(0, disponibilidad.capacidad_disponible - huespedes)
            if disponibilidad.capacidad_disponible == 0:
                disponibilidad.estado = "agotado"
            elif disponibilidad.capacidad <= 5:
                disponibilidad.estado = "pocos"
            else: 
                disponibilidad.estado = "libre"
            disponibilidad.save()

        # 5. Enviamos correo de confirmacion

        asunto = f"Reservación confirmada - {folio}"
        cuerpo = (
            f"Hola {request.user.username}, \n\n"
            f"Su reservación para el parque {parque.nombre} ha sido confirmada.\n"
            f"Detalles de la reservación:\n"
            f"- Check-in: {checkin}\n"
            f"- Check-out: {checkout}\n"
            f"- Tipo: {tipo}\n"
            f"- Huéspedes: {huespedes}\n"
            f"- Total: ${total:.2f}\n\n"
            f"Gracias por elegirnos!"
        )

        send_mail(asunto, cuerpo, None, [request.user.email], fail_silently=True)

        # 6. Limpiamos datos de reserva en sesion y redirigimos a confirmacion
        del request.session ["reserva"]
        return redirect("reservacion_confirmada_folio", reservacion_id=reservacion.id)
    
    precio_noche = parque.precio_cabana if tipo == "cabana" else parque.precio_camping
    total = precio_noche * (checkout - checkin).days

    return render(request, "reservaciones/reservar_paso_3.html", {
        "parque": parque,
        "parque_id": parque_id,
        "checkin": checkin,
        "checkout": checkout,
        "tipo": tipo,
        "huespedes": huespedes,
        "total": total,
    })
            


@login_required
def reservacion_confirmada(request, reservacion_id):
    reservacion = get_object_or_404(
        Reservacion,
        id=reservacion_id,
        usuario=request.user,
        )
    return render(request, "reservaciones/reservacion_confirmada.html", {
        "reservacion": reservacion,
    })

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
def cancelar_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(
        Reservacion,
        id=reservacion_id,
        usuario=request.user,
        estado__in = ("pendiente", "confirmada") # Solo cancelamos las activas ya que las canceladas ya no se pueden modificar
    )

    if request.method == "POST":
        #1. Cambiamos estado de reservacion a cancelada
        reservacion.estado = "cancelada"
        reservacion.save()

        #2. Liberamos la disponibilidad de cada dia
        checkin = reservacion.checkin
        checkout = reservacion.checkout
        dias = (checkout - checkin).days
        fechas = [checkin + timedelta(days=i) for i in range(dias)]
        tipo = reservacion.tipo_hospedaje
        cap_max = (reservacion.parque.capacidad_max_cabana 
                   if tipo == "cabana" else reservacion.parque.capacidad_max_camping)
        
        for fecha in fechas:
            disponibilidad = DisponibilidadParque.objects.filter(
                parque = reservacion.parque, fecha = fecha
            ).first()

            if disponibilidad:
                disponibilidad.capacidad_disponible = min(
                    cap_max, disponibilidad.capacidad_disponible + reservacion.huespedes
                )
                if disponibilidad.capacidad_disponible == cap_max:
                    disponibilidad.estado = "libre"
                elif disponibilidad.capacidad_disponible <= 5:
                    disponibilidad.estado = "pocos"
                else:
                    disponibilidad.estado = "agotado"
                disponibilidad.save()

        #3. Enviar correo de cancelacion

        asunto = f"Reservación cancelada - {reservacion.folio}"
        cuerpo = (
            f"Hola {request.user.username}, \n\n"
            f"Su reservación para el parque {reservacion.parque.nombre} ha sido cancelada.\n"
            f"Detalles de la reservación cancelada:\n"
            f"- Check-in: {reservacion.checkin}\n"
            f"- Check-out: {reservacion.checkout}\n"
            f"- Tipo: {reservacion.tipo_hospedaje}\n"
            f"- Huéspedes: {reservacion.huespedes}\n"
            f"- Total: ${reservacion.total:.2f}\n\n"
            f"Si esta cancelación fue un error o desea reprogramar, por favor contáctenos lo antes posible."
        )
        send_mail(asunto, cuerpo, None, [request.user.email], fail_silently=True)
        return redirect("mis_reservaciones")
    
    # GET para redirigir (por seguridad)
    return redirect("detalle_reservacion", reservacion_id=reservacion_id)

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

        "active_admin": "panel",
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
def crear_reservacion(request):

    if request.method == "POST":

        form = ReservacionForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("admin_reservaciones")

    else:

        form = ReservacionForm()

    return render(
        request,
        "reservaciones/reservacion_form.html",
        {"form": form}
    )


@user_passes_test(solo_admin, login_url="login")
def editar_reservacion(request, reservacion_id):

    reservacion = get_object_or_404(
        Reservacion,
        pk=reservacion_id
    )

    if request.method == "POST":

        form = ReservacionForm(
            request.POST,
            instance=reservacion
        )

        if form.is_valid():
            form.save()
            return redirect("admin_reservaciones")

    else:

        form = ReservacionForm(
            instance=reservacion
        )

    return render(
        request,
        "reservaciones/reservacion_form.html",
        {
            "form": form,
            "reservacion": reservacion
        }
    )


@user_passes_test(solo_admin, login_url="login")
def eliminar_reservacion(request, reservacion_id):

    reservacion = get_object_or_404(
        Reservacion,
        pk=reservacion_id
    )

    reservacion.delete()

    return redirect("admin_reservaciones")


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

@user_passes_test(solo_admin, login_url="login")
def crear_parque(request):

    if request.method == "POST":
        form = ParqueForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("admin_parques")

    else:
        form = ParqueForm()

    return render(
        request,
        "reservaciones/parque_form.html",
        {"form": form}
    )

@user_passes_test(solo_admin, login_url="login")
def editar_parque(request, parque_id):

    parque = get_object_or_404(
        Parque,
        pk=parque_id
    )

    if request.method == "POST":

        form = ParqueForm(
            request.POST,
            instance=parque
        )

        if form.is_valid():
            form.save()
            return redirect("admin_parques")

    else:

        form = ParqueForm(
            instance=parque
        )

    return render(
        request,
        "reservaciones/parque_form.html",
        {
            "form": form,
            "parque": parque
        }
    )

@user_passes_test(solo_admin, login_url="login")
def eliminar_parque(request, parque_id):

    parque = get_object_or_404(
        Parque,
        pk=parque_id
    )

    parque.delete()

    return redirect("admin_parques")