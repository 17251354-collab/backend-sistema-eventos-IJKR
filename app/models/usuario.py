from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)  # RN01
    senha = Column(String(255), nullable=False)
    perfil = Column(String(50), nullable=False, default="participante")  # admin | organizador | participante
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="ativo")

    eventos = relationship("Evento", back_populates="organizador", foreign_keys="Evento.organizador_id")
    inscricoes = relationship("Inscricao", back_populates="usuario", foreign_keys="Inscricao.usuario_id")
    favoritos = relationship("Favorito", back_populates="usuario", foreign_keys="Favorito.usuario_id")
