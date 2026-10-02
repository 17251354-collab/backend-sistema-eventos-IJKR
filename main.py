from fastapi import FastAPI
from app.api.v1.api import api_router
from app.database.connection import Base, engine
from app.models import Usuario, Categoria, Evento, Inscricao, Certificado, Favorito

# Cria tabelas automaticamente (para SQLite dev). Em produção use Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gerenciamento de Eventos Acadêmicos",
    description="RF01 a RF26 | FastAPI + SQLAlchemy + Alembic + SQLite | Swagger | Campo evento.nome conforme DER",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def health():
    return {"success": True, "message": "API Eventos Acadêmicos - RF01-RF26 online", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
