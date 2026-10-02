# Sistema de Gerenciamento de Eventos Acadêmicos — RF01–RF26

API REST para gerenciamento de eventos acadêmicos. Implementação completa dos
**RF-01 a RF-26** da documentação (Seções 2 e 9), com as 6 entidades do DER (Seção 7).

> **Decisão documentada:** o campo do evento é **`nome`** (igual ao DER, Seção 7),
> prevalecendo sobre os exemplos das Seções 9.5–9.8 que escrevem `"titulo"`.
> Exceção: `GET /favoritos` devolve a chave `"titulo"` no item (fiel ao exemplo 9.15),
> com valor vindo de `evento.nome`.

## Integrantes
Igor Philipo, João Vinicius, Kamylle da Silva, Roselí Maria — Orientador: Victor Henrique — Recife 2026

## Quick Start

```bash
cd "D:\projetoback end\sistema-eventos"
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

## Variáveis de Ambiente (.env)
```
DATABASE_URL=sqlite:///./eventos.db
SECRET_KEY=super-secret-key-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Migrations (Alembic — RNF10)
```bash
python3 -c "import sys; sys.path.pop(0); from alembic.config import main; main(argv=['upgrade','head'])"
# nova migração: ... main(argv=['revision','--autogenerate','-m','descricao'])
```
Migração inicial `alembic/versions/0001_initial.py` cria as 6 tabelas
(usuarios, categorias, eventos, inscricoes, certificados, favoritos).
Em dev o `main.py` ainda usa `create_all` como fallback.

## RFs Implementados (RF01–RF26)

| RF | Rota | Método | Status |
|---|---|---|---|
| RF01 Cadastrar usuário | /api/v1/usuarios | POST | 201 |
| RF02 Consultar usuários | /api/v1/usuarios | GET | 200 `{success,data,message}` |
| RF02 Detalhar | /api/v1/usuarios/{id} | GET | 200 |
| RF03 Atualizar usuário | /api/v1/usuarios/{id} | PUT | 200 |
| RF04 Login | /api/v1/auth/login e /api/v1/usuarios/login | POST | 200 JWT / 401 |
| RF05 Cadastrar categoria | /api/v1/categorias | POST | 201 |
| RF06 Consultar categorias | /api/v1/categorias (+/{id}) | GET | 200 |
| RF07 Cadastrar evento | /api/v1/eventos | POST | 201 (auth: Bearer ou X-User-*) |
| RF08 Consultar eventos | /api/v1/eventos | GET | 200 |
| RF09 Detalhar evento | /api/v1/eventos/{id} | GET | 200 / 404 |
| RF10 Atualizar evento | /api/v1/eventos/{id} | PUT | 200 / 403 RN06 / 404 |
| RF11 Excluir evento (só admin) | /api/v1/eventos/{id} | DELETE | 204 / 403 / 404 |
| RF12 Buscar (`?q=` por nome) | /api/v1/eventos?q= | GET | 200 |
| RF13 Filtrar (`?categoria_id=&data_evento=`) | /api/v1/eventos | GET | 200 |
| RF14 Realizar inscrição | /api/v1/eventos/{id}/inscricoes `{usuario_id}` | POST | 201 / 404 / 409 RN02/RN03 / 403 |
| RF15 Consultar inscrições | /api/v1/inscricoes | GET | 200 (participante: só as próprias) |
| RF16 Cancelar inscrição (lógico) | /api/v1/inscricoes/{id} | DELETE | 204 / 403 RN08 / 404 |
| RF17 Participantes do evento | /api/v1/eventos/{id}/participantes | GET | 200 (admin/org dono) / 403 |
| RF18 Controlar capacidade | (enforcement no RF14: ativas < capacidade) | — | 409 RN03 |
| RF19 Emitir certificado | /api/v1/inscricoes/{id}/certificado | POST | 201 / 400 RN09/RN14 / 409 / 403 |
| RF20 Consultar certificado | /api/v1/certificados/{id} | GET | 200 / 403 / 404 |
| RF21 Validar por código | /api/v1/certificados/validar/{codigo} | GET | 200 / 404 (pública) |
| RF22 Ver/editar próprio perfil | /api/v1/usuarios/me | GET/PATCH | 200 / 401 / 409 RN01 |
| RF23 Alterar própria senha | /api/v1/usuarios/me/senha | PUT | 200 / 401 |
| RF24 Favoritar evento | /api/v1/eventos/{id}/favoritos | POST | 201 `{message}` / 409 RN15 / 403 / 404 |
| RF25 Consultar favoritos | /api/v1/favoritos | GET | 200 `{data}` (próprios) |
| RF26 Remover favorito | /api/v1/eventos/{id}/favoritos | DELETE | 204 / 404 RN16 |

### Autenticação
- Hash bcrypt (RN11 senha oculta), JWT no login (RF04/CA10).
- Rotas de escrita aceitam `Authorization: Bearer <jwt>` (oficial) ou
  `X-User-Id` + `X-User-Perfil` (legado, depreciado).
- Sem credencial em rota protegida → 401.

### Regras de Negócio aplicadas
- RN01 email único (409) · RN02 inscrição única ativa (409) · RN03 lotação (409)
- RN04 data evento ≥ hoje (422) · RN05 só admin/organizador cadastra (403)
- RN06 organizador só altera os seus (403) · RN07 só admin exclui (403)
- RN08 só cancela as próprias (403) · RN09 vínculo c/ inscrição ativa
- RN10 código único · RN11 senha oculta · RN12 categoria obrigatória (404)
- RN13 capacidade > 0 (422) · RN14 evento já ocorrido p/ certificado (400)
- RN15 favorito único (409) · RN16 remove só o próprio (404)

## Exemplos

### POST /usuarios
```json
{"nome":"Maria Silva","email":"maria@email.com","senha":"123456","perfil":"participante"}
```

### POST /categorias
```json
{"nome":"Tecnologia","descricao":"Eventos de tecnologia"}
```

### POST /eventos (header Authorization: Bearer <jwt>)
```json
{"nome":"Workshop de Python","descricao":"Intro Python","data_evento":"2026-10-10","horario":"14:00","local":"Lab 01","capacidade":50,"categoria_id":1}
```

### POST /eventos/{id}/inscricoes
```json
{"usuario_id": 3}
```

## Testes
```bash
python3 -m pytest tests/ -q
# test_rf01_rf10.py (RF01–11, RNs base) · test_rf14_rf18.py · test_rf19_rf21.py · test_rf22_rf26.py
```

## Estrutura
```
sistema-eventos/
├── app/api/v1/routers/{usuarios,auth,categorias,eventos,inscricoes,certificados,favoritos}.py
├── app/models/{usuario,categoria,evento,inscricao,certificado,favorito}.py
├── app/schemas/{usuario,categoria,evento,inscricao,certificado,favorito}.py
├── app/database/connection.py
├── app/core/{config,security,deps}.py
├── alembic/{env.py,versions/0001_initial.py} + alembic.ini
├── tests/test_rf*.py
├── main.py
└── docs/DOCUMENTACAO.md
```

 