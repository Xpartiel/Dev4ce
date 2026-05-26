from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer  # opcional si instalas drf-gis
from .models import Parque


class ParqueSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    class Meta:
        model  = Parque
        fields = ["id", "nombre", "direccion", "servicios", "horario",
                  "capacidad_max_camping", "capacidad_max_cabania",
                  "lat", "lng"]

    def get_lat(self, obj): return obj.coordenadas.y if obj.coordenadas else None
    def get_lng(self, obj): return obj.coordenadas.x if obj.coordenadas else None


class ParqueWriteSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)
    lng = serializers.FloatField(write_only=True)

    class Meta:
        model  = Parque
        fields = ["nombre", "direccion", "servicios", "horario",
                  "capacidad_max_camping", "capacidad_max_cabania",
                  "lat", "lng"]

    def create(self, validated):
        from django.contrib.gis.geos import Point
        lat = validated.pop("lat"); lng = validated.pop("lng")
        validated["coordenadas"] = Point(lng, lat)
        return super().create(validated)

    def update(self, instance, validated):
        from django.contrib.gis.geos import Point
        if "lat" in validated and "lng" in validated:
            instance.coordenadas = Point(validated.pop("lng"), validated.pop("lat"))
        return super().update(instance, validated)
