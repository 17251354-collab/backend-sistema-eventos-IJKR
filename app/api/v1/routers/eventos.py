from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database.connection import get_db
from app.models.evento import Evento
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.schemas.evento import EventoCreate, EventoResponse, EventoUpdate
from app.core.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/eventos", tags=["Eventos"])


def _resolve_actor(
    user: Optional[Usuario],
    x_user_id: Optional[str],
    x_user_perfil: Optional[str],
    db: Session,
) -> tuple:
    """Compatibilidade: JWT (preferido) ou headers legados X-User-*.

    Retorna (organizador_id, perfil). Exige autenticação (401).
    """
    if user:
        return user.id, user.perfil
    if x_user_id:
        try:
            uid = int(x_user_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="X-User-Id inválido.")
        u = db.query(Usuario).filter(Usuario.id == uid).first()
        if not u:
            raise HTTPException(status_code=404, detail="Organizador não encontrado.")
        return u.id, (x_user_perfil or u.perfil)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário não autenticado. Envie Bearer JWT (login) ou headers X-User-Id/X-User-Perfil.",
    )


@router.post("", response_model=EventoResponse, status_code=status.HTTP_201_CREATED, summary="RF07 - Cadastrar evento")
def cadastrar_evento(
    payload: EventoCreate,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_perfil: Optional[str] = Header(None, alias="X-User-Perfil"),
):
    # RN12 - categoria obrigatória
    cat = db.query(Categoria).filter(Categoria.id == payload.categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada (RN12).")
    # RN04/RN13 validados no schema (422)

    # RN05 - somente admin/organizador (JWT ou legado)
    organizador_id, perfil = _resolve_actor(user, x_user_id, x_user_perfil, db)
    if perfil not in ["admin", "organizador"]:
        raise HTTPException(status_code=403, detail="Sem permissão para cadastrar eventos (RN05).")

    evento = Evento(
        nome=payload.nome,
        descricao=payload.descricao,
        data_evento=payload.data_evento,
        horario=payload.horario,
        local=payload.local,
        capacidade=payload.capacidade,
        categoria_id=payload.categoria_id,
        organizador_id=organizador_id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("", summary="RF08 (+RF12 busca / RF13 filtro)")
def consultar_eventos(
    q: Optional[str] = Query(None, description="Busca por nome do evento (RF12)"),
    categoria_id: Optional[int] = Query(None, description="Filtro por categoria (RF13)"),
    data_evento: Optional[date] = Query(None, description="Filtro por data (RF13)"),
    db: Session = Depends(get_db),
):
    query = db.query(Evento)
    if q:
        query = query.filter(Evento.nome.ilike(f"%{q}%"))
    if categoria_id:
        query = query.filter(Evento.categoria_id == categoria_id)
    if data_evento:
        query = query.filter(Evento.data_evento == data_evento)
    eventos = query.all()
    data = [EventoResponse.model_validate(e) for e in eventos]
    return {"success": True, "data": data, "message": "Eventos consultados com sucesso."}


@router.get("/{evento_id}", response_model=EventoResponse, summary="RF09 - Detalhar evento")
def detalhar_evento(evento_id: int, db: Session = Depends(get_db)):
    e = db.query(Evento).filter(Evento.id == evento_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    return e


@router.put("/{evento_id}", response_model=EventoResponse, summary="RF10 - Atualizar evento")
def atualizar_evento(
    evento_id: int,
    payload: EventoUpdate,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_perfil: Optional[str] = Header(None, alias="X-User-Perfil"),
):
    e = db.query(Evento).filter(Evento.id == evento_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    # RN06 - gestão do evento: participante nunca; organizador só os seus
    _, perfil = _resolve_actor(user, x_user_id, x_user_perfil, db)
    actor_id = user.id if user else (int(x_user_id) if x_user_id else None)
    if perfil not in ["admin", "organizador"]:
        raise HTTPException(status_code=403, detail="Sem permissão para alterar eventos (RN06).")
    if perfil == "organizador" and str(e.organizador_id) != str(actor_id):
        raise HTTPException(status_code=403, detail="Organizador só pode alterar eventos sob sua responsabilidade (RN06).")

    if payload.categoria_id is not None:
        cat = db.query(Categoria).filter(Categoria.id == payload.categoria_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Categoria não encontrada (RN12).")
        e.categoria_id = payload.categoria_id
    if payload.nome is not None:
        e.nome = payload.nome
    if payload.descricao is not None:
        e.descricao = payload.descricao
    if payload.data_evento is not None:
        e.data_evento = payload.data_evento
    if payload.horario is not None:
        e.horario = payload.horario
    if payload.local is not None:
        e.local = payload.local
    if payload.capacidade is not None:
        e.capacidade = payload.capacidade
    if payload.status is not None:
        e.status = payload.status

    db.commit()
    db.refresh(e)
    return e


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT, summary="RF11 - Excluir evento (só admin)")
def excluir_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_perfil: Optional[str] = Header(None, alias="X-User-Perfil"),
):
    """RF11 + RN07 + CA09: apenas Admin; 204 sucesso, 404 se inexistente."""
    _, perfil = _resolve_actor(user, x_user_id, x_user_perfil, db)
    if perfil != "admin":
        raise HTTPException(status_code=403, detail="Apenas o Admin pode excluir eventos (RN07/CA09).")
    e = db.query(Evento).filter(Evento.id == evento_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    db.delete(e)
    db.commit()
    return None


@router.get("/{evento_id}/participantes", summary="RF17 - Consultar participantes do evento")
def consultar_participantes(
    evento_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_perfil: Optional[str] = Header(None, alias="X-User-Perfil"),
):
    """RF17: admin ou organizador dono do evento. Retorna inscritos com status ativa."""
    from app.models.inscricao import Inscricao

    e = db.query(Evento).filter(Evento.id == evento_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    _, perfil = _resolve_actor(user, x_user_id, x_user_perfil, db)
    actor_id = user.id if user else (int(x_user_id) if x_user_id else None)
    if perfil == "admin" or (perfil == "organizador" and str(e.organizador_id) == str(actor_id)):
        pass
    else:
        raise HTTPException(status_code=403, detail="Sem permissão para ver participantes (matriz: admin/organizador).")
    inscricoes = (
        db.query(Inscricao).filter(Inscricao.evento_id == evento_id, Inscricao.status == "ativa").all()
    )
    data = [
        {
            "inscricao_id": i.id,
            "usuario_id": i.usuario_id,
            "nome": i.usuario.nome if i.usuario else None,
            "email": i.usuario.email if i.usuario else None,
            "data_inscricao": i.data_inscricao.isoformat() if i.data_inscricao else None,
            "status": i.status,
        }
        for i in inscricoes
    ]
    return {"success": True, "data": data, "message": "Participantes consultados com sucesso."}
