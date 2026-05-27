from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test

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

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        password = request.POST.get("password")

        if User.objects.filter(username=correo).exists():
            return render(request, "usuarios/registro.html", {
                "error": "Ya existe una cuenta registrada con ese correo."
            })

        User.objects.create_user(
            username=correo,
            email=correo,
            password=password,
            nombre_completo=nombre,
            tipoAdministrador=False
        )

        return redirect("login")

    return render(request, "usuarios/registro.html")


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

            User.objects.create_user(
                username=correo,
                email=correo,
                password=password,
                nombre_completo=nombre,
                tipoAdministrador=True,
                is_staff=True,
            )

            return redirect("admin_dashboard")

    return render(request, "usuarios/registro_admin.html", {
        "error": error
    })