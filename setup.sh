#!/bin/bash
# Script de setup para el proyecto Mediciones

echo "🚀 Configurando proyecto Mediciones..."

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cp env.example .env
    echo "✅ Archivo .env creado. Edítalo si necesitas cambiar configuraciones."
else
    echo "ℹ️  El archivo .env ya existe."
fi

# Iniciar PostgreSQL con Docker
echo "🐘 Iniciando PostgreSQL con Docker..."
docker-compose up -d postgres

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 5

# Verificar que PostgreSQL está corriendo
if docker ps | grep -q mediciones_postgres; then
    echo "✅ PostgreSQL está corriendo en puerto 5432"
else
    echo "❌ Error: PostgreSQL no pudo iniciar"
    exit 1
fi

# Activar entorno virtual (si existe)
if [ -d "env" ]; then
    echo "🐍 Activando entorno virtual..."
    source env/bin/activate
else
    echo "⚠️  No se encontró entorno virtual. Creando uno..."
    python3 -m venv env
    source env/bin/activate
fi

# Instalar dependencias
echo "📦 Instalando dependencias de Python..."
cd asistente
pip install -r requirements.txt

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate

# Crear superusuario si no existe
echo "👤 ¿Quieres crear un superusuario? (s/n)"
read -r crear_super
if [ "$crear_super" = "s" ]; then
    python manage.py createsuperuser
fi

echo ""
echo "✨ ¡Configuración completada!"
echo ""
echo "Para iniciar el proyecto:"
echo "1. Backend:  cd asistente && python manage.py runserver"
echo "2. Frontend: cd frontend && npm install && npm run dev"
echo ""
echo "Accesos:"
echo "- Backend API: http://localhost:8000"
echo "- Frontend:    http://localhost:5173"
echo "- Django Admin: http://localhost:8000/admin"
echo "- PgAdmin:     http://localhost:5050 (admin@mediciones.local / admin)"
echo ""
