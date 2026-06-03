import subprocess
import webbrowser

PYTHON = "python"

fixtures = [
    "apps/usuarios/fixture/tipos_usuario.json",
    "apps/usuarios/fixture/perfiles.json",
    "apps/usuarios/fixture/personas.json",
    "apps/usuarios/fixture/historial_tipo_usuario.json",
    "apps/parques/fixture/parques.json",
    "apps/reservaciones/fixture/reservaciones.json",
]

def run(command):
    subprocess.run(command, check=True)

print("Aplicando migraciones...")
run([PYTHON, "manage.py", "makemigrations"])
run([PYTHON, "manage.py", "migrate"])

print("Cargando fixtures...")
for fixture in fixtures:
    print(f"Cargando {fixture}...")
    run([PYTHON, "manage.py", "loaddata", fixture])

print("Creando superusuario si no existe...")
run([
    PYTHON,
    "manage.py",
    "shell",
    "-c",
    "from apps.usuarios.models import Usuario; "
    "Usuario.objects.filter(username='admin@admin.com').exists() or "
    "Usuario.objects.create_superuser(username='admin@admin.com', email='admin@admin.com', password='12345', nick_name='admin', foto_perfil='perfiles/default.png', tipoAdministrador=True)"
])

print("Iniciando servidor...")
webbrowser.open("http://127.0.0.1:8000/")
run([PYTHON, "manage.py", "runserver"])