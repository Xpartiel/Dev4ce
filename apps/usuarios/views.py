'''
Registros Funcionales cubiertos por las vistas
- 01: Registro de usuario
- 02: Inicio de sesion
- 03: Cierre de sesion
'''

from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .managers import PerfilFactory
from .models import Persona
from .serializers import LoginSerializer, PerfilSerializer, RegistroSerializer
from .services import ValidadorInicioSesion


@api_view(["POST"])
@permission_classes([AllowAny])
def registro(request):
    '''
    Vista usada para registrar un nuevo usuario
    
    Requisito Funcional cubierto
    - 1: Registro de Usuario
    '''
    serializador = RegistroSerializer(data=request.data)
    serializador.is_valid(raise_exception=True)
    data = serializador.validated_data

    # Crear la persona con los datos dados por la peticion
    persona = Persona.objects.create(
        nombre = data["nombre"],
        apellido_paterno = data["apellido_paterno"],
        apellido_materno = data.get("apellido_materno", ""),
        email = data["email"],
    )
    perfil = PerfilFactory.crear_cliente( persona, data["password"] )
    return Response( PerfilSerializer(perfil).data, status=status.HTTP_201_CREATED )

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    '''
    Requisito Funcional
    - 02: Inicio de Sesion
        Usa el Proxy ValidadorInicioSesion.
    '''
    
    serializador = LoginSerializer(data=request.data)
    serializador.is_valid(raise_exception=True)

    proxy  = ValidadorInicioSesion(
        correo=serializador.validated_data["email"],
        password=serializador.validated_data["password"],
        ip=request.META.get("REMOTE_ADDR"),
    )
    
    # Intentar obtener un perfil valido
    perfil = proxy.validar()
    
    # Si no existe...
    if perfil is None:
        # RF-02.4 — mensaje genérico
        return Response({"detail": "Credenciales inválidas."},
                        status=status.HTTP_401_UNAUTHORIZED)

    login(request, perfil)
    
    return Response(PerfilSerializer(perfil).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    '''
    Vista correspondiente al cierre de sesion
    Requisito Funcional
    - 03: Cierre de Sesion
    '''
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def yo(request):
    '''
    Vista correspondiente a un usuario específico ya loggeado
    '''
    
    return Response(PerfilSerializer(request.user).data)
