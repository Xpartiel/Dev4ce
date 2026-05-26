"""
Factory Method — PerfilFactory (Vista 1).
Encapsula la creación de Perfiles con rol predefinido (RF-01.5).
"""
from .models import Persona, Perfil, Rol


class PerfilFactory:
    """Patrón Factory Method."""

    @staticmethod
    def crear_cliente(persona: Persona, password: str, nick: str = "") -> Perfil:
        return Perfil.objects.create_user(
            email=persona.email,
            password=password,
            persona=persona,
            nick_name=nick,
            rol=Rol.CLIENTE,
        )

    @staticmethod
    def crear_admin(persona: Persona, password: str, nick: str = "") -> Perfil:
        return Perfil.objects.create_user(
            email=persona.email,
            password=password,
            persona=persona,
            nick_name=nick,
            rol=Rol.ADMINISTRADOR,
            is_staff=True,
        )
