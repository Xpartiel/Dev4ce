"""
Pruebas de UNIDAD app usuarios.

Verifican piezas aisladas (un metodo de modelo, una funcion auxiliar) sin
tocar la base de datos ni el ciclo HTTP. Cada prueba indica en comentario
el requisito en que se basa (ver documento de RF del equipo).
"""
from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from apps.usuarios.views import solo_admin

User = get_user_model()


class UsuarioModeloTests(SimpleTestCase):
    """Metodos del modelo Usuario (sin persistencia)."""

    def test_usuario_str_devuelve_identificador(self):
        # Basado en: modelo Usuario (representacion legible en admin/listados).
        usuario = User(username="ana@dev4ce.com", email="ana@dev4ce.com")
        self.assertEqual(str(usuario), "ana@dev4ce.com")


class SoloAdminTests(SimpleTestCase):
    """
    Funcion auxiliar solo_admin(): decide si un usuario puede entrar al panel
    de administracion. Se prueba en aislamiento con objetos ligeros (sin BD).
    """

    def _usuario_falso(self, autenticado, es_admin):
        return type("UsuarioFalso", (), {
            "is_authenticated": autenticado,
            "tipoAdministrador": es_admin,
        })()

    def test_solo_admin_true_para_administrador(self):
        # Basado en: RF-02.3 (identificar rol) y RNF-02 (restringir el panel admin).
        self.assertTrue(solo_admin(self._usuario_falso(True, True)))

    def test_solo_admin_false_para_cliente_y_anonimo(self):
        # Basado en: RNF-02 (un cliente o un anonimo no acceden al panel admin).
        self.assertFalse(solo_admin(self._usuario_falso(True, False)))
        self.assertFalse(solo_admin(AnonymousUser()))
