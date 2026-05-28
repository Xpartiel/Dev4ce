from django.db import models
from django.contrib.auth.models import AbstractUser

class TipoUsuario( models.Model ):
    '''
    Modelo auxiliar para dar indicar a un perfil que
    tipo de usuario es.
    
    Util para propositos de administración futura.
    '''
    
    # Nombre asignado al tipo de usuario; debe ser breve
    nombre = models.CharField( max_length = 255 )
    
    # Descripcion detallada de las responsabilidades de este tipo de usuario
    descripcion = models.TextField()
    
    # Nivel de importancia de este rol; a mas alto el numero, mas importante
    # 0 se asigna al rol con menos privilegios (usuario común)
    # Considerar usar valores negaticos para rechazar acceso (ban)
    prioridad = models.IntegerField(
        default=0
    )


class Usuario(AbstractUser):

    nombre_completo = models.CharField(max_length=255)

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    tipo_usuario = models.ForeignKey(
        TipoUsuario,
        related_name='tipo_actual',
        blank=True
    )

    tipoAdministrador = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.username