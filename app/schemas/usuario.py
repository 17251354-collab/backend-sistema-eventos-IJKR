from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, example="Maria Silva")
    email: EmailStr = Field(..., example="maria@email.com")
    senha: str = Field(..., min_length=6, max_length=50, example="123456")
    perfil: str = Field(default="participante", example="participante")  # admin|organizador|participante

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Maria Silva",
                "email": "maria@email.com",
                "senha": "123456",
                "perfil": "participante"
            }
        }

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    perfil: Optional[str] = None
    status: Optional[str] = None

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    data_cadastro: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class MeUpdate(BaseModel):
    """RF22 - editar próprio perfil (nome/e-mail; RN01 e-mail único)."""

    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None


class SenhaUpdate(BaseModel):
    """RF23 - alterar própria senha (confere atual, aplica hash)."""

    senha_atual: str = Field(..., min_length=6, max_length=50)
    nova_senha: str = Field(..., min_length=6, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
