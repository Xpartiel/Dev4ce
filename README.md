# PRISMA - Sistema de Reservación y Mapeo para el Festival Internacional de las Luciérnagas 2026

## Requisitos

Antes de comenzar, asegúrese de contar con:

* Python 3.12 o superior
* Conda (Anaconda o Miniconda)
* Git

---

## Clonar el repositorio

```bash
git clone https://github.com/Xpartiel/Dev4ce
cd Dev4ce
```

---

## Crear el entorno virtual

Desde la carpeta raíz del proyecto:

```bash
conda env create -f environment.yml
```

---

## Activar el entorno

### Windows

```bash
conda activate luciernagas
```

### Linux / macOS

```bash
conda activate luciernagas
```

---

## Configuración automática del proyecto

Una vez activado el entorno, ejecutar:

```bash
python setup_project.py
```

Este script realiza automáticamente las siguientes acciones:

* Aplica las migraciones de Django.
* Carga los fixtures iniciales:

  * tipos_usuario.json
  * perfiles.json
  * personas.json
  * historial_tipo_usuario.json
  * parques.json
  * reservaciones.json
* Crea el usuario administrador de pruebas si no existe.
* Inicia el servidor de desarrollo.
* Abre automáticamente el navegador.

---

## Acceso al sistema

### Sitio principal

```text
http://127.0.0.1:8000/
```

### Panel de administración

```text
http://127.0.0.1:8000/cliente/admin-dashboard/
```

### Usuario administrador de pruebas

Usuario:

```text
admin@admin.com
```

Contraseña:

```text
12345
```

---

## Ejecuciones posteriores

Una vez configurado el proyecto por primera vez, únicamente es necesario:

```bash
conda activate Luciernagas
python manage.py runserver
```

---

## Estructura general

```text
apps/
├── core/
├── usuarios/
├── parques/
└── reservaciones/

config/
manage.py
environment.yml
setup_project.py
```

---

## Solución de problemas

### Error: No module named 'folium'

Instalar dependencias nuevamente:

```bash
conda env update -f environment.yml --prune
```

---

### Error: No module named 'dotenv'

Verificar que el entorno esté activado y que las dependencias hayan sido instaladas correctamente.

---

### Reiniciar completamente la base de datos

Eliminar:

```text
db.sqlite3
```
y los archivos
```text
…/migrations/XXXX_initial.py
```
siendo XXXX el número de migración que se ha realizado

y posteriormente ejecutar:

```bash
python setup_project.py
```

para reconstruir la base de datos y cargar nuevamente los fixtures.
