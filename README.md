# 🔬 Sistema de Mediciones - Análisis de Coples

Sistema de visión computacional para análisis automatizado de coples utilizando modelos de Deep Learning (ONNX) con Django REST Framework y React.

## 📋 Descripción

Este proyecto es un demo de un sistema de análisis visual de coples que integra:
- **Clasificación**: Determina si un cople es aceptado o rechazado
- **Detección**: Identifica piezas y defectos en la imagen
- **Segmentación**: Genera máscaras precisas de defectos y piezas

## 🏗️ Arquitectura

### Backend
- **Framework**: Django 5.2 + Django REST Framework
- **Base de datos**: PostgreSQL
- **Autenticación**: JWT (SimpleJWT) + Session Auth
- **Modelos ML**: ONNX Runtime para inferencia
- **Captura**: Soporte para cámara GigE Vision + Webcam fallback

### Frontend
- **Framework**: React 19 + TypeScript
- **UI**: Material-UI (MUI)
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Build**: Vite

## 🚀 Requisitos Previos

### Software Necesario
- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ y npm/yarn
- Git

### Hardware (Opcional)
- Cámara GigE Vision (o webcam como fallback)
- Conexión Ethernet para cámara GigE

## 📦 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/ErnestoControla/Mediciones.git
cd Mediciones
```

### 2. Configurar PostgreSQL

```bash
# Crear base de datos y usuario
sudo -u postgres psql

# En el prompt de PostgreSQL:
CREATE DATABASE mediciones_db;
CREATE USER mediciones_user WITH PASSWORD 'mediciones_pass';
ALTER ROLE mediciones_user SET client_encoding TO 'utf8';
ALTER ROLE mediciones_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE mediciones_user SET timezone TO 'America/Mexico_City';
GRANT ALL PRIVILEGES ON DATABASE mediciones_db TO mediciones_user;
\q
```

### 3. Configurar Backend (Django)

```bash
# Crear entorno virtual
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate

# Instalar dependencias
cd asistente
pip install -r requirements.txt

# Copiar archivo de configuración
cp ../env.example ../.env

# Editar .env con tus configuraciones
nano ../.env  # o el editor de tu preferencia

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Crear configuración inicial (opcional)
python manage.py crear_configuracion_inicial
```

### 4. Configurar Frontend (React)

```bash
# Ir al directorio frontend
cd ../frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env.local

# Editar .env.local si es necesario
nano .env.local
```

## 🎯 Uso

### Ejecutar Backend

```bash
cd asistente
source ../env/bin/activate  # Activar entorno virtual
python manage.py runserver
```

El servidor estará disponible en: http://localhost:8000

- **Admin Django**: http://localhost:8000/admin/
- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/

### Ejecutar Frontend

```bash
cd frontend
npm run dev
```

La aplicación estará disponible en: http://localhost:5173

## 📁 Estructura del Proyecto

```
Mediciones/
├── asistente/                    # Backend Django
│   ├── analisis_coples/          # App principal de análisis
│   │   ├── api/                  # Endpoints REST
│   │   ├── models.py             # Modelos principales
│   │   ├── resultados_models.py  # Modelos de resultados
│   │   ├── services_real.py      # Lógica de negocio
│   │   ├── modules/              # Módulos de análisis
│   │   │   ├── capture/          # Captura de imagen
│   │   │   ├── classification/   # Clasificación
│   │   │   ├── detection/        # Detección
│   │   │   └── segmentation/     # Segmentación
│   │   └── Modelos/              # Modelos ONNX
│   ├── asistente/                # App base de Django
│   ├── core/                     # Modelos core (Roles, etc.)
│   ├── config/                   # Configuración Django
│   │   ├── settings/             # Settings por entorno
│   │   ├── urls.py               # URLs principales
│   │   └── api_router.py         # Router de API
│   └── manage.py
├── frontend/                     # Frontend React
│   ├── src/
│   │   ├── api/                  # Servicios API
│   │   ├── components/           # Componentes React
│   │   ├── pages/                # Páginas
│   │   ├── context/              # Context API
│   │   └── theme.ts              # Tema MUI
│   └── package.json
├── env.example                   # Variables de entorno ejemplo
├── .gitignore                    # Archivos ignorados
└── README.md                     # Este archivo
```

## 🔧 Configuración

### Variables de Entorno Principales

Copiar `env.example` a `.env` y configurar:

```bash
# Base de datos
DATABASE_URL=postgres://mediciones_user:mediciones_pass@localhost:5432/mediciones_db

# Django
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=tu-secret-key-aqui

# Cámara
CAMARA_IP=172.16.1.21
UMBRAL_CONFIANZA_DEFAULT=0.55
```

## 📊 Modelos de Datos

### Configuración del Sistema
- IP de cámara
- Umbrales de confianza e IoU
- Configuración de robustez

### Análisis de Cople
- Metadatos del análisis
- Timestamps de captura y procesamiento
- Tiempos de ejecución por módulo
- Archivos generados (imagen, JSON)

### Resultados
- **Clasificación**: Clase predicha y confianza
- **Detección de Piezas**: BBoxes, centroides, áreas
- **Detección de Defectos**: BBoxes, centroides, áreas
- **Segmentación**: Máscaras, coeficientes, áreas

## 🔌 API Endpoints Principales

### Autenticación
```
POST /api/token/                    # Obtener token JWT
POST /api/token/refresh/            # Refrescar token
POST /api/users/register/           # Registrar usuario
GET  /api/users/me/                 # Perfil actual
```

### Sistema de Análisis
```
GET    /api/analisis/configuraciones/     # Listar configuraciones
POST   /api/analisis/configuraciones/     # Crear configuración
POST   /api/analisis/configuraciones/{id}/activar/  # Activar configuración

GET    /api/analisis/resultados/          # Listar análisis
POST   /api/analisis/resultados/realizar_analisis/  # Realizar análisis
GET    /api/analisis/resultados/estadisticas/  # Estadísticas

GET    /api/analisis/sistema/estado/      # Estado del sistema
POST   /api/analisis/sistema/inicializar/ # Inicializar sistema
POST   /api/analisis/sistema/liberar/     # Liberar recursos
```

## 🧪 Testing

```bash
# Ejecutar tests
cd asistente
python manage.py test

# Con coverage
coverage run -m pytest
coverage report
coverage html
```

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar configuración
psql -U mediciones_user -d mediciones_db
```

### Error de cámara no disponible
El sistema usa automáticamente webcam como fallback si la cámara GigE no está disponible.

### Error de modelos ONNX no encontrados
Verificar que los modelos estén en `asistente/analisis_coples/Modelos/`

## 📝 Próximas Funcionalidades

- [ ] Sistema de reportes en PDF
- [ ] Dashboard de estadísticas en tiempo real
- [ ] Notificaciones por email
- [ ] Exportación de datos a Excel
- [ ] Sistema de backup automático
- [ ] Modo producción con Docker

## 🤝 Contribuir

Este es un proyecto de demo. Para modificaciones:

1. Crear un branch desde `main`
2. Hacer cambios
3. Ejecutar tests
4. Crear Pull Request

## 📄 Licencia

Proyecto privado de Tecnologías Controla.

## 👥 Autores

- Ernesto Controla - Desarrollo principal

## 📞 Soporte

Para soporte o preguntas, contactar al equipo de desarrollo.

---

**Nota**: Este es un proyecto de demostración para análisis visual de coples. No usar en producción sin las configuraciones de seguridad apropiadas.
