from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from api.database import get_db
from api.models import Paciente

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

# 📦 Esquema para crear un paciente desde la API (ahora incluye id enviado por el cliente)
class PacienteIn(BaseModel):
    id: str
    nombre: str
    edad: int
    sexo: str
    diagnostico: str

# 📦 Esquema para devolver paciente (incluye id)
class PacienteOut(PacienteIn):
    class Config:
        orm_mode = True

# ✅ Crear un paciente (POST)
@router.post("/", response_model=PacienteOut)
def crear_paciente(paciente: PacienteIn, db: Session = Depends(get_db)):
    nuevo = Paciente(**paciente.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ✅ Obtener todos los pacientes (GET)
@router.get("/", response_model=List[PacienteOut])
def obtener_pacientes(db: Session = Depends(get_db)):
    pacientes = db.query(Paciente).all()
    return pacientes
