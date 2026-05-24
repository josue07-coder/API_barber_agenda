from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    branch = relationship("Branch")
