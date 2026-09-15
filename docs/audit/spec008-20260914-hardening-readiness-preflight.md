# Hardening e Cutover Readiness Preflight — SPEC-008

- Data: 2026-09-14
- Estado final: `HUMAN`
- Infraestrutura/isolamento: `PASS`
- Imutabilidade histórica original: `BLOCKED_KNOWN`
- Cutover: `NOT_AUTHORIZED_NOT_EXECUTED`
- Commit: não executado

## Premissas preservadas

O estado atual de `backend/data/clinica_api.db` não foi aceito como baseline, não foi
restaurado e continua classificado como artefato historicamente alterado. Igualdade
lógica não substitui igualdade física. O baseline físico histórico permanece
`8f973f56654fb92f03c278f21934b976c76ba61318edd1f449dbe4584bed0aed`.

O relatório forense `spec008-20260914-read-only-forensic-report.md`, o snapshot e as
evidências anteriores foram preservados.

## Hardening implementado

1. A suíte define `BACKEND_DATA_DIR` e `BACKEND_DATABASE_PATH` em raiz temporária
   exclusiva antes da coleta/importação de módulos.
2. `sqlite3.connect` é guardado durante pytest: qualquer abertura write-capable do
   caminho operacional real falha antes de abrir o arquivo. Apenas URI explicitamente
   `mode=ro&immutable=1` é tecnicamente permitida.
3. Há regressões que comprovam que o fallback da suíte não resolve para o banco real
   e que uma tentativa write-capable é recusada.
4. O smoke da simulação valida que o banco apontado pertence à raiz isolada e restaura
   todas as variáveis de ambiente no teardown.
5. Temporários atômicos usam prefixos curtos; nomes finais content-addressed permanecem
   inalterados. Isso removeu as sete falhas `MAX_PATH` sem mudar a política de dados.

## Validações

| Bloco | Resultado |
|---|---|
| Isolamento/bootstrap/migrations/cutover infra | `30 passed` |
| Suíte Python completa | `194 passed` |
| Frontend | `5 passed` |
| Vite build | `PASS`, 1.582 módulos |
| Simulação nominal e rollback, candidato aprovado | `PASS` |
| Escrita no banco operacional durante pytest | fail-closed |

O primeiro build Vite no sandbox falhou com `spawn EPERM`; a repetição autorizada
fora do sandbox passou. A falha foi ambiental, não funcional.

## Simulações isoladas

A simulação válida para o preflight usou o candidato congelado:

- caminho: `%LOCALAPPDATA%/ClinicaGabriela/migration/spec008-20260911-phase1-001/canonical-candidate-v1.db`;
- SHA-256: `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46`;
- evidência: `spec008-20260914-hardening-cutover-simulation-approved-candidate.json`;
- SHA-256 da evidência: `7deb142d8ad764ee3d43cb509c8252ca51129e2951c01f9eaab092a17b1ab5d6`;
- runtime manifest: `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`;
- nominal: `PASS`;
- falha injetada antes de writes, rollback/restore: `PASS`;
- cutover real: não executado.

Uma primeira simulação desta rodada usou uma cópia de homologação com SHA-256
`a1e35a0d...aeb8`, em vez do candidato congelado. Ela permanece preservada como
evidência de teste de isolamento, mas foi excluída do gate de candidato. A repetição
acima usou a referência correta.

## Sentinela do banco operacional

Antes, entre blocos e depois de toda a validação:

- SHA-256: `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
- `mtime`: `2026-09-13T20:21:30.5809353Z` (13/09/2026 17:21 local);
- tamanho: 61.440 bytes;
- WAL: ausente;
- SHM: ausente;
- journal: ausente.

Resultado: zero alteração física observada durante hardening, suíte completa,
frontend/build e duas simulações isoladas.

## Resultado do preflight

Os gates técnicos de isolamento, regressão, build, candidato aprovado, simulação
nominal e rollback estão `PASS`. O incidente anterior não é apagado por esse
resultado: o banco operacional atual continua divergente do baseline físico histórico
e não foi promovido a baseline novo.

O processo para em `HUMAN`. Cutover, promoção, ponteiro, restore, rebaseline e commit
permanecem proibidos até decisão explícita posterior.
