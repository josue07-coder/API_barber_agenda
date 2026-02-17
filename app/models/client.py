from sqlalchemy import Column, Integer, String, Boolean
from app.database.base import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    notes = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)