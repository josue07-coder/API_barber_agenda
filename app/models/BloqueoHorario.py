# from sqlalchemy import Integer, Column, DateTime, ForeignKey, String
# from app.database.base import Base



# class BloqueoHorario(Base):
#     __tablename__ = "bloqueos_horarios"

#     id = Column(Integer, primary_key=True)
#     barbero_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
#     fecha_inicio = Column(DateTime, nullable=False)
#     fecha_fin = Column(DateTime, nullable=False)
#     motivo = Column(String(255))
#     creado_por = Column(Integer, ForeignKey("usuarios.id"))
