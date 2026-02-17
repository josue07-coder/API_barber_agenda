# from sqlalchemy import Column, Integer, Boolean, ForeignKey, Time
# from app.database.base import Base


# class BarberoHorario(Base):
#     __tablename__ = "barbero_horarios"

#     id = Column(Integer, primary_key=True)
#     barbero_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
#     dia_semana = Column(Integer, nullable=False)  # 0=lunes ... 6=domingo
#     hora_inicio = Column(Time, nullable=False)
#     hora_fin = Column(Time, nullable=False)
#     activo = Column(Boolean, default=True)
