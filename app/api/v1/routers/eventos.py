from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import require_roles
from app.database.connection import get_db
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.models.inscricao import Inscricao
from app.schemas.evento import EventoCreate, EventoOut, EventoUpdate

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.post("", response_model=EventoOut, status_code=201)
def criar_evento(
    payload: EventoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("admin", "organizador"))
):
    novo_evento = Evento(
        **payload.model_dump(),
        organizador_id=current_user.id,
        status="ativo"
    )
    db.add(novo_evento)
    db.commit()
    db.refresh(novo_evento)
    return novo_evento

@router.get("", response_model=List[EventoOut])
def listar_eventos(db: Session = Depends(get_db)):
    return db.query(Evento).all()

@router.get("/{evento_id}", response_model=EventoOut)
def detalhar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return evento

@router.put("/{evento_id}", response_model=EventoOut)
def atualizar_evento(
    evento_id: int,
    payload: EventoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("admin", "organizador"))
):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    if current_user.perfil == "organizador" and evento.organizador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(evento, key, value)
    
    db.commit()
    db.refresh(evento)
    return evento

@router.delete("/{evento_id}", status_code=204)
def deletar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("admin"))
):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    db.delete(evento)
    db.commit()
    return None

@router.get("/{evento_id}/participantes")
def listar_participantes(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("admin", "organizador"))
):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    if current_user.perfil == "organizador" and evento.organizador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    participantes = db.query(Usuario).join(Inscricao, Inscricao.usuario_id == Usuario.id).filter(
        Inscricao.evento_id == evento_id, Inscricao.status == "ativa"
    ).all()
    
    return participantes