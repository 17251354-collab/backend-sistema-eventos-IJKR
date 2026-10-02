from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base


class Inscricao(Base):
    """DER Seção 7: inscrição(usuario 1,1 / evento 1,1). Dicionário 8.4."""

    __tablename__ = "inscricoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False, index=True)
    data_inscricao = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default="ativa", nullable=False)  # ativa|cancelada

    # RN02: sem duas inscrições ativas do mesmo usuário no mesmo evento
    # (checagem em código por status; constraint protege duplicidade total)
    __table_args__ = (UniqueConstraint("usuario_id", "evento_id", name="uq_inscricao_usuario_evento"),)

    usuario = relationship("Usuario", back_populates="inscricoes", foreign_keys=[usuario_id])
    evento = relationship("Evento", back_populates="inscricoes", foreign_keys=[evento_id])
    certificado = relationship("Certificado", back_populates="inscricao", uselist=False, cascade="all, delete-orphan")
