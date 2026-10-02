from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base


class Certificado(Base):
    """DER Seção 7: certificado —possui— (1,1) inscrição (0,1). Dicionário 8.5."""

    __tablename__ = "certificados"

    id = Column(Integer, primary_key=True, index=True)
    inscricao_id = Column(Integer, ForeignKey("inscricoes.id"), nullable=False, unique=True, index=True)  # RN09/RN10
    codigo_validacao = Column(String(50), nullable=False, unique=True, index=True)  # RN10
    data_emissao = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default="emitido", nullable=False)  # emitido|cancelado

    inscricao = relationship("Inscricao", back_populates="certificado", foreign_keys=[inscricao_id])
