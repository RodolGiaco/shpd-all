import os
import logging
import time
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import redis
from sqlalchemy.dialects.postgresql import UUID
import uuid

# --- Configuración logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# --- Configuración de base de datos ---
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@postgres-service:5432/shpd_db"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modelos ---
class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    device_id = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    edad = Column(Integer)
    sexo = Column(String)
    diagnostico = Column(String)

class Sesion(Base):
    __tablename__ = "sesiones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intervalo_segundos = Column(Integer)
    modo = Column(String)

class MetricaPostural(Base):
    __tablename__ = "metricas_posturales"
    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(UUID, ForeignKey("sesiones.id"))
    porcentaje_correcta = Column(Float)
    porcentaje_incorrecta = Column(Float)
    tiempo_sentado = Column(Float)
    tiempo_parado = Column(Float)
    alertas_enviadas = Column(Integer)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Conectarse a Redis
try:
    r = redis.Redis(host='redis', port=6379, decode_responses=True) # Apuntar al servicio de Redis
    r.ping()
    logging.info("Conexión a Redis exitosa desde el Bot.")
except redis.exceptions.ConnectionError as e:
    logging.error(f"No se pudo conectar a Redis desde el Bot: {e}")
    r = None

# --- Menús y botones ---
MAIN_MENU = {
    "1": "Configurar sesión",
    "2": "Ver métricas",
    "3": "Ajustar alertas",
    "4": "Mis datos",
    "5": "Calibrar dispositivo",
    "6": "Ayuda",
    "7": "Volver al menú",
}

MENU_BUTTONS = [
    ["1. ⚙️ Configurar sesión", "2. 📊 Ver métricas"],
    ["3. 🔔 Ajustar alertas", "4. 👤 Mis datos"],
    ["5. 🎯 Calibrar dispositivo", "6. ❓ Ayuda"],
    ["7. 🔄 Volver al menú"],
]

# Configuración de sesión
SESSION_MENU = {
    "1": "10 minutos",
    "2": "30 minutos",
    "3": "1 hora",
    "4": "Personalizado",
}

SESSION_BUTTONS = [
    ["1. 10 minutos", "2. 30 minutos"],
    ["3. 1 hora", "4. Personalizado"],
]

# Estados de registro de paciente
FIELDS = ["nombre", "edad", "sexo", "diagnostico", "device_id"]

# Utilidad para extraer la opción seleccionada
def extract_choice(text: str) -> str:
    if "." in text:
        return text.split(".")[0].strip()
    return text.strip()

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("state", None)
    await update.message.reply_text(
        "👋 <b>Bienvenido al Sistema de Monitoreo Postural</b>\nElige una opción:",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardMarkup(MENU_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    choice = text.split('.')[0] if "." in text else text
    state = context.user_data.get("state")

    # Manejo de 'Mis datos' (opción 4)
    if choice == "4":
        telegram_id = str(update.effective_user.id)
        db: Session = SessionLocal()
        try:
            paciente = db.query(Paciente).filter(Paciente.telegram_id == telegram_id).first()
            if not paciente:
                context.user_data['state'] = 'awaiting_patient_data'
                context.user_data['field_index'] = 0
                return await update.message.reply_text(
                    "Por favor, ingresa tu nombre completo:",
                    reply_markup=ReplyKeyboardRemove()
                )
            # Si ya existe, mostrar y dar opción de modificar
            context.user_data['paciente_id'] = paciente.id
            context.user_data['modificar_paciente'] = True
            return await update.message.reply_text(
                f"👤 <b>Mis datos</b>\n"
                f"Nombre: {paciente.nombre}\n"
                f"Edad: {paciente.edad}\n"
                f"Sexo: {paciente.sexo}\n"
                f"Diagnóstico: {paciente.diagnostico}\n"
                "¿Deseas modificar tus datos?",
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(
                    [["Sí", "No"]], resize_keyboard=True, one_time_keyboard=True
                )
            )
        finally:
            db.close()
        return

    # Si el usuario responde a la pregunta de modificar datos
    if state is None and context.user_data.get('modificar_paciente'):
        if text.lower() == "no":
            context.user_data.pop('modificar_paciente', None)
            return await show_main_menu(update, context)
        elif text.lower() == "sí":
            context.user_data['state'] = 'awaiting_patient_data'
            context.user_data['field_index'] = 0
            context.user_data.pop('modificar_paciente', None)
            return await update.message.reply_text(
                "Por favor, ingresa tu nombre completo:",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            return await update.message.reply_text(
                "Por favor, responde 'Sí' o 'No'.",
                reply_markup=ReplyKeyboardMarkup(
                    [["Sí", "No"]], resize_keyboard=True, one_time_keyboard=True
                )
            )

    # Flujo de registro de paciente
    if state == 'awaiting_patient_data':
        idx = context.user_data['field_index']
        field = FIELDS[idx]
        val = text
        if field == 'edad':
            try:
                v = int(val)
                if v < 1 or v > 120: raise ValueError
                context.user_data['edad'] = v
            except:
                return await update.message.reply_text("❌ Edad inválida. Ingresa un número entre 1 y 120:")
        else:
            context.user_data[field] = val
        idx += 1
        if idx < len(FIELDS):
            context.user_data['field_index'] = idx
            prompts = {
                'nombre': "Ingresa tu edad:",
                'edad': "Ingresa tu sexo (M/F/O):",
                'sexo': "Ingresa tu diagnóstico médico:",
                'diagnostico': "Ingresa el ID de tu dispositivo (código de la pegatina):"
            }
            return await update.message.reply_text(prompts[field])
        # Todos los datos ingresados, guardar en BD
        db: Session = SessionLocal()
        try:
            telegram_id = str(update.effective_user.id)
            # 1) Buscamos si ya existe
            paciente = db.query(Paciente).filter(Paciente.telegram_id == telegram_id).first()
            if paciente:
                # 2a) Si existe, actualizamos campos
                paciente.device_id = context.user_data['device_id']
                paciente.nombre    = context.user_data['nombre']
                paciente.edad      = context.user_data['edad']
                paciente.sexo      = context.user_data['sexo']
                paciente.diagnostico = context.user_data['diagnostico']
                mensaje = "✅ Datos actualizados con éxito."
            else:
                # 2b) Si no existe, creamos uno nuevo
                paciente = Paciente(
                    telegram_id=telegram_id,
                    device_id=context.user_data['device_id'],
                    nombre=context.user_data['nombre'],
                    edad=context.user_data['edad'],
                    sexo=context.user_data['sexo'],
                    diagnostico=context.user_data['diagnostico']
                )
                db.add(paciente)
                mensaje = "✅ Registro completado con éxito."

            # 3) Commit y refresco
            db.commit()
            db.refresh(paciente)
            context.user_data['paciente_id'] = paciente.id

            await update.message.reply_text(mensaje)
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("❌ Error al guardar. Intenta de nuevo.")
        finally:
            db.close()
            await show_main_menu(update, context)
        return

    # --- FLUJO: Configuración de Sesión ---
    if choice == "1" and state is None:
        db: Session = SessionLocal()
        paciente = db.query(Paciente).filter(Paciente.telegram_id == str(update.effective_user.id)).first()
        db.close()
        if not paciente:
            return await update.message.reply_text(
                "❌ Primero debes registrar tus datos usando la opción 'Mis datos'."
            )
        context.user_data['state'] = 'awaiting_session_config'
        await update.message.reply_text(
            "Elige la duración de la sesión:",
            reply_markup=ReplyKeyboardMarkup(SESSION_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        )
        return

    if state == 'awaiting_session_config':
        choice_num = extract_choice(choice)
        if choice_num not in SESSION_MENU:
            return await update.message.reply_text("❌ Opción no válida. Por favor, elige una del menú.")

        # Mapeo de opciones a segundos
        duration_map = {"1": 600, "2": 1800, "3": 3600}
        
        if choice_num == "4":
            return await update.message.reply_text("La duración personalizada aún no está implementada.")
        
        intervalo_segundos = duration_map[choice_num]
        db: Session = SessionLocal()
        try:
            # Obtener el device_id del paciente
            telegram_id = str(update.effective_user.id)
            paciente = db.query(Paciente).filter(Paciente.telegram_id == telegram_id).first()
            if not paciente:
                await update.message.reply_text("Error: no se encontraron datos de paciente.")
                context.user_data['state'] = None
                await show_main_menu(update, context)
                return
            device_id = paciente.device_id

            # Crear una nueva sesión con UUID autogenerado
            sesion = Sesion(intervalo_segundos=intervalo_segundos, modo="monitor_activo")
            db.add(sesion)
            db.commit()
            db.refresh(sesion)
            session_id = str(sesion.id)

            # --- Lógica de Redis ---
            if r:
                redis_key = f"shpd-session:{session_id}"
        
                session_data = {
                    "start_ts": int(time.time()),
                    "intervalo_segundos": sesion.intervalo_segundos,
                }
                r.hset(redis_key, mapping=session_data)
                logging.info(f"Sesión {session_id} guardada en Redis.")
                
                redis_shpd_key = f"shpd-data:{device_id}"
                shpd_data = {
                    "session_id": session_id,
                }
                r.hset(redis_shpd_key, mapping=shpd_data)
                logging.info(f"Shpd-data {device_id} guardada en Redis.")
            else:
                logging.error("No se pudo guardar la sesión en Redis.")

            # Devuelve la URL con el session_id y el device_id al usuario en un mensaje aparte, interactivo
            url = f"http://172.18.0.2:30080/?session_id={session_id}&device_id={device_id}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎥 Ver monitoreo en vivo", url=url)]
            ])
            await update.message.reply_text(
                f"✅ <b>Sesión configurada</b>\n"
                f"<b>Duración:</b> {SESSION_MENU[choice_num]}\n"
                f"<b>Dispositivo:</b> <code>{device_id}</code>\n\n"
                f"Puedes abrir el monitoreo tocando el botón o copiar la URL:\n{url}",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Error configurando sesión: {e}")
            await update.message.reply_text("❌ Ocurrió un error al configurar la sesión.")
        finally:
            db.close()
            context.user_data['state'] = None
            await show_main_menu(update, context)
        return

    # Resto de opciones: 2,3,5,6,7 … (mantener lógica existente)
    if choice in MAIN_MENU and choice not in ("1", "4"):
        # ...) Aquí iría la lógica para las demás opciones, idéntica al código previo
        await update.message.reply_text("Esta opción aún no está implementada.")
        return await show_main_menu(update, context)

    # Si no coincide con ningún flujo activo, mostrar menú
    if not state:
        await show_main_menu(update, context)

if __name__ == "__main__":
    app = ApplicationBuilder()\
        .token(os.getenv("TELEGRAM_TOKEN", "7796011838:AAGFuQRg2OdEhYT-Cqvg_mGRIOeKWkYNSic"))\
        .build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
