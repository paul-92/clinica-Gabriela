# SPEC-004 — Quality Gate Remediation Plan

## FASE

`SPEC004_QUALITY_GATE_REMEDIATION_PLANNING`

## ESTADO

Entrada: `QUALITY_GATE_FAIL / READY_FOR_SPEC004_REMEDIATION_PLANNING`.

Saída deste planejamento: `READY_FOR_SPEC004_REMEDIATION_ORCHESTRATION`.

Este documento planeja somente a remediação mínima e seletiva. Não altera contrato
HUMAN, código, banco operacional, Generation, pointer, manifest, backup ou recovery.

## VALID_EVIDENCE_PRESERVED

Permanecem válidos e não devem ser refeitos:

- cadeia operacional forward-only Generation 5 → 6 → 7;
- Generation 7 em estado `canonical` e seu banco imutável;
- pointer SHA-256 `9d3300076994702b6e60d48c9c16cb0bcd5e6a38ed290e55aa663bbf2a104ba2`;
- banco SHA-256 `7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07`;
- runtime manifest SHA-256 `b2ff5b733b344b2916733acd62bfb3c05b108ca6b86c6564d96fdcc06b57b20d`;
- backup pré-promoção, backup pré-recovery, backup estabilizado e restore isolado;
- `user_version=4`, `integrity_check=ok`, zero violações de FK e zero sidecars;
- recovery que avançou para Generation 7 sem rollback silencioso;
- resultados PASS não alcançados pelos achados: duração/estados básicos, conflito
  semiaberto e adjacência, ETag/If-Match, códigos 409/412/422, serialização SQLite,
  rollback de remarcação sob fault injection, build do frontend e guards operacionais.

Esses artefatos são predecessores válidos da remediação; não são Evidence suficiente
para R1–R9.

## INVALIDATED_EVIDENCE

Somente as alegações abaixo são invalidadas:

- D4: alegação de suporte à correção excepcional de estado encerrado;
- D6: alegação de bloqueio integral de retroatividade, pois edição chama
  `_validate_new(..., allow_past=True)`;
- D7/AC-014: alegação de timezone efetivo, pois o serviço usa valor do payload/default
  fixo e não a configuração da clínica, sem detecção de fold/gap DST;
- D3: alegação de unicidade material original → sucessor no banco migrado v4;
- append-only: alegação de imutabilidade física de `appointment_events`;
- D5/AC-012: alegação de matriz completa via autenticação real;
- AC-003 e AC-005–007: alegação de cobertura independente suficiente;
- AC-015: alegação de harness completo da migration;
- AC-016: alegação de smoke default real e autenticação/autorização real.

Não se invalida o banco, o pointer, o manifest, os hashes, backups, recovery, integridade
ou demais PASS da Independent Review.

## R1–R9 REMEDIATION MAP

| Finding | Requirement | Affected code | Affected/new test | Invalidated Evidence | Remediation | Revalidation |
|---|---|---|---|---|---|---|
| R1 | D4 | `backend/api/routes/appointments.py`, `backend/schemas/appointment.py`, `backend/services/appointment_service.py` | `tests/test_spec004_exceptional_correction.py`, API matrix | D4 | Criar ação backend explícita de correção excepcional; exigir admin autenticado, `If-Match`, motivo não vazio e transição alvo válida; gravar evento com estado anterior/novo sem apagar eventos; nenhuma passagem pelo update normal | RED por ausência/403/422/409; GREEN por API real, evento persistido e histórico anterior intacto |
| R2 | D6 | `backend/services/appointment_service.py` | `tests/test_spec004_retroactivity.py` | D6 | Remover `allow_past=True`; create/edit/reschedule normais usam a mesma política não retroativa. Qualquer correção de encerrado ou passado ocorre apenas pela ação excepcional auditada | Testar admin/reception/psychologist tentando mover reserva ao passado por POST/PATCH/PUT/reschedule; todos falham sem mutation/evento espúrio |
| R3 | D7, AC-014 | `backend/models/settings.py`, `backend/schemas/settings.py`, `backend/services/settings_service.py`, `backend/schemas/appointment.py`, `backend/services/appointment_service.py` | `tests/test_spec004_timezone.py`, testes API de settings | D7/AC-014 | Carregar `ClinicSettings.timezone_name` efetivo no backend; tratar entrada nova como horário local da clínica; validar zona IANA e gap/fold; persistir zona efetiva; não reinterpretar legado | Casos normal, zona inválida, DST inexistente, DST ambíguo, mudança futura da configuração e legado byte-a-byte inalterado |
| R4 | D3, AC-008/009 | `backend/migration/spec004.py` (somente sob teste histórico), nova migration corretiva, `backend/models/appointment.py`, serviço de remarcação | `tests/test_spec004_successor_integrity.py`, harness de migration | D3 | Em v5 criar unicidade material parcial de `appointments.original_appointment_id`; preservar FK `NO ACTION`; validar que evento `rescheduled` aponta para sucessor cuja origem é o appointment; manter uma transação | Tentativa SQL e API de segundo sucessor falha; rollback não deixa original cancelado, sucessor ou evento parcial |
| R5 | append-only | nova migration v5, validação canônica/operacional | `tests/test_spec004_append_only.py` | append-only | Triggers SQLite `BEFORE UPDATE` e `BEFORE DELETE` em `appointment_events` com `RAISE(ABORT, ...)`; inserts continuam permitidos | SQLAlchemy, SQL direto e conexão separada não conseguem UPDATE/DELETE; rollback e conteúdo/hash lógico permanecem |
| R6 | D5, AC-012 | rotas, auth dependencies, serviço | `tests/test_spec004_api_authorization_matrix.py` | D5/AC-012 | Exercitar tokens/sessões obtidos por `/auth/login`; nenhuma dependency override de identidade. Preencher vínculo material apenas em fixture fictícia | Matriz completa abaixo, incluindo sem vínculo, agenda alheia e ação excepcional |
| R7 | AC-003, AC-005–007 | serviço/repository/rotas | `tests/test_spec004_independent_acceptance.py` | AC-003/005–007 | Adicionar suíte independente, sem reutilizar mocks de implementação, para referências, self-exclusion, cancelamento/liberação, estados e ocupação | Provar status HTTP, ausência/presença de writes e eventos, e contagens finais privacy-safe |
| R8 | AC-015 | `backend/migration/spec004.py`, nova `backend/migration/spec004_remediation.py`, scripts de candidato/verifier | `tests/test_spec004_migration_harness.py` | AC-015 | Não editar v3→v4; criar harness v3→v4 e v4→v5 em cópias. A evolução nova é v5 | IDs, contagens, invariantes, legado, constraints, índices, repetição e FKs antes/depois |
| R9 | AC-016 | `backend/config.py`, launchers reais, novo smoke; retirar o smoke remediado do executor histórico | `tests/test_spec004_default_runtime_smoke.py`, script dedicado | AC-016/HARNESS | Iniciar pelo launcher default com layout operacional convencional; não definir `CLINICA_OPERATIONAL_POINTER` nem `CLINICA_RUNTIME_CODE_ROOT`; fazer login real e chamar health/agenda | Provar cadeia pointer → manifest → runtime → database → launcher → health e auth/authz real; banco permanece inalterado no smoke read-only |

## SCHEMA/MIGRATION IMPACT

É necessária nova evolução forward-only `user_version 4 → 5`. A migration v3→v4 já
promovida não será editada.

A migration v5 deve, em candidato isolado e numa transação:

1. abortar se o inventário encontrar múltiplos sucessores para a mesma origem;
2. criar índice único parcial em `appointments(original_appointment_id)` para valores
   não nulos (ou reconstrução equivalente, se a inspeção SQLite exigir);
3. criar guards `BEFORE UPDATE` e `BEFORE DELETE` de `appointment_events`;
4. criar guard relacional para evento `rescheduled`: sucessor existente e
   `successor.original_appointment_id = appointment_id`;
5. manter FKs `NO ACTION`, índices existentes e conteúdo legado sem conversão;
6. elevar `PRAGMA user_version` para 5 somente após todas as garantias;
7. executar `integrity_check`, `foreign_key_check` e inventário pós-migration.

Não é necessária coluna nova para timezone: `clinic_settings.timezone_name`,
`appointments.timezone_name` e `temporal_status` já existem. A correção necessária é de
contrato/API e validação. Metadados de correção excepcional devem caber em eventos
append-only; caso o Harness RED demonstre que estado anterior/novo não pode ser provado
com as colunas atuais, a mesma v5 adicionará colunas explícitas `from_status` e
`to_status`, nulas para eventos históricos, sem inferência retroativa.

O modelo ORM deve refletir os índices/constraints v5, mas `create_all` não substitui a
migration de banco existente.

## HARNESS RED PLAN

Cada unidade preserva relatório RED antes da implementação e relatório GREEN depois:

1. R1: endpoint inexistente; fluxo normal não corrige fechado; demonstrar ausência do
   único mecanismo permitido.
2. R2: PATCH autenticado por admin move `scheduled_at` ao passado e hoje passa; capturar
   o defeito e o write resultante.
3. R3: configurar uma zona diferente de São Paulo e provar que ela é ignorada; usar
   zonas IANA com gap e fold conhecidos e provar aceitação silenciosa atual.
4. R4: em banco migrado v4 inserir dois sucessores da mesma origem por SQL e provar que
   ambos são aceitos quando o índice único material estiver ausente.
5. R5: executar UPDATE e DELETE diretos em `appointment_events` e provar sucesso atual.
6. R6: construir clientes autenticados reais para cada célula e registrar lacunas;
   proibir `dependency_overrides[get_current_user]` nesse harness.
7. R7: fixtures independentes e fictícias para 404/409, self-exclusion, liberação após
   cancelamento e ocupação por `done`/`no_show`.
8. R8: banco sintético v3 com IDs não sequenciais, `rescheduled`, timestamps naive,
   referências e conteúdo canário privacy-safe; provar verificações ausentes no harness
   atual e ausência da v5.
9. R9: processo filho pelo launcher default, ambiente limpo dos dois overrides, login
   real, `/health` e `/appointments`; registrar que o smoke atual usa overrides e
   identidade técnica.

Sequência obrigatória por requisito:

`RED → IMPLEMENT → TARGETED GREEN → DEPENDENCY REVALIDATION`.

Nenhum teste RED será reescrito para aceitar a implementação; qualquer alteração de
expectativa exige rastreabilidade ao contrato D1–D7.

## AUTHORIZATION MATRIX

Resultados esperados via API autenticada real:

| Ação | Admin | Psychologist própria | Psychologist alheia | Psychologist sem vínculo | Reception |
|---|---:|---:|---:|---:|---:|
| listar/ler agenda | todas | permitir | negar/filtrar | negar | todas |
| criar | permitir | permitir | negar | negar | permitir |
| editar scheduled | permitir | permitir | negar | negar | permitir |
| remarcar | permitir | permitir | negar | negar | permitir |
| cancelar | permitir | permitir | negar | negar | permitir |
| done | permitir | permitir | negar | negar | negar |
| no_show | permitir | permitir | negar | negar | permitir |
| correção excepcional | permitir, com motivo e evento | negar | negar | negar | negar |

Para mudança de psicólogo, a autorização deve ser validada tanto contra o registro
original quanto contra o destino. “Própria” depende exclusivamente de
`users.psychologist_id`; nome, username e CRP nunca criam vínculo implícito. Cada célula
verifica código HTTP, estado do banco e eventos.

## TIMEZONE/DST PLAN

- Fonte de autoridade: único registro efetivo de `ClinicSettings.timezone_name`; ausência,
  duplicidade ou IANA inválido falha fechada com `422`/erro de configuração sanitizado.
- O cliente envia horário civil; o backend o interpreta na zona efetiva. O payload não
  escolhe uma zona divergente. `timezone_name` de criação passa a ser output derivado ou,
  durante compatibilidade, deve coincidir exatamente com a configuração.
- Para datetime naive, construir candidatos `fold=0` e `fold=1` e fazer round-trip
  local → UTC → local. Zero candidatos equivalentes significa horário inexistente; dois
  candidatos equivalentes com offsets distintos significa horário ambíguo. Ambos são
  rejeitados com `422`. Um único instante válido é normalizado para comparação/persistência.
- Datetime aware só é aceito quando representa inequivocamente o horário civil na zona
  efetiva; não pode contornar gap/fold nem selecionar fold silenciosamente.
- Create, edit e reschedule usam o mesmo resolvedor. Conflitos comparam instantes
  normalizados; a zona efetiva é gravada em novos registros.
- Alterar a configuração afeta somente novos agendamentos/novas interpretações. Linhas
  `legacy_unverified`, timestamps, zona gravada e eventos históricos não são reescritos,
  reclassificados nem convertidos.

## DEFAULT RUNTIME SMOKE PLAN

1. Preparar somente um clone/cópia de homologação contendo a estrutura operacional
   convencional e um banco fictício derivado por migration; nunca usar o banco canonical.
2. Limpar do processo filho `CLINICA_OPERATIONAL_POINTER` e
   `CLINICA_RUNTIME_CODE_ROOT`; também limpar overrides de banco/manifest.
3. Invocar o launcher normal (`scripts/run_api.ps1` ou equivalente efetivamente usado
   pelo produto), com o diretório de trabalho/layout que faz `backend.config` descobrir
   `runtime/operational-pointer.json` pelo caminho default.
4. Verificar no processo iniciado: pointer selecionado, checksum do manifest, code root
   validado, database path/checksum, `user_version=5`, startup e `/health`.
5. Criar previamente credenciais sintéticas no banco de homologação; autenticar por
   `POST /auth/login`; usar o token/cookie real para ler agenda própria e provar uma
   negação de agenda alheia. Não usar dependency override.
6. Executar somente leituras e uma tentativa bloqueada pelo write guard quando aplicável;
   comparar checksum do banco antes/depois.
7. Encerrar o processo e preservar stdout sanitizado, códigos HTTP, hashes e manifesto
   de execução privacy-safe.

O executor histórico de promoção da Generation 7 não será reescrito para fingir que a
Evidence antiga foi produzida de outra forma; o novo smoke gera Evidence suplementar.

## FILES EXPECTED

Arquivos existentes possivelmente alterados na implementação:

- `backend/models/appointment.py`;
- `backend/schemas/appointment.py`;
- `backend/schemas/settings.py`;
- `backend/services/appointment_service.py`;
- `backend/services/settings_service.py`;
- `backend/api/routes/appointments.py`;
- `backend/migration/canonical.py` e verificadores de schema/runtime;
- `scripts/spec004_candidate_migration.py` apenas para selecionar a nova migration sem
  modificar o artefato v3→v4;
- documentação/Evidence SPEC-004 afetada, sem mudar D1–D7.

Arquivos novos esperados:

- `backend/migration/spec004_remediation.py` (v4→v5);
- `scripts/spec004_remediation_smoke.py`;
- `tests/test_spec004_exceptional_correction.py`;
- `tests/test_spec004_retroactivity.py`;
- `tests/test_spec004_timezone.py`;
- `tests/test_spec004_successor_integrity.py`;
- `tests/test_spec004_append_only.py`;
- `tests/test_spec004_api_authorization_matrix.py`;
- `tests/test_spec004_independent_acceptance.py`;
- `tests/test_spec004_migration_harness.py`;
- `tests/test_spec004_default_runtime_smoke.py`;
- relatórios RED/GREEN e manifesto de Evidence privacy-safe em `docs/audit/`.

`backend/migration/spec004.py` permanece byte-for-byte como migration histórica; será
importado pelo harness v3→v4, não corrigido retroativamente.

## TESTS EXPECTED

- RED e GREEN direcionados para R1–R9;
- matriz API com login real e fixtures sintéticas;
- SQL adversarial direto para unicidade e append-only;
- migration v3→v4 e v4→v5 com IDs, contagens, canários de conteúdo, legado
  `rescheduled`, timestamps, constraints, índices, idempotência e FKs;
- regressão de `tests/test_spec004_agenda.py`, auth, rotas, concorrência, migrations,
  canonical, manifests, cutover e runtime guards;
- suíte Python completa, testes frontend e build Vite;
- smoke default em processo isolado sem os dois overrides proibidos;
- `integrity_check`, `foreign_key_check`, inventário de órfãos/sucessores e confirmação
  de que o banco/Generation 7 não mudou durante a fase de implementação candidata.

## RISKS

- Triggers append-only podem impedir fixtures que hoje “limpam” eventos por DELETE;
  testes devem usar bancos descartáveis, não relaxar o guard.
- O índice único v5 deve abortar diante de duplicidade preexistente; nunca escolher um
  sucessor automaticamente.
- Ação excepcional mal desenhada pode virar bypass geral; endpoint, permissão, payload e
  evento devem ser específicos e fail-closed.
- Datetimes aware/naive e serialização SQLite podem mudar comparação de conflitos; manter
  uma representação canônica explícita para novos writes sem converter legado.
- Configuração ausente/duplicada não pode cair silenciosamente no default hard-coded.
- Smoke real pode tentar tocar o canonical se o layout estiver errado; executar apenas
  contra runtime de homologação e provar paths antes de iniciar writes.
- Atualização de validadores operacionais para v5 não autoriza promoção. Generation 7
  segue canonical até gate HUMAN posterior.

## HUMAN DECISIONS REQUIRED

`NONE`.

D3–D7 já determinam comportamento, autorização, auditoria, retroatividade e timezone.
Rota, nomes de triggers/índices, representação interna e decomposição de testes são
decisões técnicas. A eventual necessidade técnica das colunas `from_status/to_status`
será decidida pelo RED de auditabilidade, sem alterar o comportamento aprovado.

## STOP_CONDITION

Parar a futura orquestração diante de: necessidade de inferir sucessor, fold, timezone,
ator, motivo ou estado legado; duplicidade preexistente de sucessor; qualquer mutation
do banco/pointer/manifest/Generation 7 durante candidato; perda de IDs/conteúdo; falha de
FK/integridade; bypass de auth real; divergência não explicada do launcher default;
alteração de D1–D7; ou necessidade de promoção/migration operacional sem novo gate HUMAN.

## PRÓXIMO_READY

`READY_FOR_SPEC004_REMEDIATION_ORCHESTRATION`
