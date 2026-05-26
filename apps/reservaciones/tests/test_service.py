"""
Tests de integración del Facade ReservacionService — RF-06..09 + RF-12.
"""
from datetime import date
import pytest
from django.core import mail
from apps.reservaciones.models import EstadoReservacion, Reservacion
from apps.reservaciones.rules import ReglaInvalidaError
from apps.reservaciones.services import ReservacionService


@pytest.mark.django_db
class TestReservacionService:

    def test_rf06_crear_reservacion_exitosa(
        self, perfil_cliente, parque_con_cabanas, fechas_validas
    ):
        ini, fin = fechas_validas
        r = ReservacionService().crear(perfil_cliente, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini, "fecha_fin": fin,
            "num_asistentes": 4, "tipo_visita": "CAMPING",
        })
        assert r.estado == EstadoReservacion.CONFIRMADA
        assert r.folio is not None
        assert Reservacion.objects.filter(folio=r.folio).exists()

    def test_rf06_7_resta_cupo(
        self, perfil_cliente, parque_con_cabanas, fechas_validas
    ):
        ini, fin = fechas_validas
        ReservacionService().crear(perfil_cliente, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini, "fecha_fin": fin,
            "num_asistentes": 10, "tipo_visita": "CAMPING",
        })
        disp = parque_con_cabanas.disponibilidades.get(fecha=ini)
        assert disp.cupo_camping == parque_con_cabanas.capacidad_max_camping - 10

    def test_rf07_envia_correo_confirmacion(
        self, perfil_cliente, parque_con_cabanas, fechas_validas, settings
    ):
        settings.CELERY_TASK_ALWAYS_EAGER = True
        ini, fin = fechas_validas
        ReservacionService().crear(perfil_cliente, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini, "fecha_fin": fin,
            "num_asistentes": 2, "tipo_visita": "CAMPING",
        })
        assert len(mail.outbox) == 1
        assert perfil_cliente.email in mail.outbox[0].to
        assert "Folio" in mail.outbox[0].subject

    def test_rf06_3_rechaza_martes(
        self, perfil_cliente, parque_con_cabanas, fechas_con_martes
    ):
        ini, fin = fechas_con_martes
        with pytest.raises(ReglaInvalidaError):
            ReservacionService().crear(perfil_cliente, {
                "parque_id": parque_con_cabanas.pk,
                "fecha_inicio": ini, "fecha_fin": fin,
                "num_asistentes": 2, "tipo_visita": "CAMPING",
            })

    def test_rf09_cancelar_libera_cupo(
        self, perfil_cliente, parque_con_cabanas, fechas_validas
    ):
        ini, fin = fechas_validas
        r = ReservacionService().crear(perfil_cliente, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini, "fecha_fin": fin,
            "num_asistentes": 5, "tipo_visita": "CAMPING",
        })
        ReservacionService().cancelar(r)
        r.refresh_from_db()
        assert r.estado == EstadoReservacion.CANCELADA

        disp = parque_con_cabanas.disponibilidades.get(fecha=ini)
        assert disp.cupo_camping == parque_con_cabanas.capacidad_max_camping

    def test_rf08_listar_solo_propias(
        self, perfil_cliente, perfil_admin, parque_con_cabanas, fechas_validas
    ):
        ini, fin = fechas_validas
        ReservacionService().crear(perfil_cliente, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini, "fecha_fin": fin,
            "num_asistentes": 2, "tipo_visita": "CAMPING",
        })
        assert ReservacionService().listar_de(perfil_cliente).count() == 1
        assert ReservacionService().listar_de(perfil_admin).count() == 0
