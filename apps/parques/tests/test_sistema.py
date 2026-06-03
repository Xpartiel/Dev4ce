"""
Pruebas de SISTEMA app parques.

Flujo de extremo a extremo: el cliente explora el mapa y abre el detalle de un
parque. Sin navegador (cliente de pruebas de Django).
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.parques.models import Parque

User = get_user_model()
PASSWORD = "Passw0rd123"


class ExploracionMapaTests(TestCase):

    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cli@dev4ce.com", email="cli@dev4ce.com", password=PASSWORD)
        self.parque = Parque.objects.create(
            nombre="Valle San Rafael", slug="valle-san-rafael", estado="Puebla",
            descripcion="Valle ecologico", latitud=Decimal("19.29"),
            longitud=Decimal("-98.62"), capacidad_max_cabana=20,
            capacidad_max_camping=120, precio_cabana=Decimal("1200"),
            precio_camping=Decimal("600"), activo=True)

    def test_cliente_explora_mapa_y_abre_detalle(self):
        # Basado en: RF-04 -> RF-05 (del mapa interactivo al detalle del parque).
        self.client.force_login(self.cliente)
        mapa = self.client.get(reverse("mapa_cliente"))
        self.assertEqual(mapa.status_code, 200)
        detalle = self.client.get(reverse("detalle_parque", args=[self.parque.pk]))
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, "Valle San Rafael")
