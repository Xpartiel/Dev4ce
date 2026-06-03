from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Sum
from datetime import date, timedelta
import uuid
import folium
from django.urls import reverse
from apps.parques.forms import ParqueForm
from datetime import date, datetime, timedelta
from .forms import ReservacionForm
from .models import DisponibilidadParque, Reservacion
from apps.parques.models import Parque
from apps.parques.mapas import construir_mapa
import calendar


# Criterio único de "reservación activa" (RF-08.1).
# Lo reutilizaremos en el dashboard para mantener consistencia.
ESTADOS_ACTIVOS = ("pendiente", "confirmada")
FESTIVAL_INICIO = date(2026, 6, 26)
FESTIVAL_FIN    = date(2026, 8, 2)   # ajustar a la finalizacion del festival

# -------------------------------------------------------------------------------------------------------
# Funciones auxiliares

def validar_reservacion(parque, checkin, checkout, tipo, huespedes):
    """
    Devuelve una diccionario de errores (strings). Lista vacía = todo valido.
      1. checkin debe ser dentro de la temporada.
      2. checkin no puede caer en martes.
      3. Si tipo_hospedaje es 'cabana', el parque debe tener cabañas.
      4. huespedes no puede superar la capacidad máxima del tipo.
      5. checkout debe ser posterior a checkin.
      6. Verifica si el usuario ya tiene una reservacion activa para esas fechas (confirmada).
    """
    errores = {}

    # 1. Check-in dentro de la temporada
    if checkin < FESTIVAL_INICIO or checkin > FESTIVAL_FIN: 
        errores['checkin'] = (
            f"Solo reservaciones entre "
            f"{FESTIVAL_INICIO.strftime('%d/%m/%Y')} y "
            f"{FESTIVAL_FIN.strftime('%d/%m/%Y')}."
        )
    elif checkout < FESTIVAL_INICIO or checkout > FESTIVAL_FIN:
        errores['checkout'] = (
            f"Solo se permiten reservaciones entre "
            f"{FESTIVAL_INICIO.strftime('%d/%m/%Y')} y "
            f"{FESTIVAL_FIN.strftime('%d/%m/%Y')}."
        )
    # 2. Check-in no puede caer en martes (cambiar a 1)
    elif checkin.weekday() == 0:
        errores['checkin'] = "Las reservaciones no pueden realizarse los dias martes. Nos encontramos en mantenimiento"
    
    # 3. Verificar el tipo hospedaje de los parques
    if tipo == "cabana" and not parque.tiene_cabanas:
        errores['tipo'] = f"{parque.nombre} no tiene cabañas disponibles."

    # 3.1 Verificar que haya elegido alguna opcion de hospedaje
    elif not tipo:
        errores['tipo'] = "Debe seleccionar un tipo de hospedaje."
    elif tipo not in ("cabana", "camping"):
        errores['tipo'] = "Debe seleccionar un tipo de hospedaje válido."    

    # 4. Verificar capacidad maxima del tipo
    cap_max = parque.capacidad_max_cabana if tipo == "cabana" else parque.capacidad_max_camping
    if cap_max and huespedes > cap_max:
        errores['huespedes'] = (
            f"El máximo de huéspedes para "
            f"{'cabaña' if tipo == 'cabana' else 'camping'} "
            f"es {cap_max}."
        )

    # 5. Check-out posterior a check-in 
    if checkout <= checkin:
        errores['checkout'] = "La fecha de check-out debe ser posterior a la fecha de check-in."
    
    #6. Verifica si el usuario ya tiene una reservacion activa para esas fechas (confirmada)
    if Reservacion.objects.filter(
        estado__in=ESTADOS_ACTIVOS,
        checkin__lte=checkout,
        checkout__gte=checkin,
    ).exists():
        errores['checkin'] = "Ya tienes una reservación activa que se solapa con estas fechas."
        errores['checkout'] = "Ya tienes una reservación activa que se solapa con estas fechas."

    return errores


def noches_reservadas(request):
    return sum(
        (reservacion.checkout - reservacion.checkin).days
        for reservacion in Reservacion.objects.filter(
            usuario=request.user,
            estado__in=ESTADOS_ACTIVOS
        )
    )


def parques_visitados(request):
    return (
        Reservacion.objects
        .filter(usuario=request.user, estado__in=ESTADOS_ACTIVOS)
        .values("parque")
        .distinct()
        .count()
    )


def total_invertido(request):
    return sum(
        reservacion.total
        for reservacion in Reservacion.objects.filter(
            usuario=request.user,
            estado__in=ESTADOS_ACTIVOS
        )
    )


# -------------------------------------------------------------------------------------------------------
# Vistas de cliente (para usuarios sin tipoAdministrador)


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
        "nochesEsteFestival": noches_reservadas(request),
        "total_activas": activas.count(),
        "dias_para_festival": dias_para_festival,
        "sugeridos": Parque.objects.filter(activo=True)[:3],
        "parques_visitados": parques_visitados(request),
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


# Pasos importantes para la reservacion exitosa


@login_required
def reservar_paso_1(request, parque_id):
    parque = get_object_or_404(Parque, pk=parque_id, activo=True)

    if request.method == "POST":
        checkin_str = request.POST.get("checkin", "")
        checkout_str = request.POST.get("checkout", "")
        tipo = request.POST.get("tipo", "")

        try: 
            huespedes_str = int(request.POST.get("huespedes", 1))
        except ValueError:
            huespedes_str = 1

        # Diccionario temporal para no perder los datos ingresados en caso de error
        datos_formulario = {
            "checkin": checkin_str,
            "checkout": checkout_str,
            "tipo": tipo,  
            "huespedes": huespedes_str
        }

        try:
            checkin = date.fromisoformat(checkin_str)
            checkout = date.fromisoformat(checkout_str)
        except ValueError:
            return render(request, "reservaciones/reservar_paso_1.html", {
                "parque": parque,
                "parque_id": parque_id,
                "errores": {"checkin": "Fecha invalida", "checkout": "Fecha invalida"},
                "reserva": datos_formulario,
            })
        

        # Si hay algun error de validacion, mostramos el formulario de nuevo con los errores y los datos ingresados previamente
        errores_validacion = validar_reservacion(parque, checkin, checkout, tipo, huespedes_str)

        if errores_validacion:
            return render(request, "reservaciones/reservar_paso_1.html", {
                "parque": parque,
                "parque_id": parque_id,
                "errores": errores_validacion,
                "reserva": datos_formulario,
            })
        
        # Si es valido, guardamos datos en sesión para usarlos en el paso 2 y 3
        request.session["reserva"] = {
            "parque_id": parque_id,
            "checkin": checkin_str,
            "checkout": checkout_str,
            "tipo": tipo,
            "huespedes": huespedes_str,
        }

        return redirect("reservar_paso_2", parque_id=parque_id)
    
    reserva_previa = request.session.get("reserva", {})
    
    # GET para mostrar formulario con datos reales del parque
    return render(request, "reservaciones/reservar_paso_1.html", {
        "parque": parque,
        "parque_id": parque_id,
        "reserva": reserva_previa,
    })


@login_required
def reservar_paso_2(request, parque_id):
    reserva = request.session.get("reserva", {})

    # Si no hay datos de reserva en la sesion, redirigimos al paso 1
    if not reserva or reserva.get("parque_id") != parque_id: 
        return redirect("reservar_paso_1", parque_id=parque_id)
    
    parque = get_object_or_404(Parque, pk=parque_id, activo=True)
    checkin = date.fromisoformat(reserva["checkin"])
    checkout = date.fromisoformat(reserva["checkout"])
    tipo = reserva["tipo"]
    huespedes = reserva["huespedes"]
    precio_noche = parque.precio_cabana if tipo == "cabana" else parque.precio_camping
    dias = (checkout - checkin).days
    total = precio_noche * dias 

    tiene_perfil_completo = hasattr(request.user, 'persona') 
    telefono_bd = request.user.persona.telefono if tiene_perfil_completo else ""

    if request.method == "POST":
        # Guardamos los comentarios adicionales, telefono y redirigimos al paso 3
        
        comentarios_entrada = request.POST.get("comentarios", "") 
        telefono_entrada = request.POST.get("telefono", "").replace(" ", "").replace("-", "")
        
        if not telefono_entrada.isdigit() or len(telefono_entrada) != 10:
            return render(request, "reservaciones/reservar_paso_2.html", {
                "parque": parque,
                "parque_id": parque_id,
                "checkin": checkin,
                "checkout": checkout,
                "tipo": tipo,
                "huespedes": huespedes,
                "total": total,
                "error_telefono": "Por favor ingresa un número de celular válido a 10 dígitos.",
                "telefono_previo": request.POST.get("telefono", ""), # Para no borrarle lo que escribió
                "comentarios_previos": comentarios_entrada 
            })
        
        reserva["comentarios"] = comentarios_entrada
        reserva["telefono"] = telefono_entrada
        request.session.modified = True  # Indicamos que la sesion ha sido modificada y forzamos guardado de sesion

        
        if tiene_perfil_completo and telefono_bd != telefono_entrada:
            request.user.persona.telefono = telefono_entrada
            request.user.persona.save()


        return redirect("reservar_paso_3", parque_id=parque_id)
    
    return render(request, "reservaciones/reservar_paso_2.html", {
        "parque": parque,
        "parque_id": parque_id,
        "checkin": checkin,
        "checkout": checkout,
        "tipo": tipo,
        "huespedes": huespedes,
        "total": total,
        "telefono_previo": telefono_bd,
    })


@login_required
def reservar_paso_3(request, parque_id):
    reserva = request.session.get("reserva", {})
    
    if not reserva or reserva.get("parque_id") != parque_id:
        return redirect("reservar_paso_1", parque_id=parque_id)
    
    parque = get_object_or_404(Parque, pk=parque_id, activo=True)
    checkin = date.fromisoformat(reserva["checkin"])
    checkout = date.fromisoformat(reserva["checkout"])
    tipo = reserva["tipo"]
    huespedes = reserva["huespedes"]
    precio_noche = parque.precio_cabana if tipo == "cabana" else parque.precio_camping
    dias = (checkout - checkin).days
    total = precio_noche * dias

    if request.method == "POST":
        # 1. Validacion inicial
        errores = validar_reservacion(parque, checkin, checkout, tipo, huespedes)
        if errores:
            return render(request, "reservaciones/reservar_paso_3.html", {
                "parque": parque,
                "parque_id": parque_id,
                "checkin": checkin,
                "checkout": checkout,
                "tipo": tipo,
                "huespedes": huespedes,
                "total": total,
                "error": " ".join(errores.values()), 
            })
        
        fechas = [checkin + timedelta(days=i) for i in range(dias)]
        capacidad_base = parque.capacidad_max_cabana if tipo == "cabana" else parque.capacidad_max_camping

        # 2. Seccion critica para que no se sobrevendan los espacios
        try:
            with transaction.atomic():
                #2.1. Garantizar que existan los registros antes de bloquear
                # No podemos bloquear espacios que aún no existen en la base de datos
                for fecha in fechas:
                    DisponibilidadParque.objects.get_or_create(
                        parque=parque,
                        fecha=fecha,
                        defaults={"capacidad_disponible": capacidad_base, "estado": "libre"}
                    )

                #2.2. Adquirir los locks
                # El order_by('fecha') es importante porque nos ayuda a evitar los deadlocks en la base de datos
                disponibilidades = DisponibilidadParque.objects.select_for_update().filter(
                    parque=parque,
                    fecha__in=fechas
                ).order_by('fecha')

                #3.3. Verificacion lineal dentro de la zona de exclusión mutua
                for disp in disponibilidades:
                    if disp.capacidad_disponible < huespedes:
                        # Lanzar excepción hace rollback automático de todo el bloque atomic
                        raise ValueError(f"Los lugares para el {disp.fecha.strftime('%d/%m/%Y')} acaban de agotarse.")
                
                #4.4. Mutacion de estado (Descontamos los lugares de forma segura)
                for disp in disponibilidades:
                    disp.capacidad_disponible -= huespedes
                    
                    if disp.capacidad_disponible == 0:
                        disp.estado = "agotado"
                    elif disp.capacidad_disponible <= 5:
                        disp.estado = "pocos"
                    else:
                        disp.estado = "libre"
                        
                    disp.save()

                #5.5. Creamos la reservacion
                # Solo insertamos si la mutacion de disponibilidad fue exitosa
                folio = f"LUZ-{date.today().year}-{uuid.uuid4().hex[:5].upper()}"
                reservacion = Reservacion.objects.create(
                    usuario=request.user,
                    parque=parque,
                    folio=folio,
                    checkin=checkin,
                    checkout=checkout,
                    huespedes=huespedes,
                    tipo_hospedaje=tipo,
                    total=total,
                    estado="confirmada",
                    comentarios=reserva.get("comentarios", ""),
                )

        except ValueError as e:
            # Si alguien mas gano la condicion de carrera, mostramos el error aqui.
            return render(request, "reservaciones/reservar_paso_3.html", {
                "parque": parque,
                "parque_id": parque_id,
                "checkin": checkin,
                "checkout": checkout,
                "tipo": tipo,
                "huespedes": huespedes,
                "total": total,
                "error": str(e),
            })

        # 3. Limpieza de sesion y redireccion 
        del request.session["reserva"]
        return redirect("reservacion_confirmada_folio", reservacion_id=reservacion.id)

    # GET para mostrar resumen de reserva y confirmación final
    return render(request, "reservaciones/reservar_paso_3.html", {
        "parque": parque,
        "parque_id": parque_id,
        "checkin": checkin,
        "checkout": checkout,
        "tipo": tipo,
        "huespedes": huespedes,
        "total": total,
    })         


# Informacion de confirmacion y gestion de reservaciones activas


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
def reservacion_confirmada_legacy(request):
    """Fallback por si algún template aún apunta a la URL sin ID."""
    return redirect("mis_reservaciones")


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


# Cancelaciones de reservaciones activas (confirmada). No se pueden cancelar reservaciones ya canceladas o finalizadas.

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
                if disponibilidad.capacidad_disponible == 0:
                    disponibilidad.estado = "agotado"
                elif disponibilidad.capacidad_disponible <= 5:
                    disponibilidad.estado = "pocos"
                else:
                    disponibilidad.estado = "libre"
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
        "nochesEsteFestival": noches_reservadas(request),
        "parques_visitados": parques_visitados(request),
        "total_invertido": total_invertido(request),
    })



# -------------------------------------------------------------------------------------------------------
# Vistas de administracion (solo para usuarios con tipoAdministrador=True)


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

    # Saludo según la hora del día
    hora = datetime.now().hour
    if hora < 12:
        saludo = "Buenos días"
    elif hora < 19:
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"

    # Nombre del administrador (nombre_completo vive en Persona)
    try:
        nombre_admin = request.user.persona.nombre_completo
    except Exception:
        nombre_admin = ""
    if not nombre_admin:
        nombre_admin = request.user.nick_name or request.user.username

    # Cuenta regresiva para la apertura del festival
    hoy = date.today()
    if hoy < FESTIVAL_INICIO:
        dias = (FESTIVAL_INICIO - hoy).days
        if dias == 1:
            mensaje_festival = "Falta 1 día para la apertura del festival."
        else:
            mensaje_festival = f"Faltan {dias} días para la apertura del festival."
    elif hoy <= FESTIVAL_FIN:
        mensaje_festival = "El festival está en curso."
    else:
        mensaje_festival = "El festival ha finalizado."

    # Gráfica "Reservaciones por parque" (datos reales) 
    reservaciones_por_parque = list(
        Parque.objects
        .annotate(num_reservaciones=Count("reservaciones"))
        .filter(num_reservaciones__gt=0)
        .order_by("-num_reservaciones")
        .values("nombre", "num_reservaciones")[:8]
    )
    max_reservaciones = max(
        (p["num_reservaciones"] for p in reservaciones_por_parque),
        default=1,
    )

    # Ocupación global (espacios reservados / capacidad total)
    capacidades = Parque.objects.filter(activo=True).aggregate(
        cab=Sum("capacidad_max_cabana"),
        camp=Sum("capacidad_max_camping"),
    )
    capacidad_total = (capacidades["cab"] or 0) + (capacidades["camp"] or 0)

    espacios_reservados = Reservacion.objects.filter(
        estado__in=ESTADOS_ACTIVOS
    ).aggregate(t=Sum("huespedes"))["t"] or 0

    if capacidad_total:
        porcentaje_ocupacion = round(espacios_reservados / capacidad_total * 100)
    else:
        porcentaje_ocupacion = 0

    return render(request, "reservaciones/admin_dashboard.html", {

        "active_admin": "panel",
        "total_reservaciones": total_reservaciones,
        "ingresos": ingresos,
        "total_parques": total_parques,
        "cancelaciones": cancelaciones,
        "reservaciones_recientes": reservaciones_recientes,

        # Header dinámico
        "saludo": saludo,
        "nombre_admin": nombre_admin,
        "mensaje_festival": mensaje_festival,

        # Gráfica
        "reservaciones_por_parque": reservaciones_por_parque,
        "max_reservaciones": max_reservaciones,

        # Ocupación
        "porcentaje_ocupacion": porcentaje_ocupacion,
        "espacios_reservados": espacios_reservados,
        "capacidad_total": capacidad_total,

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

    parques = (
        Parque.objects
        .filter(activo=True)
        .order_by("nombre")
    )

    if not parques.exists():
        return render(
            request,
            "reservaciones/admin_calendario.html",
            {
                "nombre_parques": [],
                "calendario": [],
            }
        )

    parque_id = request.GET.get("parque")

    try:
        parque_activo = parques.get(pk=parque_id)
    except (Parque.DoesNotExist, ValueError, TypeError):
        parque_activo = parques.first()

    hoy = date.today()

    anio = hoy.year
    mes = hoy.month

    disponibilidades = (
        DisponibilidadParque.objects
        .filter(
            parque=parque_activo,
            fecha__year=anio,
            fecha__month=mes
        )
    )

    disponibilidad_por_dia = {
        disponibilidad.fecha.day: disponibilidad
        for disponibilidad in disponibilidades
    }

    semanas = calendar.monthcalendar(anio, mes)

    calendario_mes = []

    for semana in semanas:

        fila = []

        for numero_dia in semana:

            if numero_dia == 0:
                fila.append(None)
                continue

            disponibilidad = disponibilidad_por_dia.get(numero_dia)

            if disponibilidad:

                estado_css = {
                    "libre": "free",
                    "pocos": "few",
                    "agotado": "full",
                    "mantenimiento": "maintenance",
                }.get(
                    disponibilidad.estado,
                    "free"
                )

                fila.append({
                    "numero": numero_dia,
                    "estado": estado_css,
                    "disponibles": disponibilidad.capacidad_disponible,
                    "capacidad": parque_activo.capacidad_total,
                })

            else:

                fila.append({
                    "numero": numero_dia,
                    "estado": "free",
                    "disponibles": parque_activo.capacidad_total,
                    "capacidad": parque_activo.capacidad_total,
                })

        calendario_mes.append(fila)
    
    return render(
        request,
        "reservaciones/admin_calendario.html",
        {
            "nombre_parques": parques,
            "parque_activo": parque_activo,
            "mes_actual": hoy.strftime("%B %Y"),
            "calendario": calendario_mes,
        }
    )


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