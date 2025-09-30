#!/bin/bash

# USO:
#   ./rename_project.sh mr_dispenser asistente

OLD_NAME=$1
NEW_NAME=$2

if [ -z "$OLD_NAME" ] || [ -z "$NEW_NAME" ]; then
  echo "Uso: ./rename_project.sh <nombre_anterior> <nombre_nuevo>"
  exit 1
fi

echo "🔄 Renombrando proyecto de '$OLD_NAME' a '$NEW_NAME'..."

# 1. Renombrar carpeta principal del proyecto Django
if [ -d "$OLD_NAME" ]; then
  mv "$OLD_NAME" "$NEW_NAME"
  echo "✅ Carpeta renombrada: $OLD_NAME -> $NEW_NAME"
fi

# 2. Reemplazar en todos los archivos del proyecto
echo "🔍 Reemplazando nombres en archivos..."
grep -rl "$OLD_NAME" . | grep -v "\.git" | xargs sed -i "s/$OLD_NAME/$NEW_NAME/g"

# 3. (Opcional) Reemplazo específico de título de la API (si es necesario)
API_TITLE_OLD=$(echo "$OLD_NAME" | sed 's/_/ /g' | sed 's/\b\(.\)/\u\1/g')
API_TITLE_NEW=$(echo "$NEW_NAME" | sed 's/_/ /g' | sed 's/\b\(.\)/\u\1/g')

grep -rl "$API_TITLE_OLD API" . | grep -v "\.git" | xargs sed -i "s/${API_TITLE_OLD} API/${API_TITLE_NEW} API/g"
grep -rl "Documentation of API endpoints of $API_TITLE_OLD" . | grep -v "\.git" | xargs sed -i "s/Documentation of API endpoints of $API_TITLE_OLD/Documentation of API endpoints of $API_TITLE_NEW/g"

echo "✅ Reemplazos realizados"

# 4. Mostrar mensaje final
echo "🚀 Proyecto renombrado de '$OLD_NAME' a '$NEW_NAME'."
echo "Revisa los siguientes archivos manualmente si es necesario:"
echo "- docker-compose.*.yml"
echo "- Dockerfile"
echo "- config/settings/*"
echo "- archivos de frontend/"
echo "- documentación en docs/"

