# SPEC-005 — Plano de reconciliação da competência mensal

Data: 22/09/2026

Autoridade: decisão HUMAN D005-08

Estado: `EXECUTED / VALIDATED_BY_IMPLEMENTATION_EXECUTOR`

## 1. Objetivo e limites

Reconciliar a implementação da SPEC-005 com a competência financeira canônica de
granularidade mensal, representada por `competence_year` + `competence_month` e
apresentada como `YYYY-MM`. Nenhum dia factual ou representativo integra essa
semântica.

Este plano não autoriza implementar as mudanças, executar E011/E012, migrar dados
operacionais, criar ou promover candidato, fazer cutover, nem alterar banco,
pointer, runtime manifest ou Generation 8/canonical.

## 2. Contrato-alvo

| Aspecto | Contrato reconciliado |
|---|---|
| Granularidade | mês civil |
| Persistência/domínio/API | `competence_year` inteiro + `competence_month` inteiro |
| Validade | ambos obrigatórios; mês `1..12`; combinação validada atomicamente |
| Apresentação | `YYYY-MM`, por exemplo `2026-07` |
| Proibido | `competence_date`, dia sentinela, primeiro/último dia ou timestamp artificial |
| Caixa | `paid_at`, com intervalo temporal `[start, end)` |
| Competência | par ano/mês, com intervalo mensal `[start_month, end_month)` |
| Invariant de pagamento | `status=paid` exige `paid_at` real e confiável |

O mesmo contrato mensal aplica-se a cobranças e despesas. A apresentação
`YYYY-MM` não substitui o par canônico nem autoriza converter o período para uma
data diária.

## 3. Inventário de impacto conhecido

1. **Modelo e schema:** `backend/models/finance.py`,
   `backend/schemas/finance.py` e constraints/índices associados.
2. **Persistência e regras:** `backend/repositories/finance_repository.py` e
   `backend/services/finance_service.py`.
3. **API e seed sintético:** rotas financeiras, `backend/database/seed.py`,
   serialização, validação e documentação OpenAPI.
4. **Migração isolada:** `backend/migration/spec005.py` e
   `scripts/spec005_candidate_migration.py`.
5. **Frontend:** `frontend/src/main.jsx`, incluindo formulários, filtros,
   agrupamentos, rótulos, parsing e payloads.
6. **Testes:** `tests/test_spec005_red_harness.py`,
   `tests/test_spec005_domain_repository.py`, `tests/test_spec005_api.py` e
   `tests/test_spec005_migration.py`, além da regressão afetada.
7. **Documentação:** SPEC, API, arquitetura, relatórios e qualquer exemplo que
   ainda apresente `competence_date` como canônico.

O inventário deve ser repetido no início da execução autorizada para capturar
novos consumidores e ocorrências indiretas.

## 4. Sequência de reconciliação proposta

### RCN-01 — Harness e contrato executável

- Atualizar primeiro fixtures e testes para o par ano/mês.
- Adicionar testes negativos para mês `0`, mês `13`, campo parcial, tipo inválido,
  `competence_date`, dia sentinela e combinação inesperada de campos.
- Preservar testes que demonstram a separação CASH/ACCRUAL.

**Saída esperada:** red harness falhando exclusivamente pela implementação antiga.

### RCN-02 — Modelo, schema e persistência candidatos

- Substituir `competence_date` por colunas inteiras obrigatórias de ano e mês em
  cobranças e despesas.
- Criar constraints e índices adequados a consultas por `(year, month)`.
- Ajustar schemas de criação, atualização, resposta e filtros sem alias diário.
- Fazer repository e service compararem períodos por par cronológico, preservando
  atomicidade, versionamento otimista e trilha append-only.

**Saída esperada:** domínio candidato sem armazenamento ou transporte de dia
artificial.

### RCN-03 — API, filtros e relatórios

- Expor ano e mês explicitamente em payloads e filtros.
- Definir limites mensais semiabertos para ACCRUAL e manter limites de `paid_at`
  para CASH.
- Revisar totais, agrupamentos e relatórios para que cada regime escolha somente
  sua autoridade temporal.
- Rejeitar payloads ambíguos e `competence_date` com erro controlado.

**Saída esperada:** nenhum endpoint, resumo ou relatório mistura caixa e
competência.

### RCN-04 — Frontend

- Capturar competência com controle mensal, sem selecionar ou fabricar dia.
- Enviar/receber `competence_year` e `competence_month`; renderizar `YYYY-MM`.
- Manter CASH como visão inicial e rotular claramente o regime ativo.
- Atualizar filtros e estados de validação/erro para o contrato mensal.

**Saída esperada:** UI incapaz de produzir um dia representativo artificial.

### RCN-05 — Migração isolada e legado R1–R6

- Alterar apenas a lógica de migração candidata após autorização específica.
- Materializar a decisão HUMAN `2026-07` como ano `2026` e mês `7` para R1–R6,
  mediante mapa de decisão versionado e privacy-safe; nunca como data diária.
- R2 mantém `status=paid` e `paid_at=null/desconhecido`, sem inferência. Como viola
  `paid → paid_at obrigatório`, deve permanecer `REVIEW/BLOCK` e ser excluído de
  qualquer candidato que exija cobrança canônica válida.
- Não alterar status, não relaxar constraint e não deslocar R2 para regime de
  competência como substituto do caixa.
- Outros registros só se tornam elegíveis após todas as demais validações; a
  decisão de competência, isoladamente, não certifica validade integral.

**Saída esperada:** dry-run sintético e privacy-safe prova o mapeamento mensal e o
bloqueio fail-closed de R2, sem tocar a Generation 8.

### RCN-06 — Revalidação e documentação

- Executar suites direcionadas e regressão afetada, build frontend, verificação de
  schema/constraints, scans de privacidade/segredos e busca residual por
  `competence_date` em superfícies canônicas.
- Reconciliar documentação e gerar nova Evidence, sem reescrever o histórico.
- Demonstrar por teste que uma cobrança de competência `2026-07` paga em agosto
  pertence a julho no ACCRUAL e a agosto no CASH.

**Saída esperada:** pacote de evidência pré-E011 revisável, sem alegar E011/E012.

## 5. Gates de aceitação da reconciliação

- [x] Nenhuma coluna, schema, payload, filtro ou relatório canônico usa
  `competence_date` ou dia artificial.
- [x] Cobranças e despesas exigem par ano/mês válido e completo.
- [x] CASH usa exclusivamente `paid_at`; ACCRUAL usa exclusivamente ano/mês.
- [x] Fronteiras de virada de mês e ano estão cobertas por testes.
- [x] UI apresenta `YYYY-MM` e não fabrica dia no estado local ou payload.
- [x] A decisão de migração registra R1–R6 como `2026`/`7` e o migrador isolado
  exige ano/mês explícitos; eventual materialização operacional continua não
  autorizada e mantém R2 fora do candidato válido.
- [x] `paid → paid_at obrigatório` permanece intacta em schema, serviço e testes.
- [x] Generation 8/canonical, pointer e runtime manifest permanecem byte a byte
  inalterados durante preparações e testes não operacionais.
- [x] Evidência anterior dependente de `competence_date` foi substituída por nova
  evidência de reconciliação, sem ser apagada.
- [ ] Novo gate HUMAN explícito foi obtido antes de iniciar E011.

## 6. Condições de parada

Parar e manter `BLOCK` se houver necessidade de inferir dia ou `paid_at`, mistura
de regimes, incompatibilidade de dados, R2 incluído como cobrança canônica válida,
evidência insuficiente, mutação operacional ou ausência de autorização para a
etapa seguinte.

## 7. Estado dos gates

- Reconciliação de implementação: `EXECUTED / EXECUTOR VALIDATED`.
- Revisão independente D005-08: `PENDING`.
- E011: `NOT AUTHORIZED / NOT EXECUTED`.
- E012: `NOT AUTHORIZED / NOT EXECUTED`.
- Migração operacional: `NOT AUTHORIZED / NOT EXECUTED`.
- Candidate promotion e cutover: `NOT AUTHORIZED / NOT EXECUTED`.
- Generation 8/canonical: `PRESERVE / NO MUTATION`.
