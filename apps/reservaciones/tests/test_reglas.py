"""
Tests unitarios del Strategy — reglas de reservación (RF-06.2..06.5).
"""
import pytest
from apps.reservaciones.rules import (
    ContextoReserva, ReglaCupo, ReglaInvalidaError, ReglaSinMartes,
    ReglaTemporada, ReglaTipoVisita, ReglasReservacion,
)


@pytest.mark.django_db
class TestStrategy:
    # ----- ReglaTemporada (RF-06.2) -----
    def test_temporada_acepta_julio(self, parque_con_cabanas, fechas_validas):
        ini, fin = fechas_validas
        ReglaTemporada().validar(ContextoReserva(parque_con_cabanas, ini, fin, "CAMPING", 2))

    def test_temporada_rechaza_mayo(self, parque_con_cabanas, fechas_fuera_temporada):
        ini, fin = fechas_fuera_temporada
        with pytest.raises(ReglaInvalidaError):
            ReglaTemporada().validar(ContextoReserva(parque_con_cabanas, ini, fin, "CAMPING", 2))

    # ----- ReglaSinMartes (RF-06.3) -----
    def test_sin_martes_rechaza(self, parque_con_cabanas, fechas_con_martes):
        ini, fin = fechas_con_martes
        with pytest.raises(ReglaInvalidaError):
            ReglaSinMartes().validar(ContextoReserva(parque_con_cabanas, ini, fin, "CAMPING", 2))

    def test_sin_martes_acepta(self, parque_con_cabanas, fechas_validas):
        ini, fin = fechas_validas
        ReglaSinMartes().validar(ContextoReserva(parque_con_cabanas, ini, fin, "CAMPING", 2))

    # ----- ReglaTipoVisita (RF-06.4) -----
    def test_tipo_visita_rechaza_cabania_en_parque_sin_cabanas(
        self, parque_sin_cabanas, fechas_validas
    ):
        ini, fin = fechas_validas
        with pytest.raises(ReglaInvalidaError):
            ReglaTipoVisita().validar(
                ContextoReserva(parque_sin_cabanas, ini, fin, "CABAÑA", 2)
            )

    # ----- ReglaCupo (RF-06.5) -----
    def test_cupo_rechaza_exceso(self, parque_con_cabanas, fechas_validas):
        ini, fin = fechas_validas
        with pytest.raises(ReglaInvalidaError):
            ReglaCupo().validar(
                ContextoReserva(parque_con_cabanas, ini, fin, "CAMPING", 9999)
            )

    def test_reglas_se_evaluan_en_conjunto(self, parque_con_cabanas, fechas_con_martes):
        ini, fin = fechas_con_martes
        with pytest.raises(ReglaInvalidaError):
            ReglasReservacion().validar_todas(
                ContextoReserva(parque_con_cabanas, ini, fin, "CAMPING", 2)
            )
