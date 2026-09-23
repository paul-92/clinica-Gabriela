# SPEC-005 — Evidence de implementação E002–E010

Data: 22/09/2026
Classificação: `VERIFIED_BY_IMPLEMENTATION_EXECUTOR`; não é revisão independente E012
Escopo: E002 a E010 somente

> **Emenda HUMAN posterior:** a decisão D005-08 tornou canônica a competência
> mensal explícita por `competence_year` + `competence_month` e proibiu dia
> representativo artificial. Este relatório permanece como evidência histórica da
> execução realizada, mas seus resultados dependentes de `competence_date: DATE`
> estão seletivamente invalidados para fins de E011. Schema, API, frontend,
> migração, filtros, relatórios, testes e documentação devem ser reconciliados e
> revalidados. E011/E012, candidato operacional, promoção e cutover continuam não
> autorizados.
>
> A reconciliação foi posteriormente executada e validada pelo executor. A
> invalidação seletiva e a nova Evidence estão registradas no
> [relatório D005-08](spec005-20260922-d00508-reconciliation-report.md). Este
> relatório permanece histórico e não é reclassificado retroativamente.

## Contexto e fronteira operacional

- branch: `feature/spec-008-architecture-foundation`;
- baseline HEAD: `a2ca3f9df0728bb6e4b08b43a0f3c8bad295a767`;
- upstream inicial: sincronizado `0/0`;
- contrato: `CONTRACT FROZEN`, D005-01..D005-07 preservadas;
- Generation operacional: `8/canonical`;
- migração operacional, pointer, manifest e promoção: não executados;
- commit, push, merge, tag e release: não executados.

Sentinela read-only final da Generation 8:

- pointer SHA-256: `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`;
- runtime manifest SHA-256: `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`;
- database SHA-256: `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`;
- `integrity_check=ok`, zero violações de FK e nenhum sidecar;
- inventário financeiro agregado: 3 cobranças e 3 despesas, valores monetários
  representáveis exatamente, porém os 6 registros não possuem competência explícita.

Consequência operacional: o migrador permanece fail-closed e classifica a ausência
de competência como `REVIEW/BLOCK`. Isso não invalida a implementação técnica E004;
impede qualquer candidato operacional até revisão HUMAN específica, sem inferência.

## Execução por unidade

### E002 — Red Harness / Fixtures

`PASS`. Fixtures exclusivamente sintéticas. Após correção de uma importação incompleta
do próprio harness, a execução RED significativa produziu `4 failed, 1 passed` pelos
gaps esperados: float canônico, ausência de competência/versão/metadados, ausência de
catálogo/trilha e ausência de constraints. Os testes não foram enfraquecidos.

### E003 — Monetary Model / Schema

`PASS`. Schema candidato com `INTEGER amount_cents`, constraints positivas e de ciclo,
competência explícita, versões, metadados, índices, categorias controladas, eventos
append-only e triggers no-delete. Gate direcionado: `5 passed`.

### E004 — Forward-only Migration

`PASS` técnico / operacional não executado. Migrador separado exige snapshot/cópia,
destino novo e não operacional, converte apenas valores exatos, preserva IDs/FKs/NULL,
reconcilia contagens/hashes/totais, roda `integrity_check`, `foreign_key_check` e teste
de recovery. Valores ambíguos, competência ausente e lifecycle incoerente resultam em
`REVIEW/BLOCK`. Gate sintético: `5 passed`.

### E005 — Domain / Services

`PASS`. Caixa e competência separados, períodos `[start,end)`, overdue derivado,
máquina de estados explícita, liquidação integral única, cancelamento/estorno com
histórico, despesas/categorias controladas e erros sanitizados.

### E006 — Repository / Concurrency

`PASS`. Compare-and-update por versão, `ETag`/`If-Match`, stale write `412`, commits
atômicos, rollback e concorrência exercitada com duas conexões SQLite reais. E005/E006,
migração e schema integrados: `17 passed` no checkpoint; suíte SPEC-005 final `27 passed`.

### E007 — API / Authorization / Errors

`PASS`. Matriz admin/reception/psychologist no backend; 401, 403, 404, 409, 412, 422
e 428 controlados; filtros e períodos explícitos; ações de ciclo e categorias.
Gate API: `6 passed`.

### E008 — Electron / React

`PASS`. Centavos determinísticos com parsing textual/BigInt, regime/período rotulados,
caixa inicial, estados loading/vazio/erro, sem fallback financeiro enganoso, ações por
papel e ausência de UI financeira para psicólogo. `10 passed`; build Vite aprovado com
1.582 módulos transformados.

### E009 — Legacy Authority Isolation

`PASS`. Tkinter consulta o resumo canônico pela API. O bootstrap e seed legados não
ativam models/services/repositories financeiros e não produzem writes financeiros.
Service e repository legados falham explicitamente mesmo quando importados
manualmente. Smoke/guards: `4 passed`. Não existe dual-write.

### E010 — Regression / Privacy / Traceability (checkpoint inicial)

`PASS` no checkpoint de implementação. A auditoria pré-commit posterior encontrou
dois achados materiais e invalidou seletivamente E004 e a rastreabilidade de E010;
o histórico abaixo permanece preservado e a remediação/revalidação está registrada
na seção final deste documento.

- SPEC-005 direcionado: `27 passed`;
- regressão herdada selecionada: `74 passed`;
- suíte Python completa final: `264 passed`;
- frontend: `10 passed`;
- build frontend: `PASS`;
- `compileall`: `PASS`;
- `git diff --check`: `PASS` (somente avisos informativos de EOL);
- scan de segredo/PII nos artefatos SPEC-005: `PASS`;
- scan de float/delete no contrato financeiro backend: `PASS`.

## Rastreabilidade AC

| AC | Implementação principal | Evidência automatizada | Estado |
|---|---|---|---|
| AC-001 | centavos inteiros + constraints/Pydantic estrito | red harness, API e schema | PASS |
| AC-002 | `exact_cents`, BigInt UI, fail-closed | migração e frontend | PASS |
| AC-003 | `paid_at`/`competence_date`, `[start,end)` | domínio e API de fronteira | PASS |
| AC-004 | máquina pending/paid/canceled/reversed; overdue derivado | domínio/API | PASS |
| AC-005 | metadados, eventos e triggers no-delete | domínio/schema | PASS |
| AC-006 | schemas `extra=forbid` e liquidação única | domínio/API | PASS |
| AC-007 | FK nullable, vínculo explícito e Agenda sem efeito financeiro | schema + integração real | PASS |
| AC-008 | backend role matrix e 401/403 | matriz API + UI | PASS |
| AC-009 | catálogo controlado e despesa cancelável/auditável | domínio/API | PASS |
| AC-010 | CAS por versão, rollback e SQLite real | concorrência/API | PASS |
| AC-011 | candidato isolado, reconciliação, checks e recovery | migração | PASS técnico |
| AC-012 | UI rotulada, estados controlados e Evidence agregada | frontend + privacy scan | PASS |

## Repair loops

1. Pytest não conseguiu gerenciar temporários dentro do sandbox; execução válida foi
   repetida em raiz curta isolada fora do sandbox.
2. Esbuild retornou `spawn EPERM` no sandbox; build foi repetido fora do sandbox e passou.
3. A primeira suíte completa encontrou incompatibilidade de assinatura no Login Tkinter
   (`262 passed, 1 failed`). O cliente API foi vinculado à sessão sem reintroduzir
   autoridade local; revalidação seletiva `14 passed` e suíte completa `263 passed`.
4. O review final endureceu E009 para que service/repository legados falhem
   explicitamente mesmo em importação manual; E009 passou `4 tests`, SPEC-005 passou
   `27 tests` e a suíte completa final passou `264 tests`.

## Limites preservados

E011 e E012 não foram executados. Não houve autocertificação independente, candidato
operacional, cutover, promoção, alteração de pointer/manifest/Generation, staging ou
operação Git de publicação.

## Remediação dos achados da auditoria pré-commit

A auditoria pré-commit inicial terminou em `FAIL` com dois achados materiais. Eles
foram corrigidos sem alterar decisões do produto e sem executar E011/E012.

### F001 — segurança de caminhos operacionais

`REMEDIATED / PASS`. A causa raiz era a proteção limitada aos dois caminhos legados
conhecidos no repositório. O migrador agora resolve canonicamente e rejeita, antes de
criar diretório, candidato ou recovery:

- a raiz operacional padrão `%LOCALAPPDATA%\ClinicaGabriela\runtime` e a raiz
  configurada por ambiente;
- qualquer descendente dessas raízes;
- os pointers operacionais e o banco apontado por eles, mesmo se estiver fora da raiz;
- caminhos normalizados/relativos/aliases que resolvam para localização protegida.

O gate negativo passou com `5 passed`; a suíte completa de migração passou com
`10 passed`. A sentinela real Generation 8/canonical foi exercitada somente para
leitura e permaneceu inalterada.

### F002 — rastreabilidade do seed canônico

`REMEDIATED / PASS`. A causa raiz era a criação ORM direta de categoria, cobrança e
despesa no seed, sem `created_by_user_id` e sem `financial_events`. O seed agora usa o
`FinanceService` canônico com um ator de fixture explicitamente sintético, inativo e
determinístico. Os três fatos possuem autoria e os três eventos `created`
correspondentes. O gate específico passou com `1 passed`; domínio/repositório/seed
passaram com `8 passed`.

### Revalidação seletiva pós-remediação

- suíte SPEC-005 direcionada: `33 passed`;
- regressão afetada de bootstrap, seed e infraestrutura de migração: `92 passed`;
- suíte completa anterior de `264 passed`: não repetida, pois as alterações ficaram
  confinadas ao migrador SPEC-005 isolado e ao uso do serviço financeiro já validado
  pelo seed; os gates direcionados e a regressão afetada não expuseram risco amplo;
- E004: `REVALIDATED`;
- E010/rastreabilidade: `REVALIDATED`;
- documentação arquitetural: conteúdo SPEC-005 intencional, consistente e
  reconciliado com a remediação;
- classificação desta Evidence permanece `VERIFIED_BY_IMPLEMENTATION_EXECUTOR`, não
  `INDEPENDENTLY_VERIFIED`.

Os seis fatos legados sem competência explícita permanecem `REVIEW/BLOCK`; nenhuma
competência foi inferida ou gravada e nenhum dado operacional foi alterado. E011 e
E012 continuam não executados.

### Re-audit pré-commit final

`PASS / COMMIT PACKAGE READY`, sem staging. O manifesto futuro foi reconstruído do
estado Git real e contém 38 candidatos SPEC-005: 29 arquivos rastreados modificados e
9 arquivos novos. Conteúdo preexistente de `.baseline-staging/`, `.forensics/`,
`.homologation/` e `.sanitize-rewrite-worktree/` permanece excluído; artefatos
operacionais e gerados também permanecem excluídos.

Os guards finais passaram: privacidade, sanitização, artefatos operacionais,
compilação dos arquivos afetados e `git diff --check`. Não há arquivos staged.
