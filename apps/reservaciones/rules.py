"""
Patrón Strategy — Reglas de reservación (RF-06.2 a 06.5 / RF-12.3).
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from apps.parques.models import Parque
from .models import TipoVisita


# ---------------- Contexto / DTO ----------------
@dataclass
class ContextoReserva:
    parque:          Parque
    fecha_ini:       date
    fecha_fin:       date
    tipo:            str       # "CABAÑA" | "CAMPING"
    num_asistentes:  int

    def dias(self):
        d = self.fecha_ini
        while d <= self.fecha_fin:
            yield d
            d += timedelta(days=1)


class ReglaInvalidaError(ValueError):
    """Se lanza cuando una regla rechaza la reserva."""


# ---------------- Strategy ----------------
class ReglaReservacion:
    def validar(self, ctx: ContextoReserva) -> None:
        raise NotImplementedError


class ReglaTemporada(ReglaReservacion):       # RF-06.2
    MESES_VALIDOS = {6, 7, 8}
    def validar(self, ctx):
        for d in ctx.dias():
            if d.month not in self.MESES_VALIDOS:
                raise ReglaInvalidaError(
                    "Solo se permiten reservaciones en junio, julio y agosto.")


class ReglaSinMartes(ReglaReservacion):       # RF-06.3
    def validar(self, ctx):
        for d in ctx.dias():
            if d.weekday() == 1:  # martes
                raise ReglaInvalidaError(
                    f"La estancia incluye un martes ({d}); no se permite por mantenimiento.")


class ReglaTipoVisita(ReglaReservacion):      # RF-06.4
    def validar(self, ctx):
        if ctx.tipo == TipoVisita.CABAÑA and not ctx.parque.tiene_cabanas():
            raise ReglaInvalidaError("Este parque no ofrece cabañas.")


class ReglaCupo(ReglaReservacion):            # RF-06.5 / RF-12.3
    def validar(self, ctx):
        if not ctx.parque.tiene_cupo(ctx.fecha_ini, ctx.fecha_fin, ctx.tipo, ctx.num_asistentes):
            raise ReglaInvalidaError(
                "No hay cupo disponible para las fechas y tipo seleccionados.")


@dataclass
class ReglasReservacion:
    reglas: list = field(default_factory=lambda: [
        ReglaTemporada(), ReglaSinMartes(), ReglaTipoVisita(), ReglaCupo(),
    ])

    def validar_todas(self, ctx: ContextoReserva) -> None:
        for r in self.reglas:
            r.validar(ctx)
