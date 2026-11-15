import sys
sys.path.insert(0, "..")
from fastapi.testclient import TestClient
from main import app
from app.database.connection import Base, engine

client = TestClient(app)

def test_perfil_senha_favoritos():
    # Criação dos usuários
    client.post("/api/v1/usuarios", json={"nome":"Org Fav","email":"org.fav@email.com","senha":"123456","perfil":"organizador"})
    client.post("/api/v1/usuarios", json={"nome":"P1 Fav","email":"p1.fav@email.com","senha":"123456","perfil":"participante"})
    
    # Login atualizado
    r_org = client.post("/api/v1/auth/login", data={"username":"org.fav@email.com","password":"123456"})
    h_org = {"Authorization": f"Bearer {r_org.json()['access_token']}"}
    
    r_p1 = client.post("/api/v1/auth/login", data={"username":"p1.fav@email.com","password":"123456"})
    h_p1 = {"Authorization": f"Bearer {r_p1.json()['access_token']}"}

    # Categoria e Evento
    cat = client.post("/api/v1/categorias", json={"nome":"Cat Fav","descricao":"x"})
    cat_id = cat.json()["id"]
    ev = client.post("/api/v1/eventos", json={"nome":"Evento Fav","descricao":"x","data_evento":"2026-12-01","horario":"14:00","local":"Lab","capacidade":10,"categoria_id":cat_id}, headers=h_org)
    ev_id = ev.json()["id"]

    # RF22 - Atualizar Perfil
    upd = client.patch("/api/v1/usuarios/me", json={"nome":"P1 Atualizado"}, headers=h_p1)
    assert upd.status_code == 200
    assert upd.json()["nome"] == "P1 Atualizado"

    # RF23 - Alterar Senha
    assert client.put("/api/v1/usuarios/me/senha", json={"senha_atual":"123456","nova_senha":"nova_senha"}, headers=h_p1).status_code == 200
    
    # Testar login com a nova senha
    r_new = client.post("/api/v1/auth/login", data={"username":"p1.fav@email.com","password":"nova_senha"})
    assert r_new.status_code == 200
    h_p1_new = {"Authorization": f"Bearer {r_new.json()['access_token']}"}

    # RF24 - Favoritar Evento
    assert client.post(f"/api/v1/eventos/{ev_id}/favoritos", headers=h_p1_new).status_code == 201
    
    # RN15 - Favorito único
    assert client.post(f"/api/v1/eventos/{ev_id}/favoritos", headers=h_p1_new).status_code == 409

    # RF25 - Consultar Favoritos
    favs = client.get("/api/v1/favoritos", headers=h_p1_new)
    assert favs.status_code == 200
    assert len(favs.json()["data"]) == 1

    # RF26 - Remover Favorito
    assert client.delete(f"/api/v1/eventos/{ev_id}/favoritos", headers=h_p1_new).status_code == 204
    
    # Confirmar que removeu
    favs2 = client.get("/api/v1/favoritos", headers=h_p1_new)
    assert len(favs2.json()["data"]) == 0