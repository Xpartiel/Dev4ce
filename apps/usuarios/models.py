from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):

    nombre_completo = models.CharField(max_length=255)

    tipoAdministrador = models.BooleanField(default=False)

    def __str__(self):
        return self.username