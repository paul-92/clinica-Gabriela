# SPEC-008 Fase 10 — tentativa de cutover real

- Data: 2026-09-14
- Autorização: `HUMAN DECISION — SPEC-008 PHASE 10 CUTOVER: GO`
- Resultado: `BLOCKED`
- Momento do bloqueio: preflight read-only, antes da primeira operação mutável
- Cutover, backup final, promoção, switch e rollback: não executados
- Commit: não executado

## Revalidação pré-mutação

| Precondição | Resultado | Evidência |
|---|---|---|
| Candidato aprovado | `PASS` | `canonical-candidate-v1.db`; SHA-256 `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46` |
| Freeze vigente | `PASS` | `spec008-20260911-phase1-001-freeze-v7`; status `frozen`; SHA-256 `468517df633e482d0e1c8bb3a292da230e1b97f29c01e72c771367efa7dc3a2f` |
| RemapManifest | `PASS` | lifecycle `verified`; versão `verified-v2`; SHA-256 `f8dfcddb1947ac4d1d14519424342a015712d71609110cb3392ff3780ab82876` |
| Runtime manifest | `PASS` | checksum e arquivos conferidos: `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398` |
| Baseline sucessor backend | `PASS` | `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757` |
| Baseline desktop | `PASS` | `5aa6a8d22ecbf9b8f6d4574ae49a2c611ab089aa933132ea47dd5e1c451d793b` |
| Sidecars | `PASS` | candidato e legados sem WAL, SHM ou journal pendente |
| Writers observáveis | `PASS_WITH_OS_VISIBILITY_LIMIT` | portas 8000, 8765 e 5173 sem listener; `fsutil queryProcessesUsing` não encontrou processo com os bancos abertos; Windows informou ausência de privilégio de debug para caminhos de alguns processos |
| Promoção/rollback | `PASS_IMPLEMENTED_TESTED` | primitivas fail-closed homologadas; seleção direcionada anterior `30 passed` |
| Diretório canônico real | `BLOCK` | `%LOCALAPPDATA%/ClinicaGabriela/canonical` não existe e não foi aprovado com ACL concreta |
| Fingerprint ACL aprovado | `BLOCK` | nenhum fingerprint externo foi fornecido; `AclPolicy` proíbe inferência pelo executor |
| Ponteiro operacional inicial | `BLOCK` | `%LOCALAPPDATA%/ClinicaGabriela/runtime/operational-pointer.json` não existe |
| Maintenance lock real | `NOT_ACQUIRED` | sua criação seria a primeira mutação; o preflight bloqueou antes dela |

## Contrato interrompido

A execução parou antes de `QUIESCE`. Não foi permitido criar o diretório canônico e
autoaprovar sua ACL, pois isso transformaria uma medição feita pelo executor em
política de segurança. Também não foi inicializado um ponteiro legado sem que os
parâmetros reais de destino estivessem congelados.

Consequentemente:

- backup final e checksum: `NOT_CREATED`;
- candidato promovido: `NONE`;
- fonte operacional antes: fallback legado `backend/data/clinica_api.db`;
- fonte operacional depois: inalterada, `backend/data/clinica_api.db`;
- troca do ponteiro: `NOT_EXECUTED`, ponteiro ausente;
- startup/health/smoke pós-cutover: `NOT_EXECUTED`;
- integridade/FKs pós-cutover: `NOT_EXECUTED`;
- legado: preservado, não desativado e sem alteração observada;
- rollback: `NOT_REQUIRED_NOT_EXECUTED`, pois nenhuma promoção/switch ocorreu.

## Risco residual e requisito seguinte

O risco residual é escolher implicitamente um destino e uma ACL de produção não
aprovados, além de iniciar uma cadeia de ponteiro operacional sem parâmetros
congelados. O próximo requisito da SPEC-008 é uma decisão HUMAN que fixe:

1. caminho canônico real;
2. fingerprint ACL SHA-256 exato desse diretório já provisionado;
3. raiz do runtime, caminho do ponteiro e diretório dos runtime manifests;
4. confirmação de que o ponteiro geração 1 deve representar o baseline sucessor
   backend antes do switch.

Após esses parâmetros existirem, é necessário emitir novo GO ou continuação explícita
da janela e repetir o preflight antes da primeira mutação.

`BLOCKED`
