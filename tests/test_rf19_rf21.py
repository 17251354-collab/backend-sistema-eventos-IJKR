import sys
sys.path.insert(0, "..")
from datetime import date, timedelta
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

def test_fluxo_certificados():
    org = _mkuser("Org", "org@email.com", "organizador")
    p1 = _mkuser("P1", "p1@email.com", "participante")
    p2 = _mkuser("P2", "p2@email.com", "participante")
    h_org = _login("org@email.com")
    h_p1 = _login("p1@email.com")
    h_p2 = _login("p2@email.com")

    cat = client.post("/api/v1/categorias", json={"nome": "Tech", "descricao": "t"}).json()
    hoje = date.today().isoformat()
    futuro = (date.today() + timedelta(days=30)).isoformat()

    # Evento "já ocorrido" (hoje) -> RN14 libera; evento futuro -> RN14 bloqueia
    ev_ok = client.post("/api/v1/eventos", json={"nome": "Ev Hoje", "descricao": "d", "data_evento": hoje,
        "horario": "14:00", "local": "Lab", "capacidade": 10, "categoria_id": cat["id"]}, headers=h_org)
    assert ev_ok.status_code == 201
    ev_fut = client.post("/api/v1/eventos", json={"nome": "Ev Futuro", "descricao": "d", "data_evento": futuro,
        "horario": "14:00", "local": "Lab", "capacidade": 10, "categoria_id": cat["id"]}, headers=h_org)
    assert ev_fut.status_code == 201

    i_ok = client.post(f"/api/v1/eventos/{ev_ok.json()['id']}/inscricoes", json={"usuario_id": p1["id"]}, headers=h_p1).json()
    i_fut = client.post(f"/api/v1/eventos/{ev_fut.json()['id']}/inscricoes", json={"usuario_id": p2["id"]}, headers=h_p2).json()

    # RF19 sucesso (org) — código único RN10
    c1 = client.post(f"/api/v1/inscricoes/{i_ok['id']}/certificado", headers=h_org)
    assert c1.status_code == 201
    assert c1.json()["codigo_validacao"].startswith("CERT-")
    cid = c1.json()["id"]
    codigo = c1.json()["codigo_validacao"]

    # duplicado -> 409
    assert client.post(f"/api/v1/inscricoes/{i_ok['id']}/certificado", headers=h_org).status_code == 409
    # RN14 evento futuro -> 400
    assert client.post(f"/api/v1/inscricoes/{i_fut['id']}/certificado", headers=h_org).status_code == 400
    # participante não emite -> 403
    assert client.post(f"/api/v1/inscricoes/{i_fut['id']}/certificado", headers=h_p2).status_code == 403
    # inscrição inexistente -> 404 (RN09)
    assert client.post("/api/v1/inscricoes/9999/certificado", headers=h_org).status_code == 404

    # RF20: dono consulta ok; outro participante 403; inexistente 404
    assert client.get(f"/api/v1/certificados/{cid}", headers=h_p1).status_code == 200
    assert client.get(f"/api/v1/certificados/{cid}", headers=h_p2).status_code == 403
    assert client.get("/api/v1/certificados/9999", headers=h_p1).status_code == 404

    # RF21 validar: código válido 200; inválido 404
    v = client.get(f"/api/v1/certificados/validar/{codigo}")
    assert v.status_code == 200
    assert v.json()["valido"] is True
    assert v.json()["evento"]["nome"] == "Ev Hoje"
    assert client.get("/api/v1/certificados/validar/CERT-0000-XXXX").status_code == 404
