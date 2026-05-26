"""
Tests unitarios del patrón State.
"""
import pytest
from apps.reservaciones.models import EstadoReservacion, Reservacion
from apps.reservaciones.states import estado_de


@pytest.mark.django_db
class TestState:
    def _make(self, perfil, parque, **kw):
        from datetime import date
        defaults = dict(
            perfil=perfil, parque=parque,
            fecha_inicio=date(2026, 7, 9), fecha_fin=date(2026, 7, 10),
            num_asistentes=2, tipo_visita="CAMPING",
            estado=EstadoReservacion.PENDIENTE,
        )
        defaults.update(kw)
        return Reservacion.objects.create(**defaults)

    def test_pendiente_a_confirmada(self, perfil_cliente, parque_con_cabanas):
        r = self._make(perfil_cliente, parque_con_cabanas)
        estado_de(r).confirmar(r)
        assert r.estado == EstadoReservacion.CONFIRMADA

    def test_pendiente_a_cancelada(self, perfil_cliente, parque_con_cabanas):
        r = self._make(perfil_cliente, parque_con_cabanas)
        estado_de(r).cancelar(r)
        assert r.estado == EstadoReservacion.CANCELADA
        assert r.fecha_cancelacion is not None

    def test_cancelada_no_se_puede_volver_a_cancelar(
        self, perfil_cliente, parque_con_cabanas
    ):
        r = self._make(perfil_cliente, parque_con_cabanas,
                       estado=EstadoReservacion.CANCELADA)
        with pytest.raises(ValueError):
            estado_de(r).cancelar(r)

    def test_completada_no_se_cancela(self, perfil_cliente, parque_con_cabanas):
        r = self._make(perfil_cliente, parque_con_cabanas,
                       estado=EstadoReservacion.COMPLETADA)
        with pytest.raises(ValueError):
            estado_de(r).cancelar(r)
