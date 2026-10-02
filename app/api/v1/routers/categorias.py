from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaResponse

router = APIRouter(prefix="/categorias", tags=["Categorias"])

@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED, summary="RF05 - Cadastrar categoria")
def cadastrar_categoria(payload: CategoriaCreate, db: Session = Depends(get_db)):
    existe = db.query(Categoria).filter(Categoria.nome == payload.nome).first()
    if existe:
        raise HTTPException(status_code=409, detail="Categoria já cadastrada.")
    cat = Categoria(nome=payload.nome, descricao=payload.descricao, status=payload.status or "ativo")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.get("", summary="RF06 - Consultar categorias")
def consultar_categorias(db: Session = Depends(get_db)):
    cats = db.query(Categoria).filter(Categoria.status == "ativo").all()
    data = [CategoriaResponse.model_validate(c) for c in cats]
    return {"success": True, "data": data, "message": "Categorias consultadas com sucesso."}

@router.get("/{categoria_id}", response_model=CategoriaResponse, summary="RF06 - Detalhar categoria")
def consultar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    c = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return c
