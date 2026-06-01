"""
Pruebas de SISTEMA — app usuarios.

Recorren flujos completos de extremo a extremo con el cliente de pruebas
(varias vistas encadenadas), sin navegador. Cada prueba cita su requisito.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = "Passw0rd123"


class FlujoAutenticacionTests(TestCase):

    def test_flujo_registro_inicio_sesion_y_dashboard(self):
        # Basado en: RF-01 + RF-02 (registrarse, iniciar sesion y entrar al panel).
        # 1) Registro
        self.client.post(reverse("registro"), {
            "nombre": "Ana", "correo": "ana@dev4ce.com", "password": PASSWORD})
        self.assertTrue(User.objects.filter(username="Ana").exists())
        # 2) Inicio de sesion
        self.client.post(reverse("login"),
                         {"correo": "ana@dev4ce.com", "password": PASSWORD})
        # 3) Acceso a una vista protegida del cliente
        resp = self.client.get(reverse("dashboard_cliente"))
        self.assertEqual(resp.status_code, 200)

    def test_cliente_no_accede_al_panel_administrador(self):
        # Basado en: RNF-02 (un cliente autenticado NO debe ver el panel admin).
        User.objects.create_user(username="cli@dev4ce.com",
                                 email="cli@dev4ce.com", password=PASSWORD)
        self.client.login(username="cli@dev4ce.com", password=PASSWORD)
        resp = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(resp.status_code, 302)  # rebotado a login
        self.assertIn("login", resp.url)
