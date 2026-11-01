from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.security import hash_password, verify_password
from app.database.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import SenhaUpdate, UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existe:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    user = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha=hash_password(payload.senha),  # Criptografa a senha
        perfil=payload.perfil,
        data_cadastro=datetime.utcnow(),
        status="ativo",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

# --- ROTAS DO USUÁRIO LOGADO (PRECISAM VIR ANTES DO /{id}) ---
@router.get("/me", response_model=UsuarioOut)
def meu_perfil(current_user: Usuario = Depends(get_current_active_user)):
    return current_user

@router.patch("/me", response_model=UsuarioOut)
def atualizar_meu_perfil(
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    dados = payload.model_dump(exclude_unset=True)
    if "email" in dados and dados["email"] != current_user.email:
        existe = db.query(Usuario).filter(Usuario.email == dados["email"]).first()
        if existe:
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    for campo, valor in dados.items():
        setattr(current_user, campo, valor)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/senha")
def alterar_minha_senha(
    payload: SenhaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not verify_password(payload.senha_atual, current_user.senha):
        raise HTTPException(status_code=400, detail="Senha atual inválida")

    current_user.senha = hash_password(payload.nova_senha)
    db.commit()
    return {"success": True, "message": "Senha alterada com sucesso"}

# --- ROTAS GERAIS ---
@router.get("/{usuario_id}", response_model=UsuarioOut)
def buscar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    user = db.get(Usuario, usuario_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user