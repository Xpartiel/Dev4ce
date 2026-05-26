"""
RF-01 — Registro de usuario.
"""
import pytest
from apps.usuarios.models import Perfil, Persona, Rol


@pytest.mark.django_db
class TestRegistro:
    URL = "/api/auth/registro/"

    def test_rf01_registro_exitoso(self, api):
        """RF-01.1 / RF-01.5 / RF-01.6"""
        r = api.post(self.URL, {
            "nombre": "Sofía",
            "apellido_paterno": "Alatorre",
            "apellido_materno": "Méndez",
            "email": "sofi@luciernagas.mx",
            "password": "Luciernaga2026",
        }, format="json")
        assert r.status_code == 201
        assert r.json()["rol"] == Rol.CLIENTE
        assert Perfil.objects.filter(email="sofi@luciernagas.mx").exists()

    def test_rf01_2_email_duplicado(self, api, persona_cliente):
        r = api.post(self.URL, {
            "nombre": "X",
            "apellido_paterno": "Y",
            "apellido_materno": "Z",
            "email": persona_cliente.email,
            "password": "Luciernaga2026",
        }, format="json")
        assert r.status_code == 400

    @pytest.mark.parametrize("password", ["corta1A", "sinmayus1", "SINNUMERO", "12345678"])
    def test_rf01_3_password_debil(self, api, password):
        r = api.post(self.URL, {
            "nombre": "X", "apellido_paterno": "Y", "apellido_materno": "",
            "email": f"weak-{password}@x.mx", "password": password,
        }, format="json")
        assert r.status_code == 400

    def test_rf01_4_password_se_hashea_con_bcrypt(self, perfil_cliente):
        # No debe estar en texto plano
        assert "Luciernaga2026" not in perfil_cliente.password
        assert perfil_cliente.check_password("Luciernaga2026")
        # Hasher por defecto es bcrypt
        assert perfil_cliente.password.startswith("bcrypt")
