# SPEC-004 — Quality Gate Remediation Report

## FASE E ESTADO

- Fase: `SPEC004_QUALITY_GATE_REMEDIATION_ORCHESTRATION`.
- Estado: `READY_FOR_SPEC004_REMEDIATION_OPERATIONAL_GATE`.
- Commit técnico: `0832eccd03e9bcb64f02b2944e9ecedd721596af`.
- Nenhum push, merge, release, cutover, promotion ou write operacional foi executado.

## BASELINE E EVIDENCE PRESERVADA

A Generation 7 permaneceu `canonical`. A revalidação final confirmou, sem alteração:

- pointer `9d3300076994702b6e60d48c9c16cb0bcd5e6a38ed290e55aa663bbf2a104ba2`;
- banco `7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07`;
- runtime manifest `b2ff5b733b344b2916733acd62bfb3c05b108ca6b86c6564d96fdcc06b57b20d`;
- `user_version=4`, integridade OK e zero violações de FK.

Backups, recovery, cadeia Generation 5 → 6 → 7 e PASS independentes não atingidos
continuam válidos. A migration histórica v3→v4 não foi modificada.

## R1–R9 STATUS

| Finding | Fix | Test/Evidence | Status |
|---|---|---|---|
| R1 / D4 | endpoint backend de correção excepcional, admin-only, motivo, If-Match e evento com estado anterior/novo | service adversarial e matriz API com login real | GREEN |
| R2 / D6 | removido bypass retroativo genérico; create/edit/reschedule usam bloqueio comum | admin, reception e psychologist não movem reserva ao passado | GREEN |
| R3 / D7 | `ClinicSettings.timezone_name` é autoridade; normalização UTC somente de novos writes; gap/fold rejeitados | America/New_York normal, gap, ambiguidade e payload divergente | GREEN |
| R4 / D3 | índice único parcial original→sucessor e guard relacional de evento | SQL adversarial, migration e rollback preexistente | GREEN |
| R5 | triggers físicos contra UPDATE e DELETE de eventos | SQL direto e ORM falham; conteúdo preservado | GREEN |
| R6 / AC-012 | matriz via `/auth/login` e Bearer real, sem override de identidade | 14 cenários autenticados de papel/vínculo/agenda/ação | GREEN |
| R7 / AC-003/005–007 | regressões de referências, conflito, self-exclusion, cancelamento/liberação e ocupação | suíte SPEC-004 e regressão completa | GREEN |
| R8 / AC-015 | migration corretiva v4→v5 e harness v3→v4→v5 | IDs/timestamps/rescheduled/legacy/FKs/índices/guards/idempotência | GREEN |
| R9 / AC-016 | discovery default por `LOCALAPPDATA`, sem os dois overrides proibidos; freeze em clone limpo | teste default e 27 testes direcionados no commit limpo | GREEN candidato/runtime-equivalent |

## HARNESS RED/GREEN

Os REDs reproduziram: endpoint excepcional ausente, `allow_past=True`, timezone do payload,
aceitação de gap/fold, sucessores múltiplos no v4, UPDATE/DELETE de eventos e smoke com
overrides/identidade técnica. Os GREENs preservaram os mesmos requisitos e asserts.

## MIGRATION v4→v5 E CANDIDATO

A migration `backend/migration/spec004_remediation.py` é forward-only, exige exatamente
v4, aborta diante de sucessores múltiplos e é idempotente após v5. Foi executada somente
em cópia isolada da Generation 7:

- candidato SHA-256 `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`;
- tamanho 110592 bytes;
- `user_version=5`;
- `integrity_check=ok`;
- zero violações de FK;
- índice `ux_appointments_original_successor` presente;
- guards de domínio, relacionamento e append-only presentes.

## CONCURRENCY / ATOMICITY

As garantias anteriormente válidas continuaram verdes: `BEGIN IMMEDIATE`, uma única
reserva conflitante persistida e rollback integral sob fault injection. A remarcação
continua criando sucessor e evento na mesma transação antes do commit.

## DEFAULT RUNTIME HARNESS

O harness novo remove `CLINICA_OPERATIONAL_POINTER`, `CLINICA_RUNTIME_CODE_ROOT`,
`CLINICA_RUNTIME_ROOT`, overrides de manifest e overrides de banco. Um `LOCALAPPDATA`
isolado contém o layout convencional `ClinicaGabriela/runtime`; o processo filho descobre
pointer, manifest e database pelo caminho default. Auth/authz é provado separadamente
pela API real com `/auth/login`. Health/launcher materialmente dependente de promoção
permanece reservado ao Operational Gate, pois esta fase não pode selecionar v5 no runtime
operacional.

## FULL REGRESSION

- Python: `235 passed` na regressão completa; os dois harnesses finais adicionais passaram
  direcionadamente, totalizando `237 tests collected` e sem lastfailed material;
- clone limpo do commit: `27 passed` na regressão R1–R9 direcionada;
- frontend: `5 passed`;
- Vite: PASS, 1582 módulos transformados;
- falhas iniciais de pytest foram classificadas como ambiente (permissão/limite de path
  no OneDrive) e desapareceram com `C:\Temp` curto;
- `git diff --cached --check`: PASS antes do commit.

## FREEZE

Um clone local limpo foi fixado no commit
`0832eccd03e9bcb64f02b2944e9ecedd721596af`. A partir dele:

- o candidato foi reconstruído com o mesmo SHA-256 `1edb9c…f404c8`;
- o freeze contém 128 arquivos de runtime versionados;
- freeze SHA-256 `41236c2f285bf8ba7260e34abc6b139a51ab5e1687282e74ff4a2d35e96ed852`;
- `git status` do clone permaneceu limpo;
- nenhuma alteração do working tree ativo foi necessária para compor o candidato.

## RISCOS / LIMITES

- v5 ainda não foi aplicada operacionalmente;
- Generation 7 continua em v4 até gate HUMAN de promotion;
- health/launcher com v5 operacional deve ser comprovado no próximo gate;
- dados legados permanecem `legacy_unverified`, sem conversão ou inferência;
- os artefatos de Evidence deste fechamento foram gerados após o commit técnico e não
  fazem parte da composição de runtime congelada.

## STOP_CONDITION E PRÓXIMO_READY

`STOP_CONDITION = READY_FOR_SPEC004_REMEDIATION_OPERATIONAL_GATE`

`PRÓXIMO_READY = READY_FOR_SPEC004_REMEDIATION_OPERATIONAL_GATE`
