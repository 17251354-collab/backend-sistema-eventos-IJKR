from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.database.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if (user.status or "").lower() != "ativo":
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token = create_access_token(subject=str(user.id), perfil=user.perfil)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UsuarioOut.model_validate(user),
    }