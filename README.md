# Lucerna

En **Dev4ce** como equipo de desarrollo tecnológico, nos comprometemos al trabajo de calidad y apegado a las necesidades expresas de nuestros clientes, facilitandoles herramientas que les sean de utilidad en sus tareas y asegurando un desarrollo, mantenimiento y corrección de alta velocidad.


### Documento Final:
https://drive.google.com/file/d/1BsAPy_inq29J6KVu9JdxxND7Y0GXgTqR/view?usp=sharing

### Bitacora de Trabajo:
https://drive.google.com/file/d/1HNEcRVOt9u3qu4t-nZs_j1NqdVYUjvdE/view?usp=sharing

## Desarrollo

Para cumplir con un ciclo de desarrollo ágil, optamos por utilizar tecnologías que reflejen esta filosofía por diseño.  

Esto beneficia también la cultura de trabajo del equipo, en pro de mantener un ambiente altamente colaborativo, con un bajo peso tecnológico para los integrantes del equipo de desarrollo

- Git + GitHub para control de versiones
- Python como lenguaje de programación principal
- Django como Framework

## Documentacion

- Google Docs como sistema central de documentación
- PlantUML como herramienta de diagramación


# Dev4ce - Sistema de Reservación y Mapeo para el Festival Internacional de las Luciérnagas 2026

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

## Configuración del correo electrónico (.env)

El sistema envía un correo de confirmación al reservar. Por seguridad, las credenciales **no se incluyen en el repositorio**; se configuran en un archivo `.env` local.

1. Copie la plantilla:

   ```bash
   cp .env.example .env
   ```

2. Edite `.env` y pegue las credenciales (usuario de Gmail y **contraseña de aplicación** de 16 caracteres, no la contraseña normal de la cuenta):

   ```text
   EMAIL_USER=correo@gmail.com
   EMAIL_PASSWORD=xxxxxxxxxxxxxxxx
   ```

   > Las credenciales reales se proporcionan en el **comentario privado de la entrega en Google Classroom**, no en este repositorio.

> La aplicación funciona completa **sin** `.env`; lo único que no ocurrirá es el envío real del correo de confirmación (la reservación se crea y se muestra la confirmación de todas formas).

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
conda activate luciernagas
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

---

## Ejecución de pruebas

El proyecto cuenta con una suite de pruebas automatizadas (unidad, integración y sistema) construida con el framework de pruebas integrado de Django. Las pruebas se ejecutan sobre una base de datos temporal, por lo que **no** modifican `db.sqlite3` ni los datos cargados.

Para ejecutar todas las pruebas:

```bash
python manage.py test apps.usuarios apps.parques apps.reservaciones
```

Para ver el detalle de cada prueba, agregar **-v 2**:

```bash
python manage.py test apps.usuarios apps.parques apps.reservaciones -v 2
```

También es posible ejecutar las pruebas de una sola app o de un solo nivel:

```bash
# Una sola app
python manage.py test apps.reservaciones

# Un solo nivel (unidad / integración / sistema)
python manage.py test apps.parques.tests.test_unitarias
```
