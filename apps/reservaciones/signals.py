"""
Observer — Signal de reserva creada / cancelada.
Encola la TareaEnvioCorreo (Celery) sin acoplar al flujo principal.
"""
from django.dispatch import Signal, receiver
from .tasks import enviar_confirmacion_reserva

reserva_creada   = Signal()   # kwargs: reserva
reserva_cancelada = Signal()  # kwargs: reserva


@receiver(reserva_creada)
def _on_reserva_creada(sender, reserva, **kwargs):
    """RF-07.2 — envía correo en ≤60s vía Celery."""
    enviar_confirmacion_reserva.delay(reserva.id)
