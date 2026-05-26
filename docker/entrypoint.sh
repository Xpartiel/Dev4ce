#!/bin/sh
# ====================================================================
# Espera a que Postgres + Redis estén listos, corre migraciones,
# y arranca el comando que reciba.
# ====================================================================
set -e

echo "⏳  Esperando a PostgreSQL ($DB_HOST:$DB_PORT)..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.5
done
echo "✅  PostgreSQL listo."

echo "⏳  Esperando a Redis..."
REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's|redis://([^:/]+).*|\1|')
REDIS_PORT=$(echo "$REDIS_URL" | sed -E 's|redis://[^:]+:([0-9]+).*|\1|')
REDIS_PORT=${REDIS_PORT:-6379}
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
    sleep 0.5
done
echo "✅  Redis listo."

# Solo el servicio "web" debe correr migraciones (no Celery)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔧  Aplicando migraciones..."
    python manage.py migrate --noinput
    echo "📁  Recolectando estáticos..."
    python manage.py collectstatic --noinput || true
fi

exec "$@"
