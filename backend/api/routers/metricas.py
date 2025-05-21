# routers/metricas.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from api.database import get_db
from api.models import MetricaPostural
from api.schemas import MetricaIn, MetricaOut
from uuid import UUID
router = APIRouter(prefix="/metricas", tags=["metricas"])

@router.post("/", response_model=MetricaOut)
def crear_metrica(m: MetricaIn, db: Session = Depends(get_db)):
    nueva = MetricaPostural(**m.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/{sesion_id}", response_model=List[MetricaOut])
def listar_metricas(sesion_id: UUID, db: Session = Depends(get_db)):
    return db.query(MetricaPostural)\
             .filter_by(sesion_id=sesion_id)\
             .order_by(MetricaPostural.timestamp.desc())\
             .all()
