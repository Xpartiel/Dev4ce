from django.db import models


class Parque( models.Model ):

    nombre = models.CharField(max_length=150)
    
    # TODO ¿que es slug?
    slug = models.SlugField(max_length=160, unique=True)

    # TODO ¿que es estado?
    estado = models.CharField(max_length=100)
    
    # TODO no presente en UML
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

    # TODO ¿conservar? no acorde UML
    capacidad_total = models.PositiveIntegerField()

    # Todos los parques tienen camping; las cabañas son opcionales (regla de negocio)
    tiene_cabanas = models.BooleanField(default=True)

    capacidad_max_cabana = models.IntegerField()
    precio_cabana = models.DecimalField(max_digits=10, decimal_places=2)
    
    capacidad_max_camping = models.IntegerField()
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
    
    @property
    def capacidad_total( self ):
        '''
        Atributo calculado que se obtiene de sumar las capacidades
        maximas de reservacion
        '''
        return (self.capacidad_max_cabana if self.capacidad_max_cabana else 0
            ) + (self.capacidad_max_camping if self.capacidad_max_camping else 0)
        

class Servicio( models.Model ):
    '''
    Modelo para que se puedan registrar y referenciar servicios
    para multiples parques desde un panel de administracion.
    '''
    
    nombre = models.CharField(max_length=255)
    
    descripcion = models.TextField()



class ServiciosParque( models.Model ):
    '''
    Modelo de enlace entre Servicios y Parques
    
    '''
    
    id_parque = models.ForeignKey(
        Parque,
        on_delete=models.CASCADE
    )
    
    id_servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE
    )