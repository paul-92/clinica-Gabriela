# Backend FastAPI

O backend fica no pacote `backend/` e usa FastAPI, SQLite, SQLAlchemy e Pydantic.

## Executar

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Depois acesse:

- API: `http://127.0.0.1:8000`
- Documentacao Swagger: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Modulos

- `backend/models`: entidades do banco.
- `backend/schemas`: contratos de entrada e saida da API.
- `backend/repositories`: acesso ao banco.
- `backend/services`: regras de negocio.
- `backend/api/routes`: endpoints HTTP.
- `backend/database`: sessao SQLite, criacao de tabelas e seed.

## Endpoints principais

- `POST /auth/login`
- `GET/POST/PUT/PATCH /patients`
- `GET/POST/PUT/PATCH /psychologists`
- `POST /psychologists/{id}/aptitude`
- `GET/POST/PUT /appointments`
- `GET/POST/PUT/PATCH /clinical-records`
- `POST /clinical-records/{id}/finalize`
- `POST /clinical-records/{id}/rectifications`
- `DELETE /clinical-records/{id}` (somente DRAFT elegível)
- `GET/POST /finance/payments`
- `GET/POST /finance/expenses`
- `GET /finance/summary`
- `GET/PUT /settings`

## Integridade e concorrência

- `PATCH` preserva campos ausentes; `NULL` somente limpa campos explicitamente nullable.
- Recursos versionados expõem ETag. `PATCH` e finalização usam `If-Match`.
- Precondição ausente retorna `428`; versão obsoleta retorna `412`.
- Referência inexistente retorna `404`, conflito de estado/unicidade retorna `409` e
  payload inválido retorna `422`.
- `PUT` permanece temporariamente disponível para compatibilidade e está deprecado.
- Prontuários `FINALIZED` e `LEGACY_PRESERVED` são imutáveis; correções são
  retificações append-only.
