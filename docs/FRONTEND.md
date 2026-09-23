# Frontend Electron + React

O frontend fica em `frontend/` e usa Electron, React, Vite e lucide-react.

## Executar

```bash
cd frontend
npm install
npm run dev
```

O app abre uma janela desktop Electron e consome o backend em `http://127.0.0.1:8000`.

## Telas criadas

- Login
- Dashboard com indicadores operacionais, financeiros e agenda do dia
- Pacientes
- Psicologos
- Agenda com filtro por data, filtro por psicologo, criacao de atendimento e mudanca de status
- Prontuario com ficha de atendimento, evolucao clinica, conduta, encaminhamentos e historico
- Financeiro com período `[start,end)`, regime de caixa/competência explicitamente
  rotulado, competência mensal `YYYY-MM` sem seletor diário, cobranças manuais,
  ciclo de vida e despesas/categorias controladas
- Relatorios
- Configuracoes

## Integracao com API

A interface consulta:

- `GET /health`
- `POST /auth/login`
- `GET /dashboard/summary`
- `GET /patients`
- `GET /psychologists`
- `GET /appointments`
- `POST /appointments`
- `PUT /appointments/{appointment_id}`
- `GET /clinical-records`
- `POST /clinical-records`
- `GET /finance/payments` com datas para CASH ou ano/mês para ACCRUAL
- `POST /finance/payments`
- `PATCH /finance/payments/{id}` e ações `pay`, `cancel`, `reverse`
- `GET /finance/expenses` com datas para CASH ou ano/mês para ACCRUAL
- `POST /finance/expenses`
- `POST /finance/expenses/{id}/cancel`
- `GET/POST /finance/categories` e `PATCH /finance/categories/{id}`
- `GET /finance/summary` com datas para CASH ou ano/mês para ACCRUAL

O frontend financeiro recebe e envia centavos inteiros. A conversão de texto usa
operações decimais determinísticas; `Number` não é usado para calcular totais.
Competência é capturada com `input type="month"`, convertida diretamente para
`competence_year`/`competence_month` e exibida como `YYYY-MM`; nenhum dia artificial
é criado no estado local ou no payload.
Administração de despesas/categorias e estorno aparecem somente para admin;
psicólogos não veem o módulo financeiro. Essas regras visuais não substituem a
autorização do backend.

Se a API falhar, o financeiro exibe estado controlado de erro e limpa os dados da
visão; não apresenta fallback/demo como se fosse dado autoritativo.
