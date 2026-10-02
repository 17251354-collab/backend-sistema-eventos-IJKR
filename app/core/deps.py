"""Dependências de autenticação/autorização (Fase 0).

Estratégia "sem quebrar o projeto":
- Tenta JWT Bearer primeiro (forma oficial, RF04/CA10).
- Fallback legado: headers X-User-Id / X-User-Perfil (usados pelo teste
  RF01-RF10 original e documentados no README como MVP).
- Rotas novas exigem usuário autenticado (401); rotas legadas abertas
  (GET /usuarios, POST /categorias etc.) permanecem abertas para não
  quebrar fluxos existentes — restrição total da matriz fica como
  evolução documentada.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.usuario import Usuario
from app.core.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def _user_from_id(db: Session, user_id: str) -> Optional[Usuario]:
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="X-User-Id inválido.")
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário autenticado não encontrado.")
    return u


def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> Optional[Usuario]:
    # 1) JWT Bearer (oficial)
    if credentials and credentials.credentials:
        payload = decode_token(credentials.credentials)
        if payload and payload.get("sub"):
            u = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
            if u and u.status == "ativo":
                return u
    # 2) Fallback legado X-User-Id
    if x_user_id:
        return _user_from_id(db, x_user_id)
    return None


def get_current_user(
    user: Optional[Usuario] = Depends(get_current_user_optional),
) -> Usuario:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado. Envie Bearer JWT (login) ou headers X-User-Id/X-User-Perfil.",
        )
    return user


def require_roles(*roles: str):
    """Factory: exige usuário autenticado com um dos perfis informados (403)."""

    def _check(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.perfil not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sem permissão. Perfis autorizados: {', '.join(roles)}.",
            )
        return user

    return _check


# Atalhos por perfil (matriz Seção 12)
require_admin = require_roles("admin")
require_admin_or_org = require_roles("admin", "organizador")
