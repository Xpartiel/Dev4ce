from django.urls import path
from . import views


urlpatterns = [

    path("login/", views.login_view, name="login"),

    path("registro/", views.registro_view, name="registro"),

    path("registro-admin/", views.registro_admin_view, name="registro_admin"),

    path("recuperar-password/", views.recuperar_password_view, name="recuperar_password"),

    path("logout/", views.logout_view, name="logout"),

]