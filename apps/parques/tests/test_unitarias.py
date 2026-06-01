"""
Pruebas de UNIDAD app parques.

Metodos del modelo Parque y el constructor del mapa, en aislamiento (sin BD).
Cada prueba indica el requisito en que se basa.

Nota: se asume el modelo Parque actual, con capacidad por cabana y por camping
(capacidad_max_cabana / capacidad_max_camping) y capacidad_total como propiedad
calculada.
"""
from decimal import Decimal
from django.test import SimpleTestCase

from apps.parques.models import Parque
from apps.parques.mapas import construir_mapa


class ParqueModeloTests(SimpleTestCase):

    def test_capacidad_total_suma_cabana_y_camping(self):
        # Basado en: RF-12.1 (capacidad total del parque = cabanas + camping).
        parque = Parque(capacidad_max_cabana=30, capacidad_max_camping=50)
        self.assertEqual(parque.capacidad_total, 80)

    def test_capacidad_total_es_cero_sin_capacidades(self):
        # Basado en: RF-12.1 (borde: parque sin capacidades cargadas).
        parque = Parque(capacidad_max_cabana=0, capacidad_max_camping=0)
        self.assertEqual(parque.capacidad_total, 0)

    def test_lista_servicios_separa_por_comas(self):
        # Basado en: RF-05 (mostrar los servicios disponibles del parque).
        parque = Parque(servicios="Senderos, Estacionamiento , Banos")
        self.assertEqual(parque.lista_servicios,
                         ["Senderos", "Estacionamiento", "Banos"])

    def test_lista_servicios_vacia_devuelve_lista_vacia(self):
        # Basado en: RF-05 (borde: parque sin servicios cargados).
        self.assertEqual(Parque(servicios="").lista_servicios, [])

    def test_parque_str_devuelve_nombre(self):
        # Basado en: modelo Parque (representacion legible).
        self.assertEqual(str(Parque(nombre="Bosque Esmeralda")), "Bosque Esmeralda")


class ConstruirMapaTests(SimpleTestCase):

    def test_construir_mapa_incluye_nombres_de_parques(self):
        # Basado en: RF-04 (un marcador por parque) y RF-05 (info en el popup).
        parques = [
            Parque(nombre="Bosque Esmeralda", estado="Puebla",
                   latitud=Decimal("19.12"), longitud=Decimal("-98.73"),
                   precio_camping=Decimal("450")),
            Parque(nombre="Valle San Rafael", estado="Puebla",
                   latitud=Decimal("19.29"), longitud=Decimal("-98.62"),
                   precio_camping=Decimal("600")),
        ]
        html = construir_mapa(parques, con_enlaces=False)
        self.assertIn("Bosque Esmeralda", html)
        self.assertIn("Valle San Rafael", html)
