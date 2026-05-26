# ====================================================================
# Festival Luciérnagas 2026 — Atajos
# Uso: make <target>
# ====================================================================

.PHONY: help up down build logs restart shell dbshell migrate makemigrations \
        superuser test test-cov lint clean newman ps

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------- Docker ----------------
up:  ## Levanta toda la stack (web + db + redis + celery)
	docker compose up --build

up-d:  ## Levanta en background
	docker compose up -d --build

down:  ## Apaga todo
	docker compose down

down-v:  ## Apaga y BORRA volúmenes (¡cuidado: borra la DB!)
	docker compose down -v

build:  ## Reconstruye imágenes sin levantar
	docker compose build

logs:  ## Muestra logs en vivo
	docker compose logs -f

logs-web:  ## Logs solo del contenedor web
	docker compose logs -f web

logs-celery:  ## Logs solo de Celery
	docker compose logs -f celery

restart:  ## Reinicia el contenedor web
	docker compose restart web

ps:  ## Lista contenedores
	docker compose ps

# ---------------- Django ----------------
shell:  ## Shell de Django dentro del contenedor
	docker compose exec web python manage.py shell

bash:  ## Bash dentro del contenedor web
	docker compose exec web bash

dbshell:  ## Cliente psql conectado a la DB
	docker compose exec db psql -U postgres -d luciernagas

migrate:  ## Aplica migraciones
	docker compose exec web python manage.py migrate

makemigrations:  ## Genera migraciones
	docker compose exec web python manage.py makemigrations

superuser:  ## Crea un superusuario interactivamente
	docker compose exec web python manage.py createsuperuser

# ---------------- Tests ----------------
test:  ## Corre pytest dentro del contenedor
	docker compose exec web pytest

test-cov:  ## Pytest con coverage
	docker compose exec web pytest --cov=apps --cov-report=term-missing

newman:  ## Corre la colección de Postman vía Newman (requiere npm i -g newman)
	newman run postman/Luciernagas2026.postman_collection.json \
	       -e postman/Luciernagas2026.local.postman_environment.json

# ---------------- Producción ----------------
prod-up:  ## Levanta stack de producción (con nginx + gunicorn)
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:  ## Apaga stack de producción
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# ---------------- Utilidades ----------------
clean:  ## Borra archivos generados (.pyc, __pycache__, .pytest_cache)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

seed:  ## Carga datos de prueba (parques de ejemplo)
	docker compose exec web python manage.py loaddata fixtures/parques_demo.json
