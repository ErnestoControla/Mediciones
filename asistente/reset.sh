#!/usr/bin/env bash
set -e

COMPOSE_FILE="docker-compose.local.yml"

echo "🔴 Deteniendo contenedores y eliminando volúmenes (incluye la BD)..."
docker-compose -f $COMPOSE_FILE down -v

echo "🗑️  Borrando archivos de migraciones (todos excepto __init__.py)..."
find . -type f -path "*/migrations/*.py" ! -name "__init__.py" -delete
find . -type f -path "*/migrations/*.pyc" -delete

echo "🧹 Limpiando cachés de Django (si hay)..."
docker-compose -f $COMPOSE_FILE run --rm django python manage.py clear_cache 2>/dev/null || true

echo "📦 Volviendo a generar migraciones para todas las apps..."
docker-compose -f $COMPOSE_FILE run --rm django python manage.py makemigrations

echo "🚀 Aplicando migraciones en BD limpia..."
docker-compose -f $COMPOSE_FILE run --rm django python manage.py migrate --no-input

echo "🟢 Subiendo contenedores en background..."
docker-compose -f $COMPOSE_FILE up -d

echo "✅ Reset completo. ¡Listo para trabajar desde cero!"
