from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CertificadoResponse(BaseModel):
    id: int
    inscricao_id: int
    codigo_validacao: str = Field(..., example="CERT-2026-0001")
    data_emissao: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True
