from rest_framework import serializers
from .models import Reservacion, TipoVisita


class ReservacionCrearSerializer(serializers.Serializer):
    parque_id      = serializers.IntegerField()
    fecha_inicio   = serializers.DateField()
    fecha_fin      = serializers.DateField()
    num_asistentes = serializers.IntegerField(min_value=1)
    tipo_visita    = serializers.ChoiceField(choices=TipoVisita.choices)

    def validate(self, data):
        if data["fecha_fin"] < data["fecha_inicio"]:
            raise serializers.ValidationError("La fecha de fin debe ser posterior a la de inicio.")
        return data


class ReservacionSerializer(serializers.ModelSerializer):
    parque_nombre = serializers.CharField(source="parque.nombre", read_only=True)
    cliente       = serializers.CharField(source="perfil.email",  read_only=True)

    class Meta:
        model  = Reservacion
        fields = ["id", "folio", "parque", "parque_nombre", "cliente",
                  "fecha_inicio", "fecha_fin", "num_asistentes",
                  "tipo_visita", "estado", "fecha_registro"]
        read_only_fields = fields
