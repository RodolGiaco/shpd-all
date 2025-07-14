from sqlalchemy import Column, String, Integer
from api.database import Base
import uuid
from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    device_id = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    edad = Column(Integer)
    sexo = Column(String)
    diagnostico = Column(String)


class MetricaPostural(Base):
    __tablename__ = "metricas_posturales"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sesion_id  = Column(UUID(as_uuid=True), ForeignKey("sesiones.id", ondelete="CASCADE"), nullable=False)
    timestamp  = Column(DateTime, nullable=False)
    datos      = Column(JSONB, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
class Sesion(Base):
    __tablename__ = "sesiones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intervalo_segundos = Column(Integer, nullable=False)
    modo = Column(String, nullable=False)

class PosturaCount(Base):
    __tablename__ = "postura_counts"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    posture_label = Column(String, nullable=False)
    count = Column(Integer, default=0, nullable=False)