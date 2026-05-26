"""
Reservacion — patrón State (transiciones controladas en states.py).
RF-06 / RF-07 / RF-08 / RF-09 / RF-12
"""
import uuid
from django.conf import settings
from django.db import models
from apps.parques.models import Parque


class TipoVisita(models.TextChoices):
    CABAÑA  = "CABAÑA",  "Cabaña"
    CAMPING = "CAMPING", "Camping"


class EstadoReservacion(models.TextChoices):
    PENDIENTE   = "PENDIENTE",   "Pendiente"
    CONFIRMADA  = "CONFIRMADA",  "Confirmada"
    CANCELADA   = "CANCELADA",   "Cancelada"
    COMPLETADA  = "COMPLETADA",  "Completada"


class Reservacion(models.Model):
    folio             = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    perfil            = models.ForeignKey(settings.AUTH_USER_MODEL,
                                          on_delete=models.PROTECT,
                                          related_name="reservaciones")
    parque            = models.ForeignKey(Parque, on_delete=models.PROTECT,
                                          related_name="reservaciones")
    fecha_inicio      = models.DateField()
    fecha_fin         = models.DateField()
    num_asistentes    = models.PositiveIntegerField()
    tipo_visita       = models.CharField(max_length=10, choices=TipoVisita.choices)
    estado            = models.CharField(max_length=12, choices=EstadoReservacion.choices,
                                         default=EstadoReservacion.PENDIENTE)
    fecha_registro    = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.folio} · {self.parque.nombre} · {self.estado}"

    # --- API del diagrama ---
    def incluye_martes(self) -> bool:
        from datetime import timedelta
        d = self.fecha_inicio
        while d <= self.fecha_fin:
            if d.weekday() == 1:   # 0=lunes, 1=martes
                return True
            d += timedelta(days=1)
        return False

    def dias(self) -> list:
        from datetime import timedelta
        return [self.fecha_inicio + timedelta(days=i)
                for i in range((self.fecha_fin - self.fecha_inicio).days + 1)]

    def duracion_noches(self) -> int:
        return (self.fecha_fin - self.fecha_inicio).days

    def puede_cancelar(self) -> bool:
        from datetime import date
        return self.estado in (EstadoReservacion.PENDIENTE, EstadoReservacion.CONFIRMADA)                and self.fecha_inicio > date.today()
