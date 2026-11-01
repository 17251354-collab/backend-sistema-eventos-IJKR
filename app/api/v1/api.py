from fastapi import APIRouter
from app.api.v1.routers import auth, usuarios, categorias, eventos, inscricoes, certificados, favoritos

api_router = APIRouter()

# Registra as rotas
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(categorias.router)
api_router.include_router(eventos.router)
api_router.include_router(inscricoes.router)
api_router.include_router(certificados.router)
api_router.include_router(favoritos.router)