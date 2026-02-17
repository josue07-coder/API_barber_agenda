from fastapi import FastAPI
import app.models

from app.api.v1.router import api_router

app = FastAPI(title="Baerber Agenda API")

app.include_router(api_router, prefix="/api/v1")