from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Reservacion
from .rules import ReglaInvalidaError
from .serializers import ReservacionCrearSerializer, ReservacionSerializer
from .services import ReservacionService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def crear_reservacion(request):
    """RF-06 / RF-07"""
    ser = ReservacionCrearSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        reserva = ReservacionService().crear(request.user, ser.validated_data)
    except ReglaInvalidaError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(ReservacionSerializer(reserva).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_reservaciones(request):
    """RF-08"""
    qs = ReservacionService().listar_de(request.user)
    return Response(ReservacionSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancelar_reservacion(request, pk: int):
    """RF-09"""
    reserva = Reservacion.objects.get(pk=pk, perfil=request.user)
    try:
        ReservacionService().cancelar(reserva)
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(ReservacionSerializer(reserva).data)


class ReservacionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """RF-11 — vista global para administrador."""
    queryset = Reservacion.objects.select_related("parque", "perfil__persona").all()
    serializer_class = ReservacionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtros simples (RF-11.3)
        parque  = self.request.query_params.get("parque")
        estado  = self.request.query_params.get("estado")
        if parque: qs = qs.filter(parque_id=parque)
        if estado: qs = qs.filter(estado=estado)
        return qs

    def list(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.es_admin()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)
