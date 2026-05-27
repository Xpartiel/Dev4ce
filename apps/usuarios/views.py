from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()


def login_view(request):
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