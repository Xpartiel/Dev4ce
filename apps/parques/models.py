from django.db import models


class Parque(models.Model):

    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)

    estado = models.CharField(max_length=100)
    descripcion = models.TextField()

    direccion = models.CharField(max_length=255, blank=True, default="")
    horario = models.CharField(max_length=120, blank=True, default="")

    # Servicios separados por coma, ej: "Senderos guiados, Estacionamiento, Baños"
    servicios = models.TextField(blank=True, default="")

    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    capacidad_total = models.PositiveIntegerField()

    # Todos los parques tienen camping; las cabañas son opcionales (regla de negocio)
    tiene_cabanas = models.BooleanField(default=True)

    precio_cabana = models.DecimalField(max_digits=10, decimal_places=2)
    precio_camping = models.DecimalField(max_digits=10, decimal_places=2)

    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    @property
    def lista_servicios(self):
        """Devuelve los servicios como lista, para iterar en los templates."""
        return [s.strip() for s in self.servicios.split(",") if s.strip()]