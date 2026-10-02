from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, LoginResponse
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=LoginResponse, summary="RF04 - Login global")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not u or not verify_password(payload.senha, u.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    if u.status != "ativo":
        raise HTTPException(status_code=401, detail="Usuário inativo.")
    token = create_access_token({"sub": str(u.id), "perfil": u.perfil, "email": u.email})
    return {"access_token": token, "token_type": "bearer", "usuario": u}
