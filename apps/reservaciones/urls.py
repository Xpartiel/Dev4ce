from django.urls import path
from . import views


urlpatterns = [
    path("dashboard/", views.dashboard_cliente, name="dashboard_cliente"),
    path("mapa/",views.mapa_cliente, name="mapa_cliente"),

    # Vistas de clientes registrados
    path("parques/<int:parque_id>/", views.detalle_parque, name="detalle_parque"),
    path("reservar/<int:parque_id>/paso-1/", views.reservar_paso_1, name="reservar_paso_1"),
    path("reservar/<int:parque_id>/paso-2/", views.reservar_paso_2, name="reservar_paso_2"),
    path("reservar/<int:parque_id>/paso-3/", views.reservar_paso_3, name="reservar_paso_3"),
    path("reservacion-confirmada/", views.reservacion_confirmada, name="reservacion_confirmada"),
    path("mis-reservaciones/", views.mis_reservaciones, name="mis_reservaciones"),
    path("mis-reservaciones/<int:reservacion_id>/", views.detalle_reservacion, name="detalle_reservacion"),
    path("mi-perfil/", views.mi_perfil, name="mi_perfil"),

    # Vistas de admin
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-parques/", views.admin_parques, name="admin_parques"),
    path("admin-reservaciones/", views.admin_reservaciones, name="admin_reservaciones"),
    path("admin-calendario/", views.admin_calendario, name="admin_calendario"),
    path("admin-reportes/", views.admin_reportes, name="admin_reportes"),

    path("admin-parques/crear/", views.crear_parque,name="crear_parque"),
    path("admin-parques/<int:parque_id>/editar/",views.editar_parque,name="editar_parque"),
    path("admin-parques/<int:parque_id>/eliminar/",views.eliminar_parque,name="eliminar_parque"),

    path("admin-reservaciones/crear/",views.crear_reservacion,name="crear_reservacion"),
    path("admin-reservaciones/<int:reservacion_id>/editar/",views.editar_reservacion,name="editar_reservacion"),
    path("admin-reservaciones/<int:reservacion_id>/eliminar/",views.eliminar_reservacion,name="eliminar_reservacion"),
]