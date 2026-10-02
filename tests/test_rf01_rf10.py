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
    # RF01
    r = client.post("/api/v1/usuarios", json={"nome":"Maria Silva","email":"maria@email.com","senha":"123456","perfil":"participante"})
    assert r.status_code == 201
    assert "senha" not in r.json()  # RN11
    # RN01
    r_dup = client.post("/api/v1/usuarios", json={"nome":"Maria","email":"maria@email.com","senha":"123456","perfil":"participante"})
    assert r_dup.status_code == 409
    # RF02
    assert client.get("/api/v1/usuarios").status_code == 200
    # RF03
    uid = r.json()["id"]
    assert client.put(f"/api/v1/usuarios/{uid}", json={"nome":"Atualizada"}).status_code == 200
    # RF04
    login = client.post("/api/v1/auth/login", json={"email":"maria@email.com","senha":"123456"})
    assert login.status_code == 200
    assert "access_token" in login.json()  # CA10 JWT
    assert client.post("/api/v1/auth/login", json={"email":"maria@email.com","senha":"errada"}).status_code == 401
    # RF05
    cat = client.post("/api/v1/categorias", json={"nome":"Tecnologia","descricao":"Tech"})
    assert cat.status_code == 201
    cat_id = cat.json()["id"]
    # RF06
    assert client.get("/api/v1/categorias").status_code == 200
    # RF07 precisa organizador
    org = client.post("/api/v1/usuarios", json={"nome":"Org","email":"org@email.com","senha":"123456","perfil":"organizador"})
    org_id = org.json()["id"]
    # RN05 fail participante
    part = client.post("/api/v1/usuarios", json={"nome":"Part","email":"part@email.com","senha":"123456","perfil":"participante"})
    part_id = part.json()["id"]
    r_fail = client.post("/api/v1/eventos", json={"nome":"Fail","descricao":"x","data_evento":"2026-10-10","horario":"14:00","local":"Lab","capacidade":10,"categoria_id":cat_id}, headers={"X-User-Id":str(part_id),"X-User-Perfil":"participante"})
    assert r_fail.status_code == 403
    # 401 sem autenticação (Fase 0)
    r_anon = client.post("/api/v1/eventos", json={"nome":"Anon","descricao":"x","data_evento":"2026-10-10","horario":"14:00","local":"Lab","capacidade":10,"categoria_id":cat_id})
    assert r_anon.status_code == 401
    # RF07 sucesso (JWT também vale: usa login do organizador)
    org_login = client.post("/api/v1/auth/login", json={"email":"org@email.com","senha":"123456"})
    token = org_login.json()["access_token"]
    ev = client.post("/api/v1/eventos", json={"nome":"Workshop Python","descricao":"Intro","data_evento":"2026-10-10","horario":"14:00","local":"Lab 01","capacidade":50,"categoria_id":cat_id}, headers={"Authorization": f"Bearer {token}"})
    assert ev.status_code == 201
    assert ev.json()["organizador_id"] == org_id
    eid = ev.json()["id"]
    # RN04 e RN13
    assert client.post("/api/v1/eventos", json={"nome":"Antigo","descricao":"x","data_evento":"2020-01-01","horario":"10:00","local":"Lab","capacidade":10,"categoria_id":cat_id}, headers={"X-User-Id":str(org_id),"X-User-Perfil":"organizador"}).status_code == 422
    assert client.post("/api/v1/eventos", json={"nome":"Zero","descricao":"x","data_evento":"2026-10-10","horario":"10:00","local":"Lab","capacidade":0,"categoria_id":cat_id}, headers={"X-User-Id":str(org_id),"X-User-Perfil":"organizador"}).status_code == 422
    # RF08 (DER: campo "nome"; busca RF12 / filtro RF13)
    assert client.get("/api/v1/eventos").status_code == 200
    assert client.get("/api/v1/eventos?q=Python").status_code == 200
    assert client.get(f"/api/v1/eventos?categoria_id={cat_id}").status_code == 200
    # RF09
    assert client.get(f"/api/v1/eventos/{eid}").status_code == 200
    assert client.get("/api/v1/eventos/9999").status_code == 404
    # RF10
    upd = client.put(f"/api/v1/eventos/{eid}", json={"nome":"Avancado"}, headers={"X-User-Id":str(org_id),"X-User-Perfil":"organizador"})
    assert upd.status_code == 200
    assert upd.json()["nome"] == "Avancado"
    # RN06 - outro organizador não pode alterar
    org2 = client.post("/api/v1/usuarios", json={"nome":"Org2","email":"org2@email.com","senha":"123456","perfil":"organizador"})
    org2_id = org2.json()["id"]
    assert client.put(f"/api/v1/eventos/{eid}", json={"nome":"Hack"}, headers={"X-User-Id":str(org2_id),"X-User-Perfil":"organizador"}).status_code == 403
    # RF11 - só admin exclui (CA09/RN07)
    assert client.delete(f"/api/v1/eventos/{eid}", headers={"X-User-Id":str(org_id),"X-User-Perfil":"organizador"}).status_code == 403
    admin = client.post("/api/v1/usuarios", json={"nome":"Adm","email":"adm@email.com","senha":"123456","perfil":"admin"})
    admin_id = admin.json()["id"]
    assert client.delete(f"/api/v1/eventos/{eid}", headers={"X-User-Id":str(admin_id),"X-User-Perfil":"admin"}).status_code == 204
    assert client.get(f"/api/v1/eventos/{eid}").status_code == 404
    assert client.delete("/api/v1/eventos/9999", headers={"X-User-Id":str(admin_id),"X-User-Perfil":"admin"}).status_code == 404
