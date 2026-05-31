from django.db import models, transaction
from django.conf import settings

from django.core.exceptions import ValidationError
from django.db.models import Q, F

from datetime import timedelta, date

from apps.parques.models import Parque

class EstadoReservacion( models.TextChoices ):
    '''
    Se espera que el catalogo de reservaciones sea practicamente
    inmutable, así que se definen desde codigo por simplicidad
    del proyecto y de validaciones.
    
    Indica el estatus de una reservacion particular
    * Pendiente - Sin pago aplicado o sin confirmar
    * Confirmada - Reservacion confirmada y a la espera de la fecha reservada
    * Cancelada - El usuario cancela una reservacion antes de la fecha de uso
    * Completada - El usuario ha hecho valer su reservacion (si atendio)
    * Inconclusa - No se hizo valer la reservacion previamente confirmada (no atendio)
    * Denegada - El usuario no tiene permitido reservar para ese parque
    '''
    
    PENDIENTE = "pendiente" , "Pendiente"
    CONFIRMADA = "confirmada" , "Confirmada"
    CANCELADA = "cancelada" , "Cancelada"
    COMPLETADA = "completada" , "Completada"
    INCONCLUSA = "inconclusa" , "Inconclusa"
    DENEGADA = "denegada" , "Denegada"


class TipoHospedaje( models.TextChoices ):
    '''
    Solo se mencionan 2 tipos de hospedaje, asi que se mantiene
    esa promesa y se usa esta idea para simplificar la logica
    de relaciones.
    '''
    CABANIA = "cabania" , "Cabania"
    CAMPING = "camping" , "Camping"


class EstadoDisponibilidad( models.TextChoices ):
    '''
    Estados asignados a la disponibilidad del parque
    segun la cantidad de cupos utilizados
    
    LIBRE 80% libre o mas
    POCOS 40% libre o mas
    AGOTADO 0 libre
    MANTENIMIENTO
    '''
    
    LIBRE = "libre", "Libre"
    POCOS = "poco lugares", "Pocos lugares"
    AGOTADO = "agotado", "Agotado"
    MANTENIMIENTO = "en mantenimiento", "En Mantenimiento"


class DisponibilidadParque( models.Model ):

    parque = models.ForeignKey(
        Parque,
        on_delete=models.CASCADE,
        related_name="disponibilidades"
    )

    fecha = models.DateField()
    
    camping_disponible = models.PositiveIntegerField()
    cabania_disponible = models.PositiveIntegerField()
    
    en_mantenimiento = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parque", "fecha"],
                name="uniq_disponibilidad_parque_fecha",
            )
        ]
        indexes = [
            models.Index(fields=["parque", "fecha"]),
            models.Index(fields=["fecha"]),
        ]
        ordering = ["fecha"]
    
    @property
    def capacidad_max_camping( self ):
        return self.parque.capacidad_max_camping
    
    @property
    def capacidad_max_cabania(self):
        return self.parque.capacidad_max_camping
    
    @property
    def estado(self):
        if self.en_mantenimiento:
            return EstadoDisponibilidad.MANTENIMIENTO

        if self.camping_disponible == 0 and self.cabania_disponible == 0:
            return EstadoDisponibilidad.AGOTADO

        if self.camping_disponible <= 3 or self.cabania_disponible <= 3:
            return EstadoDisponibilidad.POCOS

        return EstadoDisponibilidad.LIBRE
    
    def __str__(self):
        return f"{self.parque.nombre} - {self.fecha} - {self.estado}"
    
    def aumentar_cupo( self , tipo_hospedaje:str , cantidad:int ):
        '''
        Intentar modificar el cupo del dia por una cantidad indicada
        - Se asegura que la cantidad sea mayor o igual a 0)
        - Se asegura que la cantidad resultante sea menor o igual a la maxima
        '''
        if self.en_mantenimiento:
            raise ValidationError(
                f"Parque en mantenimiento el {self.fecha}.")
        
        aumento = abs( cantidad )
        
        if tipo_hospedaje == TipoHospedaje.CAMPING:
            cambio = min( self.camping_disponible + aumento , self.capacidad_max_camping )
            self.camping_disponible = cambio
            
        else:
            #cabaña
            cambio = min( self.cabania_disponible + aumento , self.capacidad_max_cabania )
            self.cabania_disponible = cambio
        
        self.save(update_fields=["camping_disponible", "cabania_disponible"])

    def reducir_cupo( self , tipo_hospedaje: str , cantidad:int ):
        '''
        Intentar modificar el cupo del dia por una cantidad indicada
        - La cantidad de entrada sera positiva
        - Se asegura que la cantidad resultante sea mayor o igual a 0
        '''
        if self.en_mantenimiento:
            raise ValidationError(
                f"Parque en mantenimiento el {self.fecha}.")
            
        reduccion = abs(cantidad)
        
        if tipo_hospedaje == TipoHospedaje.CAMPING:
            if( self.camping_disponible < reduccion ):
                raise ValidationError(
                    f"Cupo insuficiente")
            
            self.camping_disponible = F("camping_disponible") - reduccion
            
        else:
            if( self.cabania_disponible < reduccion ):
                raise ValidationError(
                    f"Cupo insuficiente")
            
            self.cabania_disponible = F("cabania_disponible") - reduccion
        
        self.save(update_fields=["camping_disponible", "cabania_disponible"])


class Reservacion(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservaciones"
    )
    
    parque = models.ForeignKey(
        Parque,
        on_delete=models.CASCADE,
        related_name="reservaciones"
    )
    
    folio = models.CharField(max_length=30, unique=True)

    checkin = models.DateField()
    checkout = models.DateField()

    huespedes = models.PositiveIntegerField()

    tipo_hospedaje = models.CharField(
        max_length=20,
        choices=TipoHospedaje.choices,
    )

    total = models.DecimalField(max_digits=10, decimal_places=2)

    estado = models.CharField(
        max_length=20,
        choices=EstadoReservacion.choices,
        default="pendiente"
    )

    comentarios = models.TextField( blank=True, null=True )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            # La entrada es antes que la salida
            models.CheckConstraint(
                condition=Q(checkout__gt=F("checkin")),
                name="reservacion_checkout_gt_checkin",
            ),# Al menos 1 huesped
            models.CheckConstraint(
                condition=Q(huespedes__gt=0),
                name="reservacion_huespedes_gt_0",
            ),#
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="reservacion_total_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["parque", "checkin", "checkout"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["tipo_hospedaje"]),
        ]

    def __str__(self):
        return f"{self.folio} - {self.usuario} - {self.parque}"
    
    def fechas_registradas(self) -> list[date]:
        '''
        Obtiene todas las fechas comprendidas por la reservación;
        desde checkin hasta checkout (no incluido).
        
        Asi se indican los días en que el (los) huésped(es)
        utiliza(n) cupo(s)

        Ejemplo:
        checkin=lunes, checkout=miércoles → [lunes, martes]
        '''
        dias = list()
        cursor = self.checkin
        while cursor < self.checkout:
            dias.append(cursor)
            cursor += timedelta(days=1)
        return dias
