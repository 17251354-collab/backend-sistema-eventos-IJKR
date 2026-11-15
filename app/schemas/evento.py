from pydantic import BaseModel, field_validator, Field
from datetime import date, time
from typing import Optional

class EventoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    data_evento: date
    horario: Optional[time] = None
    local: Optional[str] = None
    capacidade: int = Field(..., gt=0)
    categoria_id: int

class EventoCreate(EventoBase):
    @field_validator('data_evento')
    def validar_data(cls, v):
        if v < date.today():
            raise ValueError("Data do evento não pode ser anterior à data atual (RN04).")
        return v

class EventoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    data_evento: Optional[date] = None
    horario: Optional[time] = None
    local: Optional[str] = None
    capacidade: Optional[int] = Field(None, gt=0)
    categoria_id: Optional[int] = None

class EventoOut(EventoBase):
    id: int
    organizador_id: int
    status: str

    model_config = {"from_attributes": True}