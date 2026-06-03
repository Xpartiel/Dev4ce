"""
Pruebas de INTEGRACION en app usuarios.

Verifican la colaboracion vista + POST + base de datos mediante el cliente de
pruebas de Django. Cada prueba cita su requisito.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = "Passw0rd123"


class RegistroTests(TestCase):

    def test_registro_rechaza_correo_duplicado(self):
        # Basado en: RF-01.2 (no permitir dos cuentas con el mismo correo).
        User.objects.create_user(username="ana@dev4ce.com",
                                 email="ana@dev4ce.com", password=PASSWORD)
        resp = self.client.post(reverse("registro"), {
            "nombre": "Otra Ana", "correo": "ana@dev4ce.com", "password": PASSWORD,
        })
        self.assertEqual(resp.status_code, 200)  # re-renderiza con error, no redirige
        self.assertEqual(User.objects.filter(username="ana@dev4ce.com").count(), 1)


class LoginLogoutTests(TestCase):

    def setUp(self):
        # Crear un usuario cliente y un administrador para probar el login.
        self.cliente = User.objects.create_user(
            username="cli@dev4ce.com", email="cli@dev4ce.com",
            password=PASSWORD, tipoAdministrador=False)
        self.admin = User.objects.create_user(
            username="adm@dev4ce.com", email="adm@dev4ce.com",
            password=PASSWORD, tipoAdministrador=True, is_staff=True)

    def test_login_redirige_cliente_a_su_dashboard(self):
        # Basado en: RF-02 / RF-02.3 (autenticar y redirigir segun el rol).
        resp = self.client.post(reverse("login"),
                                {"correo": "cli@dev4ce.com", "password": PASSWORD})
        self.assertRedirects(resp, reverse("dashboard_cliente"),
                             fetch_redirect_response=False)

    def test_login_redirige_admin_a_su_panel(self):
        # Basado en: RF-02.3 (rol administrador -> panel de administracion).
        resp = self.client.post(reverse("login"),
                                {"correo": "adm@dev4ce.com", "password": PASSWORD})
        self.assertRedirects(resp, reverse("admin_dashboard"),
                             fetch_redirect_response=False)

    def test_login_invalido_no_autentica(self):
        # Basado en: RF-02.4 (credenciales incorrectas -> no se inicia sesion).
        resp = self.client.post(reverse("login"),
                                {"correo": "cli@dev4ce.com", "password": "incorrecta"})
        self.assertEqual(resp.status_code, 200)  # re-renderiza el login
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_logout_cierra_sesion(self):
        # Basado en: RF-03 (cerrar sesion y volver al inicio).
        self.client.force_login(self.cliente)
        resp = self.client.get(reverse("logout"))
        self.assertRedirects(resp, reverse("landing"), fetch_redirect_response=False)
        # Tras cerrar sesion, una vista protegida debe rebotar a login.
        protegida = self.client.get(reverse("mis_reservaciones"))
        self.assertEqual(protegida.status_code, 302)


class RegistroAdminTests(TestCase):

    def test_registro_admin_requiere_sesion_admin(self):
        # Basado en: RNF-02 (solo un administrador da de alta administradores).
        resp = self.client.get(reverse("registro_admin"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)