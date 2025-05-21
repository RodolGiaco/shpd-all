# api/routers/sesiones.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from api.database import get_db
from api.models import Sesion
from api.schemas import SesionIn, SesionOut

router = APIRouter(prefix="/sesiones", tags=["sesiones"])

@router.post("/", response_model=SesionOut)
def crear_sesion(
    s: SesionIn,
    db: Session = Depends(get_db)
) -> SesionOut:
    nueva = Sesion(**s.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/", response_model=List[SesionOut])
def listar_sesiones(
    db: Session = Depends(get_db)
) -> List[SesionOut]:
    return db.query(Sesion).all()
