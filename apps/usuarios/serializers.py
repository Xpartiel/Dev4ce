from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Persona, Perfil


class RegistroSerializer(serializers.Serializer):
    """RF-01.1 / RF-01.3"""
    nombre           = serializers.CharField(max_length=80)
    apellido_paterno = serializers.CharField(max_length=80)
    apellido_materno = serializers.CharField(max_length=80, allow_blank=True, required=False)
    email            = serializers.EmailField()
    password         = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if Persona.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        if not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula y un número."
            )
        return value


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PerfilSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model  = Perfil
        fields = ["id", "email", "nick_name", "rol", "nombre_completo"]

    def get_nombre_completo(self, obj):
        return obj.persona.nombre_completo()
