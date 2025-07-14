import os
import asyncio
import logging
import json
import time
import cv2
import numpy as np
import time
import redis
import base64
import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.models import Sesion, Paciente, MetricaPostural, PosturaCount
from api.database import Base, engine, SessionLocal
from posture_monitor import PostureMonitor
from api.routers import sesiones, pacientes, metricas, analysis, postura_counts, timeline, calibracion
from datetime import datetime
from neural_network.pose_recognition import PoseRecognizer
from instructions.gesture_buffer import GestureBuffer

r = redis.Redis(host="redis", port=6379, decode_responses=True)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "posture_monitor": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        },
        "api_analysis_worker": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        }, 
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        },

    },
    # El logger raíz queda en WARNING, filtrando todo lo demás
    "root": {
        "handlers": ["console"],
        "level": "WARNING"
    }
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("shpd-backend")
logger.setLevel(logging.DEBUG)


# ——— CONFIGURACIÓN DEL MODELO TFLITE LOCAL ———
pose_recognizer = PoseRecognizer(model_path='model/keypoint_classifier.tflite')

# ——— COLAS ASÍNCRONAS ———
processed_frames_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
api_analysis_queue: asyncio.Queue = asyncio.Queue()
_triggered_sessions = set()  # para disparar clasificación sólo una vez por umbral

# ——— WORKER PARA ANÁLISIS CON MODELO TFLITE ———
async def api_analysis_worker():
    """
    Worker que consume de api_analysis_queue payloads con:
      { session_id, frame, keypoints, bad_time }
    Usa el modelo TFLite local y guarda el resultado en Redis.
    """
    loop = asyncio.get_running_loop()
    logger.debug("🔄 TFLite analysis worker iniciado")
    while True:
        payload = await api_analysis_queue.get()
        session_id = payload["session_id"]
        frame = payload["frame"]
        keypoints = payload["keypoints"]
        bad_time = payload["bad_time"]
        
        try:
            # Ejecutar la clasificación con el modelo TFLite
            gesture_id, labels = await loop.run_in_executor(
                None,
                pose_recognizer.recognize_pose,
                keypoints,
                frame
            )
            
            # Traducir el ID a nombre de gesto
            if gesture_id is not None and gesture_id >= 0 and gesture_id < len(labels):
                posture_name = labels[gesture_id]
                
                # Crear un resultado compatible con el formato anterior
                # Asignamos 100% a la postura detectada y 0% al resto
                result = {}
                
                # Las etiquetas del modelo ya contienen las 13 posturas correctas
                for i, label in enumerate(labels):
                    result[label] = 100 if i == gesture_id else 0
                
                # Guardar en Redis
                r.hset(f"analysis:{session_id}", mapping=result)
                logger.debug(f"✔️ TFLite analysis saved for session {session_id}: {posture_name}")
                
                # Actualizar PosturaCount en la base de datos
                if posture_name:
                    db = SessionLocal()
                    try:
                        # Intentar obtener la fila existente
                        fila = (
                            db.query(PosturaCount)
                            .filter(
                                PosturaCount.session_id == session_id,
                                PosturaCount.posture_label == posture_name
                            )
                            .first()
                        )
                        if fila:
                            # Si existe, incrementamos el contador
                            fila.count += 1
                            db.add(fila)
                        else:
                            # Si no existe, creamos una nueva fila
                            nueva = PosturaCount(
                                session_id=session_id,
                                posture_label=posture_name,
                                count=1
                            )
                            db.add(nueva)
                        db.commit()
                        logger.debug(f"✔️ PostureCount updated: {session_id} - {posture_name}")
                        
                        # Guardar evento de timeline
                        try:
                            evt = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "postura": posture_name,
                                "tiempo_mala_postura": bad_time
                            }
                            r.rpush(f"timeline:{session_id}", json.dumps(evt))
                            r.ltrim(f"timeline:{session_id}", -200, -1)
                        except Exception:
                            logger.exception("Error guardando timeline")
                    except Exception:
                        logger.exception("Error actualizando PosturaCount en DB")
                        db.rollback()
                    finally:
                        db.close()
            
        except Exception:
            logger.exception("Error en análisis TFLite")
        finally:
            api_analysis_queue.task_done()
            

# En startup, lanza el worker en background
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(api_analysis_worker())
    logger.debug("✅ TFLite analysis worker scheduled")
    yield  
    
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sesiones.router)
app.include_router(pacientes.router)
app.include_router(metricas.router)
app.include_router(analysis.router)
app.include_router(postura_counts.router)
app.include_router(timeline.router)
app.include_router(calibracion.router)
processed_frames_queue = asyncio.Queue(maxsize=10)

@app.websocket("/video/input/{device_id}")
async def video_input(websocket: WebSocket, device_id: str):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    
    # Detectar modo calibración: query ?calibracion=1
    calibrating_query = websocket.scope.get("query_string", b"").decode().find("calibracion=1") >= 0
    if calibrating_query:
        await websocket.send_text(json.dumps({"type": "modo", "calibracion": True}))
    else:
        await websocket.send_text(json.dumps({"type": "modo", "calibracion": False}))

    # Variables para manejar PostureMonitor dinámicamente
    posture_monitor = None
    current_session_id = None
    calibrating = None
    mode = None
    try:
        while True:
            # 1. Verificar el session_id desde Redis en cada iteración
            redis_shpd_key = f"shpd-data:{device_id}"
            session_id = r.hget(redis_shpd_key, "session_id")

            # ——— Determinar si seguimos en modo calibración ———
            mode = r.hget(redis_shpd_key, "mode")
            if mode is None:
                calibrating = calibrating_query  # aún no hay session_id: usa flag de la URL
            elif mode == "normal":
                calibrating = False
           
            # 2. Si el session_id cambió, reinicializar PostureMonitor con el modo correcto
            if session_id != current_session_id:
                logger.info(f"📋 Session ID cambió de {current_session_id} a {session_id}")
                posture_monitor = PostureMonitor(session_id, save_metrics=not calibrating)
                current_session_id = session_id
                logger.info(f"✅ PostureMonitor reinicializado para session {session_id}")

            # 3. Procesar frame normalmente
            data = await websocket.receive_bytes()
            frame = await loop.run_in_executor(None, _decode_jpeg, data)
            if frame is None:
                continue

            # Solo procesar si tenemos un PostureMonitor válido
            if posture_monitor is None:
                # Si no hay PostureMonitor, enviar frame sin procesar
                jpeg = await loop.run_in_executor(None, _encode_jpeg, frame)
                keypoints = None
            else:
                # process_frame ahora devuelve tupla (frame, keypoints)
                result = await loop.run_in_executor(None, posture_monitor.process_frame, frame)
                processed, keypoints = result
                jpeg = await loop.run_in_executor(None, _encode_jpeg, processed)
            
            if processed_frames_queue.full():
                processed_frames_queue.get_nowait()
            await processed_frames_queue.put(jpeg)

            # 4. Dispara análisis TFLite si guardaron un frame crudo (solo si hay session_id válido)
            if posture_monitor is not None and not calibrating and keypoints is not None:
                raw_key = f"raw_frame:{session_id}"
                flag_value = r.hget(raw_key, "flag_alert")  
                bad_time = r.hget(raw_key, "bad_time")  
                if flag_value == "1":
                    await api_analysis_queue.put({
                        "session_id": session_id,
                        "frame": frame,  # Enviamos el frame original, no el JPEG
                        "keypoints": keypoints,  # Enviamos los keypoints de MediaPipe
                        "bad_time": bad_time
                    })
                    r.delete(raw_key)
                    logger.debug(f"✔️ Disparo para análisis TFLite ejecutado para sesión {session_id}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para device_id: {device_id}")
    except Exception as e:
        logger.error(f"Error en video_input: {e}")
        logger.exception("Detalles del error:")
    finally:
        logger.info(f"Cerrando WebSocket para device_id: {device_id}")

@app.websocket("/video/output")
async def video_output(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            jpeg = await processed_frames_queue.get()
            await websocket.send_bytes(jpeg)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

def _decode_jpeg(data: bytes):
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

def _encode_jpeg(frame):
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    return buf.tobytes()

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="warning",
        access_log=True
    )
