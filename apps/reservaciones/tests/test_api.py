"""
Tests end-to-end de los endpoints REST.
"""
import pytest


@pytest.mark.django_db
class TestApiReservaciones:
    URL = "/api/reservaciones/"

    def test_anonimo_no_puede_reservar(self, api):
        r = api.post(self.URL, {}, format="json")
        assert r.status_code in (401, 403)

    def test_rf06_flujo_completo(
        self, api, perfil_cliente, parque_con_cabanas, fechas_validas
    ):
        api.force_authenticate(perfil_cliente)
        ini, fin = fechas_validas
        r = api.post(self.URL, {
            "parque_id": parque_con_cabanas.pk,
            "fecha_inicio": ini.isoformat(),
            "fecha_fin": fin.isoformat(),
            "num_asistentes": 3,
            "tipo_visita": "CAMPING",
        }, format="json")
        assert r.status_code == 201, r.content
        reserva_id = r.json()["id"]

        # RF-08
        r2 = api.get(f"{self.URL}mias/")
        assert r2.status_code == 200
        assert len(r2.json()) == 1

        # RF-09
        r3 = api.post(f"{self.URL}{reserva_id}/cancelar/")
        assert r3.status_code == 200
        assert r3.json()["estado"] == "CANCELADA"

    def test_rf11_solo_admin(self, api, perfil_cliente, perfil_admin):
        api.force_authenticate(perfil_cliente)
        assert api.get(f"{self.URL}admin/").status_code == 403

        api.force_authenticate(perfil_admin)
        assert api.get(f"{self.URL}admin/").status_code == 200
