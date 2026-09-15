# SPEC-008 Phase 11 — Database Lock Investigation

- Data: 2026-09-15
- Classificação: `ROOT_CAUSE_CONFIRMED`
- Generation 2/pointer: preservados
- Investigação em produção: estritamente read-only
- Reprodução/correção: somente fixtures isoladas
- Backup/restore/rollback/commit: não executados

## Causa confirmada

A falha não ocorreu no `create_final_backup` nem na aquisição do maintenance lock.
Ela ocorreu antes, dentro de `_start_write_enabled`, nesta instrução:

`PRAGMA journal_mode=DELETE`

O executor executava a sequência técnica WAL enquanto o contexto `TestClient` e o
engine SQLAlchemy do runtime write-enabled ainda estavam ativos:

1. startup e requests abriam conexões pelo `QueuePool`;
2. `PRAGMA journal_mode=WAL` e o marcador técnico eram executados por `sqlite3`;
3. o checkpoint era concluído;
4. ainda dentro do lifespan, outra conexão `sqlite3` tentava mudar para `DELETE`;
5. a mudança de journal mode exigia lock exclusivo e disputava com handles mantidos
   pelo pool do runtime;
6. SQLite retornava `OperationalError: database is locked`.

A reprodução isolada gerou traceback exato em
`scripts/spec008_phase11_stabilization.py`, na antiga linha da transição para
`journal_mode=DELETE`. A mesma sequência, movida para depois do shutdown/dispose,
não reproduziu a falha e permitiu adquirir imediatamente o lock de backup.

Componente responsável: executor de estabilização
`scripts/spec008_phase11_stabilization.py`, especificamente a ordem de lifecycle;
as primitivas `acquire_maintenance_lock` e `create_final_backup` não chegaram a ser
executadas na tentativa original.

## Locks, pools e timeouts

- lock disputado: lock exclusivo necessário para alterar persistentemente o journal
  mode de WAL para DELETE;
- estágio: finalização da escrita técnica, ainda dentro do lifespan write-enabled;
- runtime/health/smoke: mantinham o engine vivo; não foi comprovada sessão checked-out
  pendente, mas o pool ainda podia manter conexões físicas ociosas abertas;
- reprodução corrigida após shutdown: `Connections in pool: 0`,
  `Current Checked out connections: 0`;
- `sqlite3.connect` original e SQLAlchemy sem override usam timeout padrão de 5.000 ms;
- lock de maintenance/backup usa deliberadamente `timeout=0`, fail-closed;
- helper técnico corrigido também usa `timeout=0`, para não mascarar writer concorrente.

Não há evidência de processo externo responsável. `fsutil queryProcessesUsing` não
encontrou processo usando a Generation 2 após a falha; há limitação conhecida de
visibilidade de nomes sem debug privilege. A reprodução determinística no mesmo
processo confirma que um processo externo não é necessário para produzir o erro.

## WAL/checkpoint e estado preservado

Na tentativa original, o marcador técnico completou `0 → 1101 → 0`, o checkpoint
foi efetivado e o arquivo retornou a `journal_mode=delete` antes da exceção observada.
Não restaram WAL, SHM ou journal.

Estado atual da Generation 2:

- SHA-256 `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`;
- `mtime` `2026-09-15T01:00:05.2483535Z`;
- `integrity_check=ok`;
- zero violações de FK;
- `user_version=0`;
- `journal_mode=delete`;
- zero sidecars;
- nenhum handle observável;
- pointer generation 2/canonical SHA-256
  `55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b`.

Generation 1 mantém SHA-256
`d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`.
O backup pré-cutover mantém manifest SHA-256
`922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3`.

## Correção

A ordem foi alterada para:

`runtime write-enabled → health/smoke → shutdown/dispose → WAL técnico → persistência → checkpoint → DELETE → maintenance lock → backup`

O helper `_technical_persistence_after_shutdown` agora:

- só é chamado após sair do `TestClient`;
- usa `timeout=0`;
- valida persistência do marcador técnico;
- exige checkpoint `[0,0,0]`;
- exige retorno a `journal_mode=delete`;
- exige ausência de sidecars antes de liberar a etapa de backup.

Nenhuma correção foi aplicada ao banco operacional, pointer ou runtime provisionado.

## Testes

Comando direcionado em raiz temporária isolada:

`pytest tests/test_phase11_lock_lifecycle.py tests/test_cutover_infrastructure.py`

Resultado: `13 passed in 1.57s`.

Regressões adicionadas:

1. sessão SQLAlchemy fechada + `engine.dispose()` → persistência técnica → checkpoint
   → zero sidecars → lock exclusivo → backup íntegro/restaurável;
2. writer concorrente com `BEGIN IMMEDIATE` → falha `database is locked` imediata,
   sem corrupção, FK inválida ou marcador parcial.

Reprodução integrada corrigida em cópia isolada:

- resultado: `NO_REPRODUCTION`;
- startup/health/smoke: `PASS`;
- pool após shutdown: zero conexões e zero checked-out;
- `busy_timeout=0` no helper corrigido;
- checkpoint `[0,0,0]`;
- sidecars: zero;
- janela de backup exclusiva: `PASS`.

## Readiness e riscos residuais

`READY_TO_RETRY_CANONICAL_BACKUP = true`

Essa classificação autoriza apenas concluir tecnicamente que a causa foi corrigida em
fixtures. Ela não repete nem autoriza por si só o backup canônico real.

Riscos residuais:

1. Generation 2 já contém escrita física pós-cutover; rollback cego continua proibido;
2. o primeiro backup canônico pós-cutover continua ausente;
3. a próxima janela deve revalidar zero handles/sidecars e adquirir maintenance lock
   com `timeout=0` antes do backup;
4. se o lock reaparecer em produção, deve falhar fechado e voltar a HUMAN;
5. visibilidade de processos do Windows permanece parcialmente limitada sem debug
   privilege.

Próximo requisito: autorização HUMAN separada para repetir exclusivamente a janela de
backup canônico e restauração isolada, sem repetir o marcador técnico e sem alterar o
pointer.

`ROOT_CAUSE_CONFIRMED`
