from sqlalchemy import Integer, Column, DateTime, String, Boolean, CheckConstraint, ForeignKey
from sqlalchemy import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class User(Base):
        __tablename__ = "users"
        __table_args__ = (
                CheckConstraint(
                        "role IN ('admin', 'barber', 'client')",
                        name="ck_users_role_allowed",
                ),
        )

        id = Column(Integer, primary_key=True, index= True)
        name = Column(String(100), nullable=False)
        email = Column(String(120), unique=True, index=True, nullable=False)
        password = Column(String(255), nullable=False)
        role = Column(String(50), default="admin")
        client_id = Column(Integer, ForeignKey("clients.id"), unique=True, nullable=True, index=True)
        branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        client = relationship("Client")
        branch = relationship("Branch")
