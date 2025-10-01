# 🔬 Sistema de Mediciones - Segmentación de Coples

Sistema de visión computacional para segmentación automatizada de coples utilizando modelos de Deep Learning (ONNX) con Django REST Framework y React.

## 📋 Descripción

Este proyecto es un demo de un sistema de análisis visual enfocado en **segmentación de coples**:
- **Segmentación de Defectos**: Identifica y segmenta defectos en la imagen con máscaras precisas
- **Segmentación de Piezas**: Identifica y segmenta piezas con máscaras precisas
- **Cámara GigE Vision**: Soporte prioritario para cámara industrial GigE

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

## 🚀 Setup Rápido (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/ErnestoControla/Mediciones.git
cd Mediciones

# Ejecutar script de setup automático
./setup.sh
```

El script automáticamente:
- Crea el archivo `.env` desde `env.example`
- Inicia PostgreSQL con Docker
- Crea entorno virtual Python
- Instala dependencias
- Ejecuta migraciones

## 📦 Instalación Manual

### 1. Clonar el Repositorio

```bash
git clone https://github.com/ErnestoControla/Mediciones.git
cd Mediciones
```

### 2. Configurar PostgreSQL con Docker

```bash
# Iniciar PostgreSQL
docker-compose up -d postgres

# Ver logs (opcional)
docker-compose logs -f postgres
```

### 2.1. Configurar PostgreSQL (Alternativa nativa - no recomendado)

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

### Flujo Completo de Ejecución

#### 1. Iniciar PostgreSQL (Docker)

```bash
# En la raíz del proyecto
docker-compose up -d postgres

# Verificar que está corriendo
docker-compose ps
```

#### 2. Ejecutar Backend (Django)

```bash
# Terminal 1: Backend
cd asistente
source ../env/bin/activate  # Activar entorno virtual (Linux/Mac)
# o en Windows: ..\env\Scripts\activate

python manage.py runserver
```

El servidor estará disponible en: http://localhost:8000

**Accesos del Backend:**
- **API REST**: http://localhost:8000/api/
- **Admin Django**: http://localhost:8000/admin/
- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/

#### 3. Ejecutar Frontend (React)

```bash
# Terminal 2: Frontend
cd frontend

# Primera vez: instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm run dev
```

La aplicación estará disponible en: http://localhost:5173

#### 4. (Opcional) Administrar Base de Datos con PgAdmin

```bash
# Iniciar PgAdmin
docker-compose up -d pgadmin

# Acceder en: http://localhost:5050
# Usuario: admin@mediciones.local
# Password: admin
```

### Detener Servicios

```bash
# Detener Docker (PostgreSQL y PgAdmin)
docker-compose down

# Para eliminar también los volúmenes (¡CUIDADO! Borra la BD)
docker-compose down -v
```

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
CAMARA_IP=172.16.1.24
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
