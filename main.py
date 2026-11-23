from fastapi import FastAPI
from app.api.v1.api import api_router
from app.database.connection import Base, engine
from app.models import Usuario, Categoria, Evento, Inscricao, Certificado, Favorito

# Cria tabelas automaticamente (para SQLite dev). Em produção use Alembic.
Base.metadata.create_all(bind=engine)

tags_metadata = [
    {"name": "Autenticação", "description": "Operações de login e geração de token JWT."},
    {"name": "Usuários", "description": "Gerenciamento de usuários. O cadastro é público, mas as rotas /me exigem autenticação."},
    {"name": "Eventos", "description": "Gerenciamento de eventos acadêmicos. Criação e edição restritas a Admin e Organizador."},
    {"name": "Categorias", "description": "Gerenciamento de categorias para classificar os eventos."},
    {"name": "Inscrições", "description": "Operações de inscrição de participantes nos eventos."},
    {"name": "Certificados", "description": "Emissão e validação de certificados de participação."},
    {"name": "Favoritos", "description": "Gerenciamento da lista de eventos favoritos do participante."},
    {"name": "Health", "description": "Verificação de status da API."}
]

app = FastAPI(
    title="Sistema de Gerenciamento de Eventos Acadêmicos",
    description="""
    API REST completa para o gerenciamento de eventos acadêmicos.
    
    **Segurança:** Implementa autenticação via JWT (JSON Web Tokens) e controle de acesso baseado em perfis (Admin, Organizador, Participante).
    
    **Testes:** O projeto conta com uma suíte de testes automatizados validando regras de negócio e segurança.
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def health():
    return {"success": True, "message": "API Eventos Acadêmicos online", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}