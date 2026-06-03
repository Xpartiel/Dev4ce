"""
Pruebas de SISTEMA app usuarios.

Recorren flujos completos de extremo a extremo con el cliente de pruebas
(varias vistas encadenadas), sin navegador. Cada prueba cita su requisito.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = "Passw0rd123"


class FlujoAutenticacionTests(TestCase):

    def test_cliente_no_accede_al_panel_administrador(self):
        # Basado en: RNF-02 (un cliente autenticado NO debe ver el panel admin).
        User.objects.create_user(username="cli@dev4ce.com",
                                 email="cli@dev4ce.com", password=PASSWORD)
        self.client.login(username="cli@dev4ce.com", password=PASSWORD)
        resp = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(resp.status_code, 302)  # rebotado a login
        self.assertIn("login", resp.url)
