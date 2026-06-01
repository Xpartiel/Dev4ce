"""
Pruebas de SISTEMA — app reservaciones.

Flujos de extremo a extremo con el cliente de pruebas: gestion de parques del
administrador y flujo de reservacion del cliente (reservar con validacion de
cupo, correo de confirmacion y cancelacion con liberacion de cupo). Cada prueba
cita su requisito.
"""
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

from apps.parques.models import Parque
from apps.reservaciones.models import DisponibilidadParque, Reservacion

User = get_user_model()
PASSWORD = "Passw0rd123"


def crear_parque(slug="bosque-esmeralda"):
    return Parque.objects.create(
        nombre="Bosque Esmeralda", slug=slug, estado="Puebla", descripcion="...",
        latitud=Decimal("19.12"), longitud=Decimal("-98.73"),
        capacidad_max_cabana=20, capacidad_max_camping=80,
        precio_cabana=Decimal("800"), precio_camping=Decimal("450"), activo=True)


class AdminGestionParquesTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm@dev4ce.com", email="adm@dev4ce.com",
            password=PASSWORD, tipoAdministrador=True, is_staff=True)

    def test_admin_crea_parque_y_aparece_en_listado(self):
        # Basado en: RF-10 / RF-10.1 (el admin da de alta un parque y queda registrado).
        self.client.force_login(self.admin)
        datos = {
            "nombre": "Nuevo Parque", "slug": "nuevo-parque",
            "estado": "Puebla", "descripcion": "Alta de prueba",
            "direccion": "Camino al bosque s/n", "horario": "8:00 - 20:00",
            "servicios": "Senderos, Banos",
            "latitud": "19.50", "longitud": "-98.60",
            "capacidad_total": "100",
            "capacidad_max_cabana": "20", "capacidad_max_camping": "80",
            "tiene_cabanas": "on",
            "precio_cabana": "800", "precio_camping": "400",
            "activo": "on",
        }
        resp = self.client.post(reverse("crear_parque"), datos)
        self.assertRedirects(resp, reverse("admin_parques"),
                             fetch_redirect_response=False)
        self.assertTrue(Parque.objects.filter(slug="nuevo-parque").exists())
        listado = self.client.get(reverse("admin_parques"))
        self.assertContains(listado, "Nuevo Parque")


class FlujoReservacionClienteTests(TestCase):
    """
    Flujo central del visitante: reservar (con validacion de cupo y correo de
    confirmacion) y cancelar (liberando el cupo). Durante las pruebas, Django
    usa un backend de correo en memoria, por lo que los envios se capturan en
    mail.outbox sin enviar correos reales.
    """

    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cli@dev4ce.com", email="cli@dev4ce.com", password=PASSWORD)
        self.parque = crear_parque()

    def _poner_reserva_en_sesion(self, checkin, checkout, tipo, huespedes):
        # El flujo guarda los datos del paso 1/2 en la sesion; los preparamos aqui.
        session = self.client.session
        session["reserva"] = {
            "parque_id": self.parque.pk,
            "checkin": checkin, "checkout": checkout,
            "tipo": tipo, "huespedes": huespedes,
        }
        session.save()

    def test_cliente_reserva_y_recibe_correo_de_confirmacion(self):
        # Basado en: RF-06 (reservar) + RF-07 (confirmacion + correo) + RF-12 (descuenta cupo).
        DisponibilidadParque.objects.create(
            parque=self.parque, fecha=date(2026, 7, 1), capacidad_disponible=2)
        self.client.force_login(self.cliente)
        self._poner_reserva_en_sesion("2026-07-01", "2026-07-02", "camping", 2)

        resp = self.client.post(reverse("reservar_paso_3", args=[self.parque.pk]))

        self.assertEqual(resp.status_code, 302)                      # -> confirmacion
        self.assertEqual(Reservacion.objects.filter(
            usuario=self.cliente, parque=self.parque).count(), 1)    # se creo la reserva
        self.assertEqual(len(mail.outbox), 1)                        # se envio el correo
        self.assertIn(self.cliente.email, mail.outbox[0].to)
        disp = DisponibilidadParque.objects.get(parque=self.parque, fecha=date(2026, 7, 1))
        self.assertEqual(disp.capacidad_disponible, 0)               # se descuento el cupo

    def test_cliente_cancela_reservacion_y_se_libera_cupo(self):
        # Basado en: RF-09 (cancelar) + liberar disponibilidad + correo de cancelacion.
        reservacion = Reservacion.objects.create(
            usuario=self.cliente, parque=self.parque, folio="LUZ-TEST-1",
            checkin=date(2026, 7, 1), checkout=date(2026, 7, 2),
            huespedes=2, tipo_hospedaje="camping",
            total=Decimal("450"), estado="confirmada")
        DisponibilidadParque.objects.create(
            parque=self.parque, fecha=date(2026, 7, 1), capacidad_disponible=10)
        self.client.force_login(self.cliente)

        resp = self.client.post(reverse("cancelar_reservacion", args=[reservacion.pk]))

        self.assertEqual(resp.status_code, 302)                      # -> mis-reservaciones
        reservacion.refresh_from_db()
        self.assertEqual(reservacion.estado, "cancelada")
        disp = DisponibilidadParque.objects.get(parque=self.parque, fecha=date(2026, 7, 1))
        self.assertEqual(disp.capacidad_disponible, 12)              # 10 + 2 liberados
        self.assertEqual(len(mail.outbox), 1)                        # correo de cancelacion