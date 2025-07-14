# Documentación Técnica del Sistema SHPD (Smart Healthy Posture Detector)

**Autor:** Rodolfo Giacomodonatto  
**Email:** rodol.giacomodonatto@gmail.com  
**Universidad:** Universidad Tecnológica Nacional - Facultad Regional Mendoza  
**Carrera:** Ingeniería en Electrónica  

## 1. Introducción Técnica

El sistema SHPD (Smart Healthy Posture Detector) constituye una solución integral para el monitoreo y análisis postural en tiempo real, específicamente diseñada para entornos de trabajo sedentarios. El sistema implementa técnicas de visión por computadora y aprendizaje automático para detectar y analizar posturas corporales, proporcionando retroalimentación continua y generando métricas relevantes para el análisis kinesiológico y ergonómico.

La arquitectura del sistema se basa en un diseño distribuido que integra dispositivos de captura de video (Raspberry Pi 3B+), procesamiento en tiempo real mediante MediaPipe, almacenamiento de métricas en bases de datos relacionales y Redis, comunicación con usuarios a través de Telegram, y una interfaz web para visualización de datos.

## 2. Arquitectura General del Sistema

### 2.1 Visión General

El sistema SHPD implementa una arquitectura de microservicios desplegada en un clúster local de Kubernetes mediante Kind. La arquitectura se compone de los siguientes elementos principales:

1. **Dispositivo de Captura**: Raspberry Pi 3B+ configurada para captura de video y transmisión mediante WebSocket
2. **Backend de Procesamiento**: Servicio FastAPI que procesa los frames de video y ejecuta la detección postural
3. **Base de Datos**: PostgreSQL para almacenamiento persistente y Redis para caché y datos temporales
4. **Frontend Web**: Aplicación React para visualización de métricas y estado del paciente
5. **Bot de Telegram**: Sistema de notificaciones y comunicación con el usuario
6. **API-Bot**: Servicio intermediario para comunicación entre el backend y el bot de Telegram

### 2.2 Diagrama de Arquitectura

```
┌─────────────────────┐
│   Raspberry Pi 3B+  │
│  (Captura de Video) │
└──────────┬──────────┘
           │ WebSocket
           ▼
┌─────────────────────┐     ┌──────────────┐
│   Backend FastAPI   │────▶│    Redis     │
│  (Procesamiento)    │     └──────────────┘
└──────────┬──────────┘             │
           │                        │
           ▼                        ▼
┌─────────────────────┐     ┌──────────────┐
│    PostgreSQL       │     │   Frontend   │
│   (Base de Datos)   │◀────│    React     │
└─────────────────────┘     └──────────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────┐
│      API-Bot        │────▶│ Bot Telegram │
└─────────────────────┘     └──────────────┘
```

## 3. Componentes del Sistema

### 3.1 Módulo de Captura - Raspberry Pi 3B+

#### 3.1.1 Configuración de Modo AP

El dispositivo Raspberry Pi puede operar en dos modos:

1. **Modo Access Point (AP)**: Para configuración inicial
2. **Modo Cliente**: Para operación normal

El script `shpd-init.sh` gestiona la lógica de arranque:

```bash
#!/bin/bash
CONFIG_FILE="/home/rodo/shpd.conf"
HOTSPOT_FLAG="/home/rodo/.hotspot_active"

# Si no hay configuración del cliente, entramos en modo hotspot
if [ ! -f "$CONFIG_FILE" ]; then
  # Activa hotspot y servidor de configuración
  bash /home/rodo/enable_hostspot.sh
  sudo systemctl restart setup_server.service
else
  # Inicia streaming normal
  source /home/rodo/shpd37/bin/activate
  python3 home/rodo/test_websocket.py
fi
```

#### 3.1.2 Servidor de Configuración

El archivo `setup_server.py` implementa un servidor web para la configuración inicial del dispositivo:

- Permite configurar credenciales WiFi
- Asigna el device_id único
- Gestiona la transición entre modo AP y modo cliente

#### 3.1.3 Cliente WebSocket

El módulo `test_websocket.py` implementa la captura y transmisión de video:

- Captura frames desde la cámara conectada
- Codifica en formato JPEG
- Transmite mediante WebSocket al backend

### 3.2 Backend de Procesamiento

#### 3.2.1 Arquitectura del Backend

El backend está implementado en Python utilizando FastAPI y se estructura en los siguientes módulos:

- `main.py`: Punto de entrada principal y configuración de WebSockets
- `posture_monitor.py`: Lógica de detección postural usando MediaPipe
- `api/`: Módulo con modelos, esquemas y routers de la API REST

#### 3.2.2 Procesamiento de Video

El backend implementa dos endpoints WebSocket principales:

```python
@app.websocket("/video/input/{device_id}")
async def video_input(websocket: WebSocket, device_id: str):
    # Recibe frames del dispositivo y los almacena en Redis
    
@app.websocket("/video/output")
async def video_output(websocket: WebSocket):
    # Transmite frames procesados al frontend
```

#### 3.2.3 Detección Postural

La clase `PostureMonitor` implementa la lógica de detección:

```python
class PostureMonitor:
    def __init__(self, session_id: str, *, save_metrics: bool = True):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
```

El sistema detecta los siguientes parámetros posturales:

1. **Ángulo del cuello**: Formado entre los puntos del hombro y la oreja
2. **Ángulo del torso**: Inclinación del tronco respecto a la vertical
3. **Desplazamiento lateral**: Offset horizontal de la postura

Los umbrales de detección son configurables mediante el archivo `calibration.json`:

```json
{
    "offset_threshold": valor,
    "neck_angle_threshold": valor,
    "torso_angle_threshold": valor,
    "time_threshold": valor
}
```

#### 3.2.4 Análisis con IA

El sistema integra OpenAI para análisis avanzado de posturas:

```python
async def api_analysis_worker():
    # Worker que procesa frames y envía a OpenAI para análisis
    # Genera reportes periódicos con recomendaciones posturales
```

### 3.3 Base de Datos

#### 3.3.1 Modelos de Datos

El sistema utiliza SQLAlchemy con PostgreSQL y define los siguientes modelos:

```python
class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    device_id = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    edad = Column(Integer)
    sexo = Column(String)
    diagnostico = Column(String)

class Sesion(Base):
    __tablename__ = "sesiones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intervalo_segundos = Column(Integer, nullable=False)
    modo = Column(String, nullable=False)

class MetricaPostural(Base):
    __tablename__ = "metricas_posturales"
    id = Column(UUID(as_uuid=True), primary_key=True)
    sesion_id = Column(UUID(as_uuid=True), ForeignKey("sesiones.id"))
    timestamp = Column(DateTime, nullable=False)
    datos = Column(JSONB, nullable=False)

class PosturaCount(Base):
    __tablename__ = "postura_counts"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    posture_label = Column(String, nullable=False)
    count = Column(Integer, default=0, nullable=False)
```

#### 3.3.2 Redis para Caché

Redis se utiliza para:

- Almacenamiento temporal de frames de video
- Contadores de posturas en tiempo real
- Estado de calibración
- Comunicación entre servicios

### 3.4 Frontend Web

#### 3.4.1 Arquitectura

El frontend está desarrollado con:

- **React** con TypeScript
- **Tailwind CSS** para estilos
- **WebSocket** para comunicación en tiempo real

#### 3.4.2 Componentes Principales

El componente principal `App.tsx` gestiona:

```typescript
export default function App() {
  const [session, setSession] = useState<SessionData | null>(null);
  const [progress, setProgress] = useState<SessionProgressData | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
```

Los componentes visuales incluyen:

- `PostureCard`: Muestra el estado postural actual
- `SessionInfo`: Información de la sesión activa
- `HistoryChart`: Gráficos históricos de posturas
- `SessionProgress`: Progreso en tiempo real
- `PostureTimelineTable`: Timeline detallado de eventos posturales

### 3.5 Bot de Telegram

#### 3.5.1 Funcionalidades

El bot implementa las siguientes funcionalidades:

1. **Registro de pacientes**: Vinculación del usuario con el sistema
2. **Gestión de sesiones**: Inicio y finalización de monitoreo
3. **Recepción de reportes**: Resúmenes generados por IA
4. **Consulta de métricas**: Estadísticas de sesiones anteriores

#### 3.5.2 Flujo de Interacción

```python
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Maneja el flujo conversacional con el usuario
    # Estados: registro, menú principal, sesión activa
```

### 3.6 Sistema de Despliegue

#### 3.6.1 Kubernetes con Kind

El script `script.sh` automatiza el despliegue:

```bash
#!/bin/bash
# Crea el cluster
kind delete cluster --name=rodo
kind create cluster --name=rodo

# ingress-nginx:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/...

# Aplica todos los manifiestos
kubectl apply -f deploy/
kubectl apply -f services/
kubectl apply -f database/deploy/
kubectl apply -f frontend/deploy/
kubectl apply -f backend/deploy/
```

#### 3.6.2 Contenedores Docker

Cada componente incluye su Dockerfile:

- **Backend**: Python 3.11 con dependencias de ML
- **Frontend**: Node.js para build y Nginx para servir
- **Bot**: Python con python-telegram-bot
- **Database**: PostgreSQL oficial

## 4. Flujo de Datos del Sistema

### 4.1 Flujo de Captura y Procesamiento

1. **Captura**: La Raspberry Pi captura video a 30 FPS
2. **Transmisión**: Los frames se envían via WebSocket al backend
3. **Procesamiento**: MediaPipe detecta 33 puntos corporales
4. **Análisis**: Se calculan ángulos y desplazamientos posturales
5. **Clasificación**: Se determina si la postura es correcta o incorrecta
6. **Almacenamiento**: Las métricas se guardan en PostgreSQL y Redis

### 4.2 Flujo de Visualización

1. **Polling**: El frontend consulta actualizaciones cada 3 segundos
2. **WebSocket**: Recibe frames procesados en tiempo real
3. **Renderizado**: Actualiza componentes React con nuevos datos
4. **Timeline**: Construye histórico de eventos posturales

### 4.3 Flujo de Notificaciones

1. **Detección**: El backend detecta postura incorrecta sostenida
2. **Trigger**: Se activa el envío de notificación
3. **API-Bot**: Recibe la solicitud de envío
4. **Telegram**: El bot envía mensaje al usuario

## 5. Tecnologías Utilizadas

### 5.1 Lenguajes de Programación

- **Python 3.11**: Backend, bot, procesamiento de IA
- **TypeScript**: Frontend React
- **Bash**: Scripts de configuración y despliegue

### 5.2 Frameworks y Bibliotecas

#### Backend
- **FastAPI**: Framework web asíncrono
- **MediaPipe**: Detección de poses
- **OpenCV**: Procesamiento de imágenes
- **SQLAlchemy**: ORM para base de datos
- **Redis-py**: Cliente Redis
- **OpenAI**: SDK para integración con GPT

#### Frontend
- **React 18**: Framework UI
- **Tailwind CSS**: Framework de estilos
- **WebSocket API**: Comunicación tiempo real

#### Bot
- **python-telegram-bot**: Framework para bots de Telegram

### 5.3 Infraestructura

- **Docker**: Contenedorización
- **Kubernetes**: Orquestación
- **Kind**: Kubernetes local
- **PostgreSQL**: Base de datos relacional
- **Redis**: Base de datos en memoria
- **Nginx**: Servidor web y proxy reverso

## 6. Módulos Técnicos Principales

### 6.1 Módulo de Detección Postural

El núcleo del sistema reside en `posture_monitor.py`:

#### 6.1.1 Cálculo de Ángulos

```python
def findAngle(self, x1, y1, x2, y2):
    theta = m.acos((y2 - y1) * (-y1) / 
                   (m.sqrt((x2 - x1)**2 + (y2 - y1)**2) * y1))
    degree = int(180 / m.pi) * theta
    return degree
```

#### 6.1.2 Procesamiento de Frame

```python
def process_frame(self, image):
    # 1. Detección de landmarks con MediaPipe
    # 2. Cálculo de ángulos cervical y torácico
    # 3. Evaluación contra umbrales
    # 4. Generación de métricas
    # 5. Almacenamiento en Redis
```

### 6.2 API REST

El backend expone los siguientes routers:

- `/pacientes`: CRUD de pacientes
- `/sesiones`: Gestión de sesiones de monitoreo
- `/metricas`: Consulta de métricas posturales
- `/analysis`: Endpoints para análisis con IA
- `/calibracion`: Ajuste de umbrales
- `/timeline`: Eventos posturales cronológicos
- `/postura_counts`: Contadores de posturas

### 6.3 Sistema de Calibración

El sistema permite calibración dinámica de umbrales:

```python
@router.post("/calibracion/start/{session_id}")
async def start_calibracion(session_id: str):
    # Inicia modo calibración sin guardar métricas
    
@router.post("/calibracion/ajustar")
async def ajustar_umbrales(umbrales: UmbralesCalib):
    # Actualiza calibration.json con nuevos valores
```

## 7. Integración entre Componentes

### 7.1 Comunicación Backend-Frontend

- **REST API**: Para operaciones CRUD y consultas
- **WebSocket**: Para streaming de video y actualizaciones en tiempo real
- **Polling**: Para actualización periódica de métricas

### 7.2 Comunicación Backend-Bot

- **API-Bot**: Servicio intermediario con endpoint `/send_report`
- **Webhook**: El bot recibe actualizaciones de Telegram
- **Base de datos compartida**: Ambos acceden a PostgreSQL

### 7.3 Comunicación Raspberry Pi-Backend

- **WebSocket persistente**: Conexión continua para streaming
- **Reconexión automática**: En caso de pérdida de conectividad
- **Buffering en Redis**: Para manejo de latencia

## 8. Consideraciones de Diseño y Rendimiento

### 8.1 Optimizaciones Implementadas

1. **Procesamiento asíncrono**: Uso de asyncio para operaciones no bloqueantes
2. **Caché en Redis**: Reducción de accesos a base de datos
3. **Compresión JPEG**: Reducción de ancho de banda en transmisión
4. **MediaPipe Lite**: Versión optimizada para dispositivos embebidos

### 8.2 Escalabilidad

- **Microservicios**: Permite escalar componentes independientemente
- **Kubernetes**: Facilita replicación y balanceo de carga
- **Stateless design**: Backend sin estado para horizontal scaling

### 8.3 Tolerancia a Fallos

- **Reconexión automática**: En WebSockets y conexiones de base de datos
- **Persistencia**: Métricas críticas en PostgreSQL
- **Logs estructurados**: Para debugging y monitoreo

### 8.4 Seguridad

- **CORS configurado**: Control de acceso desde frontend
- **Validación de datos**: Mediante Pydantic schemas
- **Aislamiento**: Cada servicio en su contenedor

## 9. Conclusiones Técnicas

El sistema SHPD representa una implementación integral de monitoreo postural que combina:

1. **Hardware dedicado**: Raspberry Pi para captura descentralizada
2. **Procesamiento en tiempo real**: MediaPipe para detección eficiente
3. **Arquitectura distribuida**: Microservicios para modularidad
4. **Múltiples canales**: Web y Telegram para máxima accesibilidad
5. **Inteligencia artificial**: Análisis avanzado mediante OpenAI

La arquitectura implementada permite extensibilidad futura, manteniendo la separación de responsabilidades y facilitando la incorporación de nuevas funcionalidades como modelos de ML propios, análisis biomecánico avanzado, o integración con dispositivos IoT adicionales.