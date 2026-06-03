from django.db import models
from django.conf import settings

from apps.parques.models import Parque


class DisponibilidadParque(models.Model):

    ESTADO_CHOICES = [
        ("libre", "Libre"),
        ("pocos", "Pocos lugares"),
        ("agotado", "Agotado"),
        ("mantenimiento", "Mantenimiento"),
    ]

    parque = models.ForeignKey(
        Parque,
        on_delete=models.CASCADE,
        related_name="disponibilidades"
    )

    fecha = models.DateField()

    capacidad_disponible = models.PositiveIntegerField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="libre"
    )

    class Meta:
        unique_together = ("parque", "fecha")
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.parque.nombre} - {self.fecha} - {self.estado}"


class Reservacion(models.Model):

    TIPO_HOSPEDAJE_CHOICES = [
        ("cabana", "Cabaña"),
        ("camping", "Camping"),
    ]

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
        ("completada", "Completada"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservaciones"
    )

    parque = models.ForeignKey(
        Parque,
        on_delete=models.CASCADE,
        related_name="reservaciones"
    )

    folio = models.CharField(max_length=30, unique=True)

    checkin = models.DateField()
    checkout = models.DateField()

    huespedes = models.PositiveIntegerField()

    tipo_hospedaje = models.CharField(
        max_length=20,
        choices=TIPO_HOSPEDAJE_CHOICES
    )

    total = models.DecimalField(max_digits=10, decimal_places=2)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="confirmada"
    )

    comentarios = models.TextField(blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.folio} - {self.usuario} - {self.parque}"