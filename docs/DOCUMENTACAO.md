# Documentação — Sistema de Gerenciamento de Eventos Acadêmicos (RF01 a RF26)

> Implementação completa da documentação conceitual (20 seções): RF-01–RF-26,
> RN01–RN16, 6 entidades do DER, contratos 9.1–9.16, status codes, matriz de permissões.

## 1. Contexto (Pág. 4–6)
API REST centralizada (FastAPI) para cadastro/consulta de usuários, categorias e eventos,
inscrições, certificados e favoritos — Admin, Organizador, Participante.

## 2. Requisitos Funcionais — todos implementados
| Código | Requisito | Rota |
|---|---|---|
| RF01 | Cadastrar usuário | POST /api/v1/usuarios (201, RN01, RN11) |
| RF02 | Consultar usuário | GET /api/v1/usuarios + GET /{id} (200 envelope) |
| RF03 | Atualizar usuário | PUT /api/v1/usuarios/{id} (200, RN01) |
| RF04 | Realizar login | POST /api/v1/auth/login (+ alias /usuarios/login) (200 JWT, 401) |
| RF05 | Cadastrar categoria | POST /api/v1/categorias (201) |
| RF06 | Consultar categorias | GET /api/v1/categorias (200, só ativas) |
| RF07 | Cadastrar evento | POST /api/v1/eventos (201, RN04/RN05/RN12/RN13) |
| RF08 | Consultar eventos | GET /api/v1/eventos (200) |
| RF09 | Detalhes do evento | GET /api/v1/eventos/{id} (200/404) |
| RF10 | Atualizar evento | PUT /api/v1/eventos/{id} (200, RN06) |
| RF11 | Excluir evento (só admin) | DELETE /api/v1/eventos/{id} (204/403/404, CA09/RN07) |
| RF12 | Buscar por nome (`?q=`) | GET /api/v1/eventos?q= (200) |
| RF13 | Filtrar categoria/data | GET /api/v1/eventos?categoria_id=&data_evento= (200) |
| RF14 | Realizar inscrição | POST /api/v1/eventos/{id}/inscricoes (201/409 RN02/RN03) |
| RF15 | Consultar inscrições | GET /api/v1/inscricoes (200; participante: próprias) |
| RF16 | Cancelar inscrição (lógico) | DELETE /api/v1/inscricoes/{id} (204/403 RN08/404) |
| RF17 | Consultar participantes | GET /api/v1/eventos/{id}/participantes (admin/org dono) |
| RF18 | Controlar capacidade | enforcement no RF14 (ativas < capacidade, 409 RN03) |
| RF19 | Emitir certificado | POST /api/v1/inscricoes/{id}/certificado (201/400 RN09/RN14/409) |
| RF20 | Consultar certificado | GET /api/v1/certificados/{id} (dono/admin/org) |
| RF21 | Validar por código | GET /api/v1/certificados/validar/{codigo} (pública; sem contrato em 9.x — proposta) |
| RF22 | Ver/editar próprio perfil | GET/PATCH /api/v1/usuarios/me (409 RN01) |
| RF23 | Alterar própria senha | PUT /api/v1/usuarios/me/senha (401 se atual incorreta) |
| RF24 | Favoritar evento | POST /api/v1/eventos/{id}/favoritos (201 `{message}`/409 RN15) |
| RF25 | Consultar favoritos | GET /api/v1/favoritos (200 `{data}`, próprios) |
| RF26 | Remover favorito | DELETE /api/v1/eventos/{id}/favoritos (204/404 RN16) |

## 3. RNF aplicados
RNF01 desempenho · RNF02 hash bcrypt · RNF03 JWT (`app/core/security.py`, `deps.py`)
RNF04 autorização por perfil (403) · RNF05 Pydantic (422) · RNF06 FKs/SQLite/Postgres
RNF07 `app/models|schemas|routers|core` · RNF08 Swagger `/docs` · RNF09 SQLite dev
RNF10 Alembic (`alembic.ini`, `env.py`, `versions/0001_initial.py`) · RNF11 status codes Seção 10
RNF12 manutenibilidade · RNF14 Python · RNF15 4 arquivos pytest · RNF16 GitHub (repositório a ser disponibilizado).

## 4. Perfis / 12. Matriz
Admin (tudo, único que exclui eventos), Organizador (eventos próprios, inscrições, certificados),
Participante (consulta, inscreve-se, cancela as próprias, certificados próprios, favoritos, perfil/senha).
JWT Bearer oficial; `X-User-*` legado depreciado. Divergências conscientes do MVP mantidas:
`GET /usuarios` e `POST /categorias` abertos (testes legados), `PUT /usuarios/{id}` sem trava admin.

## 5. Regras de Negócio — todas vigentes
RN01 409 · RN02 409 · RN03 409 · RN04 422 · RN05 403 · RN06 403 · RN07 403 · RN08 403 ·
RN09 400/404 · RN10 unique · RN11 oculta · RN12 404 · RN13 422 · RN14 400 (evento ≤ hoje + ativa) ·
RN15 409 · RN16 404.

## 6–8. Entidades, DER e dicionário
Tabelas: `usuarios`, `categorias`, `eventos`, `inscricoes`, `certificados`, `favoritos`
(ver `app/models/` e migração `0001_initial`).
**Decisão:** `eventos.nome` igual ao DER (Seção 7), prevalecendo sobre 8.3/9.5–9.8 (`"titulo"`).
`GET /favoritos` mantém chave `"titulo"` do exemplo 9.15 (valor = `evento.nome`).

## 9. Contratos 9.1–9.16 — aderência
9.1–9.8 ✅ (com `nome` no lugar de `titulo`); 9.9–9.11 ✅ (inscrição/cancelamento 204);
9.12–9.13 ✅ (código `CERT-AAAA-NNNN`); 9.14–9.16 ✅ (201 `{message}` / 200 `{data}` / 204).
Ajustes: 9.13 com barra simples; RF21 sem contrato na doc → `GET /certificados/validar/{codigo}`.

## 10/11. Status e padrão
200/201/204/400/401/403/404/409/422 (Seção 10). Listas: `{success,data,message}`;
criações: objeto; erros: `{detail}`.

## 13–15. Estrutura, tecnologias, banco
Seção 13 ✅ com os 7 routers (inclui `auth.py` extra). Alembic funcional
(`upgrade head` verificado: 6 tabelas + `alembic_version`). `.env` p/ `DATABASE_URL`.

## 16–17. Backlog (US01–US21) e aceitação (CA01–CA10)
Todos os US com rota correspondente; CA01–CA10 cobertos por 4 arquivos de teste:
`pytest tests/` → **4 passed**.

## 18–20. Protótipo, GitHub, considerações
Seção 18 = este MVP completo. Seção 19: repositório a ser disponibilizado.
Seção 20: sistema pronto p/ apresentação; evoluções sugeridas — paginação,
`PUT /usuarios/{id}` admin-only, `GET /usuarios` admin-only, refresh tokens.
