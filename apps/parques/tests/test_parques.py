"""
RF-04 / RF-05 / RF-10 — Parques.
"""
import pytest
from apps.parques.models import Parque
from apps.parques.services import ParqueService


@pytest.mark.django_db
class TestParques:
    URL = "/api/parques/"

    def test_rf04_listado_publico(self, api, parque_con_cabanas):
        r = api.get(self.URL)
        assert r.status_code == 200
        assert any(p["nombre"] == parque_con_cabanas.nombre for p in r.json())

    def test_rf05_detalle_incluye_lat_lng(self, api, parque_con_cabanas):
        r = api.get(f"{self.URL}{parque_con_cabanas.pk}/")
        body = r.json()
        assert r.status_code == 200
        assert body["lat"] == pytest.approx(19.8125, rel=1e-3)
        assert body["lng"] == pytest.approx(-100.1693, rel=1e-3)
        assert "servicios" in body and "horario" in body

    def test_rf10_solo_admin_crea_parque(self, api, perfil_cliente):
        api.force_authenticate(perfil_cliente)
        r = api.post(self.URL, {
            "nombre": "Hacker", "direccion": "X", "servicios": [],
            "horario": "", "lat": 19.0, "lng": -99.0,
            "capacidad_max_camping": 10, "capacidad_max_cabania": 0,
        }, format="json")
        assert r.status_code == 403

    def test_rf10_admin_crea_parque(self, api, perfil_admin):
        api.force_authenticate(perfil_admin)
        r = api.post(self.URL, {
            "nombre": "Parque Test", "direccion": "Calle 1",
            "servicios": ["wifi"], "horario": "10-22",
            "lat": 19.5, "lng": -99.5,
            "capacidad_max_camping": 20, "capacidad_max_cabania": 5,
        }, format="json")
        assert r.status_code == 201
        assert Parque.objects.filter(nombre="Parque Test").exists()

    def test_rf10_4_no_elimina_con_reservas_activas(
        self, parque_con_cabanas, perfil_cliente, fechas_validas
    ):
        from apps.reservaciones.services import ReservacionService
        ini, fin = fechas_validas
        ReservacionService().crear(perfil_cliente, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini, "fecha_fin": fin,
            "num_asistentes": 2, "tipo_visita": "CAMPING",
        })
        with pytest.raises(ValueError):
            ParqueService.eliminar_parque(parque_con_cabanas.pk)

    def test_parque_sin_cabanas_no_tiene_cabanas(self, parque_sin_cabanas):
        assert parque_sin_cabanas.tiene_cabanas() is False

    def test_parque_con_cabanas_si_tiene(self, parque_con_cabanas):
        assert parque_con_cabanas.tiene_cabanas() is True
