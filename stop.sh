#!/bin/bash
# Script para detener el proyecto Mediciones

echo "🛑 Deteniendo Sistema de Mediciones..."
echo ""

# Detener Backend Django
echo "1️⃣  Deteniendo Backend Django..."
pkill -f "manage.py runserver" 2>/dev/null && echo "   ✅ Backend detenido" || echo "   ℹ️  Backend no estaba corriendo"

# Detener Frontend Vite
echo "2️⃣  Deteniendo Frontend React..."
pkill -f "vite" 2>/dev/null && echo "   ✅ Frontend detenido" || echo "   ℹ️  Frontend no estaba corriendo"

# Detener Docker (PostgreSQL)
echo "3️⃣  Deteniendo PostgreSQL..."
cd /home/ernesto/Documentos/Proyectos/Mediciones
docker-compose down && echo "   ✅ PostgreSQL detenido" || echo "   ℹ️  PostgreSQL no estaba corriendo"

echo ""
echo "✅ Sistema detenido completamente"
echo ""

