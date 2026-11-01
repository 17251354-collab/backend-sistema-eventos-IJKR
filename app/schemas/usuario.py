from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: str = "participante"

class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: EmailStr | None = None

class SenhaUpdate(BaseModel):
    senha_atual: str
    nova_senha: str

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: str
    status: str | None = None

    model_config = {"from_attributes": True}