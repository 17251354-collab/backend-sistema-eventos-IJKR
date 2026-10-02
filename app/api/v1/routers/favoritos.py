from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database.connection import get_db
from app.models.favorito import Favorito
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.schemas.favorito import FavoritoResponse
from app.core.deps import get_current_user_optional

router = APIRouter(tags=["Favoritos"])


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


@router.post("/eventos/{evento_id}/favoritos", status_code=status.HTTP_201_CREATED, summary="RF24 - Favoritar evento")
def favoritar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF24 + RN15 (favorito único, 409). Matriz: só participante."""
    me = _me(db, user, x_user_id)
    if me.perfil != "participante":
        raise HTTPException(status_code=403, detail="Apenas participantes podem favoritar eventos.")
    ev = db.query(Evento).filter(Evento.id == evento_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    dup = (
        db.query(Favorito)
        .filter(Favorito.usuario_id == me.id, Favorito.evento_id == evento_id)
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="Evento já está nos favoritos (RN15).")
    fav = Favorito(usuario_id=me.id, evento_id=evento_id)
    db.add(fav)
    db.commit()
    return {"message": "Evento adicionado aos favoritos."}


@router.get("/favoritos", summary="RF25 - Consultar favoritos")
def consultar_favoritos(
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF25: lista os favoritos do próprio usuário (contrato 9.15)."""
    me = _me(db, user, x_user_id)
    favs = db.query(Favorito).filter(Favorito.usuario_id == me.id).all()
    data = [
        {"id": f.id, "evento_id": f.evento_id, "titulo": f.evento.nome if f.evento else None}
        for f in favs
    ]
    return {"data": data}


@router.delete("/eventos/{evento_id}/favoritos", status_code=status.HTTP_204_NO_CONTENT, summary="RF26 - Remover favorito")
def remover_favorito(
    evento_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF26 + RN16: remove só o que o próprio usuário favoritou (404 se não favoritado)."""
    me = _me(db, user, x_user_id)
    fav = (
        db.query(Favorito)
        .filter(Favorito.usuario_id == me.id, Favorito.evento_id == evento_id)
        .first()
    )
    if not fav:
        raise HTTPException(status_code=404, detail="Favorito não encontrado.")
    db.delete(fav)
    db.commit()
    return None
