# syntax=docker/dockerfile:1.6
# ====================================================================
# Festival Luciérnagas 2026 — Backend Django
# ====================================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# --- Dependencias del sistema ---
# GeoDjango necesita: GDAL, GEOS, PROJ
# psycopg necesita: libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Dependencias Python ---
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt

# En dev queremos también pytest, etc.
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then pip install -r requirements-dev.txt; fi

# --- Código ---
COPY . .

# --- Entrypoint ---
RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["bash", "/app/docker/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
