from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class MetricaIn(BaseModel):
    sesion_id: UUID
    timestamp: datetime
    datos: dict

class MetricaOut(MetricaIn):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True
        
class PacienteOut(BaseModel):
    id: int
    telegram_id: str
    device_id: str
    nombre: str
    edad: int
    sexo: str | None = None
    diagnostico: str | None = None

    class Config:
        orm_mode = True
        
class SesionIn(BaseModel):
    intervalo_segundos: int
    modo: str

class SesionOut(SesionIn):
    id: UUID
    class Config:
        orm_mode = True
        
class PosturaCountOut(BaseModel):
    session_id: str
    posture_label: str
    count: int
    class Config:
        orm_mode = True
