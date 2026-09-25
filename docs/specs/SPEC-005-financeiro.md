# SPEC-005 — Financeiro

**Estado atual (2026-09-24):** `CLOSED_PASS_PROMOTED_INDEPENDENTLY_VERIFIED`; Generation 9/canonical é autoritativa; `QUALITY_GATE_PASS`. [Verificação independente pós-promoção](../audit/spec005-20260924-post-promotion-independent-verification.md). As declarações de status e gates nas seções históricas abaixo registram seus checkpoints de origem.
**Status histórico do checkpoint D005-09:** D005-08 independent review PASS; D005-09 HUMAN APPROVED / CONTRACT FORMALIZED; E011–E012 não executados
**Prioridade:** P1  
**Dependências preservadas:** SPEC-002, SPEC-003, SPEC-004 e SPEC-008
**Autoridade:** decisões HUMAN D005-01 a D005-09
**Implementação:** E002–E010 reconciliados com D005-08 e revalidados pelo executor
**Migração operacional:** não autorizada / não executada

## 1. Objetivo e autoridade

Esta SPEC congela o contrato funcional e técnico do módulo financeiro. A decisão
HUMAN D005-08, registrada em 22/09/2026, emenda o contrato para representar a
competência canônica exclusivamente como ano e mês. Uma autorização HUMAN posterior
permitiu reconciliar código, schema declarativo, API, serviços/repositories,
frontend, relatórios/filtros, migrador isolado, testes, documentação e Evidence.
Ela não autoriza alteração de banco operacional, ponteiro, manifesto ou Generation,
nem E011, E012, migração operacional, criação/promoção de candidato ou cutover.
D005-01 a D005-08 são normativas e não podem ser reinterpretadas ou ampliadas.

Continuam herdados, sem reabertura: autenticação/autorização da SPEC-002;
integridade, auditoria e privacidade da SPEC-003; agenda da SPEC-004; fonte de
verdade e limites arquiteturais da SPEC-008.

## 2. Escopo

Abrange cobranças/receitas, pagamentos integrais, despesas, categorias
controladas, datas financeiras, vínculos explícitos, filtros, indicadores
separados por regime e histórico auditável.

Ficam fora do escopo: pagamentos parciais, múltiplas liquidações, parcelamento,
contabilidade fiscal, tributação, folha, nota fiscal, boleto, gateway, Pix
automático, integração/conciliação bancária e cobrança automática. Combinações
fora do escopo são rejeitadas, nunca representadas ambiguamente.

## 3. Dinheiro — D005-02

A representação canônica é **INTEGER CENTS** (R$ 150,37 = 15037).

- float não é representação canônica.
- Valores normais são inteiros maiores que zero.
- Zero e negativos são rejeitados; negativos não representam cancelamento,
  estorno ou ajuste.
- Conversões na API/UI são explícitas, determinísticas e testáveis.
- Cálculos e agregações operam em centavos inteiros.

Conversão legada de FLOAT só converte equivalência exata e demonstrável em
centavos. É proibido arredondar ou truncar silenciosamente. Valor incompatível
ou ambíguo é REVIEW/BLOCK e faz a migração falhar fechada.

## 4. Regimes e períodos — D005-01

O sistema suporta visões semanticamente separadas:

1. **Caixa:** determinado pela data real de pagamento (paid_at).
2. **Competência:** determinada pelo par explícito `competence_year` +
   `competence_month`.

A visão operacional inicial é caixa. Indicadores não misturam
previsto/competência com caixa recebido sem rótulo explícito. Uma transação de
setembro paga em outubro pertence a setembro na competência e a outubro no
caixa.

### 4.1 Representação canônica mensal — D005-08

- A competência é um período mensal, nunca um dia factual.
- Persistência, domínio e API usam `competence_year` inteiro e
  `competence_month` inteiro; o mês válido está no intervalo `1..12` e a
  combinação é obrigatória.
- A forma textual de apresentação e intercâmbio humano é `YYYY-MM`, com mês em
  dois dígitos. Assim, `2026-07` significa julho de 2026 como período financeiro.
- `competence_date`, `DATE`, timestamp, primeiro/último dia do mês e qualquer dia
  sentinela ou representativo são proibidos como representação canônica.
- Filtros de competência recebem limites mensais explícitos e usam intervalo
  semiaberto `[start_month, end_month)`. A ordenação/comparação é cronológica pelo
  par `(year, month)`, sem conversão persistida para dia.
- Filtros de caixa continuam usando `paid_at` e limites temporais `[start, end)`.
  Nenhum filtro, total ou relatório pode usar competência para preencher caixa ou
  `paid_at` para preencher competência.

Criação, competência mensal, vencimento, pagamento, cancelamento e estorno são
conceitos distintos e não são inferidos uns dos outros.

## 5. Ciclo de vida — D005-03 e D005-04

Estados persistidos canônicos: **pending, paid, canceled, reversed**.

Overdue é derivado, nunca persistido:

status == pending AND due_date < reference_date → overdue

A data de referência é explícita ou controlada pelo serviço. Transições:

| Origem | Destino | Condição mínima |
|---|---|---|
| pending | paid | liquidação integral e paid_at informado |
| pending | canceled | cancelamento autorizado e histórico preservado |
| paid | reversed | estorno autorizado e original preservado |

Qualquer outra transição e status arbitrário são rejeitados. Não há reabertura
implícita. Cancelamento e estorno são distintos, explícitos e auditáveis; não
apagam ou substituem o original.

Uma cobrança tem no máximo uma liquidação integral. Pagamento parcial,
múltiplas liquidações e parcelamento são rejeitados explicitamente e exigem
novo contrato HUMAN para suporte futuro.

## 6. Despesas e categorias — D005-07

Despesas usam centavos inteiros, competência mensal explícita pelo mesmo par
`competence_year` + `competence_month` e categoria de
catálogo simples controlado. Texto livre irrestrito não é categoria canônica,
nem o catálogo é enum de negócio inflexível codificado.

Somente papel autorizado administra o catálogo. Despesas preservam histórico;
cancelamento é explícito e auditável. Exclusão física não integra o ciclo
operacional normal.

## 7. Agenda — D005-05

A criação de cobrança permanece manual. Transições de atendimento não criam,
cancelam ou alteram finanças; appointment = done não cria cobrança.

appointment_id só é associado quando fornecido explicitamente em operação
autorizada e íntegra. Um appointment_id = NULL permanece NULL sem esse
fornecimento. É proibida inferência por paciente, data, valor, profissional ou
estado. A SPEC-004 permanece ACCEPTED/DONE.

## 8. Autorização e erros — D005-06

O backend é a autoridade; visibilidade no frontend é apenas UX. Aplica-se
privilégio mínimo.

| Capacidade | ADMIN | RECEPTION | PSYCHOLOGIST |
|---|---:|---:|---:|
| Visibilidade financeira | total | operacional | não |
| Criar cobranças | sim | sim | não |
| Atualizar campos | autorizados | operacionais permitidos | não |
| Registrar pagamento | sim | sim | não |
| Cancelar conforme ciclo | sim | sim, quando permitido | não |
| Estornar | sim | não | não |
| Gerir despesas sensíveis | sim | não | não |
| Gerir categorias/configuração permitida | sim | não | não |

Autenticação ausente/inválida retorna 401; autenticação válida sem permissão,
403. Validação, transição e concorrência geram erros controlados, sem expor
exceções internas, com semântica HTTP documentada pela futura API.

## 9. Concorrência, atomicidade, auditoria e no-delete

- Operações mutáveis são transacionais e atômicas; falha causa rollback.
- Concorrência não gera pagamento duplicado, transição perdida ou
  sobrescrita silenciosa.
- O repositório detecta conflito de modo compatível com SQLite; o conflito
  falha controladamente e exige nova leitura, sem last-write-wins silencioso.
- Criação, pagamento, cancelamento, estorno e administração de
  despesas/categorias registram ator, instante e mudança relevante.
- Registros financeiros/auditoria não são fisicamente excluídos no fluxo normal.

## 10. API e interface

Endpoints existentes são preservados quando compatíveis; esta SPEC não inventa
novo desenho de API. A API usa centavos, valida papel, status, transição,
vínculo e período no backend e distingue 401 de 403.

A UI usa dados autoritativos, inicia na visão de caixa, rotula regime/período,
não apresenta acumulado como mensal e explicita loading, vazio e erro. Dados
de demonstração não podem parecer dados reais.

## 11. Migração futura

### D005-11 — Identidades separadas (HUMAN APPROVED)

A origem operacional e o código migrador possuem autoridades independentes. A
identidade da origem vincula Generation, pointer, runtime manifest, SHA-256 do
banco, schema e checks de integridade/FK. O freeze da Generation 8 é verificado
contra uma baseline histórica byte a byte comprovada pelo manifest ativo; o
working tree de desenvolvimento não precisa coincidir com ela.

A identidade do migrador é o SHA-256 de um manifest canônico UTF-8, JSON com
chaves ordenadas, separadores compactos e LF final. Seu inventário ordenado é a
closure dos imports Python locais dos entrypoints SPEC-005, inclusive os
`__init__.py` executados. Cada SHA-256 é dos bytes reais, sem normalização EOL.
BUILD cria arquivo novo; VERIFY recalcula a closure e os hashes sem atualizar a
baseline. Git é provenance auxiliar. Arquivos fora do inventário não invalidam
essa identidade.

O vínculo de transformação inclui identidade da origem, SHA do manifest migrador,
SPEC-005 e D005-09/D005-10/D005-11. A futura E011 exige as duas identidades e o
vínculo verificados, revisões independentes D005-09/D005-10 e D005-11 válidas e
autorização HUMAN E011. Um checkpoint proposto não constitui autorização. A
reconstrução byte a byte da baseline operacional real segue bloqueada em arquivo
histórico com finais de linha mistos; E011 permanece suspensa.

### D005-12 — Evidência operacional persistida como autoridade da fonte (HUMAN APPROVED)

Após o bloqueio do freeze, a validação sintética D005-11 e a busca histórica
exaustiva, foram recuperados bytes exatos para 111 das 128 entradas do manifest
ativo. As outras 17 continuam sem fonte verificável; a última pasta examinada,
`.review-spec005-rereview`, estava vazia. A recuperação histórica permanece
`PARTIAL_111_OF_128`, sem alegação de verificação integral do código antigo.

Para a Generation 8, D005-12 permite estabelecer a identidade da fonte por
artefatos operacionais persistidos: hash externo esperado e bytes reais do pointer,
estado e número da Generation, hash e inventário do runtime manifest, hash do banco
apontado e do snapshot isolado, schema, `user_version`, integridade, FKs, ausência
de sidecars e maintenance lock. Qualquer divergência bloqueia. O runtime manifest
continua Evidence histórica, sem regeneração ou reconstrução presumida de seus
arquivos. O snapshot futuro deve coincidir byte a byte com o SHA verificado do
banco apontado.

O código migrador mantém verificação independente da closure de imports e de cada
SHA. Seu manifest v4 fica preservado como baseline D005-11 anterior; mudanças
D005-12 exigem manifest sucessor. A transformação vincula a identidade operacional
persistida, o SHA do manifest migrador, SPEC-005 e D005-09/D005-10/D005-11/D005-12.
O checkpoint não autoriza E011. D005-12 e o binding real requerem revisão
independente antes de reabrir E011; E012 continua sem autorização.

**FORWARD_ONLY / ISOLATED_CANDIDATE / FAIL_CLOSED**

A migração operacional não foi executada. O migrador reconciliado foi validado
somente com snapshots e candidatos sintéticos isolados. Execução futura exige:

1. inventário privacy-safe;
2. backup verificado e recuperação testada;
3. dry-run isolado;
4. conversão exata, sem arredondamento/truncamento;
5. preservação de IDs e FKs;
6. preservação de appointment_id = NULL;
7. nenhuma inferência de competência, dia representativo, pagamento ou atendimento;
8. ambiguidades REVIEW/BLOCK;
9. integrity_check e foreign_key_check;
10. reconciliação de contagens, IDs, vínculos e totais em centavos;
11. teste de recovery;
12. manifesto/Evidence sem PII, dados clínicos, credenciais ou valores
    identificáveis;
13. gate HUMAN separado para promoção.

Generation 8/canonical não pode ser mutada. Falha interrompe o candidato sem
promoção. Recovery preserva fonte/backup e descarta ou substitui somente o
candidato isolado mediante autorização.

### 11.1 Legado financeiro não resolvido — D005-09

D005-09 aprova **quarentena persistida**, separada de `payments` e `expenses`
canônicos, exclusivamente para preservar e reconciliar legado incompatível. Não é
um segundo sistema financeiro. A estrutura mínima terá identidade interna estável,
identidade/hash da fonte, geração, tipo e ID interno da linha, fingerprint versionado,
status e valor legados, competência mensal, código do bloqueio, instante de entrada,
proveniência, estado de resolução e eventos append-only. Dados necessários à futura
resolução ficam restritos; Evidence, logs e manifests não levam PII.

R2 tem disposition `QUARANTINED_UNRESOLVED`, reason
`PAID_WITH_UNKNOWN_PAID_AT`, status legado `paid`, competência `2026/7` e valor
legado preservados. R2 não vira payment canônico enquanto `paid_at` for desconhecido.
É proibido inferir, sintetizar ou estimar `paid_at` de competência, vencimento,
criação ou qualquer timestamp não comprovado. `paid -> paid_at` permanece sem
exceção. Quarentena não participa de CASH, ACCRUAL, receitas, indicadores, totais,
relatórios, repositório, API ou UI financeiros normais.

Para payments e expenses separadamente e no conjunto, o conjunto de registros da
fonte deve ser particionado sem perda ou duplicação:

`SOURCE_FINANCIAL_RECORDS = CANONICAL_MIGRATED_RECORDS + QUARANTINED_LEGACY_RECORDS`.

Reconciliar contagens, tipo/ID/fingerprint, valor, status observado e disposition.
D005-10 substitui a antiga precondition de vínculo R1–R6: esses labels são
referências históricas, não identidades técnicas. A recuperação do vínculo foi
`FAILED` e não será reconstruída por inferência. A identidade operacional é
`source_database_sha + entity_type + source_internal_id + source_row_fingerprint`.
O [manifesto D005-10](../audit/spec005-20260923-d00510-legacy-source-identity-manifest.json)
vincula os seis registros autorizados à competência `2026/7` e à disposition
pretendida; payment/4 vai para `QUARANTINED_UNRESOLVED` somente após verificação
de hash e atributos. Ausência, duplicidade ou divergência bloqueiam.

Resolução futura de R2 exige evidência confiável do `paid_at` real ou nova decisão
HUMAN explícita. A ação terá autorização, transação única, idempotência, before
state, ator, evidência, resultado, timestamp e evento append-only; o original não
será apagado. Consulta administrativa da quarentena requer contrato próprio.
Detalhes de implementação e testes estão no
[plano D005-09](../audit/spec005-20260923-d00509-contract-and-implementation-plan.md).
A implementação D005-09/D005-10 é autorizada apenas em código, fixtures e
ambientes isolados; E011 continua sem autorização.

## 12. Critérios de aceitação congelados

- **AC-001 — Valor:** apenas positivos em INTEGER CENTS persistem; zero,
  negativos e float canônico são rejeitados.
- **AC-002 — Precisão/legado:** cálculo exato; conversão sem
  arredondamento/truncamento; ambiguidades REVIEW/BLOCK fail-closed.
- **AC-003 — Regimes/período:** caixa usa `paid_at`; competência usa somente
  `competence_year` + `competence_month`, apresentada como `YYYY-MM`; visões são
  separadas e consultas usam limites semiabertos no respectivo domínio temporal.
- **AC-004 — Ciclo:** apenas estados/transições autorizados; overdue derivado.
- **AC-005 — Histórico:** cancelamento, estorno e cancelamento de despesa
  preservam original/trilha, sem negativos ou delete normal.
- **AC-006 — Liquidação:** parcial, múltipla liquidação e parcela rejeitados.
- **AC-007 — Agenda:** transições não alteram finanças; vínculo explícito e
  appointment_id = NULL preservado.
- **AC-008 — Autorização/erros:** matriz aplicada no backend, com 401/403.
- **AC-009 — Despesas/categorias:** catálogo controlado, administração
  restrita e histórico preservado.
- **AC-010 — Atomicidade/concorrência:** sem estado parcial, duplicado ou
  sobrescrito.
- **AC-011 — Migração/recovery:** candidato preserva IDs/FKs/nulls, passa
  checks/reconciliação/recovery e exige promoção HUMAN.
- **AC-012 — Interface/privacidade:** UI rotula regime/período e toda Evidence
  é privacy-safe.

Os ACs dependentes da representação de competência foram revalidados pelo executor
após D005-08. Essa evidência não é revisão independente e não autoriza E011.

## 13. Rastreabilidade

| Decisão | Requisito | AC | Área planejada | Validação/Evidence planejada |
|---|---|---|---|---|
| D005-01 | regimes separados; caixa inicial; [start,end) | 003, 012 | service/repository/API/UI | fronteiras e setembro/outubro; captura sem PII |
| D005-02 | INTEGER CENTS; conversão exata/fail-closed | 001, 002, 011 | model/schema/migration/API/UI | precisão e dry-run privacy-safe |
| D005-03 | estados/transições; overdue; histórico | 004, 005, 010 | domain/service/repository/audit | matriz, relógio, rollback/trilha |
| D005-04 | sem parcial/múltipla liquidação/parcela | 006 | schema/service/API | testes negativos |
| D005-05 | faturamento manual; vínculo explícito | 007, 011 | service/API/FK | não efeito da agenda e NULL |
| D005-06 | menor privilégio; backend; 401/403 | 008 | API/auth/UI | matriz por endpoint/papel |
| D005-07 | catálogo controlado; despesa sem delete | 005, 009 | model/repository/service/API/UI | catálogo autorizado e histórico |
| D005-08 | competência mensal explícita; nenhum dia artificial; caixa separado | 003, 011, 012 | model/schema/migration/service/repository/API/UI/reports | constraints ano/mês, fronteiras mensais, ausência de `competence_date`, R1–R6 e bloqueio R2 |

## 14. DAG de execução congelado

Cada unidade depende de autorização futura.

### E001 — Contract Freeze
- **INPUTS:** D005-01..07, SPECs herdadas, documentos vigentes.
- **OUTPUTS:** contrato, ACs, rastreabilidade e DAG.
- **DEPENDENCIES:** decisões HUMAN.
- **AUTHORITY:** documentação somente.
- **VALIDATION:** contradições, escopo e cobertura.
- **EVIDENCE:** diff/checklist privacy-safe.
- **ROLLBACK/RECOVERY BOUNDARY:** documentação não promovida.
- **STOP CONDITIONS:** decisão ausente, contradição ou mutação de produto.

### E002 — Red Harness / Fixtures
- **INPUTS:** AC-001..012 e inventário.
- **OUTPUTS:** testes red e fixtures sintéticas.
- **DEPENDENCIES:** E001 e autorização.
- **AUTHORITY:** testes sem mudar contrato.
- **VALIDATION:** cada AC falha pela causa esperada.
- **EVIDENCE:** resultados red sanitizados.
- **ROLLBACK/RECOVERY BOUNDARY:** harness novo.
- **STOP CONDITIONS:** dado real, não determinismo ou lacuna.

### E003 — Monetary Model + Schema
- **INPUTS:** AC-001/002 e schema.
- **OUTPUTS:** modelo candidato em centavos, competência ano/mês, datas factuais/status.
- **DEPENDENCIES:** E002.
- **AUTHORITY:** candidato isolado.
- **VALIDATION:** precisão, constraints de ano/mês, ausência de dia artificial e compatibilidade.
- **EVIDENCE:** testes/diff sanitizado.
- **ROLLBACK/RECOVERY BOUNDARY:** descartar candidato.
- **STOP CONDITIONS:** perda, ambiguidade ou impacto na Generation 8.

### E004 — Forward-only Migration
- **INPUTS:** E003, inventário e backup.
- **OUTPUTS:** candidato, manifesto e reconciliação.
- **DEPENDENCIES:** E003 e autorização HUMAN específica.
- **AUTHORITY:** forward-only/isolated/fail-closed.
- **VALIDATION:** dry-run, checks, exatidão, IDs/FKs/nulls/recovery.
- **EVIDENCE:** manifesto/checks sanitizados.
- **ROLLBACK/RECOVERY BOUNDARY:** descartar candidato; preservar fonte/backup.
- **STOP CONDITIONS:** REVIEW/BLOCK, falha ou falta de gate.

### E005 — Domain / Services
- **INPUTS:** contrato e modelo candidato.
- **OUTPUTS:** regimes separados, competência mensal, ciclo, despesas, vínculos.
- **DEPENDENCIES:** E003; E004 quando necessário.
- **AUTHORITY:** D005 sem expansão.
- **VALIDATION:** AC-003..009.
- **EVIDENCE:** suíte sanitizada.
- **ROLLBACK/RECOVERY BOUNDARY:** transação/módulo candidato.
- **STOP CONDITIONS:** inferência proibida ou nova decisão.

### E006 — Repository / Concurrency
- **INPUTS:** E003/E005 e SQLite.
- **OUTPUTS:** atomicidade e conflitos detectados.
- **DEPENDENCIES:** E005.
- **AUTHORITY:** sem last-write-wins silencioso.
- **VALIDATION:** corrida, duplicidade e rollback.
- **EVIDENCE:** testes/logs sanitizados.
- **ROLLBACK/RECOVERY BOUNDARY:** transação/candidato.
- **STOP CONDITIONS:** parcial, duplicado ou conflito oculto.

### E007 — API / Authorization / Errors
- **INPUTS:** E005/E006 e SPEC-002.
- **OUTPUTS:** API, papéis, erros controlados.
- **DEPENDENCIES:** E006.
- **AUTHORITY:** backend.
- **VALIDATION:** endpoints, 401/403, conflito/validação.
- **EVIDENCE:** integração sem tokens/PII.
- **ROLLBACK/RECOVERY BOUNDARY:** rotas candidatas.
- **STOP CONDITIONS:** bypass ou erro interno exposto.

### E008 — Electron/React
- **INPUTS:** API e apresentação.
- **OUTPUTS:** caixa inicial, rótulos, estados UX.
- **DEPENDENCIES:** E007.
- **AUTHORITY:** UX sem autoridade local.
- **VALIDATION:** UI/API e totais corretos.
- **EVIDENCE:** build/testes/capturas sintéticas.
- **ROLLBACK/RECOVERY BOUNDARY:** frontend candidato.
- **STOP CONDITIONS:** fallback como real ou regra apenas na UI.

### E009 — Legacy Authority Isolation
- **INPUTS:** fluxos inventariados.
- **OUTPUTS:** legado não atua como segunda autoridade.
- **DEPENDENCIES:** E007/E008 e SPEC-008.
- **AUTHORITY:** isolamento; licenciamento preservado.
- **VALIDATION:** fonte única/regressão.
- **EVIDENCE:** mapa/testes sanitizados.
- **ROLLBACK/RECOVERY BOUNDARY:** roteamento sem tocar dados.
- **STOP CONDITIONS:** duas autoridades ou divergência.

### E010 — Regression / Privacy / Traceability
- **INPUTS:** E002..E009 e matriz.
- **OUTPUTS:** regressão e cobertura completa.
- **DEPENDENCIES:** E009.
- **AUTHORITY:** validação, sem autocertificação independente.
- **VALIDATION:** suíte, privacidade, rastreabilidade 100%.
- **EVIDENCE:** relatório sanitizado.
- **ROLLBACK/RECOVERY BOUNDARY:** invalidar Evidence defeituosa.
- **STOP CONDITIONS:** regressão, vazamento ou lacuna.

### E011 — Operational Candidate
- **INPUTS:** E004/E010, backup/recovery, decisão D005-09 implementada/validada e mapa R1–R6 verificável.
- **OUTPUTS:** candidato não promovido com dispositions `CANONICAL_MIGRATED` e `QUARANTINED_UNRESOLVED` reconciliadas.
- **DEPENDENCIES:** E010, validação independente D005-09, preconditions verdes e autorização HUMAN separada de E011.
- **AUTHORITY:** preparar, não promover.
- **VALIDATION:** smoke, integridade, partição sem perda/duplicação por tipo/ID/valor, isolamento de queries e recovery.
- **EVIDENCE:** manifesto/checkpoint sanitizado.
- **ROLLBACK/RECOVERY BOUNDARY:** descartar; preservar Generation 8.
- **STOP CONDITIONS:** mapa/R2 ambíguo, divergência, Evidence incompleta ou promoção sem gate.

### E012 — Independent Quality Review
- **INPUTS:** candidato e Evidence E001..E011.
- **OUTPUTS:** parecer independente e findings.
- **DEPENDENCIES:** E011.
- **AUTHORITY:** revisão; promoção permanece HUMAN.
- **VALIDATION:** reexecução e todos os ACs.
- **EVIDENCE:** relatório independente privacy-safe.
- **ROLLBACK/RECOVERY BOUNDARY:** reprovar/invalidate candidato.
- **STOP CONDITIONS:** finding, Evidence insuficiente ou falta de independência.

## 15. Estado e gates

O contrato possui 9 decisões normativas/rastreáveis, AC-001..012 e DAG. A
representação anterior `competence_date: DATE` e sua Evidence dependente foram
invalidadas seletivamente. As camadas afetadas foram reconciliadas e revalidadas pelo
executor conforme o
[plano de reconciliação](../audit/spec005-20260922-competence-reconciliation-plan.md)
e o
[relatório D005-08](../audit/spec005-20260922-d00508-reconciliation-report.md).

- D005-01..D005-09: HUMAN APPROVED / RECORDED; D005-09 apenas contrato formalizado.
- Contrato: AMENDED / MONTHLY COMPETENCE CANONICAL.
- Implementação E002–E010: D005-08 RECONCILED / EXECUTOR VALIDATED.
- E011/E012: NOT AUTHORIZED / NOT EXECUTED.
- MIGRATION operacional/candidate promotion/cutover: NOT AUTHORIZED / NOT EXECUTED.
- Generation 8/canonical: deve permanecer preservada e inalterada.
- R1–R6: competência HUMAN `2026-07`, a materializar futuramente como ano `2026`
  e mês `7`, nunca como data diária.
- R2: `status=paid`, `paid_at` ausente/desconhecido; disposition futura
  `QUARANTINED_UNRESOLVED`, fora de `payments` canônicos. A invariant
  `paid → paid_at obrigatório` permanece sem exceção.
- Revisão independente D005-08: PASS. Próximo gate:
  `READY_FOR_SPEC005_D00509_IMPLEMENTATION_AUTHORIZATION`; autorização HUMAN
  posterior e separada continua obrigatória para E011.
