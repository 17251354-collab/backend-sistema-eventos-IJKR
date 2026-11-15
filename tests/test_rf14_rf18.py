import sys
sys.path.insert(0, "..")
from fastapi.testclient import TestClient
from main import app
from app.database.connection import Base, engine

client = TestClient(app)

def test_fluxo_inscricoes():
    # Criação dos usuários
    client.post("/api/v1/usuarios", json={"nome":"Org Inc","email":"org.inc@email.com","senha":"123456","perfil":"organizador"})
    client.post("/api/v1/usuarios", json={"nome":"P1 Inc","email":"p1.inc@email.com","senha":"123456","perfil":"participante"})
    client.post("/api/v1/usuarios", json={"nome":"P2 Inc","email":"p2.inc@email.com","senha":"123456","perfil":"participante"})

    # Login atualizado para data= (Form-Data)
    r_org = client.post("/api/v1/auth/login", data={"username":"org.inc@email.com","password":"123456"})
    h_org = {"Authorization": f"Bearer {r_org.json()['access_token']}"}
    
    r_p1 = client.post("/api/v1/auth/login", data={"username":"p1.inc@email.com","password":"123456"})
    h_p1 = {"Authorization": f"Bearer {r_p1.json()['access_token']}"}
    p1_id = r_p1.json()["user"]["id"]

    # Categoria e Evento com capacidade 1 (para testar limite)
    cat = client.post("/api/v1/categorias", json={"nome":"Cat Inc","descricao":"x"})
    cat_id = cat.json()["id"]
    ev = client.post("/api/v1/eventos", json={"nome":"Evento Inc","descricao":"x","data_evento":"2026-12-10","horario":"14:00","local":"Lab","capacidade":1,"categoria_id":cat_id}, headers=h_org)
    ev_id = ev.json()["id"]

    # RF14 - Realizar inscrição
    assert client.post(f"/api/v1/eventos/{ev_id}/inscricoes", json={"usuario_id": p1_id}, headers=h_p1).status_code == 201
    
    # RN02 - Inscrição única
    assert client.post(f"/api/v1/eventos/{ev_id}/inscricoes", json={"usuario_id": p1_id}, headers=h_p1).status_code == 409

    # RF15 - Consultar inscrições
    assert client.get("/api/v1/inscricoes", headers=h_p1).status_code == 200

    # RN03 - Limite de capacidade
    r_p2 = client.post("/api/v1/auth/login", data={"username":"p2.inc@email.com","password":"123456"})
    h_p2 = {"Authorization": f"Bearer {r_p2.json()['access_token']}"}
    p2_id = r_p2.json()["user"]["id"]
    assert client.post(f"/api/v1/eventos/{ev_id}/inscricoes", json={"usuario_id": p2_id}, headers=h_p2).status_code == 409

    # RF17 - Participantes do evento (visão do organizador)
    assert client.get(f"/api/v1/eventos/{ev_id}/participantes", headers=h_org).status_code == 200