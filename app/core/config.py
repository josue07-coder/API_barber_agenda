from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from datetime import time


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Barber Agenda API"
    DATABASE_URL: str
    SECRET_KEY: str


settings = Settings()

BUSINESS_OPEN_TIME = time(9, 0)
BUSINESS_CLOSE_TIME = time(18, 0)
APPOINTMENT_BUFFER_MINUTES = 10

NO_SHOW_TOLERANCE_MINUTES = 15

