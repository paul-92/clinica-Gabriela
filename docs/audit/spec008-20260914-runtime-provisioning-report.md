# Runtime Provisioning Report — SPEC-008

- Data: 2026-09-14
- Estado final: `HUMAN`
- Escopo: provisionamento inicial da infraestrutura operacional
- Cutover: `NOT_EXECUTED`
- Candidato `verified-v2`: `NOT_PROMOTED`
- Commit: não executado

## Resultado executivo

A generation 1 foi provisionada por cópia atômica fail-existing do baseline sucessor
reconhecido. A fonte `backend/data/clinica_api.db` permaneceu byte a byte inalterada.
O pointer operacional geração 1 foi criado atomicamente em estado `legacy`. Nenhuma
troca de fonte, promoção do candidato, desativação do legado ou cutover ocorreu.

## Infraestrutura efetiva

- raiz operacional: `%LOCALAPPDATA%\ClinicaGabriela\runtime`;
- generations: `runtime\generations`;
- pointer: `runtime\operational-pointer.json`;
- histórico de pointers: `runtime\pointer-history`;
- backups: `runtime\backups`;
- evidências: `runtime\evidence`;
- runtime manifests: `runtime\runtime-manifests`.

### Generation 1

- ID: `1`;
- estado: `legacy`;
- arquivo: `generations\generation-0001-d0123c58c57f.db`;
- SHA-256: `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
- `integrity_check=ok`;
- violações de FK: `0`;
- WAL/SHM/journal: ausentes.

### Pointer operacional

- generation: `1`;
- state: `legacy`;
- database: generation 1 acima;
- schema: `backend-models-v2-credential-reset`;
- runtime manifest: `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`;
- checksum do pointer: `8320039f393fb55baaa877f3fceb80848d03237c6b16ef1d3cd342055d6161bf`;
- leitura/validação pela implementação homologada: `PASS`.

## ACL efetiva

A herança foi removida na raiz e foram concedidas somente estas regras `Allow`:

| Identidade técnica | Direito | Herança |
|---|---|---|
| usuário efetivo do runtime, identidade pessoal registrada apenas por hash de SID | `FullControl` | arquivos e subdiretórios |
| `SYSTEM` (`S-1-5-18`) | `FullControl` | arquivos e subdiretórios |
| `Administrators` (`S-1-5-32-544`) | `FullControl` | arquivos e subdiretórios |

- hash SHA-256 do SID do usuário efetivo:
  `1378bdd7a74c28fefa01b08bb5cefbf5ca77076a8616133f2a854f12c5e7d201`;
- grants genéricos de escrita: nenhum;
- fingerprint determinístico medido após o provisionamento:
  `f58389254ac21f4890d95ad00ed1039fd0820183855e90a33ea9715f7c05b5f0`;
- status do fingerprint: `MEASURED_PENDING_HUMAN_APPROVAL_FOR_CUTOVER`.

`icacls` confirmou as três regras na raiz e sua herança efetiva na generation 1 e no
pointer. Um write probe transitório do usuário efetivo passou e foi removido.

## Validações executadas

| Validação | Resultado |
|---|---|
| Primitivas de pointer, rollback, ACL e runtime antes do provisionamento | `17 passed` |
| Baseline sucessor antes/depois | `PASS`, checksum/tamanho/mtime estáveis |
| Cópia generation 1 versus baseline | `PASS`, SHA-256 idêntico |
| SQLite generation 1 | `PASS`, integridade e FKs |
| Pointer generation 1 | `PASS`, leitura e checksum |
| Runtime manifest e arquivos congelados | `PASS` |
| Resolução do runtime para generation 1 | `PASS` com `CLINICA_RUNTIME_MANIFEST_DIR` explícito |
| ACL raiz e artefatos herdados | `PASS` |
| Permissão do usuário efetivo | `PASS` |
| Sidecars da origem e generation 1 | `PASS`, zero |
| Rollback do pointer | `PASS` em cadeia isolada, terminou generation 3/state `legacy` |

A primeira invocação de provisionamento parou depois de criar a raiz vazia e aplicar
a ACL, porque o PowerShell local não oferecia `SHA256.HashData`. Nenhuma generation ou
pointer havia sido criado. A raiz vazia e sua ACL foram verificadas, e a execução foi
retomada com API de hash compatível. O executor fail-existing concluiu sem overwrite.

## Artefatos

- evidência operacional:
  `runtime\evidence\runtime-provisioning-generation-0001.json`;
- SHA-256 da evidência:
  `8d5344e0b4e7662ad379ce1f1ee1303fe222778d3850b39c748cafe6c680ad41`;
- cadeia isolada de rollback:
  `runtime\evidence\pointer-rollback-validation`;
- executor auditável:
  `scripts/spec008_runtime_provisioning.py`;
- este relatório privacy-safe.

## Preservação

`backend/data/clinica_api.db` permaneceu com:

- SHA-256 `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
- tamanho 61.440 bytes;
- `mtime` `2026-09-13T20:21:30.5809353Z`;
- nenhum WAL/SHM/journal.

O diretório `backups` foi apenas provisionado e permanece vazio, pois backup final é
etapa do cutover e estava fora desta autorização.

## Riscos residuais e próximo gate

1. O fingerprint ACL foi medido, mas ainda requer aprovação HUMAN explícita para uso
   na promoção/cutover.
2. Com o pointer no caminho padrão, o runtime congelado precisa receber
   `CLINICA_RUNTIME_MANIFEST_DIR=%LOCALAPPDATA%\ClinicaGabriela\runtime\runtime-manifests`;
   sem esse vínculo explícito, a resolução padrão procura o manifest fora da raiz.
3. O pointer real permanece generation 1/state `legacy`; a cadeia de rollback real
   somente começará quando houver SWITCH autorizado.
4. Backup final coordenado ainda não existe, por desenho; deverá ser criado e validado
   depois do maintenance lock e antes de qualquer promoção.

Próximo requisito: aprovação HUMAN do fingerprint ACL e do vínculo persistente do
diretório de runtime manifests; depois, novo GO/continuação explícita da Fase 10.

`HUMAN`
