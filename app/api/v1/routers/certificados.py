from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database.connection import get_db
from app.models.certificado import Certificado
from app.models.inscricao import Inscricao
from app.models.usuario import Usuario
from app.schemas.certificado import CertificadoResponse
from app.core.deps import get_current_user_optional

router = APIRouter(tags=["Certificados"])


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


@router.post("/inscricoes/{inscricao_id}/certificado", response_model=CertificadoResponse, status_code=status.HTTP_201_CREATED, summary="RF19 - Emitir certificado")
def emitir_certificado(
    inscricao_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_perfil: Optional[str] = Header(None, alias="X-User-Perfil"),
):
    """RF19 + RN09 (vínculo) + RN10 (código único) + RN14 (critério) + CA06."""
    actor = _actor(user, x_user_id, db)
    if not actor:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")
    perfil = actor.perfil if user else (x_user_perfil or actor.perfil)
    # Matriz: emitir = admin/organizador
    if perfil not in ["admin", "organizador"]:
        raise HTTPException(status_code=403, detail="Sem permissão para emitir certificados.")

    # RN09 - vinculado a inscrição válida (existe + ativa)
    inscr = db.query(Inscricao).filter(Inscricao.id == inscricao_id).first()
    if not inscr:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada (RN09).")
    if inscr.status != "ativa":
        raise HTTPException(status_code=400, detail="Certificado exige inscrição ativa (RN09).")

    # RN14 (coerente): evento já ocorrido
    if inscr.evento and inscr.evento.data_evento > date.today():
        raise HTTPException(status_code=400, detail="Evento ainda não ocorreu (RN14).")

    # 409 se já existe certificado para a inscrição
    existente = db.query(Certificado).filter(Certificado.inscricao_id == inscricao_id).first()
    if existente:
        raise HTTPException(status_code=409, detail="Inscrição já possui certificado.")

    # RN10 - código único CERT-AAAA-NNNN
    ano = date.today().year
    base = f"CERT-{ano}-{inscricao_id:04d}"
    codigo = base
    sufixo = 0
    while db.query(Certificado).filter(Certificado.codigo_validacao == codigo).first():
        sufixo += 1
        codigo = f"{base}-{sufixo}"

    cert = Certificado(inscricao_id=inscricao_id, codigo_validacao=codigo, status="emitido")
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@router.get("/certificados/validar/{codigo}", summary="RF21 - Validar certificado por código")
def validar_certificado(codigo: str, db: Session = Depends(get_db)):
    """RF21: pública; 200 com dados, 404 se código inválido."""
    cert = db.query(Certificado).filter(Certificado.codigo_validacao == codigo).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificado não encontrado para este código.")
    inscr = cert.inscricao
    return {
        "valido": cert.status == "emitido",
        "certificado": CertificadoResponse.model_validate(cert).model_dump(mode="json"),
        "inscricao_id": cert.inscricao_id,
        "usuario": {"id": inscr.usuario_id, "nome": inscr.usuario.nome} if inscr and inscr.usuario else None,
        "evento": {"id": inscr.evento_id, "nome": inscr.evento.nome} if inscr and inscr.evento else None,
    }


@router.get("/certificados/{certificado_id}", response_model=CertificadoResponse, summary="RF20 - Consultar certificado")
def consultar_certificado(
    certificado_id: int,
    db: Session = Depends(get_db),
    user: Optional[Usuario] = Depends(get_current_user_optional),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """RF20: dono da inscrição, admin ou organizador."""
    actor = _actor(user, x_user_id, db)
    if not actor:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")
    cert = db.query(Certificado).filter(Certificado.id == certificado_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificado não encontrado.")
    inscr = cert.inscricao
    if actor.perfil == "participante" and (not inscr or inscr.usuario_id != actor.id):
        raise HTTPException(status_code=403, detail="Sem permissão para consultar este certificado.")
    return cert
