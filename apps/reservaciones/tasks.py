"""
Celery — TareaEnvioCorreo (RF-07.4 ≤ 60s).
"""
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def enviar_confirmacion_reserva(self, reserva_id: int):
    from .models import Reservacion
    try:
        r = Reservacion.objects.select_related("parque", "perfil__persona").get(pk=reserva_id)
        asunto  = f"Confirmación de reservación · Folio {r.folio}"
        cuerpo  = (
            f"Hola {r.perfil.persona.nombre_completo()},\n\n"
            f"Tu reservación ha sido confirmada:\n"
            f"  • Parque: {r.parque.nombre}\n"
            f"  • Fechas: {r.fecha_inicio} a {r.fecha_fin}\n"
            f"  • Personas: {r.num_asistentes}\n"
            f"  • Tipo: {r.tipo_visita}\n"
            f"  • Folio: {r.folio}\n\n"
            f"¡Te esperamos en el Festival de las Luciérnagas 2026!"
        )
        send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL,
                  [r.perfil.email], fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)
