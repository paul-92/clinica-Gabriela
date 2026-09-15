# SPEC-008 Phase 11 — Stabilization Closure

- Execução: `spec008-phase11-backup-retry-20260915T125755Z`
- Resultado: `STABILIZATION_PASS`
- Estado de decisão: `HUMAN ACCEPTED` em 15/09/2026
- Pointer/rollback/cleanup/commit: não executados

## Estado operacional preservado

- generation ativa: `2`;
- pointer state: `canonical`;
- pointer SHA-256: `55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b`;
- Generation 2 SHA-256: `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`;
- runtime write-enabled permaneceu encerrado; o retry ocorreu em processo separado,
  exclusivo de backup, sem criar engine/pool operacional;
- conexões físicas remanescentes do pool operacional: zero conforme o shutdown/dispose
  corrigido e reproduzido na regressão da causa-raiz.

O pointer foi preservado byte a byte. Seu campo histórico
`database_checksum_sha256` continua registrando o checksum pré-marcador
`96b27238c038...`; nenhuma tentativa de atualização foi feita nesta autorização.

## Preflight e janela fail-closed

- `integrity_check=ok`;
- zero violações de FK;
- `user_version=0`;
- `journal_mode=delete`;
- WAL, SHM e journal ausentes;
- nenhum handle da Generation 2 encontrado pelo `fsutil queryProcessesUsing`, antes
  e depois da janela (com a limitação registrada de ausência de debug privilege);
- maintenance lock e lock SQLite exclusivo adquiridos com `timeout=0`;
- nenhum writer concorrente observado;
- maintenance lock liberado e nenhum staging parcial remanescente.

## Backup canônico e provenance

- diretório: `%LOCALAPPDATA%\ClinicaGabriela\runtime\backups\spec008-phase11-backup-retry-20260915T125755Z`;
- banco: `canonical_generation_2.backup.db`;
- banco SHA-256: `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`;
- manifest SHA-256: `70ba5acb0e7838629f39866720c138209ffc243c5e1127ed952fc7734aadafa1`;
- provenance SHA-256: `b0418ade215e8ea0b694b3b7892b287e59bbd79f10f8359bcd6794d3feaafdb9`.

## Restauração isolada

- artefato: `%LOCALAPPDATA%\ClinicaGabriela\runtime\evidence\spec008-phase11-backup-retry-20260915T125755Z\isolated-restore-validation.db`;
- SHA-256: `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`;
- identidade: idêntica à Generation 2 e ao backup;
- schema: idêntico;
- contagens: idênticas (`appointments=2`, `clinic_settings=1`,
  `clinical_records=2`, `expenses=3`, `patients=1`, `payments=3`,
  `psychologists=1`, `users=3`);
- `integrity_check=ok` e zero violações de FK;
- SQLite: UTF-8, page size 4096, page count 15, schema version 12,
  synchronous 2, journal mode delete e user version 0;
- sidecars inesperados: zero.

Resultado auditável SHA-256:
`aa30f7d5ec8643be1b467bf22460cc4816eb3966bfb6b5b60e874b6f8350d4ac`.

## Rollback boundary e legado

- boundary: `NO_SILENT_POINTER_ROLLBACK`;
- rollback para Generation 1 não executado e continua proibido sem decisão HUMAN;
- Generation 1 preservada, SHA-256
  `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
- backup final pré-cutover preservado, manifest SHA-256
  `922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3`;
- nenhuma limpeza de legado ou alteração de dados clínicos/financeiros foi executada.

## Riscos residuais e encerramento formal

1. A enumeração de handles do Windows permanece parcialmente limitada sem debug
   privilege; o lock SQLite exclusivo com `timeout=0` foi a prova autoritativa da
   janela livre de writer.
2. O checksum histórico gravado no pointer difere do checksum físico pós-marcador;
   o pointer deve permanecer inalterado até decisão específica.
3. O aceite final/encerramento da janela de estabilidade foi aprovado pelo HUMAN em
   15/09/2026. Qualquer política futura de retenção ou limpeza do legado permanece
   sujeita a decisão própria e não foi autorizada pelo fechamento.

`STABILIZATION_PASS`
