from fastapi import FastAPI
from routers import pacientes
from database import Base, engine
from models import Paciente

app = FastAPI()
app.include_router(pacientes.router)
Base.metadata.create_all(bind=engine)
