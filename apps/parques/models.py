"""
Vista 2 (parte) — Parque y DisponibilidadParque.
RF-04 / RF-05 / RF-10 / RF-12
"""
from django.contrib.gis.db import models as geomodels
from django.db import models


class Parque(models.Model):
    nombre                 = models.CharField(max_length=120)
    direccion              = models.CharField(max_length=255)
    servicios              = models.JSONField(default=list, blank=True)   # ["wifi","fogata",...]
    horario                = models.CharField(max_length=120, blank=True)
    coordenadas            = geomodels.PointField(geography=True)         # RF-04.3 / PostGIS
    capacidad_max_camping  = models.PositiveIntegerField(default=0)
    capacidad_max_cabania  = models.PositiveIntegerField(default=0)       # 0 = no tiene cabañas
    fecha_creacion         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    # --- API del diagrama de clases ---
    def tiene_cabanas(self) -> bool:
        return self.capacidad_max_cabania > 0

    def cupo_restante(self, fecha, tipo: str) -> int:
        disp, _ = DisponibilidadParque.objects.get_or_create(
            parque=self, fecha=fecha,
            defaults={
                "cupo_camping": self.capacidad_max_camping,
                "cupo_cabania": self.capacidad_max_cabania,
            },
        )
        return disp.cupo_cabania if tipo == "CABAÑA" else disp.cupo_camping

    def tiene_cupo(self, fecha_ini, fecha_fin, tipo: str, n: int) -> bool:
        from datetime import timedelta
        d = fecha_ini
        while d <= fecha_fin:
            if self.cupo_restante(d, tipo) < n:
                return False
            d += timedelta(days=1)
        return True


class DisponibilidadParque(models.Model):
    """RF-12 — una fila por (parque, fecha)."""
    parque        = models.ForeignKey(Parque, on_delete=models.CASCADE, related_name="disponibilidades")
    fecha         = models.DateField()
    cupo_camping  = models.PositiveIntegerField()
    cupo_cabania  = models.PositiveIntegerField()

    class Meta:
        unique_together = ("parque", "fecha")
        ordering = ["parque", "fecha"]

    def disponible(self, tipo: str, n: int) -> bool:
        actual = self.cupo_cabania if tipo == "CABAÑA" else self.cupo_camping
        return actual >= n

    def restar(self, tipo: str, n: int) -> None:
        if tipo == "CABAÑA": self.cupo_cabania -= n
        else:                 self.cupo_camping -= n
        self.save(update_fields=["cupo_cabania", "cupo_camping"])

    def liberar(self, tipo: str, n: int) -> None:
        if tipo == "CABAÑA": self.cupo_cabania += n
        else:                 self.cupo_camping += n
        self.save(update_fields=["cupo_cabania", "cupo_camping"])
