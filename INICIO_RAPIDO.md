# ⚡ Inicio Rápido - Sistema de Mediciones

## 🔄 **DESPUÉS DE REINICIAR EL EQUIPO**

### **Método RECOMENDADO: Django Local + Docker** 📹🐳

**Este método es NECESARIO para usar la cámara GigE en 172.16.1.24**

```bash
cd /home/ernesto/Documentos/Proyectos/Mediciones

# Iniciar servicios en Docker (PostgreSQL, Frontend, Mailpit)
docker-compose -f asistente/docker-compose.local.yml up -d postgres frontend mailpit

# Ejecutar Django localmente con soporte GigE (en otra terminal)
./run_django_local.sh
```

**Esto inicia:**
- ✅ PostgreSQL (Docker)
- ✅ Frontend React (Docker)
- ✅ Mailpit (Docker)
- ✅ Django con pygigev para cámara GigE (Local - ambiente sapera_django)

**Espera ~10 segundos** y todos los servicios estarán listos.

---

### **Método Alternativo: Todo en Docker (Solo Webcam)** 🐳

Solo si NO necesitas la cámara GigE (usará webcam como fallback):

```bash
cd /home/ernesto/Documentos/Proyectos/Mediciones
docker-compose -f asistente/docker-compose.local.yml up -d
```

**Esto inicia TODO en Docker:**
- ✅ PostgreSQL
- ✅ Django (con fallback a webcam)
- ✅ Frontend (React)
- ✅ Mailpit

---

## 🌐 **ACCESOS:**

Una vez que todo esté corriendo:

- **Frontend**: http://localhost:5173
- **Admin Django**: http://localhost:8000/admin/ (admin/admin)
- **API Docs**: http://localhost:8000/api/docs/
- **PgAdmin**: http://localhost:5050 (admin@mediciones.local / admin)

---

## 🛑 **DETENER TODO:**

### **Si usas Docker (Recomendado):**
```bash
cd /home/ernesto/Documentos/Proyectos/Mediciones
docker-compose -f asistente/docker-compose.local.yml down
```

### **Si usas desarrollo local:**
```bash
./stop.sh
```

---

## ⚠️ **IMPORTANTE:**

### **Ambiente Correcto:**
**SIEMPRE** usa `sapera_django` (NO `sapera` ni `base`):
```bash
conda activate sapera_django
```

### **Variable de Entorno:**
**SIEMPRE** exporta antes de ejecutar Django:
```bash
export DJANGO_READ_DOT_ENV_FILE=True
```

### **Orden de Inicio:**
1. PostgreSQL (Docker) - PRIMERO
2. Backend (Django) - SEGUNDO
3. Frontend (React) - TERCERO

---

## 🔧 **SOLUCIÓN DE PROBLEMAS:**

### **PostgreSQL no inicia:**
```bash
docker-compose down
docker-compose up -d postgres
docker-compose logs -f postgres
```

### **Backend falla con "No module named 'X'":**
```bash
conda activate sapera_django
pip install -r asistente/requirements.txt
```

### **Frontend falla:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### **Ver logs del Backend:**
```bash
tail -f /tmp/django_mediciones.log
```

---

## 📝 **COMANDOS ÚTILES:**

```bash
# Ver estado de Docker
docker-compose ps

# Ver procesos corriendo
ps aux | grep "manage.py runserver"
ps aux | grep "vite"

# Verificar puertos
netstat -tuln | grep -E ":(8000|5173|5432)"

# Ver logs de PostgreSQL
docker-compose logs -f postgres
```

---

## 🎯 **QUICK START (Una sola terminal):**

```bash
# Iniciar todo en background
cd /home/ernesto/Documentos/Proyectos/Mediciones

# 1. PostgreSQL
docker-compose up -d postgres

# 2. Backend (en background)
conda activate sapera_django
cd asistente
export DJANGO_READ_DOT_ENV_FILE=True
nohup python manage.py runserver > /tmp/django_mediciones.log 2>&1 &

# 3. Frontend (en background)
cd ../frontend
nohup npm run dev > /tmp/vite_mediciones.log 2>&1 &

# Ver logs
tail -f /tmp/django_mediciones.log
tail -f /tmp/vite_mediciones.log
```

---

**✨ ¡Listo! El sistema está corriendo y listo para trabajar.**
