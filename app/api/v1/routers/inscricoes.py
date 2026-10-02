from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.connection import get_db
from app.models.inscricao import Inscricao
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.schemas.inscricao import InscricaoCreate, InscricaoResponse
from app.core.deps import get_current_user_optional

router = APIRouter(tags=["Inscrições"])


def _actor(user, x_user_id, db) -> Optional[Usuario]:
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
    return None


@router.post("/eventos/{evento_id}/inscricoes", response_model=InscricaoResponse, status_code=status.HTTP_201_CREATED, summary="RF14 - Realizar inscrição")
def realizar_inscricao(
    evento_id: int,
    payload: InscricaoCreate,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF14 + RN02 (única ativa) + RN03 (capacidade) + CA04."""
    actor = _actor(user, x_user_id, db)
    if not actor:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")

    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    alvo = db.query(Usuario).filter(Usuario.id == payload.usuario_id).first()
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Participante só inscreve a si mesmo (simetria RN08/matriz); admin/org podem inscrever terceiros
    if actor.perfil == "participante" and actor.id != payload.usuario_id:
        raise HTTPException(status_code=403, detail="Participante só pode realizar a própria inscrição.")

    # RN02 - sem duas inscrições ativas no mesmo evento
    dup = (
        db.query(Inscricao)
        .filter(
            Inscricao.usuario_id == payload.usuario_id,
            Inscricao.evento_id == evento_id,
            Inscricao.status == "ativa",
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="Usuário já possui inscrição ativa neste evento (RN02).")

    # RN03/RF18 - capacidade máxima (conta ativas)
    ocupadas = (
        db.query(Inscricao)
        .filter(Inscricao.evento_id == evento_id, Inscricao.status == "ativa")
        .count()
    )
    if ocupadas >= evento.capacidade:
        raise HTTPException(status_code=409, detail="Capacidade máxima do evento atingida (RN03).")

    # Reinscrição após cancelamento: remove registro cancelado antigo (histórico preservado via status? não —
    # opta-se por reativar: mantém unicidade e histórico). Aqui: reativa se existir cancelada.
    antiga = (
        db.query(Inscricao)
        .filter(
            Inscricao.usuario_id == payload.usuario_id,
            Inscricao.evento_id == evento_id,
            Inscricao.status == "cancelada",
        )
        .first()
    )
    if antiga:
        antiga.status = "ativa"
        db.commit()
        db.refresh(antiga)
        return antiga

    nova = Inscricao(usuario_id=payload.usuario_id, evento_id=evento_id, status="ativa")
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router.get("/inscricoes", summary="RF15 - Consultar inscrições")
def consultar_inscricoes(
    usuario_id: Optional[int] = Query(None),
    evento_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF15: participante vê só as próprias; admin/organizador veem todas (filtros opcionais)."""
    actor = _actor(user, x_user_id, db)
    if not actor:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")
    query = db.query(Inscricao)
    if actor.perfil == "participante":
        query = query.filter(Inscricao.usuario_id == actor.id)
    else:
        if usuario_id:
            query = query.filter(Inscricao.usuario_id == usuario_id)
    if evento_id:
        query = query.filter(Inscricao.evento_id == evento_id)
    inscricoes = query.all()
    data = [InscricaoResponse.model_validate(i) for i in inscricoes]
    return {"success": True, "data": data, "message": "Inscrições consultadas com sucesso."}


@router.delete("/inscricoes/{inscricao_id}", status_code=status.HTTP_204_NO_CONTENT, summary="RF16 - Cancelar inscrição")
def cancelar_inscricao(
    inscricao_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF16 + RN08 + CA05: cancelamento lógico (status=cancelada, doc 9.11 'remove ou cancela').
    Só o dono ou admin. 204 sem corpo; 404 se inexistente."""
    actor = _actor(user, x_user_id, db)
    if not actor:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")
    inscr = db.query(Inscricao).filter(Inscricao.id == inscricao_id).first()
    if not inscr:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada.")
    if actor.perfil != "admin" and inscr.usuario_id != actor.id:
        raise HTTPException(status_code=403, detail="O participante só pode cancelar as próprias inscrições (RN08).")
    inscr.status = "cancelada"
    db.commit()
    return None
