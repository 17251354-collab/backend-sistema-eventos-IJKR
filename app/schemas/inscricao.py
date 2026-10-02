from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class InscricaoCreate(BaseModel):
    """Contrato 9.9: corpo {usuario_id}."""

    usuario_id: int = Field(..., example=3)


class InscricaoResponse(BaseModel):
    id: int
    usuario_id: int
    evento_id: int
    data_inscricao: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True
