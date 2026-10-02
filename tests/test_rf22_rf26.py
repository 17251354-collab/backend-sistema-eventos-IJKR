import sys
sys.path.insert(0, "..")
from fastapi.testclient import TestClient
from main import app
from app.database.connection import Base, engine

client = TestClient(app)

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def _mkuser(nome, email, perfil):
    r = client.post("/api/v1/usuarios", json={"nome": nome, "email": email, "senha": "123456", "perfil": perfil})
    assert r.status_code == 201
    return r.json()

def _login(email, senha="123456"):
    r = client.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_perfil_senha_favoritos():
    org = _mkuser("Org", "org@email.com", "organizador")
    p1 = _mkuser("P1", "p1@email.com", "participante")
    p2 = _mkuser("P2", "p2@email.com", "participante")
    h_org = _login("org@email.com")
    h_p1 = _login("p1@email.com")

    # RF22 ver/editar próprio perfil
    me = client.get("/api/v1/usuarios/me", headers=h_p1)
    assert me.status_code == 200 and me.json()["email"] == "p1@email.com"
    assert client.get("/api/v1/usuarios/me").status_code == 401
    upd = client.patch("/api/v1/usuarios/me", json={"nome": "P1 Novo"}, headers=h_p1)
    assert upd.status_code == 200 and upd.json()["nome"] == "P1 Novo"
    # RN01 no próprio perfil
    assert client.patch("/api/v1/usuarios/me", json={"email": "org@email.com"}, headers=h_p1).status_code == 409

    # RF23 alterar senha
    assert client.put("/api/v1/usuarios/me/senha",
        json={"senha_atual": "errada", "nova_senha": "nova123"}, headers=h_p1).status_code == 401
    assert client.put("/api/v1/usuarios/me/senha",
        json={"senha_atual": "123456", "nova_senha": "nova123"}, headers=h_p1).status_code == 200
    h_p1_new = _login("p1@email.com", "nova123")  # login com a nova senha

    cat = client.post("/api/v1/categorias", json={"nome": "Tech", "descricao": "t"}).json()
    ev = client.post("/api/v1/eventos", json={"nome": "Evento Fav", "descricao": "d", "data_evento": "2026-10-10",
        "horario": "14:00", "local": "Lab", "capacidade": 50, "categoria_id": cat["id"]}, headers=h_org)
    eid = ev.json()["id"]

    # RF24 favoritar (só participante; RN15 409)
    assert client.post(f"/api/v1/eventos/{eid}/favoritos", headers=h_p1_new).status_code == 201
    assert client.post(f"/api/v1/eventos/{eid}/favoritos", headers=h_p1_new).status_code == 409
    assert client.post(f"/api/v1/eventos/{eid}/favoritos", headers=h_org).status_code == 403
    assert client.post("/api/v1/eventos/9999/favoritos", headers=h_p1_new).status_code == 404

    # RF25 consultar próprios
    favs = client.get("/api/v1/favoritos", headers=h_p1_new).json()
    assert len(favs["data"]) == 1 and favs["data"][0]["evento_id"] == eid

    # RF26 remover (RN16: só o próprio; 404 se não favoritado)
    h_p2 = _login("p2@email.com")
    assert client.delete(f"/api/v1/eventos/{eid}/favoritos", headers=h_p2).status_code == 404
    assert client.delete(f"/api/v1/eventos/{eid}/favoritos", headers=h_p1_new).status_code == 204
    assert client.get("/api/v1/favoritos", headers=h_p1_new).json()["data"] == []
