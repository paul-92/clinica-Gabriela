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
- `GET/POST/PUT /patients`
- `GET/POST/PUT /psychologists`
- `GET/POST/PUT /appointments`
- `GET/POST/PUT /clinical-records`
- `GET/POST /finance/payments`
- `GET/POST /finance/expenses`
- `GET /finance/summary`
- `GET/PUT /settings`
