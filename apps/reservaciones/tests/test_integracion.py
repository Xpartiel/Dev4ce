"""
Pruebas de INTEGRACION — app reservaciones.

Vistas de cliente y de administrador + ORM, mediante el cliente de pruebas.
Cada prueba cita su requisito.
"""
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.parques.models import Parque
from apps.reservaciones.models import Reservacion
from apps.reservaciones.forms import ReservacionForm

User = get_user_model()
PASSWORD = "Passw0rd123"


def crear_parque(slug="bosque-esmeralda"):
    return Parque.objects.create(
        nombre="Bosque Esmeralda", slug=slug, estado="Puebla", descripcion="...",
        latitud=Decimal("19.12"), longitud=Decimal("-98.73"),
        capacidad_max_cabana=20, capacidad_max_camping=80,
        precio_cabana=Decimal("800"), precio_camping=Decimal("450"), activo=True)


def crear_reservacion(usuario, parque, folio, estado="confirmada"):
    return Reservacion.objects.create(
        usuario=usuario, parque=parque, folio=folio,
        checkin=date(2026, 7, 1), checkout=date(2026, 7, 3),
        huespedes=2, tipo_hospedaje="camping",
        total=Decimal("900"), estado=estado)


class MisReservacionesTests(TestCase):

    def setUp(self):
        self.ana = User.objects.create_user(
            username="ana@dev4ce.com", email="ana@dev4ce.com", password=PASSWORD)
        self.beto = User.objects.create_user(
            username="beto@dev4ce.com", email="beto@dev4ce.com", password=PASSWORD)
        self.parque = crear_parque()

    def test_mis_reservaciones_solo_activas_del_usuario(self):
        # Basado en: RF-08 / RF-08.1 (el cliente ve SOLO sus reservaciones activas).
        activa = crear_reservacion(self.ana, self.parque, "ANA-1", "confirmada")
        crear_reservacion(self.ana, self.parque, "ANA-2", "cancelada")   # inactiva
        crear_reservacion(self.beto, self.parque, "BETO-1", "confirmada")  # de otro
        self.client.force_login(self.ana)
        resp = self.client.get(reverse("mis_reservaciones"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context["reservaciones"]), [activa])

    def test_detalle_reservacion_de_otro_usuario_devuelve_404(self):
        # Basado en: RF-08.3 + RNF-02 (no se pueden ver reservaciones ajenas).
        ajena = crear_reservacion(self.beto, self.parque, "BETO-1")
        self.client.force_login(self.ana)
        resp = self.client.get(reverse("detalle_reservacion", args=[ajena.pk]))
        self.assertEqual(resp.status_code, 404)


class PanelAdminTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm@dev4ce.com", email="adm@dev4ce.com",
            password=PASSWORD, tipoAdministrador=True, is_staff=True)
        self.cliente = User.objects.create_user(
            username="cli@dev4ce.com", email="cli@dev4ce.com", password=PASSWORD)
        self.parque = crear_parque()

    def test_admin_reservaciones_lista_todas(self):
        # Basado en: RF-11.1 (vista global con TODAS las reservaciones).
        crear_reservacion(self.cliente, self.parque, "CLI-1")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("admin_reservaciones"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["reservaciones"]), 1)

    def test_admin_dashboard_suma_totales_e_ingresos(self):
        # Basado en: RF-11 (indicadores): total de reservaciones e ingresos.
        crear_reservacion(self.cliente, self.parque, "CLI-1", "confirmada")  # 900
        crear_reservacion(self.cliente, self.parque, "CLI-2", "confirmada")  # 900
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["total_reservaciones"], 2)
        self.assertEqual(resp.context["ingresos"], Decimal("1800"))


class ReservacionFormTests(TestCase):

    def test_reservacion_form_invalida_sin_campos_obligatorios(self):
        # Basado en: RF-06.1 (la reservacion requiere parque, fechas, personas, tipo...).
        form = ReservacionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("parque", form.errors)