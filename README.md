# Sistema de Gerenciamento de Eventos Acadêmicos

API REST completa para o gerenciamento de eventos acadêmicos, desenvolvida com FastAPI. O sistema implementa os 26 Requisitos Funcionais (RF01–RF26), 16 Regras de Negócio (RN01–RN16), autenticação segura via JWT, controle de acesso baseado em perfis (RBAC), persistência em nuvem e suíte de 15 testes automatizados.

## Integrantes

- **Equipe:** Igor Philipo, João Vinicius, Kamylle da Silva, Roselí Maria
- **Orientador:** Victor Henrique
- **Local / Ano:** Recife - PE, 2026

## Links de Produção

- **Repositório GitHub (v3.0.0):** https://github.com/17251354-collab/backend-sistema-eventos-IJKR
- **API Pública (HTTPS):** https://backend-sistema-eventos-ijkr.onrender.com
- **Documentação Swagger:** https://backend-sistema-eventos-ijkr.onrender.com/docs

## Evolução entre a Primeira e a Segunda Unidade

Na Primeira Unidade (v1.0), foi estruturada a concepção técnica e o MVP local (`http://127.0.0.1:8000`) com FastAPI, SQLAlchemy, Alembic, SQLite (`eventos.db`), as 6 entidades do DER (`usuarios`, `categorias`, `eventos`, `inscricoes`, `certificados`, `favoritos`) e a base inicial de rotas e JWT.

Na Segunda Unidade (v3.0.0), o projeto evoluiu nos seguintes pontos:

- **Persistência em Nuvem (SQLite → Turso/libSQL):** Migração do arquivo local `eventos.db` para o banco relacional em nuvem Turso (libSQL), garantindo persistência real dos registros em ambiente publicado sem expor credenciais no repositório.
- **Deploy em Produção com HTTPS:** Publicação contínua da API e do Swagger no Render (`https://backend-sistema-eventos-ijkr.onrender.com`).
- **Suíte de Testes Automatizados (Pytest):** Evolução dos testes manuais no Swagger para 15 testes automatizados (`tests/`), validando segurança (401/403), regras de negócio (RN01–RN16) e fluxos funcionais (RF01–RF26).
- **Consolidação do RBAC e Qualidade de Código:** Aplicação integral da matriz de permissões por perfil (Admin, Organizador, Participante), separação modular de responsabilidades (`api/v1`, `core`, `database`, `models`, `schemas`, `services`) e padronização das respostas HTTP e documentação OpenAPI.

## Matriz de Permissões (RBAC)

| Funcionalidade | Admin | Organizador | Participante |
| :--- | :--- | :--- | :--- |
| Cadastrar usuário (`POST /api/v1/usuarios`) | SIM | NÃO | SIM |
| Consultar usuários (`GET /api/v1/usuarios`) | SIM | NÃO | NÃO |
| Cadastrar categoria (`POST /api/v1/categorias`) | SIM | NÃO | NÃO |
| Cadastrar evento (`POST /api/v1/eventos`) | SIM | SIM | NÃO |
| Alterar evento (`PUT /api/v1/eventos/{id}`) | SIM | SIM | NÃO |
| Excluir evento (`DELETE /api/v1/eventos/{id}`) | SIM | NÃO | NÃO |
| Consultar / Buscar / Filtrar eventos | SIM | SIM | SIM |
| Realizar e cancelar própria inscrição | NÃO | NÃO | SIM |
| Ver participantes do evento | SIM | SIM | NÃO |
| Emitir certificado | SIM | SIM | NÃO |
| Consultar próprio certificado | NÃO | NÃO | SIM |
| Validar certificado (`GET /certificados/validar/{codigo}`) | Público | Público | Público |
| Editar próprio perfil e alterar senha | SIM | SIM | SIM |
| Favoritar / Consultar / Remover favoritos | NÃO | NÃO | SIM |

## Tecnologias Utilizadas

- **Python 3.12+ / FastAPI:** Linguagem base e framework web assíncrono.
- **SQLAlchemy / Alembic:** ORM, relacionamentos do DER e controle de migrations.
- **Turso (libSQL) / SQLite:** Banco de dados em nuvem (produção) e local (desenvolvimento/testes).
- **Passlib / Bcrypt / Python-Jose:** Hash seguro de senhas e tokens JWT com expiração.
- **Pytest:** Execução da suíte de 15 testes automatizados.
- **Render:** Hospedagem em produção com HTTPS.

## Estrutura do Projeto

```text
backend-sistema-eventos-IJKR/
├── api/
│   └── v1/          # Rotas e endpoints da API REST
├── core/            # Configurações, segurança e autenticação JWT
├── database/        # Conexão com SQLite (local/testes) e Turso/libSQL (produção)
├── models/          # Modelos ORM (SQLAlchemy) das 6 entidades
├── schemas/         # Schemas de validação e serialização (Pydantic)
├── services/        # Regras de negócio, RBAC e serviços da aplicação
└── tests/           # Suíte de 15 testes automatizados (Pytest)

