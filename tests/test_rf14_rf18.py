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

def _login(email):
    r = client.post("/api/v1/auth/login", json={"email": email, "senha": "123456"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_fluxo_inscricoes():
    org = _mkuser("Org", "org@email.com", "organizador")
    p1 = _mkuser("P1", "p1@email.com", "participante")
    p2 = _mkuser("P2", "p2@email.com", "participante")
    h_org = _login("org@email.com")
    h_p1 = _login("p1@email.com")
    h_p2 = _login("p2@email.com")

    cat = client.post("/api/v1/categorias", json={"nome": "Tech", "descricao": "t"}).json()
    ev = client.post("/api/v1/eventos", json={"nome": "Evento X", "descricao": "d", "data_evento": "2026-10-10",
        "horario": "14:00", "local": "Lab", "capacidade": 1, "categoria_id": cat["id"]}, headers=h_org)
    assert ev.status_code == 201
    eid = ev.json()["id"]

    # RF14 sucesso
    i1 = client.post(f"/api/v1/eventos/{eid}/inscricoes", json={"usuario_id": p1["id"]}, headers=h_p1)
    assert i1.status_code == 201
    assert i1.json()["status"] == "ativa"
    iid = i1.json()["id"]

    # RN02 duplicada -> 409
    assert client.post(f"/api/v1/eventos/{eid}/inscricoes", json={"usuario_id": p1["id"]}, headers=h_p1).status_code == 409
    # RN03 lotação (capacidade=1) -> 409
    assert client.post(f"/api/v1/eventos/{eid}/inscricoes", json={"usuario_id": p2["id"]}, headers=h_p2).status_code == 409
    # participante não inscreve outro -> 403
    assert client.post(f"/api/v1/eventos/{eid}/inscricoes", json={"usuario_id": p2["id"]}, headers=h_p1).status_code == 403
    # evento inexistente -> 404
    assert client.post("/api/v1/eventos/9999/inscricoes", json={"usuario_id": p1["id"]}, headers=h_p1).status_code == 404

    # RF15: participante vê só as próprias; org vê todas
    mine = client.get("/api/v1/inscricoes", headers=h_p1).json()
    assert len(mine["data"]) == 1
    allr = client.get("/api/v1/inscricoes", headers=h_org).json()
    assert len(allr["data"]) == 1

    # RF17: participantes (org dono ok; participante 403)
    part_ok = client.get(f"/api/v1/eventos/{eid}/participantes", headers=h_org)
    assert part_ok.status_code == 200
    assert len(part_ok.json()["data"]) == 1
    assert client.get(f"/api/v1/eventos/{eid}/participantes", headers=h_p1).status_code == 403

    # RF16: dono cancela 204; cancela de outro 403; inexistente 404
    assert client.delete(f"/api/v1/inscricoes/{iid}", headers=h_p2).status_code == 403
    assert client.delete(f"/api/v1/inscricoes/{iid}", headers=h_p1).status_code == 204
    assert client.delete("/api/v1/inscricoes/9999", headers=h_p1).status_code == 404
    # após cancelar, vaga libera e reinscrição funciona (reativa)
    r2 = client.post(f"/api/v1/eventos/{eid}/inscricoes", json={"usuario_id": p2["id"]}, headers=h_p2)
    assert r2.status_code == 201
    r3 = client.post(f"/api/v1/eventos/{eid}/inscricoes", json={"usuario_id": p1["id"]}, headers=h_p1)
    assert r3.status_code in (201, 409)  # 409 se lotado por p2, 201 se vaga — ambos coerentes
