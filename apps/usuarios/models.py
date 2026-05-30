from django.db import models
from django.contrib.auth.models import AbstractUser

class TipoUsuario( models.Model ):
    '''
    Modelo auxiliar para dar indicar a un perfil el tipo de usuario es.
    
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


class Usuario( AbstractUser ):
    '''
    Modelo de Usuario que contiene datos publicos.
        Tabla Correspondiente: Perfil
    Hereda de AbstractUser para aprovechar las funciones
    de autenticacion de Django
    '''

    # Nombre publico de usuario.
    # Se asigna por defecto el email antes del domino
    # EJ
    # ejemplo@correo.com -> ejemplo
    nick_name = models.CharField( max_length=128, blank=True, null=True)
    
    # TODO considerar si incluir foto de perfil
    foto_perfil = models.ImageField( upload_to='perfiles/', default='perfiles/default.png', blank=True )
    
    # Esto se considera dato privado
    # TODO removerlo de este modelo y reservarlo a *Persona*
    nombre_completo = models.CharField(max_length=255, blank=True, null=True)

    # Esto se considera dato privado
    # TODO removerlo de este modelo y reservarlo a *Persona*
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    tipo_usuario = models.ForeignKey(
        TipoUsuario,
        related_name='tipo_actual',
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )

    tipoAdministrador = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email

class HistorialTipoUsuario( models.Model ):
    '''
    Modelo que pretende mantener un registro historico de las
    fechas y tipos de usuario que adquiere un dado usuario a
    lo largo del tiempo
    '''
    
    # Referencia al usuario que se da seguimiento
    usuario = models.ForeignKey(
        Usuario,
        related_name='historico_ususario',
        on_delete=models.PROTECT
    )
    
    # Referencia al tipo asignado
    tipo = models.ForeignKey(
        TipoUsuario,
        related_name='historico_asignacion',
        on_delete=models.PROTECT
    )
    
    # Fecha de registro de inicio con este estatus
    fecha_inicio = models.DateTimeField( auto_now_add=True )
    
    # Fecha de fin de vigencia de estatus
    # null indica vigencia activa
    fecha_fin = models.DateTimeField( null=True )
    
    motivo_cambio = models.TextField( null=True , blank=True )



class Persona( models.Model ):
    '''
    Modelo dedicado a manejar los datos privados de un usuario
        Tabla Correspondiente: Persona
    '''
    
    usuario = models.OneToOneField(
        Usuario,
        primary_key=True,
        on_delete=models.CASCADE
    )
    
    nombre = models.CharField( max_length=255 )
    apellido_paterno = models.CharField( max_length=255 )
    apellido_materno = models.CharField( max_length=255 )
    email = models.CharField(
        max_length = 255,
        unique=True,
        blank=False,
        null=False
    )
    
    @property
    def nombre_completo( self ) -> str:
        return str(
            self.nombre) if self.nombre else '' + str(
            self.self.apellido_paterno ) if self.self.apellido_paterno else '' + str(
            self.self.apellido_materno ) if self.self.apellido_materno else ''