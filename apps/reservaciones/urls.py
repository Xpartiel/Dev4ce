from django.urls import path
from . import views


urlpatterns = [
    path("dashboard/", views.dashboard_cliente, name="dashboard_cliente"),
    path("mapa/",views.mapa_cliente, name="mapa_cliente"),
    path("parques/<int:parque_id>/", views.detalle_parque, name="detalle_parque"),
]