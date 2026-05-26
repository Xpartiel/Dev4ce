"""
RF-01 Registro · RF-02 Login · RF-03 Logout
"""
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
    """RF-01"""
    ser = RegistroSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    persona = Persona.objects.create(
        nombre=data["nombre"],
        apellido_paterno=data["apellido_paterno"],
        apellido_materno=data.get("apellido_materno", ""),
        email=data["email"],
    )
    perfil = PerfilFactory.crear_cliente(persona, data["password"])
    return Response(PerfilSerializer(perfil).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """RF-02 — usa el Proxy ValidadorInicioSesion."""
    ser = LoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    proxy  = ValidadorInicioSesion(
        correo=ser.validated_data["email"],
        password=ser.validated_data["password"],
        ip=request.META.get("REMOTE_ADDR"),
    )
    perfil = proxy.validar()
    if perfil is None:
        # RF-02.4 — mensaje genérico
        return Response({"detail": "Credenciales inválidas."},
                        status=status.HTTP_401_UNAUTHORIZED)

    login(request, perfil)
    return Response(PerfilSerializer(perfil).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """RF-03"""
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def yo(request):
    return Response(PerfilSerializer(request.user).data)
