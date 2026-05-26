from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("admin", views.ReservacionAdminViewSet, basename="reservaciones-admin")

urlpatterns = [
    path("",               views.crear_reservacion,    name="crear-reservacion"),
    path("mias/",          views.mis_reservaciones,    name="mis-reservaciones"),
    path("<int:pk>/cancelar/", views.cancelar_reservacion, name="cancelar-reservacion"),
] + router.urls
