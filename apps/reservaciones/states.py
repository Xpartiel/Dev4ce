"""
Patrón State  ciclo de vida de Reservacion.
PENDIENTE -> CONFIRMADA --> COMPLETADA
          -> CANCELADA
"""
from django.utils import timezone
from .models import Reservacion, EstadoReservacion


class _EstadoBase:
    nombre: str

    def confirmar(self, r: Reservacion): raise self._err("confirmar")
    def cancelar (self, r: Reservacion): raise self._err("cancelar")
    def completar(self, r: Reservacion): raise self._err("completar")

    def _err(self, accion):
        return ValueError(f"No se puede {accion} una reservación {self.nombre}.")


class _Pendiente(_EstadoBase):
    nombre = "PENDIENTE"
    def confirmar(self, r):
        r.estado = EstadoReservacion.CONFIRMADA
        r.save(update_fields=["estado"])
    def cancelar(self, r):
        r.estado = EstadoReservacion.CANCELADA
        r.fecha_cancelacion = timezone.now()
        r.save(update_fields=["estado", "fecha_cancelacion"])


class _Confirmada(_EstadoBase):
    nombre = "CONFIRMADA"
    def cancelar(self, r):
        r.estado = EstadoReservacion.CANCELADA
        r.fecha_cancelacion = timezone.now()
        r.save(update_fields=["estado", "fecha_cancelacion"])
    def completar(self, r):
        r.estado = EstadoReservacion.COMPLETADA
        r.save(update_fields=["estado"])


class _Cancelada(_EstadoBase):
    nombre = "CANCELADA"


class _Completada(_EstadoBase):
    nombre = "COMPLETADA"


_MAPA = {
    EstadoReservacion.PENDIENTE:  _Pendiente(),
    EstadoReservacion.CONFIRMADA: _Confirmada(),
    EstadoReservacion.CANCELADA:  _Cancelada(),
    EstadoReservacion.COMPLETADA: _Completada(),
}

def estado_de(r: Reservacion) -> _EstadoBase:
    return _MAPA[r.estado]
