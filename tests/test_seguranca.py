def test_criar_usuario_participante(test_client):
    response = test_client.post("/api/v1/usuarios", json={
        "nome": "Participante Teste", "email": "part@teste.com", "senha": "123", "perfil": "participante"
    })
    assert response.status_code == 201
    assert "senha" not in response.json()

def test_criar_usuario_organizador(test_client):
    response = test_client.post("/api/v1/usuarios", json={
        "nome": "Organizador Teste", "email": "org@teste.com", "senha": "123", "perfil": "organizador"
    })
    assert response.status_code == 201

def test_login_sucesso(test_client):
    response = test_client.post("/api/v1/auth/login", data={"username": "part@teste.com", "password": "123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_senha_errada(test_client):
    response = test_client.post("/api/v1/auth/login", data={"username": "part@teste.com", "password": "errada"})
    assert response.status_code == 401

def test_acesso_sem_token_401(test_client):
    response = test_client.get("/api/v1/usuarios/me")
    assert response.status_code == 401

def test_participante_tenta_criar_evento_403(test_client):
    # Login do participante
    login = test_client.post("/api/v1/auth/login", data={"username": "part@teste.com", "password": "123"})
    token = login.json()["access_token"]
    
    response = test_client.post("/api/v1/eventos", json={
        "nome": "Evento P", "data_evento": "2026-12-01", "capacidade": 10, "categoria_id": 1
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403 # Bloqueado!

def test_organizador_pode_criar_evento_201(test_client):
    # Login do organizador
    login = test_client.post("/api/v1/auth/login", data={"username": "org@teste.com", "password": "123"})
    token = login.json()["access_token"]
    
    # Cria uma categoria primeiro para não dar erro de chave estrangeira
    test_client.post("/api/v1/categorias", json={"nome": "Cat Teste"})
    
    response = test_client.post("/api/v1/eventos", json={
        "nome": "Evento O", "data_evento": "2026-12-01", "capacidade": 10, "categoria_id": 1
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201 # Autorizado!

def test_rota_publica_funciona_200(test_client):
    response = test_client.get("/api/v1/eventos")
    assert response.status_code == 200