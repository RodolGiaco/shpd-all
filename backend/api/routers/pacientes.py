from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Paciente
from api.schemas import PacienteOut

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

@router.get("/{device_id}", response_model=PacienteOut)
def obtener_paciente_por_device_id(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un paciente específico basado en el ID de su dispositivo registrado.
    """
    paciente = db.query(Paciente).filter(Paciente.device_id == device_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente con ese device_id no fue encontrado")
    return paciente