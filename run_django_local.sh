#!/bin/bash
# Script para ejecutar Django localmente con ambiente Sapera
# 
# Uso: ./run_django_local.sh
#
# Este script:
# 1. Activa el ambiente conda sapera_django (que tiene pygigev para cámara GigE)
# 2. Configura las variables de entorno
# 3. Ejecuta Django en modo desarrollo

set -e

echo "🚀 Iniciando Django localmente con soporte para cámara GigE..."

# Verificar que estamos en el directorio correcto
if [ ! -f "asistente/manage.py" ]; then
    echo "❌ Error: Debe ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que PostgreSQL y Frontend estén corriendo en Docker
if ! docker ps | grep -q "asistente_local_postgres"; then
    echo "❌ Error: PostgreSQL no está corriendo"
    echo "   Ejecuta: docker-compose -f asistente/docker-compose.local.yml up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL encontrado"

# Activar ambiente conda
echo "📦 Activando ambiente conda sapera_django..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate sapera_django

# Verificar que el ambiente tenga Django
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Error: Django no está instalado en el ambiente sapera_django"
    echo "   Instala las dependencias: pip install -r asistente/requirements/local.txt"
    exit 1
fi

echo "✅ Ambiente sapera_django activado"

# Configurar variable de entorno para leer .env
export DJANGO_READ_DOT_ENV_FILE=True

# Cambiar al directorio de Django
cd asistente

echo "📡 Verificando conexión a PostgreSQL..."
python manage.py check --database default

echo ""
echo "=========================================="
echo "✅ Django listo para iniciar"
echo "=========================================="
echo ""
echo "Configuración:"
echo "  - Ambiente: sapera_django (con pygigev para GigE)"
echo "  - Base de datos: PostgreSQL en localhost:5432"
echo "  - Cámara GigE: 172.16.1.24"
echo "  - Frontend: http://localhost:5173"
echo ""
echo "Iniciando servidor en http://localhost:8000"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "=========================================="
echo ""

# Ejecutar Django
python manage.py runserver

