# Homologation Report — SPEC-008 / `verified-v2`

- Data: 2026-09-13
- Execução: `spec008-20260911-phase1-001`
- Freeze vigente: `spec008-20260911-phase1-001-freeze-v7`
- Schema: `backend-models-v2-credential-reset`
- Escopo: Fase 9, sem promoção e sem cutover
- Recomendação técnica: `READY_FOR_CUTOVER_REVIEW`
- Cutover: não autorizado e não executado

## 1. Identificação do candidato

O único pacote coerente foi localizado no armazenamento protegido de migration do
perfil local. O candidato físico é `canonical-candidate-v1.db`, vinculado logicamente
ao `RemapManifest` `spec008-20260911-phase1-001-remap-v3-schema-v2-verified-v2`.

- SHA-256 esperado e observado: `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46`
- Tamanho: 61.440 bytes
- Lifecycle do remap: `verified`
- Checksum do remap `verified-v2`: `f8dfcddb1947ac4d1d14519424342a015712d71609110cb3392ff3780ab82876`
- `integrity_check`: `ok`
- Violações de FK: `0`
- Sidecars WAL/SHM/journal pendentes: `0`

A acessibilidade foi reidratada por cópia byte-idêntica em área isolada. Todos os
writes funcionais ocorreram somente em cópias de homologação.

## 2. Freeze e cadeia vinculante

| Artefato | Resultado | SHA-256 |
|---|---|---|
| Freeze v7 | `PASS` | `468517df633e482d0e1c8bb3a292da230e1b97f29c01e72c771367efa7dc3a2f` |
| MigratorToolManifest | `PASS` | `99b4c1a5825f3dbcbc69d7218ec81d876bd7c5f82036ddf79064f975d70219a9` |
| Snapshot manifest desktop | `PASS` | `548a402873bfdf2ce1eff65d55be71776cdfb59c60d66e7119a48aadee32770e` |
| Snapshot manifest backend | `PASS` | `e8f4779a11590bfc6e682970c7bc8a0cfc4631ca131b10b05d0e77466b8d8767` |
| HistoricalProvenanceSupplement | `PASS` | `1fb147ea7df6e8b56b70c6182b1df39c9b23b5d9e4012ca3a78450acef286340` |
| Relatório Fases 5–8 v1 | `SUPERSEDED` | correção v1 declara sua invalidação por sidecars pós-carga |
| Correção Fases 7–8 v1 | `PASS` | `a9893eb63e613ebff2b0132c449b0a1c0dc146cd34d14384c96b5574498aed56` |
| Relatório Fases 7–8 v2 | `PASS` | `e014f91df67d5eede896f838b626fddc4f573a0886b43cc997ffcadb16d0029b` |

O freeze v7 vincula o mesmo execution ID, schema e MigratorToolManifest. Os cinco
módulos do bundle e o Execution Contract conferiram com os checksums congelados.
Os dois snapshots foram validados por modelos tipados, checksum, schema, integridade
e FKs. Timestamps e checksums do pacote protegido permaneceram inalterados após os
testes.

## 3. Fluxos homologados

| Fluxo | Resultado |
|---|---|
| Startup exclusivo no candidato | `PASS` |
| Health check | `PASS` |
| Encerramento e reinício controlados | `PASS` — dois ciclos reais |
| Autenticação válida | `PASS` |
| `password_reset_required` | `PASS` — login bloqueado enquanto ativo |
| Credencial desabilitada | `PASS` — login bloqueado |
| Patients | `PASS` — create/get/update/persistência |
| Psychologists | `PASS` — create/get |
| Appointments | `PASS` — create/get/conflito de horário |
| Clinical records | `PASS` — create/get e controle de acesso |
| Payments | `PASS` |
| Expenses | `PASS` |
| Resumo financeiro | `PASS` |
| `clinic_settings` | `PASS` — configuração única consultada/atualizada |
| Persistência após reinício | `PASS` |
| Backup/restauração | `PASS` |
| Integridade/FKs da restauração | `PASS` — `ok`, zero violações |

Foram usados exclusivamente dados sintéticos nas cópias de homologação. O relatório
não contém PII, conteúdo clínico, credenciais, IDs ou FKs reais.

## 4. Testes executados

- Backend real com `BACKEND_DATABASE_PATH` apontado somente à cópia reidratada:
  dois startups, dois health checks e dois encerramentos controlados; ambos passaram.
- Harness funcional da Fase 9: passou após correção, incluindo reinício e restore.
- Testes direcionados: `20 passed`.
- Regressão Python completa: `175 passed`.
- Frontend: `5 passed`.
- Build Vite: passou, 1.582 módulos transformados.
- Smoke arquitetural: startup, health, autenticação, escrita isolada, reinício,
  persistência, integridade e restauração aprovados.

## 5. Falhas e correções

1. `FAILED_TECHNICAL`: execução inicial do harness pelo caminho do arquivo não
   resolveu o pacote `backend`. Corrigido operacionalmente usando execução modular.
2. `FAILED_VALIDATION`: a API aceitava agendamentos sobrepostos para o mesmo
   psicólogo. Corrigidos repository/service para rejeitar sobreposição ativa com
   HTTP 409; criação, atualização e fronteiras receberam testes automatizados.
3. `FAILED_TECHNICAL`: pytest não conseguiu gerenciar temporários no sandbox e,
   depois, encontrou limite de comprimento de caminho. Reexecutado com autorização
   e `basetemp` curto; regressão final passou integralmente.
4. `FAILED_TECHNICAL`: build Vite recebeu `spawn EPERM` no sandbox. Reexecutado fora
   do sandbox; passou.

Nenhuma correção alterou bytes do candidato protegido, snapshots ou históricos.

## 6. Reinício, backup e integridade

- O startup não alterou o checksum da cópia antes dos testes funcionais.
- Dados sintéticos persistiram após novo lifespan do backend.
- Backup produzido pela SQLite Backup API e restauração byte-for-byte operacional.
- Restauração: `integrity_check=ok`, FK violations `0`.
- Cópia funcional final: `integrity_check=ok`, FK violations `0`.

## 7. Autenticação e reset obrigatório

O estado migrado inicial foi confirmado: todas as credenciais estavam desabilitadas e
com reset obrigatório. Um hash sintético válido continuou bloqueado enquanto
`password_reset_required=true`; a credencial sentinela desabilitada continuou
impossível de autenticar mesmo após remover o flag. Credenciais sintéticas foram
habilitadas apenas na cópia para exercitar rotas autenticadas.

## 8. Ausência de dual-write e runtime legado

O backend resolve uma única fonte pelo `BACKEND_DATABASE_PATH`; durante a homologação
esse valor apontou somente para cada cópia isolada. Não foram encontrados jobs ou
fluxos de sincronização implícita no runtime. Referências simultâneas aos dois bancos
existem apenas nas ferramentas explícitas de migration/inventário.

Não houve mudança nos arquivos de configuração do runtime operacional. Os bancos
legados conservaram tamanho, timestamp e os checksums observados antes dos testes:

- desktop: `5aa6a8d22ecbf9b8f6d4574ae49a2c611ab089aa933132ea47dd5e1c451d793b`
- backend: `8f973f56654fb92f03c278f21934b976c76ba61318edd1f449dbe4584bed0aed`

Nenhum sidecar apareceu no pacote protegido ou nos bancos legados.

## 9. Rollback pré-cutover validado

O plano foi validado sem promoção: parar o processo supervisionado, descartar somente
a cópia de homologação, manter o candidato protegido e os legados intactos e repetir
startup sobre nova cópia byte-idêntica. Backup/restauração também foi exercitado.
Como nenhum ponteiro operacional foi trocado, o rollback pré-cutover não depende de
reversão de configuração nem de dual-write.

## 10. Riscos residuais

- O bloqueio de conflito de agenda é aplicado na camada de serviço; corrida entre
  writers realmente concorrentes ainda merece teste de concorrência/constraint em
  uma evolução da SPEC-004.
- Os testes clínicos e financeiros foram técnicos e sintéticos; aceite humano de
  domínio continua necessário quando aplicável.
- A janela, responsáveis e tratamento de writes pós-cutover permanecem decisões da
  futura revisão de cutover.

## 11. Gates ainda abertos

- revisão HUMAN deste relatório e das correções;
- aceite funcional/clínico/financeiro, quando exigido pelos responsáveis;
- autorização explícita separada de cutover;
- gates da Fase 10, incluindo manutenção, quiescência e repetição das validações;
- critérios e responsáveis da janela de rollback pós-cutover.

## 12. Recomendação final

`READY_FOR_CUTOVER_REVIEW`

Esta recomendação abre somente a revisão humana. Não promove o candidato, não troca a
fonte operacional, não autoriza writes canônicos de produção e não autoriza cutover.
