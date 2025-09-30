#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.local.yml"

echo "🛑 Parando contenedores y eliminando volúmenes (incluye la BD)..."
docker-compose -f $COMPOSE_FILE down -v

echo "🗑  Borrando migraciones antiguas de core y users..."
find core/migrations -type f -name "*.py" ! -name "__init__.py" -delete
find asistente/users/migrations -type f -name "*.py" ! -name "__init__.py" -delete
find core/migrations -type f -name "*.pyc" -delete
find asistente/users/migrations -type f -name "*.pyc" -delete

echo "📦 Generando migraciones iniciales para core..."
docker-compose -f $COMPOSE_FILE run --rm django python manage.py makemigrations core

echo "📦 Generando migraciones iniciales para users..."
docker-compose -f $COMPOSE_FILE run --rm django python manage.py makemigrations users

echo "🚀 Aplicando todas las migraciones en la BD limpia..."
docker-compose -f $COMPOSE_FILE run --rm django python manage.py migrate --no-input

echo "🔃 Subiendo de nuevo los contenedores en background..."
docker-compose -f $COMPOSE_FILE up -d

echo "✅ ¡Reset completo! Base de datos y migraciones arrancadas desde cero."
