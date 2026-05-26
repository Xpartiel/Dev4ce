# 📖 Manual del Backend
### Festival Internacional de las Luciérnagas 2026 · Dev4ce

Este manual te lleva de **cero a correr el sistema** y explica dónde vive cada cosa para que cualquiera del equipo pueda contribuir sin perderse.

---

## Índice

1. [¿Qué es esto?](#1-qué-es-esto)
2. [Prerrequisitos](#2-prerrequisitos)
3. [Primera vez · Setup paso a paso](#3-primera-vez--setup-paso-a-paso)
4. [Estructura del proyecto](#4-estructura-del-proyecto)
5. [Cómo funcionan los servicios](#5-cómo-funcionan-los-servicios-docker)
6. [Variables de entorno (.env)](#6-variables-de-entorno-env)
7. [Comandos del día a día](#7-comandos-del-día-a-día)
8. [Probar la API](#8-probar-la-api)
9. [Cómo está organizado el código](#9-cómo-está-organizado-el-código)
10. [Patrones de diseño implementados](#10-patrones-de-diseño-implementados)
11. [Testing](#11-testing)
12. [Flujo de trabajo recomendado para el equipo](#12-flujo-de-trabajo-recomendado-para-el-equipo)
13. [Troubleshooting](#13-troubleshooting)
14. [Glosario rápido](#14-glosario-rápido)

---

## 1. ¿Qué es esto?

Backend del **Sistema de Reservación y Mapeo** del Festival de las Luciérnagas 2026.

Implementa los **12 RFs** del documento de requerimientos:

```
┌─────────────────────────────────────────────────────────────┐
│  RF-01  Registro              RF-07  Confirmación + correo  │
│  RF-02  Login                 RF-08  Mis reservaciones      │
│  RF-03  Logout                RF-09  Cancelar reservación   │
│  RF-04  Mapa interactivo      RF-10  Gestión de parques     │
│  RF-05  Info de parques       RF-11  Vista admin reservas   │
│  RF-06  Crear reservación     RF-12  Control disponibilidad │
└─────────────────────────────────────────────────────────────┘
```

**Stack:**
- **Django 5** + **Django REST Framework** → API JSON
- **PostgreSQL 16 + PostGIS 3.4** → base de datos geoespacial (RF-04.3)
- **Redis + Celery** → correos asíncronos (RF-07.4)
- **bcrypt** → hashing de contraseñas (RF-01.4)
- **Docker Compose** → orquesta todos los servicios

---

## 2. Prerrequisitos

Solo necesitas **una cosa** en tu compu:

- **Docker Desktop** (Mac/Windows) o **Docker Engine + docker compose** (Linux)
  https://www.docker.com/products/docker-desktop/

Verifica que está bien instalado:

```bash
docker --version          # Docker version 24.x ó mayor
docker compose version    # Docker Compose version v2.x
```

Opcional (útil pero no necesario):
- **Make** (viene preinstalado en Mac/Linux; en Windows usa `choco install make` o ejecuta los comandos manualmente)
- **Postman** o **Insomnia** para probar la API → https://www.postman.com/downloads/
- **Newman** (CLI de Postman) si vas a correr la colección en consola: `npm i -g newman`

> 💡 **No necesitas** instalar Python, Postgres, ni Redis localmente. Docker los corre por ti dentro de contenedores.

---

## 3. Primera vez · Setup paso a paso

### 3.1 — Descomprimir el ZIP

```bash
cd ~/proyectos          # o donde quieras
unzip backend.zip
cd backend
```

### 3.2 — Crear el archivo `.env`

```bash
cp .env.example .env
```

Abre `.env` con tu editor. Para desarrollo local **no necesitas tocar nada** — los valores por defecto funcionan.

Si vas a probar el envío real de correos (RF-07), cambia:
```env
EMAIL_HOST_USER=tu-correo@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-app
```
En desarrollo (`DEBUG=True`) los correos se imprimen en la consola del worker de Celery, así que **no urge** configurarlo.

### 3.3 — Levantar todo

```bash
make up
```

(Si no tienes `make`, equivalente: `docker compose up --build`)

La primera vez tarda **~3 minutos** porque descarga PostGIS y compila las librerías de GeoDjango. Las siguientes veces son segundos.

Cuando veas:

```
luciernagas_web     | Starting development server at http://0.0.0.0:8000/
luciernagas_celery  | celery@xxx ready.
```

…está listo. Abre **http://localhost:8000/api/parques/** y deberías ver una lista vacía `[]`.

### 3.4 — Crear el usuario administrador

En **otra terminal** (deja la anterior corriendo):

```bash
make superuser
```

Te pedirá email y contraseña. Úsalo para entrar al admin en http://localhost:8000/admin/

### 3.5 — Cargar parques de demo

```bash
make seed
```

Carga 3 parques reales (Nanacamilpa, El Faro, Cofre de Perote) con coordenadas geoespaciales. Refresca `http://localhost:8000/api/parques/` y los verás.

### 3.6 — Correr las pruebas

```bash
make test
```

Deberían pasar **~30 tests** que validan los 12 RFs.

✅ **Si llegaste hasta aquí, tienes el sistema funcionando.**

---

## 4. Estructura del proyecto

```
backend/
│
├── 📄 Dockerfile                  # Imagen del contenedor de Django
├── 📄 docker-compose.yml          # Orquesta los 4 servicios (dev)
├── 📄 docker-compose.prod.yml     # Overlay para producción (+ nginx)
├── 📄 Makefile                    # Atajos: make up, make test, etc.
├── 📄 requirements.txt            # Dependencias Python (runtime)
├── 📄 requirements-dev.txt        # Dependencias para tests
├── 📄 .env.example                # Plantilla de variables de entorno
├── 📄 manage.py                   # CLI de Django
├── 📄 pytest.ini                  # Config de pytest
├── 📄 conftest.py                 # Fixtures globales para tests
│
├── 📁 config/                     # Configuración del proyecto Django
│   ├── settings.py                # Settings (DB, Celery, CORS, auth...)
│   ├── urls.py                    # URLs raíz
│   ├── celery.py                  # Setup de Celery
│   └── wsgi.py / asgi.py          # Entrada para servidores
│
├── 📁 apps/                       # Apps de Django (una por contexto)
│   │
│   ├── 📁 usuarios/               # 🔐 Vista 1: Autenticación
│   │   ├── models.py              #   Persona, Perfil, AuditLog
│   │   ├── managers.py            #   PerfilFactory (Factory Method)
│   │   ├── services.py            #   ValidadorInicioSesion (Proxy)
│   │   ├── serializers.py         #   Validación de entrada/salida
│   │   ├── views.py               #   Endpoints: registro, login, logout
│   │   ├── urls.py
│   │   └── tests/                 #   Tests RF-01, RF-02, RF-03
│   │
│   ├── 📁 parques/                # 🏞️ Vista 2 (parte): Parques
│   │   ├── models.py              #   Parque, DisponibilidadParque
│   │   ├── services.py            #   ParqueService (CRUD + RF-10.4)
│   │   └── tests/                 #   Tests RF-04, RF-05, RF-10
│   │
│   └── 📁 reservaciones/          # 🎟️ Vista 2 (parte) + Vista 3
│       ├── models.py              #   Reservacion + enums
│       ├── states.py              #   Patrón State (ciclo de vida)
│       ├── rules.py               #   Strategy: 4 reglas de validación
│       ├── services.py            #   Facade: ReservacionService
│       ├── signals.py             #   Observer (Signal de Django)
│       ├── tasks.py               #   Celery: envío de correo
│       └── tests/                 #   Tests RF-06..09, RF-11, RF-12
│
├── 📁 docker/
│   ├── entrypoint.sh              # Script de arranque del contenedor
│   └── nginx.conf                 # Reverse proxy para producción
│
├── 📁 fixtures/
│   └── parques_demo.json          # Datos de prueba (3 parques)
│
└── 📁 postman/
    ├── Luciernagas2026.postman_collection.json
    ├── Luciernagas2026.local.postman_environment.json
    └── README.md
```

---

## 5. Cómo funcionan los servicios (Docker)

Cuando corres `make up`, Docker arranca **4 contenedores** que se hablan entre sí por nombre:

```
┌────────────────────────────────────────────────────────────────┐
│                      docker compose network                    │
│                                                                │
│   ┌─────────────┐         ┌─────────────┐                      │
│   │   web       │ ──────▶ │   db        │                      │
│   │  Django     │  :5432  │  PostGIS    │                      │
│   │  :8000      │         │             │                      │
│   └──────┬──────┘         └─────────────┘                      │
│          │                                                     │
│          ▼ encola tarea                                        │
│   ┌─────────────┐         ┌─────────────┐                      │
│   │   redis     │ ◀────── │   celery    │                      │
│   │   :6379     │ consume │   worker    │                      │
│   └─────────────┘         └─────────────┘                      │
│                                  │                             │
│                                  ▼ envía correo SMTP           │
└──────────────────────────────────┼─────────────────────────────┘
                                   │
                            (a Gmail / Sendgrid / etc.)
```

| Servicio | Imagen | Puerto | Función |
|----------|--------|--------|---------|
| `web` | `python:3.12-slim` (custom) | 8000 | Django + DRF: atiende requests HTTP |
| `db` | `postgis/postgis:16-3.4` | 5432 | Base de datos con extensión geoespacial |
| `redis` | `redis:7-alpine` | 6379 | Cola de mensajes para Celery |
| `celery` | misma que `web` | — | Procesa tareas en background (correos) |

**Flujo típico cuando un usuario crea una reservación:**

1. Frontend manda `POST /api/reservaciones/` → llega a **`web`**
2. `web` consulta y escribe en **`db`** (validar cupo, guardar reserva) dentro de una **transacción atómica** con `SELECT ... FOR UPDATE` (evita sobre-reservaciones, RF-12).
3. Al hacer `commit`, `web` emite una **Signal** que encola la tarea en **`redis`**.
4. **`celery`** (que está escuchando Redis) toma la tarea y envía el correo.
5. `web` ya respondió al usuario en el paso 2; el correo viaja "por detrás".

> Esto cumple **RNF-03** (respuesta del servidor ≤ 3s) y **RF-07.4** (correo ≤ 60s) sin acoplarlos.

---

## 6. Variables de entorno (.env)

| Variable | Default | ¿Para qué? |
|----------|---------|------------|
| `SECRET_KEY` | `dev-insecure-key` | Firma cookies y tokens. **Cambiar en prod.** |
| `DEBUG` | `True` | Si `True`: muestra errores detallados + envía correos a consola. |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Hosts permitidos. En prod: `tu-dominio.com` |
| `DB_NAME` | `luciernagas` | Nombre de la base de datos |
| `DB_USER` / `DB_PASSWORD` | `postgres` / `postgres` | Credenciales DB |
| `DB_HOST` | `127.0.0.1` (local) o `db` (Docker) | Host de Postgres |
| `DB_PORT` | `5432` | |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | URL del broker |
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP |
| `EMAIL_HOST_USER` | (vacío) | Tu correo |
| `EMAIL_HOST_PASSWORD` | (vacío) | App password (no la contraseña normal) |
| `DEFAULT_FROM_EMAIL` | `Festival Luciernagas <no-reply@...>` | Remitente |

### Cómo generar `SECRET_KEY` para producción

```bash
docker compose exec web python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado a tu `.env` de prod.

### App password de Gmail (para que Celery envíe correos reales)

1. Activa **verificación en 2 pasos** en tu cuenta Google.
2. Ve a https://myaccount.google.com/apppasswords
3. Genera una contraseña de aplicación → cópiala a `EMAIL_HOST_PASSWORD`.

---

## 7. Comandos del día a día

Todo se ejecuta vía `make`. Si no tienes Make, equivale a `docker compose exec web <comando>`.

### Levantar / apagar

```bash
make up            # Levanta toda la stack (foreground)
make up-d          # Levanta en background
make down          # Apaga todo (conserva datos)
make down-v        # Apaga y BORRA volúmenes (¡reset total!)
make restart       # Reinicia solo el contenedor web
make logs          # Logs en vivo de todos los servicios
make logs-web      # Logs solo de Django
make logs-celery   # Logs solo del worker de correos
```

### Django

```bash
make shell             # Shell de Django (Python interactivo con models cargados)
make bash              # Bash dentro del contenedor web
make migrate           # Aplica migraciones pendientes
make makemigrations    # Genera migraciones nuevas (después de cambiar models.py)
make superuser         # Crea un admin
make dbshell           # psql conectado a la DB
make seed              # Carga los 3 parques de demo
```

### Tests

```bash
make test                 # Corre todos los tests (~30)
make test-cov             # Tests + reporte de cobertura
make newman               # Corre la colección de Postman (necesita Newman)
```

### Producción

```bash
make prod-up           # Levanta con nginx + gunicorn + DEBUG=False
make prod-down         # Apaga stack de prod
```

### Limpieza

```bash
make clean             # Borra __pycache__, .pyc, .pytest_cache
```

### Ver todos los comandos disponibles

```bash
make help
```

---

## 8. Probar la API

### Opción A — DRF Browsable API (en navegador)

Abre directamente:
- http://localhost:8000/api/parques/ — Lista parques
- http://localhost:8000/api/auth/yo/ — Tu sesión actual
- http://localhost:8000/admin/ — Panel de admin

Te muestra formularios HTML automáticos para hacer GET/POST sin escribir JSON.

### Opción B — Postman (recomendado para el equipo)

1. Abre Postman → **Import** → arrastra:
   - `postman/Luciernagas2026.postman_collection.json`
   - `postman/Luciernagas2026.local.postman_environment.json`
2. Arriba a la derecha selecciona el entorno **Luciernagas · Local**.
3. Ejecuta los requests en el orden que aparecen (cada uno guarda variables que el siguiente usa).

### Opción C — curl rápido

```bash
# Registro
curl -X POST http://localhost:8000/api/auth/registro/ \
  -H "Content-Type: application/json" \
  -d '{"nombre":"André","apellido_paterno":"Zambrano","apellido_materno":"",
       "email":"andre@test.mx","password":"Luciernaga2026"}'

# Login (guarda cookies en un archivo)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"andre@test.mx","password":"Luciernaga2026"}'

# Listar parques con la sesión
curl http://localhost:8000/api/parques/ -b cookies.txt
```

### Endpoints disponibles

| Método | Ruta | RF | Quién |
|--------|------|----|----|
| `POST` | `/api/auth/registro/` | RF-01 | Cualquiera |
| `POST` | `/api/auth/login/` | RF-02 | Cualquiera |
| `POST` | `/api/auth/logout/` | RF-03 | Autenticado |
| `GET`  | `/api/auth/yo/` | — | Autenticado |
| `GET`  | `/api/parques/` | RF-04 | Cualquiera |
| `GET`  | `/api/parques/<id>/` | RF-05 | Cualquiera |
| `POST` | `/api/parques/` | RF-10.1 | Admin |
| `PATCH`| `/api/parques/<id>/` | RF-10.2 | Admin |
| `DELETE`| `/api/parques/<id>/` | RF-10.3 | Admin |
| `POST` | `/api/reservaciones/` | RF-06, RF-07 | Cliente |
| `GET`  | `/api/reservaciones/mias/` | RF-08 | Cliente |
| `POST` | `/api/reservaciones/<id>/cancelar/` | RF-09 | Cliente (dueño) |
| `GET`  | `/api/reservaciones/admin/` | RF-11 | Admin |

---

## 9. Cómo está organizado el código

Seguimos arquitectura por **apps de Django**, una por contexto del dominio:

```
usuarios/        ←  todo lo de identidad y auth
parques/         ←  catálogo de parques + cupos
reservaciones/   ←  núcleo del negocio (reglas, transacciones, correos)
```

Dentro de cada app, los archivos siguen la convención de Django:

| Archivo | Contiene |
|---------|----------|
| `models.py` | Definición de tablas (ORM) |
| `serializers.py` | Validación de entrada/salida JSON (DRF) |
| `views.py` | Endpoints (controladores HTTP) |
| `urls.py` | Rutas |
| `services.py` | **Lógica de negocio** (no en views) |
| `admin.py` | Configuración del panel de admin |
| `tests/` | Pruebas unitarias e integración |

### Regla de oro: **fat models, thin views**

```
HTTP request → view → serializer → SERVICE → model → DB
                         ↑
                  (validación de forma)
                                       ↑
                            (toda la lógica de negocio)
```

Las **views nunca** validan reglas de negocio directamente. Llaman al `Service` correspondiente. Esto hace que la lógica sea **reutilizable** (CLI, tests, otra view) y **testeable sin HTTP**.

---

## 10. Patrones de diseño implementados

Mapeo directo de los diagramas a archivos:

| Patrón | ¿Dónde vive? | ¿Por qué se usa? |
|--------|--------------|------------------|
| **Proxy de protección** | `apps/usuarios/services.py` → `ValidadorInicioSesion` | Aplica rate-limit + auditoría antes de delegar la verificación real de contraseña. Encapsula RNF-02 (seguridad). |
| **Factory Method** | `apps/usuarios/managers.py` → `PerfilFactory` | Crear perfiles con rol predefinido (cliente / admin) sin que el código cliente sepa los detalles. |
| **State** | `apps/reservaciones/states.py` | El ciclo de vida `PENDIENTE → CONFIRMADA → CANCELADA / COMPLETADA` se modela con clases. Cada estado decide qué transiciones permite. Evita un `if/elif` gigante. |
| **Strategy** | `apps/reservaciones/rules.py` | Las 4 reglas (RF-06.2..06.5) se componen como una lista intercambiable. Añadir una regla nueva = añadir una clase, sin tocar el resto. |
| **Facade / Service Layer** | `apps/reservaciones/services.py` → `ReservacionService` | Un único punto de entrada que orquesta: validación (Strategy) + persistencia atómica + notificación (Observer). Las views llaman solo a este. |
| **Observer** | `apps/reservaciones/signals.py` | Cuando una reserva se crea, se emite una **Signal** de Django; el handler encola la tarea de Celery. Desacopla el envío de correo del flujo principal. |

### Ejemplo: añadir una nueva regla de reservación

Supongamos que el comité quiere prohibir grupos de más de 10 personas:

```python
# apps/reservaciones/rules.py
class ReglaMaxAsistentes(ReglaReservacion):
    def validar(self, ctx):
        if ctx.num_asistentes > 10:
            raise ReglaInvalidaError("Máximo 10 personas por reserva.")

# añadir a la lista por defecto:
class ReglasReservacion:
    reglas = [..., ReglaMaxAsistentes()]
```

Eso es todo. **No tocas** views, serializers ni el service. Tests siguen pasando.

---

## 11. Testing

### Ejecutar la suite

```bash
make test                          # todos
make test-cov                      # con cobertura
docker compose exec web pytest apps/reservaciones/  # solo una app
docker compose exec web pytest -k "rf06"            # solo tests que matchean
docker compose exec web pytest -v --tb=long         # más verbose
```

### Tipos de prueba

| Carpeta | Tipo | Qué valida |
|---------|------|------------|
| `apps/usuarios/tests/` | Unidad + integración | RF-01, RF-02, RF-03, Proxy rate-limit |
| `apps/parques/tests/` | Integración | RF-04, RF-05, RF-10, permisos admin vs cliente |
| `apps/reservaciones/tests/test_reglas.py` | **Unitarias** | Cada Strategy aislada |
| `apps/reservaciones/tests/test_state.py` | **Unitarias** | Transiciones del State |
| `apps/reservaciones/tests/test_service.py` | Integración | Facade completo + correo Celery |
| `apps/reservaciones/tests/test_api.py` | E2E | Flujo HTTP completo (cliente DRF) |

### Fixtures (datos preparados)

Viven en `conftest.py` en la raíz. Disponibles en cualquier test:

```python
def test_xxx(perfil_cliente, parque_con_cabanas, fechas_validas):
    ini, fin = fechas_validas
    # ...
```

| Fixture | Qué te da |
|---------|-----------|
| `api` | Cliente HTTP de DRF |
| `perfil_cliente` | Un usuario cliente listo |
| `perfil_admin` | Un usuario admin listo |
| `parque_con_cabanas` | Parque con 50 camping + 10 cabañas |
| `parque_sin_cabanas` | Parque solo con camping |
| `fechas_validas` | Tupla `(ini, fin)` jueves-sábado de julio (sin martes) |
| `fechas_con_martes` | Tupla que incluye un martes |
| `fechas_fuera_temporada` | Tupla en mayo |

---

## 12. Flujo de trabajo recomendado para el equipo

### Para todos

```bash
git pull
make down                    # apaga lo viejo
make up                      # levanta versión nueva
make migrate                 # aplica migraciones nuevas (si hubo)
make test                    # verifica que todo sigue pasando
```

### Andrés (Backend)

1. Crea o modifica modelos en `apps/<app>/models.py`
2. Genera migración: `make makemigrations`
3. Aplica: `make migrate`
4. Implementa lógica en `services.py` (no en views)
5. Expón en `views.py` y `urls.py`
6. Escribe tests en `tests/`
7. Corre `make test` antes de hacer commit

### Juan Carlos (Frontend)

1. Arranca solo el backend: `make up-d` (en background)
2. Apunta tu frontend a `http://localhost:8000/api/`
3. Si necesitas datos: `make seed`
4. Para CORS, los puertos `3000`, `5173`, `5500` ya están permitidos

### Pedro (QA)

1. Diseña casos de prueba en Postman → agrupa por RF
2. Exporta y commitea actualizaciones a `postman/`
3. Antes de la entrega: `make test && make newman`
4. Documenta hallazgos en `bitacora/` (créala si quieres)

### Uriel (Líder técnico)

1. Code reviews enfocados en: ¿la lógica vive en `services.py`? ¿hay tests?
2. Cuida que no se rompan los patrones (ver sección 10)
3. Para RNF-07 (mantenibilidad), documenta cada refactorización en el README

### Sofía (Scrum Master) / André (PO)

- Para demo de sprint: `make up && make seed` y muestra Postman con la colección.
- El admin (http://localhost:8000/admin/) es buen lugar para mostrar datos al cliente.

---

## 13. Troubleshooting

### "Cannot connect to the Docker daemon"
→ Docker Desktop no está corriendo. Ábrelo.

### Puerto 5432 / 8000 / 6379 ocupado
→ Tienes Postgres / otro proyecto Django / Redis corriendo en tu máquina. Apágalo o cambia el puerto en `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"   # mapea local 5433 → contenedor 5432
```

### "relation does not exist" al correr la app
→ Faltan migraciones:
```bash
make migrate
```

### Los cambios en `models.py` no se reflejan
→ Genera la migración + aplica:
```bash
make makemigrations
make migrate
```

### Correos no se envían
→ En `DEBUG=True` los correos van a la consola del worker:
```bash
make logs-celery
```
Si quieres envío real, configura `EMAIL_HOST_*` en `.env` y reinicia: `make restart`.

### "permission denied" en `entrypoint.sh` (Linux)
→ Dale permisos:
```bash
chmod +x docker/entrypoint.sh
```

### Reset total (borrar DB y empezar de cero)
```bash
make down-v       # ⚠️ borra el volumen pg_data
make up
make superuser
make seed
```

### Quiero correr sin Docker (Python local)
1. `python -m venv .venv && source .venv/bin/activate`
2. Instala PostGIS y Redis en tu sistema
3. En `config/settings.py` comenta el bloque de PostGIS y descomenta el de SQLite (línea con `sqlite3`) — útil solo para pruebas sin GeoDjango.
4. `pip install -r requirements.txt -r requirements-dev.txt`
5. `python manage.py migrate && python manage.py runserver`

> 💡 No es recomendado. Docker es más estable para el equipo.

---

## 14. Glosario rápido

| Término | Significado en este proyecto |
|---------|------------------------------|
| **App** | Módulo de Django (no es una app móvil). Una por contexto: `usuarios`, `parques`, `reservaciones`. |
| **Model** | Clase Python que representa una tabla de la DB. |
| **Migration** | Archivo generado que describe cambios al esquema de la DB. Versionable. |
| **Serializer** | Convierte JSON ↔ objetos Python y valida la forma. |
| **View** | Función o clase que atiende un endpoint HTTP. |
| **Service** | Clase con lógica de negocio. Llamada por views, tests, CLI. |
| **Signal** | Mecanismo de Django para emitir eventos. Lo usamos para el Observer. |
| **Celery task** | Función que se ejecuta en background, fuera del request HTTP. |
| **Broker** | Cola de mensajes (Redis) que conecta a quien encola con quien ejecuta. |
| **GeoDjango** | Extensión de Django para datos geoespaciales (puntos, polígonos, distancias). |
| **PostGIS** | Extensión de PostgreSQL que añade tipos y funciones geoespaciales. |
| **Fixture** | Datos precargados (JSON) que sirven para demos y tests. |
| **DRF** | Django REST Framework. La librería que convierte Django en API JSON. |

---

## 📚 Recursos extra

- Django: https://docs.djangoproject.com/es/5.0/
- Django REST Framework: https://www.django-rest-framework.org/
- GeoDjango: https://docs.djangoproject.com/en/5.0/ref/contrib/gis/
- Celery: https://docs.celeryq.dev/
- PostGIS: https://postgis.net/documentation/
- pytest-django: https://pytest-django.readthedocs.io/

---

**Dev4ce · Festival Luciérnagas 2026**
*¿Algo no quedó claro? Pregunta al canal del equipo antes de "googlear y romper algo".* 🪲
