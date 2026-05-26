"""
ReservacionService — Facade / Service Layer.
Orquesta: validación (Strategy) + persistencia atómica + emisión de Signal (Observer).
"""
from datetime import timedelta
from django.db import transaction
from apps.parques.models import DisponibilidadParque, Parque
from .models import Reservacion, EstadoReservacion
from .rules import ContextoReserva, ReglasReservacion
from .states import estado_de
from .signals import reserva_creada, reserva_cancelada


class ReservacionService:
    """Facade."""

    def __init__(self):
        self.reglas = ReglasReservacion()

    # ---------------- RF-06 ----------------
    @transaction.atomic
    def crear(self, perfil, datos: dict) -> Reservacion:
        parque = Parque.objects.select_for_update().get(pk=datos["parque_id"])
        ctx = ContextoReserva(
            parque=parque,
            fecha_ini=datos["fecha_inicio"],
            fecha_fin=datos["fecha_fin"],
            tipo=datos["tipo_visita"],
            num_asistentes=datos["num_asistentes"],
        )
        self.reglas.validar_todas(ctx)

        # Descontar cupo por día (RF-06.7)
        d = ctx.fecha_ini
        while d <= ctx.fecha_fin:
            disp, _ = DisponibilidadParque.objects.select_for_update().get_or_create(
                parque=parque, fecha=d,
                defaults={
                    "cupo_camping": parque.capacidad_max_camping,
                    "cupo_cabania": parque.capacidad_max_cabania,
                },
            )
            disp.restar(ctx.tipo, ctx.num_asistentes)
            d += timedelta(days=1)

        reserva = Reservacion.objects.create(
            perfil=perfil,
            parque=parque,
            fecha_inicio=ctx.fecha_ini,
            fecha_fin=ctx.fecha_fin,
            num_asistentes=ctx.num_asistentes,
            tipo_visita=ctx.tipo,
            estado=EstadoReservacion.CONFIRMADA,
        )

        # Observer: dispara correo de confirmación (RF-07)
        transaction.on_commit(lambda: reserva_creada.send(
            sender=Reservacion, reserva=reserva))
        return reserva

    # ---------------- RF-09 ----------------
    @transaction.atomic
    def cancelar(self, reserva: Reservacion) -> None:
        if not reserva.puede_cancelar():
            raise ValueError("Esta reservación ya no puede cancelarse.")

        # Liberar cupo por día (RF-09.4)
        d = reserva.fecha_inicio
        while d <= reserva.fecha_fin:
            disp = DisponibilidadParque.objects.select_for_update().get(
                parque=reserva.parque, fecha=d)
            disp.liberar(reserva.tipo_visita, reserva.num_asistentes)
            d += timedelta(days=1)

        estado_de(reserva).cancelar(reserva)
        transaction.on_commit(lambda: reserva_cancelada.send(
            sender=Reservacion, reserva=reserva))

    # ---------------- RF-08 ----------------
    def listar_de(self, perfil):
        return Reservacion.objects.filter(perfil=perfil)
