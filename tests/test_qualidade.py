import sys
sys.path.insert(0, "..")
from fastapi.testclient import TestClient
from main import app
from app.database.connection import Base, engine

client = TestClient(app)

def test_criar_usuario_sem_email_422():
    """Teste negativo: tentar criar usuário sem e-mail deve dar erro 422."""
    r = client.post("/api/v1/usuarios", json={"nome": "Sem Email", "senha": "123", "perfil": "participante"})
    assert r.status_code == 422

def test_login_usuario_inexistente_401():
    """Teste negativo: login com e-mail que não existe deve dar 401."""
    r = client.post("/api/v1/auth/login", data={"username": "fantasma@email.com", "password": "123"})
    assert r.status_code == 401

def test_buscar_evento_inexistente_404():
    """Teste negativo: buscar um evento com ID que não existe deve dar 404."""
    r = client.get("/api/v1/eventos/99999")
    assert r.status_code == 404