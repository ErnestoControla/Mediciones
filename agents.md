AGENTS.md
Piense en este archivo como la guía de inicio y el manual de estilo para cualquier agente de codificación (como Cursor) que trabaje en el proyecto.

# 1. Visión General del Proyecto (Project Overview)

Este es un proyecto **Demo** de aplicación web (Django + React) para **Visión por Computadora** enfocado en **medición dimensional de coples**.

## 1.1 Propósito
El objetivo principal es la **medición dimensional de objetos** (coples) detectados mediante **segmentación de imágenes**.

## 1.2 Tecnología de Visión Computacional
- **Modelos**: YOLO 11 con segmentación reentrenada
- **Dos modelos ONNX independientes**:
  - `CopleSegPZ1C1V.onnx` - Segmentación de Piezas
  - `CopleSegDef1C8V.onnx` - Segmentación de Defectos
- **Carga individual**: Solo se carga UN modelo a la vez en memoria (optimización de RAM)
- **Precisión**: La generación de máscaras debe ser lo más precisa posible

## 1.3 Lógica de Medición
La implementación debe incluir:
1. **Captura de imagen** desde cámara GigE Vision
2. **Segmentación** con modelo ONNX correspondiente
3. **Posprocesamiento** para refinar máscaras (módulos por desarrollar)
4. **Cálculo de dimensiones geométricas**:
   - Ancho y alto de BBox (en píxeles)
   - Ancho y alto de máscara (en píxeles)
   - Perímetro de máscara (en píxeles)
   - Área de máscara (en píxeles)
   - Excentricidad (adimensional)
   - Orientación (en grados)
5. **Conversión a milímetros** (futuro, basado en factor de conversión)

## 1.4 Almacenamiento de Datos
- **Base de datos**: PostgreSQL
- **Persistencia**: Mediciones y metadatos de análisis
- **Imágenes**: Almacenamiento temporal (últimas 10 imágenes, auto-eliminación)
- **Schema**: Modelos Django definen la estructura de datos

## 1.5 Unidades de Medida
- **Medición primaria**: Píxeles (px)
- **Conversión futura**: Milímetros (mm)
- **Factor de conversión**: Calculado por distancia objeto-cámara
- **Almacenamiento**: Campos separados para px y mm (mm nullable para futuro)
## 1.6 Flujo del Sistema (Optimizado para RAM)

**El sistema opera en modo secuencial para optimizar memoria:**

1. **Seleccionar y inicializar cámara GigE**
   - Conexión a cámara industrial GigE Vision (IP: 172.16.1.24)
   - Iniciar previsualización a 5 FPS

2. **Inicializar UN modelo** (NO ambos simultáneamente)
   - Usuario selecciona: Modelo de Piezas O Modelo de Defectos
   - Se carga en memoria solo el modelo seleccionado

3. **Ejecutar análisis**
   - Captura de imagen
   - Segmentación con modelo cargado
   - Posprocesamiento de máscara
   - Cálculo de dimensiones

4. **Guardar resultados**
   - Datos en PostgreSQL
   - Imagen temporal (últimas 10, auto-eliminación)

5. **Sistema en espera**
   - Puede cambiar de modelo
   - Puede realizar otro análisis
   - Preview se mantiene activo (con hibernación)

## 1.7 Tipos de Análisis

El sistema soporta **3 tipos** de análisis:

1. **`medicion_piezas`**: Medir dimensiones de piezas
   - Usa modelo: `CopleSegPZ1C1V.onnx`
   - Identifica y mide componentes físicos

2. **`medicion_defectos`**: Medir dimensiones de defectos
   - Usa modelo: `CopleSegDef1C8V.onnx`
   - Identifica y mide irregularidades

3. **`rutina_inspeccion`**: Inspección multi-ángulo
   - Simula brazo robótico
   - 6 capturas del mismo objeto desde diferentes ángulos
   - Análisis individual por imagen
   - 1 reporte consolidado
   - 1 imagen consolidada guardada
   - Se almacena como UN solo evento en BD

## 1.8 Sistema de Previsualización y Hibernación

**Preview de Cámara:**
- **Frame rate**: 5 FPS (optimizado para bajo consumo)
- **Tiempo activo**: 1 minuto
- **Auto-hibernación**: Después de 1 minuto sin uso
- **Reactivación**: Manual por usuario desde frontend
- **Estado visible**: Frontend muestra imagen en vivo o alerta de hibernación

**Modelo de Estado** (si necesario):
```python
class EstadoCamara:
    activa: bool
    en_preview: bool  
    hibernada: bool
    ultimo_uso: datetime
    modelo_cargado: str  # 'piezas', 'defectos', None
```

## 1.9 Gestión de Imágenes

**Almacenamiento Temporal:**
- **Cantidad**: Últimas 10 imágenes procesadas
- **Auto-eliminación**: FIFO (First In, First Out)
- **Propósito**: Permitir visualización de resultados recientes
- **Optimización**: No llenar espacio innecesariamente

**Imágenes de Rutina:**
- 6 imágenes individuales procesadas
- 1 imagen consolidada guardada
- Las 6 imágenes individuales se eliminan después de crear la consolidada

---

# 2. Comandos de Configuración y Entorno (Setup Commands)

El entorno de desarrollo se gestiona a través de **Anaconda/Conda**.

## 2.1 Gestor de Entorno
**Anaconda/Conda**

## 2.2 Nombre del Entorno
**`sapera_django`**

Este ambiente fue clonado de `sapera` para mantener las librerías de la cámara GigE (Sapera SDK).

## 2.3 Instrucciones de Instalación de Dependencias

```bash
conda activate sapera_django
cd /home/ernesto/Documentos/Proyectos/Mediciones/asistente
pip install -r requirements.txt
```

## 2.4 Lanzamiento del Sistema (Docker Compose)

**Archivo de configuración**: `asistente/docker-compose.local.yml`

**Servicios incluidos:**
- Django (backend containerizado)
- PostgreSQL (base de datos)
- Frontend (React containerizado)
- Mailpit (servidor de email para desarrollo)

**Comando de arranque:**
```bash
cd /home/ernesto/Documentos/Proyectos/Mediciones
docker-compose -f asistente/docker-compose.local.yml up -d
```

**Scripts de utilidad:**
```bash
# Iniciar PostgreSQL y mostrar instrucciones
./start.sh

# Detener todos los servicios
./stop.sh
```

## 2.5 Comando de Ejecución del Servidor Django

**IMPORTANTE**: Siempre exportar variable de entorno antes de ejecutar:

```bash
conda activate sapera_django
cd /home/ernesto/Documentos/Proyectos/Mediciones/asistente
export DJANGO_READ_DOT_ENV_FILE=True
python manage.py runserver
```

## 2.6 Comando de Ejecución del Frontend

```bash
cd /home/ernesto/Documentos/Proyectos/Mediciones/frontend
npm run dev
```

## 2.7 Accesos del Sistema

- **Frontend**: http://localhost:5173
- **Django Admin**: http://localhost:8000/admin/ (admin/admin)
- **API REST**: http://localhost:8000/api/
- **Swagger Docs**: http://localhost:8000/api/docs/
- **PgAdmin**: http://localhost:5050 (admin@mediciones.local / admin)
---

# 3. Arquitectura de Datos (Data Architecture)

## 3.1 Modelos Django Principales

### **ConfiguracionSistema**
```python
- nombre: str (único)
- ip_camara: IP (default: 172.16.1.24)
- umbral_confianza: float (0.0-1.0, configurable para ambos modelos)
- umbral_iou: float (0.0-1.0)
- distancia_camara_mm: float (para cálculo de factor de conversión)
- factor_conversion_px_mm: float (calculado o manual)
- configuracion_robustez: choice
- activa: bool (solo una puede estar activa)
```

### **AnalisisCople**
```python
- id_analisis: str (único)
- tipo_analisis: choice ('medicion_piezas', 'medicion_defectos', 'rutina_inspeccion')
- estado: choice ('procesando', 'completado', 'error')
- timestamp_captura: datetime
- configuracion: FK → ConfiguracionSistema
- usuario: FK → User
- archivo_imagen: str
- resolucion: int (ancho, alto, canales)
- tiempos_ms: float (captura, segmentacion_*, total)
- metadatos_json: JSON
- es_rutina: bool (indica si es parte de rutina de inspección)
- rutina_padre: FK → RutinaInspeccion (nullable)
```

### **SegmentacionDefecto / SegmentacionPieza**
```python
# Relación
- analisis: FK → AnalisisCople

# Identificación
- clase: str

# Confianza
- confianza: float (0.0-1.0)

# BBox (coordenadas)
- bbox_x1, bbox_y1, bbox_x2, bbox_y2: int

# BBox (dimensiones en píxeles)
- ancho_bbox_px: float
- alto_bbox_px: float

# Centroide
- centroide_x, centroide_y: int

# Máscara (dimensiones en píxeles)
- area_mascara_px: int
- ancho_mascara_px: int
- alto_mascara_px: int
- perimetro_mascara_px: float (NUEVO)

# Geometría avanzada (NUEVO)
- excentricidad: float (0.0-1.0, adimensional)
- orientacion_grados: float (0-360)

# Máscara (coeficientes)
- coeficientes_mascara: JSON

# Mediciones en milímetros (futuro, nullable)
- ancho_mm: float (null=True, blank=True)
- alto_mm: float (null=True, blank=True)
- perimetro_mm: float (null=True, blank=True)
- area_mm: float (null=True, blank=True)
```

### **RutinaInspeccion** (NUEVO)
```python
- id_rutina: str (único)
- timestamp_inicio: datetime
- timestamp_fin: datetime
- configuracion: FK → ConfiguracionSistema
- usuario: FK → User
- estado: choice ('en_progreso', 'completado', 'error')
- num_imagenes_capturadas: int (debe ser 6)
- imagen_consolidada: str
- reporte_json: JSON (resumen de las 6 mediciones)
```

### **EstadoCamara** (NUEVO)
```python
- activa: bool
- en_preview: bool
- hibernada: bool
- ultimo_uso: datetime
- modelo_cargado: str (choice: 'piezas', 'defectos', None)
- frame_rate_actual: int (default: 5)
```

## 3.2 Campos de Medición Requeridos

Para cada segmentación (pieza o defecto):

**En píxeles:**
1. Ancho de BBox
2. Alto de BBox
3. Ancho de máscara
4. Alto de máscara
5. Perímetro de máscara
6. Área de máscara
7. Excentricidad
8. Orientación (grados)

**En milímetros (futuro):**
- Mismo set de medidas con sufijo `_mm`
- Todos nullable/blank
- Se calculan multiplicando por `factor_conversion_px_mm`

---

# 4. Guías de Estilo y Arquitectura (Code Style Guidelines)

El objetivo principal es el **orden**, la **predictibilidad** y el **respeto por la estructura de Django** para facilitar la modificación futura por parte del equipo.

## 4.1 Estructura del Proyecto
- **Convención Django**: Respetar estructura estándar de apps Django
- **Lógica de negocio**: NO en vistas, usar servicios (archivos `services.py`)
- **Separación de responsabilidades**: Models, Views, Serializers, Services
- **Módulos CV**: En `analisis_coples/modules/` organizados por funcionalidad

## 4.2 Tipado de Python
- **Tipado estricto**: REQUERIDO para todas las funciones
- **Type hints**: Usar `typing` module (`Dict`, `List`, `Optional`, `Tuple`, etc.)
- **Ejemplo**:
```python
def calcular_dimensiones(mascara: np.ndarray) -> Dict[str, float]:
    """Calcula dimensiones geométricas de una máscara."""
    ...
```

## 4.3 Front-end (TypeScript/React)
- **TypeScript**: Tipado estricto en todos los componentes
- **Mejores prácticas**: Hooks, Context API, componentes funcionales
- **Organización**: Componentes reutilizables en `components/`, páginas en `pages/`

## 4.4 Generación de Archivos
**EXTREMADAMENTE IMPORTANTE:**
- **NO generar archivos fuera de la estructura de la aplicación**
- **NO crear carpetas fuera de `asistente/`**
- **Ubicación lógica**: Todos los archivos deben tener una ubicación que respete la estructura Django
- **Ejemplo correcto**: `asistente/analisis_coples/modules/mediciones/dimensiones.py`
- **Ejemplo incorrecto**: `scripts_temp/calcular.py` (fuera de estructura)

## 4.5 Arquitectura de Servicios

**Patrón recomendado:**
```
analisis_coples/
  services/
    __init__.py
    base.py              # Clases base abstractas
    camera_service.py    # Gestión de cámara
    segmentation_service.py  # Lógica de segmentación
    measurement_service.py   # Cálculo de dimensiones
    image_service.py     # Gestión de imágenes temporales
```

**Principio**: Un modelo a la vez en memoria
---

# 5. Módulos a Desarrollar (Development Roadmap)

## 5.1 Módulos de Posprocesamiento (Por Desarrollar)
Los módulos actuales de posprocesamiento son del proyecto anterior y deben ser **reemplazados**.

**Nuevos módulos necesarios:**
```
analisis_coples/modules/postprocessing/
  __init__.py
  mask_refinement.py    # Refinamiento de máscaras
  noise_removal.py      # Eliminación de ruido
  edge_smoothing.py     # Suavizado de bordes
```

**Técnicas a implementar:**
- Suavizado de bordes (smoothing)
- Erosión/Dilatación morfológica
- Eliminación de componentes pequeños
- Cierre de huecos (hole filling)

## 5.2 Módulo de Cálculo de Dimensiones (Por Desarrollar)
```
analisis_coples/modules/measurements/
  __init__.py
  dimensions.py         # Cálculo de dimensiones geométricas
  geometry.py           # Características geométricas avanzadas
  converter.py          # Conversión píxeles → milímetros
```

**Funcionalidades:**
- Cálculo de ancho/alto de BBox y máscara
- Cálculo de perímetro con OpenCV
- Cálculo de excentricidad
- Cálculo de orientación
- Conversión a milímetros

## 5.3 Módulo de Gestión de Imágenes (Por Desarrollar)
```
analisis_coples/services/image_service.py
```

**Funcionalidades:**
- Almacenamiento de imagen procesada
- Mantenimiento de últimas 10 imágenes (FIFO)
- Auto-eliminación de imágenes antiguas
- Generación de imagen consolidada (para rutinas)

## 5.4 Sistema de Hibernación de Cámara (Por Desarrollar)
```
analisis_coples/services/camera_service.py
```

**Funcionalidades:**
- Control de preview a 5 FPS
- Timer de 1 minuto para auto-hibernación
- API para reactivar preview manualmente
- WebSocket para streaming de preview al frontend

---

# 6. Instrucciones de Pruebas (Testing Instructions)

No existe un suite de pruebas definido. El agente debe ayudar a establecer esta rutina.

## 6.1 Definición de Tests
Para cualquier nueva funcionalidad (mediciones, segmentación, posprocesamiento), el agente debe crear o actualizar los tests relevantes.

## 6.2 Framework de Tests
Utilizar el framework de pruebas integrado de Django (unittest o pytest).

## 6.3 Comando de Ejecución de Tests
```bash
python manage.py test
```

## 6.4 Regla de Commit
El agente debe:
1. Ejecutar las comprobaciones programáticas pertinentes
2. Corregir las fallas antes de finalizar la tarea
3. El código debe pasar todas las pruebas antes de cualquier commit

---

# 7. Protocolo de Modificación Incremental y Recuperación

## 7.1 Desarrollo Incremental
Para garantizar que las modificaciones sean pequeñas y probables, el agente debe:
- Desglosar tareas complejas en pasos pequeños
- Usar comentarios TODO para tracking
- Validar cada paso antes de avanzar

## 7.2 Scripts de Recuperación del Sistema

**Ya implementados:**
- `start.sh` - Inicia PostgreSQL y muestra instrucciones
- `stop.sh` - Detiene todos los servicios
- `setup.sh` - Configuración inicial completa
- `INICIO_RAPIDO.md` - Guía post-reinicio

**Uso:**
```bash
# Después de reiniciar el equipo
./start.sh

# Luego en terminales separadas:
# Terminal 1: Backend Django
# Terminal 2: Frontend React
```

## 7.3 Plan de Trabajo por Etapas

### **ETAPA 1: Ajustar Estructura Base** ✅ COMPLETADA
- [x] Migrar a PostgreSQL con Docker
- [x] Simplificar modelos (solo segmentación)
- [x] Actualizar modelos con campos de medición dimensional
- [x] Agregar modelo RutinaInspeccion
- [x] Agregar modelo EstadoCamara
- [x] Actualizar tipos de análisis
- [x] Regenerar migraciones

### **ETAPA 2: Sistema de Cámara y Preview** ✅ COMPLETADA
- [x] Módulo de control de cámara GigE (prioridad)
- [x] Preview a 5 FPS con polling HTTP
- [x] Sistema de hibernación automática (1 minuto)
- [x] API REST para control de cámara (/api/camara/*)
- [x] Frontend para visualización de preview
- [x] Manejo de estados (activa, hibernada, etc.)
- [x] Webcam fallback funcional
- [x] Conversión Bayer correcta (BayerBG2BGR)

### **ETAPA 3: Cálculo de Dimensiones** ✅ COMPLETADA (2025-10-02)
- [x] Módulo de extracción de características geométricas (MeasurementService)
- [x] Cálculo de dimensiones (ancho, alto, perímetro)
- [x] Cálculo de excentricidad y orientación
- [x] Almacenamiento en BD (campos px y mm)
- [x] Configuración de factor de conversión (en ConfiguracionSistema)
- [x] Conversión píxeles → milímetros (preparada, campos nullable)
- [x] Integración con SegmentationAnalysisService
- [x] Frontend unificado (captura + análisis)
- [x] Popup de confirmación con resultados
- [x] Visualización de imagen procesada
- [x] Optimización RAM (un modelo a la vez)

**NOTA ETAPA 3**: Modelo CopleSegDef1C8V.onnx causa segfault, usando CopleSegPZ1C1V.onnx temporalmente para defectos. Sistema completamente funcional.

### **ETAPA 4: Posprocesamiento de Máscaras** 🎨
- [ ] Desarrollo de módulos de refinamiento
- [ ] Eliminación de ruido
- [ ] Suavizado de bordes
- [ ] Integración en pipeline de análisis

### **ETAPA 5: Rutina de Inspección Multi-Ángulo** 🔍
- [ ] Modelo RutinaInspeccion
- [ ] Lógica de captura secuencial (6 imágenes)
- [ ] Análisis individual por imagen
- [ ] Generación de imagen consolidada
- [ ] Reporte consolidado
- [ ] API para rutinas

### **ETAPA 6: Gestión de Imágenes Temporales** 🖼️
- [ ] Sistema de almacenamiento FIFO (últimas 10)
- [ ] Auto-eliminación de imágenes antiguas
- [ ] API para servir imágenes temporales
- [ ] Frontend para visualizar resultados

---

# 8. Decisiones de Diseño Documentadas

## 8.1 Optimización de RAM
**Decisión**: No cargar ambos modelos simultáneamente
- **Razón**: Reducir consumo de RAM en navegador
- **Implementación**: Cargar solo el modelo necesario según tipo de análisis
- **Impacto**: El usuario debe seleccionar el modelo antes de analizar

## 8.2 Tipos de Análisis Simplificados
**Decisión**: Solo 3 tipos (eliminado "análisis completo")
- `medicion_piezas` - Solo modelo de piezas
- `medicion_defectos` - Solo modelo de defectos
- `rutina_inspeccion` - 6 capturas multi-ángulo

## 8.3 Umbral de Confianza Único
**Decisión**: Un solo umbral configurable para ambos modelos
- **Razón**: Simplificar configuración
- **Campo**: `ConfiguracionSistema.umbral_confianza`
- **Aplicación**: Se usa para piezas y defectos por igual

## 8.4 Rutina de Inspección
**Decisión**: 1 objeto, 6 ángulos, 1 evento consolidado
- **Flujo**: Captura secuencial de 6 imágenes del mismo objeto
- **Análisis**: Individual por imagen (6 análisis)
- **Almacenamiento**: 
  - 1 evento `RutinaInspeccion` en BD
  - 6 análisis individuales vinculados
  - 1 imagen consolidada guardada
  - 6 imágenes individuales eliminadas después de consolidar

## 8.5 Gestión de Imágenes
**Decisión**: Mantener solo últimas 10 imágenes
- **Estrategia**: FIFO (First In, First Out)
- **Auto-eliminación**: Automática al guardar nueva imagen
- **Razón**: Balance entre visualización de resultados y uso de disco

## 8.6 Factor de Conversión
**Decisión**: Calculado por distancia objeto-cámara
- **Método**: Usar distancia conocida + parámetros de cámara
- **Almacenamiento**: En `ConfiguracionSistema`
- **Campos**:
  - `distancia_camara_mm` - Distancia en milímetros
  - `factor_conversion_px_mm` - Factor calculado o manual

## 8.7 Estado de Cámara
**Decisión**: Modelo en BD + visualización en frontend
- **Modelo**: `EstadoCamara` (singleton) para persistir estado
- **Frontend**: Muestra preview en vivo o alerta de hibernación
- **API**: WebSocket o polling para actualización de estado

---

# 9. Prioridades de Desarrollo

## 9.1 Hardware
**Cámara GigE Vision** es la prioridad
- Marca/Modelo: Compatible con Sapera SDK
- IP fija: 172.16.1.24
- Conexión: Ethernet
- Webcam: Solo como fallback en caso de falla

## 9.2 Performance
- **RAM**: Crítico - Un modelo a la vez
- **Preview**: Optimizado a 5 FPS
- **Hibernación**: Automática después de 1 minuto
- **Imágenes**: Solo últimas 10 en disco

## 9.3 Funcionalidad
1. **Prioridad Alta**: Segmentación y medición dimensional
2. **Prioridad Media**: Preview y hibernación
3. **Prioridad Baja**: Rutina de inspección multi-ángulo

---

# 10. Instrucciones de Pruebas (Testing Instructions)

No existe un suite de pruebas definido. El agente debe ayudar a establecer esta rutina.

## 10.1 Definición de Tests
Para cualquier nueva funcionalidad (mediciones, segmentación, posprocesamiento), el agente debe crear o actualizar los tests relevantes.

## 10.2 Framework de Tests
Utilizar el framework de pruebas integrado de Django (unittest o pytest).

## 10.3 Comando de Ejecución de Tests
```bash
python manage.py test
```

## 10.4 Regla de Commit
El agente debe:
1. Ejecutar comprobaciones programáticas
2. Corregir fallas antes de finalizar
3. Código debe pasar tests antes de commit
4. Usar mensajes de commit descriptivos (convención conventional commits)

## 10.5 Áreas de Testing Críticas
- **Modelos**: Validación de datos, constraints, métodos
- **Servicios**: Lógica de negocio, manejo de errores
- **API**: Endpoints, autenticación, respuestas
- **Cálculo de dimensiones**: Precisión de mediciones
- **Gestión de imágenes**: FIFO, eliminación automática

---

# 11. Notas Importantes para el Equipo

## 11.1 Ambiente SIEMPRE sapera_django
⚠️ **CRÍTICO**: No usar ambiente `base` o `sapera`, solo `sapera_django`
- Contiene librerías de Sapera SDK para cámara GigE
- Contiene todas las dependencias de Django
- Es el único ambiente compatible con el proyecto completo

## 11.2 Variable de Entorno Obligatoria
⚠️ **SIEMPRE** antes de ejecutar comandos Django:
```bash
export DJANGO_READ_DOT_ENV_FILE=True
```

## 11.3 Orden de Inicio
1. PostgreSQL (Docker) - PRIMERO
2. Backend Django - SEGUNDO  
3. Frontend React - TERCERO

## 11.4 Consultar Documentación
- `README.md` - Documentación general
- `INICIO_RAPIDO.md` - Guía post-reinicio
- `agents.md` - Este archivo (guía completa para agentes de IA)

## 11.5 Archivos a NO Modificar Sin Consultar
- Migraciones generadas automáticamente
- `docker-compose.local.yml`
- Modelos ONNX en `Modelos/`
- Configuración de Sapera SDK

---

# 12. Glosario de Términos

- **Cople**: Objeto a analizar (componente industrial)
- **GigE**: Gigabit Ethernet (cámara industrial)
- **Sapera**: SDK de Teledyne DALSA para cámaras industriales
- **ONNX**: Open Neural Network Exchange (formato de modelo ML)
- **YOLO**: You Only Look Once (arquitectura de detección/segmentación)
- **Máscara**: Imagen binaria que delimita un objeto segmentado
- **BBox**: Bounding Box (caja delimitadora rectangular)
- **FIFO**: First In, First Out (primero en entrar, primero en salir)
- **Excentricidad**: Medida de qué tan alargado es un objeto (0=círculo, 1=línea)
- **Orientación**: Ángulo de rotación del eje mayor del objeto
- **FPS**: Frames Per Second (cuadros por segundo)

---

**Última actualización**: 2025-10-01  
**Versión**: 2.0  
**Estado**: Activo y en desarrollo  
**Responsable**: Ernesto Controla