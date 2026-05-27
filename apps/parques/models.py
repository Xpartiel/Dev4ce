from django.db import models


class Parque(models.Model):

    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)

    estado = models.CharField(max_length=100)
    descripcion = models.TextField()

    capacidad_total = models.PositiveIntegerField()

    precio_cabana = models.DecimalField(max_digits=10, decimal_places=2)
    precio_camping = models.DecimalField(max_digits=10, decimal_places=2)

    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre