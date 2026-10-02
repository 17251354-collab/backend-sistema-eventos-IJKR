from sqlalchemy import Column, Integer, String, Text, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False, index=True)  # DER Seção 7: "nome"
    descricao = Column(Text, nullable=True)
    data_evento = Column(Date, nullable=False)  # RN04
    horario = Column(Time, nullable=True)
    local = Column(String(200), nullable=True)
    capacidade = Column(Integer, nullable=False)  # RN13 >0
    status = Column(String(20), default="ativo")
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)  # RN12
    organizador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    categoria = relationship("Categoria", back_populates="eventos")
    organizador = relationship("Usuario", back_populates="eventos", foreign_keys=[organizador_id])
    inscricoes = relationship("Inscricao", back_populates="evento", foreign_keys="Inscricao.evento_id")
    favoritos = relationship("Favorito", back_populates="evento", foreign_keys="Favorito.evento_id")
