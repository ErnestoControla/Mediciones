#!/bin/bash
# Script para iniciar el proyecto Mediciones después de reiniciar el equipo

echo "🚀 Iniciando Sistema de Mediciones..."
echo ""

# 1. Iniciar PostgreSQL con Docker
echo "1️⃣  Iniciando PostgreSQL..."
cd /home/ernesto/Documentos/Proyectos/Mediciones
docker-compose up -d postgres

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 3

# Verificar PostgreSQL
if docker ps | grep -q mediciones_postgres; then
    echo "   ✅ PostgreSQL corriendo en puerto 5432"
else
    echo "   ❌ Error: PostgreSQL no pudo iniciar"
    echo "   Intenta: docker-compose logs postgres"
    exit 1
fi

echo ""
echo "2️⃣  Backend Django:"
echo "   Ejecuta en una terminal:"
echo "   -------------------------------------------"
echo "   conda activate sapera_django"
echo "   cd /home/ernesto/Documentos/Proyectos/Mediciones/asistente"
echo "   export DJANGO_READ_DOT_ENV_FILE=True"
echo "   python manage.py runserver"
echo "   -------------------------------------------"
echo ""

echo "3️⃣  Frontend React:"
echo "   Ejecuta en otra terminal:"
echo "   -------------------------------------------"
echo "   cd /home/ernesto/Documentos/Proyectos/Mediciones/frontend"
echo "   npm run dev"
echo "   -------------------------------------------"
echo ""

echo "✨ Accesos una vez iniciado todo:"
echo "   - Frontend:     http://localhost:5173"
echo "   - Backend API:  http://localhost:8000/api/"
echo "   - Django Admin: http://localhost:8000/admin/"
echo "   - API Docs:     http://localhost:8000/api/docs/"
echo "   - PgAdmin:      http://localhost:5050"
echo ""
echo "🔐 Credenciales Admin: admin / admin"
echo ""

