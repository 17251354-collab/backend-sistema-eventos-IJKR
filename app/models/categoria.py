from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    status = Column(String(20), default="ativo")

    eventos = relationship("Evento", back_populates="categoria")
