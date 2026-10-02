from pydantic import BaseModel, Field, field_validator
from datetime import date, time
from typing import Optional
from datetime import date as date_type


class EventoCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200, example="Workshop de Python")  # DER: "nome"
    descricao: Optional[str] = Field(None, example="Introdução à programação Python.")
    data_evento: date_type = Field(..., example="2026-10-10")
    horario: Optional[time] = Field(None, example="14:00")
    local: Optional[str] = Field(None, example="Laboratório 01")
    capacidade: int = Field(..., gt=0, example=50)  # RN13
    categoria_id: int = Field(..., example=1)  # RN12
    # organizador_id vem do usuário autenticado, não do body (auto-vinculo)

    @field_validator("data_evento")
    @classmethod
    def valida_data_futura(cls, v: date_type):
        # RN04: data não pode ser anterior à atual
        if v < date.today():
            raise ValueError("Data do evento não pode ser anterior à data atual (RN04).")
        return v


class EventoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    descricao: Optional[str] = None
    data_evento: Optional[date_type] = None
    horario: Optional[time] = None
    local: Optional[str] = None
    capacidade: Optional[int] = Field(None, gt=0)
    categoria_id: Optional[int] = None
    status: Optional[str] = None

    @field_validator("data_evento")
    @classmethod
    def valida_data_futura_update(cls, v: Optional[date_type]):
        if v is not None and v < date.today():
            raise ValueError("Data do evento não pode ser anterior à data atual (RN04).")
        return v


class EventoResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    data_evento: date_type
    horario: Optional[time] = None
    local: Optional[str] = None
    capacidade: int
    status: Optional[str] = None
    categoria_id: int
    organizador_id: int

    class Config:
        from_attributes = True
