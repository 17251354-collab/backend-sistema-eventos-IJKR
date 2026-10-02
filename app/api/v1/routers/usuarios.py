from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate,
    LoginRequest, LoginResponse, MeUpdate, SenhaUpdate,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user_optional

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _me(db: Session, user: Optional[Usuario], x_user_id: Optional[str]) -> Usuario:
    if user:
        return user
    if x_user_id:
        try:
            uid = int(x_user_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="X-User-Id inválido.")
        u = db.query(Usuario).filter(Usuario.id == uid).first()
        if not u:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        return u
    raise HTTPException(status_code=401, detail="Usuário não autenticado.")


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED, summary="RF01 - Cadastrar usuário")
def cadastrar_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    # RN01 - E-mail único
    existe = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existe:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado (RN01).")
    # RN11 senha não retornada (response_model filtra)
    if payload.perfil not in ["admin", "organizador", "participante"]:
        raise HTTPException(status_code=400, detail="Perfil inválido. Use admin, organizador ou participante.")
    novo = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha=hash_password(payload.senha),
        perfil=payload.perfil
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("", summary="RF02 - Consultar usuários")
def consultar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    data = [UsuarioResponse.model_validate(u) for u in usuarios]
    return {"success": True, "data": data, "message": "Usuários consultados com sucesso."}


# RF22/RF23 antes de /{usuario_id} (evita "me" cair no path param)
@router.get("/me", response_model=UsuarioResponse, summary="RF22 - Ver próprio perfil")
def ver_proprio_perfil(
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    return _me(db, user, x_user_id)


@router.patch("/me", response_model=UsuarioResponse, summary="RF22 - Editar próprio perfil")
def editar_proprio_perfil(
    payload: MeUpdate,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF22: nome/e-mail próprios; RN01 e-mail único (409)."""
    me = _me(db, user, x_user_id)
    if payload.email and payload.email != me.email:
        existe = db.query(Usuario).filter(Usuario.email == payload.email).first()
        if existe:
            raise HTTPException(status_code=409, detail="E-mail já cadastrado (RN01).")
        me.email = payload.email
    if payload.nome:
        me.nome = payload.nome
    db.commit()
    db.refresh(me)
    return me


@router.put("/me/senha", summary="RF23 - Alterar própria senha")
def alterar_propria_senha(
    payload: SenhaUpdate,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF23: confere senha atual (401), aplica hash na nova (RN11)."""
    me = _me(db, user, x_user_id)
    if not verify_password(payload.senha_atual, me.senha):
        raise HTTPException(status_code=401, detail="Senha atual incorreta.")
    me.senha = hash_password(payload.nova_senha)
    db.commit()
    return {"success": True, "message": "Senha alterada com sucesso."}


@router.get("/{usuario_id}", response_model=UsuarioResponse, summary="RF02 - Detalhar usuário")
def consultar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return u


@router.put("/{usuario_id}", response_model=UsuarioResponse, summary="RF03 - Atualizar usuário")
def atualizar_usuario(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if payload.email and payload.email != u.email:
        existe = db.query(Usuario).filter(Usuario.email == payload.email).first()
        if existe:
            raise HTTPException(status_code=409, detail="E-mail já cadastrado (RN01).")
        u.email = payload.email
    if payload.nome:
        u.nome = payload.nome
    if payload.perfil:
        if payload.perfil not in ["admin", "organizador", "participante"]:
            raise HTTPException(status_code=400, detail="Perfil inválido.")
        u.perfil = payload.perfil
    if payload.status:
        u.status = payload.status
    db.commit()
    db.refresh(u)
    return u


# RF04 - Login isolado (mantém prefix /usuarios para compatibilidade mas também expõe /auth/login global via api.py)
@router.post("/login", response_model=LoginResponse, summary="RF04 - Realizar login")
def login_usuarios(payload: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not u or not verify_password(payload.senha, u.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    if u.status != "ativo":
        raise HTTPException(status_code=401, detail="Usuário inativo.")
    token = create_access_token({"sub": str(u.id), "perfil": u.perfil, "email": u.email})
    return {"access_token": token, "token_type": "bearer", "usuario": u}
