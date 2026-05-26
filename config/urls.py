from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/",          include("apps.usuarios.urls")),
    path("api/parques/",       include("apps.parques.urls")),
    path("api/reservaciones/", include("apps.reservaciones.urls")),
]
