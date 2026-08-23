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
- Financeiro com resumo, lancamento de receitas, lancamento de despesas e tabelas
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
- `GET /finance/payments`
- `POST /finance/payments`
- `GET /finance/expenses`
- `POST /finance/expenses`
- `GET /finance/summary`

Se a API estiver desligada, a interface usa dados locais de demonstracao para que as telas continuem navegaveis.
