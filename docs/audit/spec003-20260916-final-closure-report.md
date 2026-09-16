# SPEC-003 — Final Closure Report

- Data: 2026-09-16
- Autoridade de aceite: HUMAN/Product Owner
- Resultado da revisão final independente: `QUALITY_GATE_PASS`
- Estado documental: `ACCEPTED / DONE`
- Classificação: privacy-safe
- Regra de fechamento: `ACCEPTED/DONE ≠ DESTRUCTIVE CLEANUP`

## SPEC-003 CLOSED — ACCEPTED/DONE

O HUMAN/Product Owner aceitou formalmente o Final Independent Quality / Closure
Re-Review e autorizou o encerramento da `SPEC-003 — Integridade Clínica`. A decisão
auditável está em `spec003-20260916-human-final-acceptance.json`.

O fechamento é documental. Não executou nem autoriza nova migration, promoção,
alteração de pointer, rollback, cleanup destrutivo, push, merge ou release.

## Contrato e escopo final

A SPEC-003 estabeleceu integridade clínica e consistência de dados sobre a baseline
canônica da SPEC-008, com estes invariantes:

- CPF opcional, normalizado e validado quando informado, único na forma canônica e com
  legado inválido preservado como `legacy_unverified`;
- identidade profissional mínima por `regional + número`, aptidão clínica explícita e
  conflitos mantidos em `REVIEW`;
- inativação sem perda histórica, exclusão física estritamente limitada e ausência de
  cascata destrutiva sobre conteúdo clínico ou financeiro protegido;
- prontuário em ciclo `DRAFT → FINALIZED`, legado como `LEGACY_PRESERVED`, finalizados
  imutáveis e retificação append-only com autoria, motivo, timestamp e predecessor;
- autoria ou atendimento histórico ausente preservado explicitamente, sem inferência;
- prechecks de existência/atividade/coerência, FKs SQLite ativas, rollback de
  `IntegrityError` e respostas sanitizadas;
- `PATCH` distinguindo campo ausente, `NULL` e vazio; `PUT` temporário e deprecado;
- concorrência otimista por versão/ETag e `If-Match`, sem last-write-wins silencioso;
- migration forward-only com backup, dry-run, validação e recovery;
- `NO_AUTOMATIC_DELETION` enquanto a política externa de retenção estiver pendente.

Ficaram fora do escopo prazo jurídico definitivo, regras profissionais completas para
múltiplos CRPs, regras de agenda da SPEC-004, regras contábeis da SPEC-005, cloud,
interface, instalador e novos módulos clínicos.

## Decisões HUMAN relevantes

- `BLOCK-003-01`: representação canônica mínima de CRP por `regional + número`;
  regras adicionais permanecem `EXTERNAL_POLICY_PENDING`.
- `BLOCK-003-02`: registros anteriores à SPEC são `LEGACY_PRESERVED`, com
  `author_unknown` quando aplicável e sem `appointment_id` inferido.
- `BLOCK-003-03`: exclusão física somente para draft elegível, nunca finalizado nem
  legado, sem dependência de preservação e por ator autorizado, com evento auditável
  privacy-safe.
- Política provisória de retenção: `NO_AUTOMATIC_DELETION`.
- Promoção operacional forward-only e posterior recuperação seletiva foram autorizadas
  nos gates correspondentes; rollback silencioso de pointer permaneceu proibido.
- Em 2026-09-16, o resultado final `QUALITY_GATE_PASS` foi aceito e a SPEC foi encerrada
  como `ACCEPTED / DONE`.

## Implementação e migration

Provenance principal:

| Papel | Referência |
|---|---|
| Baseline operacional aceita | `ebc8604d5e97230ccfe86ecb65a593fcfddf9fb5` |
| Implementação funcional SPEC-003 | `00ee65e8dc1541783cf4c798f08b40af6b9fd266` |
| Primeira estabilização do runtime | `9c983aff8be9eca7b482953453c3a8c375a75ada` |
| Evidence do primeiro closure gate reprovado | `12e4c3762d9ec73ffd670487c2e4b3940e1bc9d8` |
| Correção do binding de manifest | `4329cb3326c60244c427afd84dd51589c9cb4f31` |
| Integração/remediação final | `8e2d162854db84ac9352ca1a96a911870eb6a1f3` |
| Registro documental da remediação | `30cdd7a` |

A migration SPEC-003 foi executada forward-only sobre cópia/candidato previamente
validado. Preservou IDs, conteúdo e contagens das tabelas de domínio; classificou apenas
estados determinísticos e não inventou autoria, atendimento ou identidade profissional.
O banco promovido permaneceu com SHA-256
`143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506`.

## Quality Gates, falhas e remediações

### `QUALITY_GATE_FAIL` 1 — smoke pós-promoção

O primeiro smoke após a passagem para Generation 3 encontrou revalidação destrutiva de
CPF histórico `legacy_unverified` por `PatientRead`, violando `D-CPF-04`.

- Root cause: o schema de leitura reutilizava validação destinada a entrada/escrita.
- Efeito: `POST_SWITCH_FAILURE`; maintenance lock foi liberado e o pointer não sofreu
  rollback silencioso.
- Remediação: separação entre validação de entrada (`PatientCreate`/`PatientUpdate`) e
  leitura histórica (`PatientRead`), com regressão dedicada.
- Invalidação seletiva: smoke/runtime daquela tentativa e seu resultado de promoção;
  banco migrado, generations anteriores, backup e Evidence foram preservados.
- Revalidação independente: suíte limpa com `205 passed`, bootstrap, health, GETs dos
  módulos, write guard e checksum antes/depois; recovery forward-only Generation 3 → 4.

### `QUALITY_GATE_FAIL` 2 — Independent Quality / Closure Review

O runtime congelado falhou no layout operacional real sem o override
`CLINICA_RUNTIME_MANIFEST_DIR`: procurava manifests um nível acima do diretório aprovado.
O smoke anterior havia mascarado o defeito ao injetar explicitamente esse override.

- Root cause: resolução default em `backend/config.py` usava
  `pointer_path.parent.parent`, incompatível com
  `%LOCALAPPDATA%\ClinicaGabriela\runtime\runtime-manifests`.
- Remediação: default alterado para `pointer_path.parent`; smoke passou a testar o
  contrato normal sem override; launchers propagam falhas do supervisor; testes antigos
  foram isolados de pointers reais; regressões de layout/import/PowerShell foram criadas.
- Invalidação seletiva: conclusão do closure gate e binding runtime/manifest da
  Generation 4; migration, banco, schema, integridade, histórico e evidências anteriores
  permaneceram válidos.
- Revalidações: `22 passed` dirigidos, `210 passed` pré-commit, `210 passed` em extração
  limpa da correção e `210 passed in 19.67s` na worktree limpa do runtime final.
- Final Independent Quality / Closure Re-Review: `QUALITY_GATE_PASS`.

## FINAL OPERATIONAL STATE

| Item | Estado aceito |
|---|---|
| Generation | `5 / canonical` |
| Pointer SHA-256 | `723a28330bce6ebd1821737675651c905f2c5a358cf96db4e8218a908fea65d7` |
| Pointer predecessor | `ace795b20122c478fb862b84ec74de8bbafb929ea23a84cde4fb90680700146a` |
| Runtime manifest vigente | `e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1` |
| Runtime commit | `8e2d162854db84ac9352ca1a96a911870eb6a1f3` |
| Banco SHA-256 | `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506` |
| Schema físico | `backend-models-v3-spec003-integrity` |
| `PRAGMA user_version` | `3` |
| `integrity_check` | `ok` |
| `foreign_key_check` | `0` violações |
| Maintenance lock | ausente |
| Sidecars anômalos | `0` |
| Startup default / health | `PASS` / HTTP 200 |
| Guard de endpoint protegido | HTTP 403 sem autorização |

O avanço Generation 4 → 5 foi exclusivamente o binding forward-only do runtime
remediado ao banco já aceito e inalterado, por CAS atômico e geração monotônica. O ensaio
isolado de recovery Generation 4 → 5 → 6 passou. Não houve nova migration de dados.

O `schema_version` do pointer mantém o label de protocolo legado
`backend-models-v2-credential-reset` por compatibilidade com o loader; o schema físico e
o `user_version=3` estão vinculados de modo explícito no runtime manifest.

## FINAL EVIDENCE

- Contrato: `docs/specs/SPEC-003-integridade-clinica.md`.
- Candidato: `docs/audit/spec003-20260915-implementation-candidate-report.md`.
- Promoção/estabilização: `docs/audit/spec003-20260915-operational-promotion-report.md`.
- Remediação: `docs/audit/spec003-20260916-quality-gate-remediation-report.md`.
- Aceite HUMAN: `docs/audit/spec003-20260916-human-final-acceptance.json`.
  SHA-256: `ba6429b6e31426cdcbd298601e4b68413704cadf7ad4b61754ff8a7c178c7edb`.
- Evidence de promoção reprovada: `spec003-promotion-20260915T205904Z.json`, SHA-256
  `e29169a718f27092abd093809427fc0cc72e0837a21317fdfee35cfb267b6e59`.
- Evidence de promoção estabilizada: `spec003-promotion-20260915T210259Z.json`, SHA-256
  `f3f048437f3406ce997dc52e20f017d6e1d061015465d869bf880b808b1aae6a`.
- Evidence de binding/recovery final:
  `spec003-runtime-binding-recovery-20260916T140424Z.json`, SHA-256
  `f2b48ed88b3c5f1fe9c01a865e6134da0c61e8891e75c4853dc3d15e5b1c92b0`.
- Manifest vigente content-addressed:
  `runtime-manifest-e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1.json`.
- Suíte final independente: `210 passed`; testes dirigidos: `22 passed`; resultado final:
  `0 FAILED`.

Toda Evidence listada é privacy-safe: não inclui nomes reais, CPF/CRP, conteúdo clínico,
credenciais ou fatos financeiros individualizados.

## Backups, recovery e `NO_SILENT_POINTER_ROLLBACK`

- Backup pré-recovery manifest SHA-256:
  `a6950e532efa0b9b35ab69b287270a2d59f8d1fa19855780cba1433fa9049004`.
- Backup inicial da Generation 4 manifest SHA-256:
  `7d13cd4e1a4df981b79d2b4b24c3a0709120209891b6ebac214eddba5036dfa6`.
- Restore isolado reproduziu o SHA-256 do banco, `integrity_check=ok`, zero violações FK
  e zero sidecars.
- Falhas pós-switch não causaram retorno silencioso do pointer. A recuperação foi sempre
  forward-only, atômica, por CAS e com geração monotônica.
- Após novas escritas reais, recovery continua limitado a forward recovery ou restauração
  seguida de reconciliação explicitamente autorizada.

`NO_SILENT_POINTER_ROLLBACK` permanece uma boundary operacional obrigatória.

## RESIDUAL RISKS / FOLLOW-UPS

| Item | Classificação | Destino |
|---|---|---|
| Prazo, marco inicial, anonimização, exceções LGPD e workflow de eliminação | `EXTERNAL_POLICY_PENDING` / alto impacto externo, mitigado por `NO_AUTOMATIC_DELETION` | validação jurídica e profissional futura |
| Múltiplas inscrições, principal/secundária, situações especiais e validação externa de CRP | `EXTERNAL_POLICY_PENDING` / política profissional | validação profissional futura; manter `REVIEW` e aptidão interna fail-closed |
| Label v2 no `schema_version` do pointer versus schema físico v3 no manifest | `NON_MATERIAL_METADATA` / technical debt baixo | evoluir protocolo/loader em manutenção planejada |
| `PUT` temporário e deprecado | technical debt médio | migrar clientes para `PATCH` + ETag antes de remover compatibilidade |
| Operação persistente deve usar exclusivamente artefato/worktree correspondente ao manifest | risco operacional médio controlado | disciplina de deploy e verificação content-addressed |
| Recovery depois de novos fatos reais exige reconciliação | risco operacional alto, controlado por boundary | runbook e autorização HUMAN; nunca rollback cego |
| Cleanup/retention de generations e backups não definido neste fechamento | manutenção futura; não autorizado agora | política operacional própria, com novo gate e preservação legal |

Itens explicitamente transferidos para operação/manutenção futura: monitoramento de
startup/health, verificação periódica do pointer e manifest, testes de restore, rotação
somente sob política aprovada, evolução do protocolo do pointer, retirada coordenada do
`PUT`, validações externas de CRP, política jurídica de retenção e workflow de eliminação.

## PRESERVED RECOVERY ASSETS

Permanecem preservados e fora de qualquer cleanup deste fechamento:

- Generations 1, 2, 3, 4 e a Generation 5/canonical;
- bancos canônicos/legados e cópias de pré-promoção necessárias à recuperação;
- backups de SPEC-008, promoção SPEC-003 e recovery;
- manifests antigos e vigente, todos content-addressed;
- histórico integral dos pointers e seus checksums/predecessores;
- Evidence de sucesso e falha, inclusive os dois Quality Gates reprovados;
- relatórios de candidato, promoção, remediação, re-review e aceite;
- scripts, manifests e artefatos necessários ao restore/recovery validado.

Nenhum desses ativos foi removido, compactado, sobrescrito ou reclassificado.

## GIT STATE

No momento do fechamento:

- branch: `feature/spec-008-architecture-foundation`;
- `HEAD` anterior a este registro documental: `30cdd7a`;
- nenhum commit, push, merge ou release foi executado por este fechamento;
- alterações locais preexistentes em `.context/COMMANDS.md` e
  `backend/services/appointment_service.py`, além de artefatos não rastreados em
  `.baseline-staging/`, `.forensics/` e `.homologation/`, foram preservadas e não foram
  incorporadas para limpar a árvore;
- mudanças deste fechamento limitam-se ao estado documental da SPEC-003, ao índice do
  roadmap, à decisão HUMAN e a este relatório.

## Próximo item do roadmap

O próximo item permanece `SPEC-004 — Agenda e Gestão de Atendimentos`. Ele não foi
iniciado, alterado nem autorizado por este fechamento.

`SPEC-003 CLOSED — ACCEPTED/DONE`
