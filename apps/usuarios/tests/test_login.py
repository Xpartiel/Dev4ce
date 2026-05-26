"""
RF-02 / RF-03 — Login + Logout + Proxy (rate limit).
"""
import pytest
from django.core.cache import cache
from apps.usuarios.services import ValidadorInicioSesion


@pytest.mark.django_db
class TestLogin:
    URL_LOGIN  = "/api/auth/login/"
    URL_LOGOUT = "/api/auth/logout/"

    def setup_method(self):
        cache.clear()

    def test_rf02_login_exitoso(self, api, perfil_cliente):
        r = api.post(self.URL_LOGIN,
                     {"email": perfil_cliente.email, "password": "Luciernaga2026"},
                     format="json")
        assert r.status_code == 200
        assert r.json()["email"] == perfil_cliente.email

    def test_rf02_4_mensaje_generico(self, api, perfil_cliente):
        r = api.post(self.URL_LOGIN,
                     {"email": perfil_cliente.email, "password": "Mala1"},
                     format="json")
        assert r.status_code == 401
        # No revela qué campo es inválido
        assert "inválid" in r.json()["detail"].lower()

    def test_rf02_proxy_rate_limit(self, perfil_cliente):
        """El Proxy bloquea después de MAX_INTENTOS fallos."""
        for _ in range(ValidadorInicioSesion.MAX_INTENTOS):
            ValidadorInicioSesion(perfil_cliente.email, "WRONG").validar()
        # Siguiente intento — incluso con password correcto — debe ser None
        resultado = ValidadorInicioSesion(perfil_cliente.email, "Luciernaga2026").validar()
        assert resultado is None

    def test_rf03_logout(self, api, perfil_cliente):
        api.post(self.URL_LOGIN,
                 {"email": perfil_cliente.email, "password": "Luciernaga2026"},
                 format="json")
        r = api.post(self.URL_LOGOUT)
        assert r.status_code == 204

    def test_factory_crea_cliente_y_admin(self, perfil_cliente, perfil_admin):
        assert perfil_cliente.es_cliente()
        assert not perfil_cliente.es_admin()
        assert perfil_admin.es_admin()
        assert perfil_admin.is_staff
