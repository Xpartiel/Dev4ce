from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Persona, Perfil


class RegistroSerializer(serializers.Serializer):
    '''
    Serializador de guardado y reconstruccion de informacion
    REGISTRO
    
    Requisitos Funcionales
    - 1.1 
    - 1.3 
    '''
    
    nombre = serializers.CharField(max_length=80)
    apellido_paterno = serializers.CharField(max_length=80)
    apellido_materno = serializers.CharField(max_length=80, allow_blank=True, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

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
    '''
    Serializador para guardado y reconstruccion
    LOGIN
    '''
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PerfilSerializer(serializers.ModelSerializer):
    '''
    Serializador para guardado y reconstruccion de informacion
    PERFIL
    '''
    
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model  = Perfil
        fields = ["id", "email", "nick_name", "rol", "nombre_completo"]

    def get_nombre_completo(self, obj):
        return obj.persona.nombre_completo()
