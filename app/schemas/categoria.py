from pydantic import BaseModel, Field
from typing import Optional

class CategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, example="Tecnologia")
    descricao: Optional[str] = Field(None, example="Eventos relacionados à tecnologia e programação.")
    status: Optional[str] = Field(default="ativo")

class CategoriaResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True
