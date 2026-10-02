from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base


class Favorito(Base):
    """DER Seção 7: favorito(usuario 1,1 / evento 1,1). Dicionário 8.6."""

    __tablename__ = "favoritos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False, index=True)
    data_favorito = Column(DateTime, default=datetime.utcnow, nullable=False)

    # RN15: favorito único por (usuário, evento)
    __table_args__ = (UniqueConstraint("usuario_id", "evento_id", name="uq_favorito_usuario_evento"),)

    usuario = relationship("Usuario", back_populates="favoritos", foreign_keys=[usuario_id])
    evento = relationship("Evento", back_populates="favoritos", foreign_keys=[evento_id])
