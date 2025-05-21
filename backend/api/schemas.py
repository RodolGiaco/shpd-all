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
    nombre: str
    edad: int
    sexo: str
    diagnostico: str

    class Config:
        orm_mode = True
        
class SesionIn(BaseModel):
    intervalo_segundos: int
    modo: str

class SesionOut(SesionIn):
    id: UUID
    class Config:
        orm_mode = True
