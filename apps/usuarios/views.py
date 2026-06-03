from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from .models import Usuario, Persona

User = get_user_model()


def login_view(request):

    if request.method == "POST":

        correo = request.POST.get("correo")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=correo,
            password=password
        )

        if user is not None:
            login(request, user)

            if getattr(user, "tipoAdministrador", False):
                return redirect("admin_dashboard")

            return redirect("dashboard_cliente")

        return render(request, "usuarios/login.html", {
            "error": "Correo o contraseña incorrectos."
        })

    return render(request, "usuarios/login.html")

def registro_view(request):

    if request.method != "POST":
        return render(request, "usuarios/registro.html")

    nombre = request.POST.get("nombres")
    apellido_p = request.POST.get("apellidoP","")
    apellido_m = request.POST.get("apellidoM","")
    correo = request.POST.get("correo")
    password = request.POST.get("password")
    
    #Primeras validaciones
        
    if not nombre:
        return render(request, "usuarios/registro.html", {
            "error": "Debe indicar un nombre."
        })

    if not (apellido_p):
        return render(request, "usuarios/registro.html", {
            "error": "Debe indicarse al menos el apellido paterno."
        })
        
    if not correo:
        return render(request, "usuarios/registro.html", {
            "error": "Debe indicarse un correo electrónico."
        })
    
    if not password:
        return render(request, "usuarios/registro.html", {
            "error": "Debe indicarse una contraseña."
        })

    # Evitar segundo registro con mismo correo
        
    if User.objects.filter(username=correo).exists():
        return render(request, "usuarios/registro.html", {
            "error": "Este correo ya tiene cuenta asociada."
        })
        
    # Crear atomicamente los registros de Usuario y Persona
    try:
        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                username=correo,
                password=password,
                nick_name=correo.split("@")[0]
            )

            Persona.objects.create(
                usuario=usuario,
                nombre=nombre,
                apellido_paterno=apellido_p,
                apellido_materno=apellido_m
            )
        
    except Exception as e:
        return render(request, "usuarios/registro.html", {
        "error": f"No pudo completarse el registro: {e}"
    })

    return redirect("login")


def recuperar_password_view(request):
    return render(request, "usuarios/recuperar_password.html")

def logout_view(request):
    logout(request)
    return redirect("landing")

def solo_admin(user):
    return user.is_authenticated and getattr(user, "tipoAdministrador", False)

@user_passes_test(solo_admin, login_url="login")
def registro_admin_view(request):

    error = None

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        password = request.POST.get("password")

        if User.objects.filter(username=correo).exists():
            error = "Ya existe un administrador con ese correo."

        else:

            with transaction.atomic():

                usuario = User.objects.create_user(
                    username=correo,
                    email=correo,
                    password=password,
                    nick_name=nombre,
                    tipoAdministrador=True,
                    is_staff=True,
                )

                Persona.objects.create(
                    usuario=usuario,
                    nombre=nombre,
                    apellido_paterno="",
                    apellido_materno=""
                )

            return redirect("admin_dashboard")

    return render(request, "usuarios/registro_admin.html", {
        "error": error
    })