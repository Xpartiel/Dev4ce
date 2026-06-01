"""
Pruebas de INTEGRACION — app parques.

Vista + ORM + plantilla mediante el cliente de pruebas. Cada prueba cita su
requisito.
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.parques.models import Parque

User = get_user_model()
PASSWORD = "Passw0rd123"


def crear_parque(nombre="Bosque Esmeralda", slug="bosque-esmeralda", activo=True):
    # Helper: crea un Parque valido en la BD de pruebas.
    return Parque.objects.create(
        nombre=nombre, slug=slug, estado="Puebla",
        descripcion="Parque de prueba",
        latitud=Decimal("19.12"), longitud=Decimal("-98.73"),
        capacidad_max_cabana=20, capacidad_max_camping=80,
        precio_cabana=Decimal("800"), precio_camping=Decimal("450"),
        activo=activo,
    )


class LandingTests(TestCase):

    def test_landing_responde_y_muestra_parques_activos(self):
        # Basado en: RF-04 (mapa publico con los parques del festival).
        crear_parque()
        resp = self.client.get(reverse("landing"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bosque Esmeralda")

    def test_landing_omite_parques_inactivos(self):
        # Basado en: RF-04 (solo se muestran parques activos).
        crear_parque(nombre="Parque Inactivo", slug="inactivo", activo=False)
        resp = self.client.get(reverse("landing"))
        self.assertNotContains(resp, "Parque Inactivo")


class MapaClienteTests(TestCase):

    def test_mapa_cliente_requiere_autenticacion(self):
        # Basado en: RF-04 + control de acceso (el mapa del cliente es privado).
        resp = self.client.get(reverse("mapa_cliente"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)


class DetalleParqueTests(TestCase):

    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cli@dev4ce.com", email="cli@dev4ce.com", password=PASSWORD)
        self.parque = crear_parque()

    def test_detalle_parque_muestra_informacion(self):
        # Basado en: RF-05 (nombre, direccion, servicios y horario del parque).
        self.client.force_login(self.cliente)
        resp = self.client.get(reverse("detalle_parque", args=[self.parque.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bosque Esmeralda")

    def test_detalle_parque_inactivo_devuelve_404(self):
        # Basado en: RF-05 (un parque inactivo no debe ser visible al cliente).
        self.client.force_login(self.cliente)
        inactivo = crear_parque(nombre="Oculto", slug="oculto", activo=False)
        resp = self.client.get(reverse("detalle_parque", args=[inactivo.pk]))
        self.assertEqual(resp.status_code, 404)
