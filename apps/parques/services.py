"""
ParqueService — RF-10
"""
from django.db import transaction
from .models import Parque


class ParqueService:

    @staticmethod
    @transaction.atomic
    def crear_parque(data: dict) -> Parque:
        return Parque.objects.create(**data)

    @staticmethod
    @transaction.atomic
    def editar_parque(pk: int, data: dict) -> Parque:
        parque = Parque.objects.select_for_update().get(pk=pk)
        for k, v in data.items():
            setattr(parque, k, v)
        parque.save()
        return parque

    @staticmethod
    def eliminar_parque(pk: int) -> None:
        """RF-10.4 — no eliminar con reservaciones activas."""
        from apps.reservaciones.models import Reservacion, EstadoReservacion
        if Reservacion.objects.filter(
            parque_id=pk,
            estado__in=[EstadoReservacion.PENDIENTE, EstadoReservacion.CONFIRMADA],
        ).exists():
            raise ValueError("El parque tiene reservaciones activas.")
        Parque.objects.filter(pk=pk).delete()
