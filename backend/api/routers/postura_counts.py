# api/routers/postura_counts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.database import get_db
from api.models import PosturaCount
from api.schemas import PosturaCountOut

router = APIRouter(prefix="/postura_counts", tags=["postura_counts"])

@router.get("/{session_id}", response_model=List[PosturaCountOut])
def obtener_postura_counts(session_id: str, db: Session = Depends(get_db)):
    """
    Devuelve la lista de PosturaCount (por session_id),
    es decir, cada label con su count actual.
    """
    resultados = (
        db.query(PosturaCount)
        .filter(PosturaCount.session_id == session_id)
        .all()
    )
    if resultados is None:
        raise HTTPException(status_code=404, detail="No counts found")
    return resultados
