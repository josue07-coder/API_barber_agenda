from sqlalchemy import Integer, Column, DateTime, String, Boolean
from sqlalchemy import func
from app.database.base import Base

class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, index= True)
        name = Column(String(100), nullable=False)
        email = Column(String(120), unique=True, index=True, nullable=False)
        password = Column(String(255), nullable=False)
        role = Column(String(50), default="admin")
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())