import sys
sys.path.insert(0, "..")
from fastapi.testclient import TestClient
from main import app
from app.database.connection import Base, engine

client = TestClient(app)

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_fluxo_rf01_rf10():
    r = client.post("/api/v1/usuarios", json={"nome":"Maria Silva","email":"maria@email.com","senha":"123456","perfil":"participante"})
    assert r.status_code == 201
    assert "senha" not in r.json()

    r_dup = client.post("/api/v1/usuarios", json={"nome":"Maria","email":"maria@email.com","senha":"123456","perfil":"participante"})
    assert r_dup.status_code == 409

    assert client.get("/api/v1/usuarios").status_code == 200

    login = client.post("/api/v1/auth/login", data={"username":"maria@email.com","password":"123456"})
    assert login.status_code == 200
    assert "access_token" in login.json()

    login_err = client.post("/api/v1/auth/login", data={"username":"maria@email.com","password":"errada"})
    assert login_err.status_code == 401

    cat = client.post("/api/v1/categorias", json={"nome":"Tecnologia","descricao":"Tech"})
    assert cat.status_code == 201
    cat_id = cat.json()["id"]

    assert client.get("/api/v1/categorias").status_code == 200

    org = client.post("/api/v1/usuarios", json={"nome":"Org","email":"org@email.com","senha":"123456","perfil":"organizador"})
    org_id = org.json()["id"]

    part = client.post("/api/v1/usuarios", json={"nome":"Part","email":"part@email.com","senha":"123456","perfil":"participante"})
    part_login = client.post("/api/v1/auth/login", data={"username":"part@email.com","password":"123456"})
    part_token = part_login.json()["access_token"]

    r_fail = client.post("/api/v1/eventos", json={"nome":"Fail","descricao":"x","data_evento":"2030-10-10","horario":"14:00","local":"Lab","capacidade":10,"categoria_id":cat_id}, headers={"Authorization": f"Bearer {part_token}"})
    assert r_fail.status_code == 403

    r_anon = client.post("/api/v1/eventos", json={"nome":"Anon","descricao":"x","data_evento":"2030-10-10","horario":"14:00","local":"Lab","capacidade":10,"categoria_id":cat_id})
    assert r_anon.status_code == 401

    org_login = client.post("/api/v1/auth/login", data={"username":"org@email.com","password":"123456"})
    token = org_login.json()["access_token"]

    ev = client.post("/api/v1/eventos", json={"nome":"Workshop Python","descricao":"Intro","data_evento":"2030-10-10","horario":"14:00","local":"Lab 01","capacidade":50,"categoria_id":cat_id}, headers={"Authorization": f"Bearer {token}"})
    assert ev.status_code == 201
    assert ev.json()["organizador_id"] == org_id
    eid = ev.json()["id"]

    assert client.post("/api/v1/eventos", json={"nome":"Antigo","descricao":"x","data_evento":"2020-01-01","horario":"10:00","local":"Lab","capacidade":10,"categoria_id":cat_id}, headers={"Authorization": f"Bearer {token}"}).status_code == 422
    assert client.post("/api/v1/eventos", json={"nome":"Zero","descricao":"x","data_evento":"2030-10-10","horario":"10:00","local":"Lab","capacidade":0,"categoria_id":cat_id}, headers={"Authorization": f"Bearer {token}"}).status_code == 422

    assert client.get("/api/v1/eventos").status_code == 200
    assert client.get("/api/v1/eventos?q=Python").status_code == 200
    assert client.get(f"/api/v1/eventos?categoria_id={cat_id}").status_code == 200

    assert client.get(f"/api/v1/eventos/{eid}").status_code == 200
    assert client.get("/api/v1/eventos/9999").status_code == 404

    upd = client.put(f"/api/v1/eventos/{eid}", json={"nome":"Avancado"}, headers={"Authorization": f"Bearer {token}"})
    assert upd.status_code == 200
    assert upd.json()["nome"] == "Avancado"

    org2 = client.post("/api/v1/usuarios", json={"nome":"Org2","email":"org2@email.com","senha":"123456","perfil":"organizador"})
    org2_login = client.post("/api/v1/auth/login", data={"username":"org2@email.com","password":"123456"})
    org2_token = org2_login.json()["access_token"]

    assert client.put(f"/api/v1/eventos/{eid}", json={"nome":"Hack"}, headers={"Authorization": f"Bearer {org2_token}"}).status_code == 403

    assert client.delete(f"/api/v1/eventos/{eid}", headers={"Authorization": f"Bearer {token}"}).status_code == 403

    admin = client.post("/api/v1/usuarios", json={"nome":"Adm","email":"adm@email.com","senha":"123456","perfil":"admin"})
    admin_login = client.post("/api/v1/auth/login", data={"username":"adm@email.com","password":"123456"})
    admin_token = admin_login.json()["access_token"]

    assert client.delete(f"/api/v1/eventos/{eid}", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 204
    assert client.get(f"/api/v1/eventos/{eid}").status_code == 404
    assert client.delete("/api/v1/eventos/9999", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 404