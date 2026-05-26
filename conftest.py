"""
Fixtures globales — Festival Luciérnagas 2026.
"""
from datetime import date
import pytest
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient

from apps.usuarios.managers import PerfilFactory
from apps.usuarios.models import Persona
from apps.parques.models import Parque


# ---------------------------------------------------------------
# Cliente API
# ---------------------------------------------------------------
@pytest.fixture
def api():
    return APIClient()


# ---------------------------------------------------------------
# Personas / Perfiles
# ---------------------------------------------------------------
@pytest.fixture
def persona_cliente(db):
    return Persona.objects.create(
        nombre="André",
        apellido_paterno="Zambrano",
        apellido_materno="Jerónimo",
        email="cliente@luciernagas.mx",
    )


@pytest.fixture
def perfil_cliente(persona_cliente):
    return PerfilFactory.crear_cliente(persona_cliente, "Luciernaga2026")


@pytest.fixture
def persona_admin(db):
    return Persona.objects.create(
        nombre="Uriel",
        apellido_paterno="Balderas",
        apellido_materno="Aguilar",
        email="admin@luciernagas.mx",
    )


@pytest.fixture
def perfil_admin(persona_admin):
    return PerfilFactory.crear_admin(persona_admin, "Luciernaga2026")


# ---------------------------------------------------------------
# Parques
# ---------------------------------------------------------------
@pytest.fixture
def parque_con_cabanas(db):
    return Parque.objects.create(
        nombre="Parque El Faro",
        direccion="Tlalpujahua, Michoacán",
        servicios=["estacionamiento", "fogata"],
        horario="18:00-23:00",
        coordenadas=Point(-100.1693, 19.8125),
        capacidad_max_camping=50,
        capacidad_max_cabania=10,
    )


@pytest.fixture
def parque_sin_cabanas(db):
    return Parque.objects.create(
        nombre="Parque Las Luciérnagas",
        direccion="Nanacamilpa, Tlaxcala",
        servicios=["estacionamiento"],
        horario="19:00-23:00",
        coordenadas=Point(-98.5440, 19.4670),
        capacidad_max_camping=30,
        capacidad_max_cabania=0,
    )


# ---------------------------------------------------------------
# Fechas válidas
# ---------------------------------------------------------------
@pytest.fixture
def fechas_validas():
    """Jueves a sábado de julio 2026 (no incluye martes)."""
    return date(2026, 7, 9), date(2026, 7, 11)


@pytest.fixture
def fechas_con_martes():
    return date(2026, 7, 6), date(2026, 7, 8)   # lunes a miércoles → incluye martes 7


@pytest.fixture
def fechas_fuera_temporada():
    return date(2026, 5, 9), date(2026, 5, 11)
