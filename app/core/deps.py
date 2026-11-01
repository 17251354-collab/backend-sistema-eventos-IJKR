from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.usuario import Usuario

# Obrigatório (dá 401 se não tiver token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Opcional (não dá erro se não tiver token)
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
    except JWTError:
        raise credentials_exception

    if not sub:
        raise credentials_exception

    try:
        user_id = int(sub)
    except ValueError:
        raise credentials_exception

    user = db.get(Usuario, user_id)
    if not user:
        raise credentials_exception

    return user

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            return None
        user_id = int(sub)
        return db.get(Usuario, user_id)
    except Exception:
        return None

def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    if (current_user.status or "").lower() != "ativo":
        raise HTTPException(status_code=403, detail="Usuário inativo")
    return current_user

def require_roles(*roles: str):
    def checker(current_user: Usuario = Depends(get_current_active_user)) -> Usuario:
        if current_user.perfil not in roles:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return current_user
    return checker