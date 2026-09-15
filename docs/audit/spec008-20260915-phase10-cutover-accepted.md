# SPEC-008 Phase 10 Cutover Report

- Execução: `spec008-phase10-20260915T004517Z`
- Resultado operacional: `CUTOVER_ACCEPTED`
- Sequência: `QUIESCE → FINAL BACKUP → REVALIDATE → PROMOTE → SWITCH → START → HEALTH → SMOKE → VERIFY`
- Cleanup/remoção/commit: não executados

## Generation e pointer

| Estado | Antes | Depois |
|---|---|---|
| Generation | `1` | `2` |
| Pointer state | `legacy` | `canonical` |
| Pointer SHA-256 | `8320039f393fb55baaa877f3fceb80848d03237c6b16ef1d3cd342055d6161bf` | `55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b` |
| Banco | `generation-0001-d0123c58c57f.db` | `canonical-verified-v2-96b27238c038.db` |
| Banco SHA-256 | `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757` | `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46` |

A troca foi feita por compare-and-swap atômico. O histórico imutável do pointer
anterior está em `runtime\pointer-history\pointer-8320039f...61bf.json`.

## Backup final

Diretório:

`%LOCALAPPDATA%\ClinicaGabriela\runtime\backups\spec008-phase10-20260915T004517Z`

- manifest: `final-backup-manifest.json`;
- SHA-256 do manifest:
  `922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3`.

| Fonte preservada | SHA-256 do backup | Integridade | FKs |
|---|---|---|---:|
| Generation 1 | `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757` | `ok` | 0 |
| Backend legado | `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757` | `ok` | 0 |
| Desktop legado | `5aa6a8d22ecbf9b8f6d4574ae49a2c611ab089aa933132ea47dd5e1c451d793b` | `ok` | 0 |

O backup foi concluído e validado sob maintenance lock antes da promoção.

## Promoção

- candidato protegido: `canonical-candidate-v1.db`, lifecycle `verified-v2`;
- checksum esperado/observado:
  `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46`;
- destino content-addressed:
  `%LOCALAPPDATA%\ClinicaGabriela\runtime\generations\canonical-verified-v2-96b27238c038.db`;
- mecanismo: cópia, fsync, checksum, validação SQLite e publicação atômica
  fail-existing;
- candidato protegido original: inalterado.

## Runtime, health e smoke

O runtime congelado `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`
foi iniciado em modo de verificação estritamente read-only, com o binding HUMAN
aprovado de `CLINICA_RUNTIME_MANIFEST_DIR`.

| Verificação | Resultado |
|---|---|
| Startup/lifespan real da aplicação | `PASS` |
| Caminho efetivamente aberto | generation 2 promovida |
| `GET /health` | `PASS` |
| GETs críticos: pacientes, psicólogos, agenda, prontuários, financeiro e settings | `PASS` |
| Guard de writes | `PASS`, POST recebeu `503` |
| Autenticação de credenciais migradas | `PASS`, bloqueada |
| `password_reset_required` | `PASS`, obrigatório em todos os usuários migrados |
| Credencial desabilitada | `PASS` |
| Checksum antes/depois do smoke | `PASS`, inalterado |
| SQLite promovido | `integrity_check=ok`, zero FKs, zero sidecars |

O runtime de verificação foi encerrado de forma controlada após VERIFY. Writes
canônicos não foram habilitados nesta execução.

## Writers, sidecars e legado

- portas 8000, 8765 e 5173: sem listeners após VERIFY;
- `fsutil queryProcessesUsing`: nenhum processo encontrado usando Generation 1,
  generation 2 ou os dois bancos legados;
- limitação: Windows informou ausência de debug privilege para exibir alguns caminhos
  de imagem; locks SQLite exclusivos foram a barreira autoritativa durante a janela;
- WAL/SHM/journal: ausentes em generation 1, generation 2 e legados;
- Generation 1: preservada e checksum inalterado;
- backend e desktop legados: preservados e checksums inalterados;
- dual-write: não ocorreu;
- banco legado: não removido nem sobrescrito.

## ACL

- raiz runtime, aprovado/observado:
  `f58389254ac21f4890d95ad00ed1039fd0820183855e90a33ea9715f7c05b5f0`;
- destino generations, aprovado/observado:
  `5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91`.

## Rollback

Rollback permanece disponível e não foi necessário. Estão preservados:

- pointer generation 1 no histórico content-addressed;
- Generation 1 original;
- três backups finais verificados;
- mecanismo CAS de rollback homologado;
- legados sem alteração.

## Evidências

- evidência operacional:
  `%LOCALAPPDATA%\ClinicaGabriela\runtime\evidence\spec008-phase10-20260915T004517Z-cutover.json`;
- SHA-256:
  `1ca7e601cb3ca182d448c9c0319a1ae221941638211a40bf0808c8d846b985f2`;
- backup manifest SHA-256:
  `922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3`;
- executor:
  `scripts/spec008_phase10_cutover.py`;
- decisões HUMAN, relatórios de readiness, homologação, forensic report e provenance
  anteriores permanecem preservados.

## Incidentes e riscos residuais

Não houve incidente durante a execução aceita. A tentativa anterior foi bloqueada
antes de qualquer mutação pela diferença de fingerprint do diretório de promoção; a
aprovação HUMAN específica resolveu esse gate.

Riscos residuais:

1. o runtime não permanece iniciado após o smoke controlado;
2. writes canônicos ainda não foram exercitados em produção;
3. o binding `CLINICA_RUNTIME_MANIFEST_DIR` precisa ser aplicado a todo launcher ou
   serviço operacional futuro;
4. a limitação de visibilidade de processos sem debug privilege permanece;
5. rollback após qualquer write canônico exige reconciliação/forward recovery, não
   rollback cego ao legado.

## Próximo gate

Fase 11 — pós-cutover: decisão HUMAN para iniciar o runtime operacional write-enabled
com o binding aprovado, seguida de backup inicial do canônico, monitoramento,
validações de persistência e estabilidade, preservando legados e rollback window.

`CUTOVER_ACCEPTED`
