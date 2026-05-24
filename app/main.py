from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import app.models

from app.api.v1.router import api_router, openapi_tags
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.middleware import RequestIDMiddleware


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API REST para gestion de barberia: usuarios, barberos, clientes, "
        "servicios, horarios por barbero, bloqueos, disponibilidad real, "
        "citas, cancelaciones, reprogramaciones, historial, pagos/depositos, "
        "caja, comisiones, penalizaciones, inventario, ventas POS y reportes. "
        "Los errores usan un formato estandar con success, message, "
        "error_code, details y request_id."
    ),
    version="1.0.0",
    contact={
        "name": "BARBER_AGENDA Backend",
    },
    openapi_tags=openapi_tags,
)

register_exception_handlers(app)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
