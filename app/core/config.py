from datetime import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "Barber Agenda API"
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ]
    ALLOWED_HOSTS: list[str] = [
        "localhost",
        "127.0.0.1",
        "testserver",
    ]
    LOGIN_RATE_LIMIT_REQUESTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    CLIENT_CANCEL_CUTOFF_HOURS: int = 24
    CLIENT_RESCHEDULE_CUTOFF_HOURS: int = 24
    CLIENT_MAX_ACTIVE_PENALTY_POINTS: int = 5
    CLIENT_BLOCK_BOOKING_ON_PENALTY: bool = True
    CLIENT_NO_SHOW_PENALTY_POINTS: int = 3
    CLIENT_NO_SHOW_PENALTY_AMOUNT: float = 0.0
    CLIENT_LATE_CANCEL_PENALTY_POINTS: int = 1
    CLIENT_LATE_CANCEL_PENALTY_AMOUNT: float = 0.0

    @field_validator("CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_csv_list(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY in {"secret", "supersecretkey", "changeme"}:
                raise ValueError("SECRET_KEY inseguro para produccion")
            if "*" in self.CORS_ALLOWED_ORIGINS:
                raise ValueError("CORS_ALLOWED_ORIGINS no puede usar '*' en produccion")
            if "*" in self.ALLOWED_HOSTS:
                raise ValueError("ALLOWED_HOSTS no puede usar '*' en produccion")
        return self


settings = Settings()

BUSINESS_OPEN_TIME = time(9, 0)
BUSINESS_CLOSE_TIME = time(18, 0)
APPOINTMENT_BUFFER_MINUTES = 10

NO_SHOW_TOLERANCE_MINUTES = 15
