from rest_framework import viewsets, permissions
from .models import Parque
from .serializers import ParqueSerializer, ParqueWriteSerializer


class EsAdminOSoloLectura(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.es_admin())


class ParqueViewSet(viewsets.ModelViewSet):
    """RF-04 / RF-05 / RF-10"""
    queryset = Parque.objects.all()
    permission_classes = [EsAdminOSoloLectura]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ParqueWriteSerializer
        return ParqueSerializer
