# Final Cutover Readiness Preflight — SPEC-008

- Data: 2026-09-14
- Resultado: `READY_FOR_HUMAN_CUTOVER_DECISION`
- Escopo: preflight final não destrutivo
- Cutover/promoção/switch: não executados
- Commit: não executado

## Decisão HUMAN incorporada

A aprovação da ACL e do binding está registrada em
`spec008-20260914-runtime-acl-manifest-binding-human-decision.json`, SHA-256
`9776b506ee79fbae33a43bf672e0197474c9e1f5d7efef4c750ce81235f7006a`,
acompanhada de sidecar de checksum.

- ACL aprovada, fingerprint exato:
  `f58389254ac21f4890d95ad00ed1039fd0820183855e90a33ea9715f7c05b5f0`;
- binding aprovado:
  `CLINICA_RUNTIME_MANIFEST_DIR=%LOCALAPPDATA%\ClinicaGabriela\runtime\runtime-manifests`;
- qualquer mudança material da ACL invalida este gate;
- nenhuma equivalência de ACL pode ser inferida.

## Gates

| Gate | Resultado | Evidência |
|---|---|---|
| Raiz canônica provisionada | `PASS` | `%LOCALAPPDATA%\ClinicaGabriela\runtime` |
| ACL raiz | `PASS` | fingerprint observado exatamente igual ao aprovado |
| Proteção de `runtime-manifests` | `PASS` | herda exclusivamente usuário efetivo, `SYSTEM` e `Administrators`; nenhum grant genérico de escrita |
| Generation 1 | `PASS` | `generation-0001-d0123c58c57f.db`; checksum `d0123c58c57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757` |
| Pointer operacional | `PASS` | generation `1`, state `legacy`, checksum `8320039f393fb55baaa877f3fceb80848d03237c6b16ef1d3cd342055d6161bf` |
| Resolução de runtime | `PASS` | com o binding aprovado, resolve exclusivamente para generation 1 |
| Runtime manifest | `PASS` | `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`; conteúdo e arquivos conferidos |
| Candidato `verified-v2` | `PASS` | checksum `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46` |
| Freeze | `PASS` | `spec008-20260911-phase1-001-freeze-v7`, status `frozen`, checksum `468517df633e482d0e1c8bb3a292da230e1b97f29c01e72c771367efa7dc3a2f` |
| RemapManifest | `PASS` | lifecycle `verified`, versão `verified-v2`, checksum `f8dfcddb1947ac4d1d14519424342a015712d71609110cb3392ff3780ab82876` |
| Validação Fases 7–8 | `PASS` | candidato e gate vinculados |
| SQLite generation 1 | `PASS` | `integrity_check=ok`, zero FKs, 8 tabelas |
| SQLite candidato | `PASS` | `integrity_check=ok`, zero FKs, 8 tabelas |
| Sidecars | `PASS` | generation 1, candidato e dois legados sem WAL/SHM/journal |
| Writers observáveis | `PASS_WITH_OS_VISIBILITY_LIMIT` | portas 8000/8765/5173 livres; `fsutil` não encontrou processos usando os três bancos; ausência de debug privilege limita nomes de alguns processos |
| Maintenance lock | `READY_NOT_ACQUIRED` | mecanismo fail-closed homologado; lock real não criado no preflight não destrutivo |
| Promoção e switch | `READY_NOT_EXECUTED` | primitivas atômicas/fail-closed homologadas |
| Rollback | `PASS` | cadeia isolada terminou generation 3/state `legacy`; simulação nominal e rollback aprovadas |

Uma primeira composição do comando read-only teve erro de quoting do PowerShell antes
do bloco Python por causa do `*` de uma consulta SQL. Portas, handles e ACL foram
coletados normalmente. O bloco Python foi repetido sem mutação usando
`PRAGMA table_list` e passou integralmente.

## Preservação

- pointer real permaneceu generation 1/state `legacy`;
- generation 1 permaneceu inalterada;
- candidato `verified-v2` não foi promovido;
- baseline original `8f973f...aed` e baseline sucessor `d0123c58...e757`
  permanecem preservados na cadeia de provenance;
- `backend/data/clinica_api.db` não foi alterado;
- nenhum legado foi desativado;
- nenhum backup final foi criado, pois pertence à futura janela de cutover;
- nenhum commit foi criado.

## Resultado

Todos os parâmetros antes pendentes estão agora provisionados, explicitamente
aprovados e revalidados sem divergência. Na futura janela autorizada, a ACL deverá ser
comparada byte-exatamente pelo fingerprint antes da primeira mutação, o binding do
manifest deverá ser aplicado, e o maintenance lock deverá ser adquirido antes do
backup final.

`READY_FOR_HUMAN_CUTOVER_DECISION`

Este resultado não autoriza cutover, promoção, switch, writes canônicos ou
desativação do legado.
