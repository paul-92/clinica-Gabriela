# Relatório forense read-only — `backend/data/clinica_api.db`

- Data da investigação: 2026-09-14
- Classificação: `ROOT_CAUSE_PROBABLE`
- Estado operacional: `HUMAN`
- Cutover, promoção, ponteiro, restore, rebaseline e commit: não executados

## Preservação e método

O banco investigado e o snapshot congelado não foram abertos pelo SQLite durante a
perícia. Foram lidos pelo filesystem para hash/cópia e toda consulta SQLite foi feita
com `mode=ro&immutable=1` sobre cópias transitórias em
`.forensics/spec008-db-20260914/`. As cópias binárias foram removidas após gerar a
evidência agregada, para não manter duplicatas potencialmente sensíveis no workspace;
os originais permaneceram preservados.

Fontes:

- atual: `backend/data/clinica_api.db`;
- snapshot: `%LOCALAPPDATA%/ClinicaGabriela/migration/spec008-20260911-phase1-001/backend_legacy.snapshot.db`;
- análise privacy-safe: `.forensics/spec008-db-20260914/analysis.json`.

O snapshot foi produzido pela SQLite Backup API. Seu hash físico
`baf687d642b0896149bac78cd48555ca87072cbeac5bf363d63ef59a70e3019c`
difere corretamente do hash físico da origem histórica congelada
`8f973f56654fb92f03c278f21934b976c76ba61318edd1f449dbe4584bed0aed`;
a Backup API normaliza campos físicos do destino. Portanto o snapshot é baseline
lógico validado, enquanto o hash congelado é o baseline físico da origem.

## Evidência física

| Propriedade | Snapshot congelado | Banco atual |
|---|---:|---:|
| SHA-256 | `baf687...019c` | `d0123c...e757` |
| SHA-256 histórico da origem | `8f973f...aed` | divergente |
| Tamanho | 61.440 B | 61.440 B |
| Page size | 4.096 B | 4.096 B |
| Page count/header | 15 | 15 |
| Freelist | 0 | 0 |
| Primeira trunk freelist | 0 | 0 |
| Read/write version | 1/1 (rollback journal) | 1/1 |
| `journal_mode` | `delete` | `delete` |
| `user_version` | 0 | 0 |
| `application_id` | 0 | 0 |
| Encoding | UTF-8 | UTF-8 |
| Auto-vacuum/incremental vacuum | 0/0 | 0/0 |
| Schema cookie (`schema_version`) | 1* | 19 |
| File change counter | 1* | 27 |
| Version-valid-for | 1* | 27 |

`*` Campos normalizados no arquivo de destino criado pela Backup API; não devem ser
interpretados como os valores do header da origem histórica em 2026-07-06.

Na comparação das cópias, 3.634 bytes diferem, todos na página 1. As páginas 2 a 15
são byte a byte idênticas. Isso localiza a alteração na página que contém o header e
o `sqlite_schema`, sem reescrita das páginas de dados.

O arquivo atual preserva a criação no filesystem em 2026-07-06 e tem `mtime`
`2026-09-13T20:21:30.5809353Z` (17:21:30 local). O acesso da própria perícia altera
somente o `atime`, que não é usado para inferir a causa. O File ID NTFS atual é
`0x000000000000000000960000000438a1`.

## Evidência lógica privacy-safe

- `integrity_check=ok` nos dois arquivos;
- `foreign_key_check`: zero violações nos dois;
- oito tabelas em ambos;
- contagens idênticas: `appointments=2`, `clinic_settings=1`,
  `clinical_records=2`, `expenses=2`, `patients=1`, `payments=2`,
  `psychologists=1`, `users=3`;
- projeções das colunas comuns: conteúdo agregado idêntico em todas as oito tabelas;
- diferença lógica comprovada: somente o schema de `users` ganhou a coluna
  `password_reset_required BOOLEAN NOT NULL DEFAULT 0`;
- nenhuma diferença de valores pré-existentes foi detectada.

Os digests de conteúdo foram calculados por linha e novamente agregados, sem incluir
valores, IDs ou PII no relatório.

## WAL, SHM e journal

Não há atualmente `clinica_api.db-wal`, `clinica_api.db-shm` ou
`clinica_api.db-journal`; o header persiste `journal_mode=delete`. O NTFS/SQLite não
mantém, neste diretório, histórico consultável de sidecars já removidos. Assim, a
ausência atual está comprovada, mas a inexistência passada não pode ser provada.

Nenhum processo mantinha o arquivo aberto no momento da consulta por
`fsutil file queryProcessesUsing`. Não há log de processo/PID preservado para
2026-09-13 17:21.

## Causa e caminho responsável

A alteração é exatamente o DDL introduzido nesta frente em
`backend/database/migrations.py` e executado por:

`backend.main.bootstrap_backend()` → `run_light_migrations()` →
`ALTER TABLE users ADD COLUMN password_reset_required ...`.

O `mtime` do banco (17:21) coincide no mesmo minuto com a atualização de
`.pytest_cache/v/cache/lastfailed`. A suíte importava estado global em
`backend.database.session` e alguns `finally` restauravam
`configure_database(get_runtime_settings())`. Sem um override obrigatório para toda
a sessão pytest, o fallback de `get_runtime_settings()` volta ao caminho operacional
`backend/data/clinica_api.db`; um bootstrap posterior então pode aplicar a migration.

A simulação de cutover copiava fixtures e usava ponteiro para sua raiz isolada, mas
seu helper também removia temporariamente `BACKEND_DATABASE_PATH` e
`BACKEND_DATA_DIR` do processo. O ponteiro válido evitava a fonte real na execução
nominal, porém a mutação de ambiente não era restaurada e ampliava a superfície de
contaminação em uso no mesmo processo.

O DDL, a página afetada, a diferença de schema e a janela pytest são convergentes.
Ainda assim, sem telemetria histórica de PID/comando, não é possível provar qual
invocação Python executou o DDL. Por isso a classificação conservadora é
`ROOT_CAUSE_PROBABLE`, não `ROOT_CAUSE_CONFIRMED`.

## Correções aplicadas

1. `tests/conftest.py` define, antes da coleta/importação, banco e diretório backend
   em raiz temporária exclusiva e restaura o ambiente ao encerrar.
2. `tests/test_backend_bootstrap.py` comprova que o default da suíte não é o banco
   operacional nem descendente dele.
3. `scripts/spec008_cutover_simulation.py` agora recusa banco fora da raiz da
   simulação e restaura todas as variáveis de ambiente alteradas.

Nenhuma correção tocou o banco histórico.

## Regressões

- `tests/test_backend_bootstrap.py` + `tests/test_backend_migrations.py`:
  **12 passed** em raiz temporária curta e isolada.
- Hash do banco histórico antes e depois:
  `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
  `mtime` permaneceu 2026-09-13 17:21 local e nenhum sidecar apareceu.
- Execução ampliada: 22 testes passaram e 7 falharam por um problema preexistente
  de criação de diretórios pais em helpers content-addressed; essas falhas ocorreram
  em fixtures e não alcançaram o banco histórico. Elas não invalidam a regressão de
  isolamento, mas impedem declarar a seleção ampliada totalmente verde.

## Opções HUMAN para o banco alterado

1. Preservar o arquivo atual como evidência e manter o gate bloqueado.
2. Após aprovação separada, restaurar byte-for-byte uma fonte histórica validada;
   exige decidir qual artefato é autoritativo e preservar antes o atual.
3. Após aprovação separada, aceitar formalmente a alteração como novo baseline;
   isso muda a premissa de imutabilidade e não é recomendado sem decisão registrada.
4. Manter ambos preservados e produzir um novo banco operacional somente por fluxo
   aprovado, sem sobrescrever nenhum histórico.

## Recomendação

Preservar o banco atual e o snapshot, manter cutover bloqueado e não rebaselinear.
Tratar o snapshot/manifest congelado como baseline lógico e o checksum `8f973f...`
como baseline físico da origem. Se a necessidade for recuperar a imutabilidade
histórica, executar restore apenas após aprovação HUMAN explícita, com cópia de
preservação do atual, verificação de cadeia/checksum e nova perícia pós-operação.
