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
- `GET/POST/PUT/PATCH /appointments`
- `POST /appointments/{id}/cancel`
- `POST /appointments/{id}/done`
- `POST /appointments/{id}/no-show`
- `POST /appointments/{id}/reschedule`
- `POST /appointments/{id}/exceptional-correction` (somente admin, motivo e `If-Match` obrigatórios)
- `GET/POST/PUT/PATCH /clinical-records`
- `POST /clinical-records/{id}/finalize`
- `POST /clinical-records/{id}/rectifications`
- `DELETE /clinical-records/{id}` (somente DRAFT elegível)
- `GET /finance/payments?start=YYYY-MM-DD&end=YYYY-MM-DD&regime=cash|accrual`
- `POST /finance/payments` (cobrança manual pendente, `amount_cents` inteiro)
- `GET/PATCH /finance/payments/{id}` (`PATCH` exige `If-Match`)
- `POST /finance/payments/{id}/pay`
- `POST /finance/payments/{id}/cancel`
- `POST /finance/payments/{id}/reverse` (somente admin)
- `GET /finance/expenses?start=YYYY-MM-DD&end=YYYY-MM-DD&regime=cash|accrual`
- `POST /finance/expenses` e `POST /finance/expenses/{id}/cancel` (somente admin)
- `GET/POST /finance/categories` e `PATCH /finance/categories/{id}` (mutações somente admin)
- `GET /finance/summary?start=YYYY-MM-DD&end=YYYY-MM-DD&regime=cash|accrual`
- `GET /finance/events/{resource_type}/{resource_id}` (auditoria somente admin)
- `GET/PUT /settings`

O timezone IANA efetivo de `settings` governa novos horários da agenda. Horários locais
inexistentes ou ambíguos por DST são rejeitados; timestamps históricos não são
reinterpretados automaticamente.

## Integridade e concorrência

- `PATCH` preserva campos ausentes; `NULL` somente limpa campos explicitamente nullable.
- Recursos versionados expõem ETag. `PATCH` e finalização usam `If-Match`.
- Precondição ausente retorna `428`; versão obsoleta retorna `412`.
- Referência inexistente retorna `404`, conflito de estado/unicidade retorna `409` e
  payload inválido retorna `422`.
- `PUT` permanece temporariamente disponível para compatibilidade e está deprecado.
- Prontuários `FINALIZED` e `LEGACY_PRESERVED` são imutáveis; correções são
  retificações append-only.

## Contrato financeiro SPEC-005

O contrato abaixo incorpora a decisão HUMAN D005-08. A implementação foi
reconciliada e validada pelo executor, sem executar E011 ou criar candidato
operacional.

- Dinheiro e agregados financeiros usam centavos inteiros (`amount_cents`); zero,
  negativo, float canônico, arredondamento e truncamento são rejeitados.
- Caixa usa `paid_at`. Competência é mensal e usa exclusivamente o par inteiro
  `competence_year` + `competence_month`, apresentado como `YYYY-MM`; não existe
  dia representativo canônico. Filtros mantêm os regimes separados e usam limites
  semiabertos no respectivo domínio temporal.
- Payloads de cobrança e despesa exigem `competence_year` e `competence_month` e
  retornam também `competence_period` como apresentação `YYYY-MM`.
- Consultas CASH usam `start`/`end` como datas ISO. Consultas ACCRUAL não aceitam
  datas diárias: usam `start_year`, `start_month`, `end_year` e `end_month`.
- Payload legado com `competence_date` retorna `422`; não existe alias que fabrique
  primeiro ou último dia do mês.
- Estados persistidos da cobrança: `pending`, `paid`, `canceled`, `reversed`.
  `overdue` é apenas derivado.
- Pagamento parcial, múltiplas liquidações e parcelamento retornam `422`.
- Cobranças são manuais. Agenda não cria, associa, cancela nem altera finanças.
- Admin tem autoridade integral; recepção opera cobranças, sem estorno nem
  administração de despesas/categorias; psicólogo recebe `403`.
- Escritas versionadas usam `ETag`/`If-Match`; versão obsoleta retorna `412`.
- Cancelamentos, estornos e despesas preservam o registro e a trilha append-only;
  não existe endpoint de exclusão financeira.
