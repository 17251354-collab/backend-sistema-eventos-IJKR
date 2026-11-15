import sys
sys.path.insert(0, "..")
from fastapi.testclient import TestClient
from main import app
from app.database.connection import Base, engine

client = TestClient(app)

def test_fluxo_certificados():
    client.post("/api/v1/usuarios", json={"nome":"Org Cert","email":"org.cert@email.com","senha":"123456","perfil":"organizador"})
    client.post("/api/v1/usuarios", json={"nome":"P1 Cert","email":"p1.cert@email.com","senha":"123456","perfil":"participante"})
    
    r_org = client.post("/api/v1/auth/login", data={"username":"org.cert@email.com","password":"123456"})
    h_org = {"Authorization": f"Bearer {r_org.json()['access_token']}"}
    
    r_p1 = client.post("/api/v1/auth/login", data={"username":"p1.cert@email.com","password":"123456"})
    h_p1 = {"Authorization": f"Bearer {r_p1.json()['access_token']}"}
    p1_id = r_p1.json()["user"]["id"]

    cat = client.post("/api/v1/categorias", json={"nome":"Cat Cert","descricao":"x"})
    cat_id = cat.json()["id"]
    
    # 1. Cria o evento com data no FUTURO (para passar na validação RN04)
    ev = client.post("/api/v1/eventos", json={"nome":"Evento Cert","descricao":"x","data_evento":"2030-01-01","horario":"14:00","local":"Lab","capacidade":10,"categoria_id":cat_id}, headers=h_org)
    assert ev.status_code == 201
    ev_id = ev.json()["id"]

    # 2. Atualiza a data para o PASSADO (para permitir emitir o certificado - RN14)
    upd = client.put(f"/api/v1/eventos/{ev_id}", json={"data_evento":"2024-01-01"}, headers=h_org)
    assert upd.status_code == 200

    insc = client.post(f"/api/v1/eventos/{ev_id}/inscricoes", json={"usuario_id": p1_id}, headers=h_p1)
    assert insc.status_code == 201
    insc_id = insc.json()["id"]

    cert = client.post(f"/api/v1/inscricoes/{insc_id}/certificado", headers=h_org)
    assert cert.status_code == 201
    cert_data = cert.json()
    cert_id = cert_data["id"]
    codigo = cert_data["codigo_validacao"]

    assert client.get(f"/api/v1/certificados/validar/{codigo}").status_code == 200
    assert client.get(f"/api/v1/certificados/{cert_id}", headers=h_p1).status_code == 200