'''
Factory Method
PerfilFactory (Vista 1).
Encapsula la creación de Perfiles con rol predefinido

Requisito Funcional 1.5
    El sistema debe almacenar la información de usuario en
    la base de datos asignando el rol "cliente" por defecto.
'''
from .models import Persona, Perfil, Rol


class PerfilFactory:
    '''
    Patron Factory Method
    '''

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
