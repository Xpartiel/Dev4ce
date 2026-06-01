"""
Pruebas de UNIDAD — app reservaciones.

Verifican piezas aisladas del modelo Reservacion (sin base de datos). Cada
prueba cita su requisito.
"""
from django.test import SimpleTestCase

from apps.reservaciones.models import Reservacion


class ReservacionModeloTests(SimpleTestCase):

    def test_reservacion_define_tipos_de_hospedaje(self):
        # Basado en: RF-06.1 (tipo de visita: cabana o camping).
        valores = dict(Reservacion.TIPO_HOSPEDAJE_CHOICES)
        self.assertIn("cabana", valores)
        self.assertIn("camping", valores)

    def test_reservacion_tiene_estado_por_defecto(self):
        # Basado en: RF-06.6 (la reservacion se registra con un estado inicial).
        self.assertEqual(Reservacion._meta.get_field("estado").default, "confirmada")