# Festival Luciérnagas 2026 — Backend (Django)

Esqueleto inicial del backend para el Sistema de Reservación y Mapeo.
Sigue los tres diagramas de clases (Autenticación / Dominio / Servicios)
y los 12 requerimientos funcionales del documento.

## Stack
- Django 5.x + Django REST Framework
- PostgreSQL + PostGIS (GeoDjango — RF-04.3)
- Celery + Redis (envío async de correos — RF-07.4 ≤ 60s)
- bcrypt para hashing de contraseñas (RF-01.4)
- python-decouple para variables de entorno

## Estructura
```
backend/
  manage.py
  requirements.txt
  .env.example
  config/              # settings, urls, celery, wsgi
  apps/
    usuarios/          # RF-01, RF-02, RF-03  (Vista 1: Autenticación)
      models.py        # Persona, Contraseña, Perfil
      managers.py      # PerfilFactory (Factory Method)
      services.py      # ValidadorInicioSesion (Proxy)
    parques/           # RF-04, RF-05, RF-10, RF-12  (Vista 2: parte)
      models.py        # Parque, DisponibilidadParque
      services.py      # ParqueService
    reservaciones/     # RF-06..RF-09, RF-11
      models.py        # Reservacion + enums
      states.py        # patrón State (ciclo de vida)
      rules.py         # patrón Strategy (4 reglas)
      services.py      # ReservacionService (Facade / Service Layer)
      signals.py       # patrón Observer (SignalReservaCreada)
      tasks.py         # Celery TareaEnvioCorreo
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # ajustar credenciales

# Postgres con PostGIS — crear DB:
#   CREATE DATABASE luciernagas;
#   \c luciernagas
#   CREATE EXTENSION postgis;

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Celery (otra terminal):
```bash
celery -A config worker -l info
```

## Endpoints base
- `POST /api/auth/registro/`        RF-01
- `POST /api/auth/login/`           RF-02
- `POST /api/auth/logout/`          RF-03
- `GET  /api/parques/`              RF-04, RF-05
- `POST /api/parques/`              RF-10  (admin)
- `POST /api/reservaciones/`        RF-06, RF-07
- `GET  /api/reservaciones/mias/`   RF-08
- `POST /api/reservaciones/<id>/cancelar/`  RF-09
- `GET  /api/admin/reservaciones/`  RF-11  (admin)


---

## Testing

### Pytest (unitarias + integración)
```bash
pip install -r requirements-dev.txt
pytest                              # corre todo
pytest apps/reservaciones/tests/    # solo un módulo
pytest -k "rf06"                    # solo tests que matchean 'rf06'
pytest --cov=apps --cov-report=term # con cobertura
```

### Postman (manual + Newman para CI)
Ver `postman/README.md`.
```bash
npm i -g newman
newman run postman/Luciernagas2026.postman_collection.json \
       -e postman/Luciernagas2026.local.postman_environment.json
```

## Mapeo Patrón → Archivo (para QA / Documentación de Pedro)

| Patrón                  | Diagrama                  | Archivo                                    |
|-------------------------|---------------------------|--------------------------------------------|
| Proxy de protección     | Vista 1 (Autenticación)   | `apps/usuarios/services.py`              |
| Factory Method          | Vista 1 (Autenticación)   | `apps/usuarios/managers.py`              |
| State                   | Vista 2 (Dominio)         | `apps/reservaciones/states.py`           |
| Strategy                | Vista 3 (Servicios)       | `apps/reservaciones/rules.py`            |
| Facade / Service Layer  | Vista 3 (Servicios)       | `apps/reservaciones/services.py`         |
| Observer (Signal+Celery)| Vista 3 (Servicios)       | `apps/reservaciones/signals.py` + `tasks.py` |


---

## 🐳 Docker — modo recomendado

Levanta **todo el stack** (Django + PostGIS + Redis + Celery) con un solo comando:

```bash
cp .env.example .env       # ajusta credenciales si hace falta
make up                    # ó: docker compose up --build
```

La primera vez tarda ~3 min (descarga PostGIS y compila libs de GeoDjango).
Después: `make up` arranca en segundos.

### Servicios

| Contenedor              | Puerto | Descripción                       |
|-------------------------|--------|-----------------------------------|
| `luciernagas_web`     | 8000   | Django + DRF                      |
| `luciernagas_db`      | 5432   | PostgreSQL 16 + PostGIS 3.4       |
| `luciernagas_redis`   | 6379   | Broker Celery                     |
| `luciernagas_celery`  | —      | Worker que envía correos (RF-07)  |

### Atajos del Makefile

```bash
make up            # levanta todo
make superuser     # crea admin
make seed          # carga 3 parques de demo
make test          # corre pytest dentro del contenedor
make newman        # corre la colección Postman
make logs          # logs en vivo
make down          # detiene todo
make help          # lista completa
```

### Producción

```bash
make prod-up       # añade nginx + gunicorn + variables DEBUG=False
```

### Acceso

- API:        http://localhost:8000/api/
- Admin:      http://localhost:8000/admin/
- DB (psql):  `make dbshell`
