# Cutover Readiness Gate — baseline sucessor — SPEC-008

- Data: 2026-09-14
- Classificação final: `READY_FOR_HUMAN_CUTOVER_DECISION`
- Cutover: `NOT_AUTHORIZED_NOT_EXECUTED`
- Promoção, troca de ponteiro e desativação do legado: não executadas
- Commit: não executado

## Decisão humana e cadeia histórica

A decisão HUMAN está registrada em
`spec008-20260914-successor-baseline-human-decision.json`, SHA-256
`9c31ecf7ab3b29377f9e18c2e039d326584a0c4e18df3c757f9e0b7921be3621`, com
checksum sidecar. Ela reconhece o estado físico atual como baseline sucessor
conhecido sem substituir ou apagar o baseline original.

| Papel | SHA-256 | Estado |
|---|---|---|
| Baseline físico original | `8f973f56654fb92f03c278f21934b976c76ba61318edd1f449dbe4584bed0aed` | preservado |
| Baseline físico sucessor | `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757` | reconhecido por decisão HUMAN |

A provenance registra a relação causal como inclusão provável, por execução não
autorizada do DDL, de `users.password_reset_required BOOLEAN NOT NULL DEFAULT 0`.
O incidente permanece identificado como `spec008-db-20260914`, a mutação original
permanece não autorizada e a classificação forense permanece
`ROOT_CAUSE_PROBABLE`. O relatório
`spec008-20260914-read-only-forensic-report.md` continua sendo a evidência forense
vinculante. A decisão não reclassifica nem altera sua conclusão.

## Revalidação mínima do gate

Somente as verificações necessárias para remover o bloqueio do baseline e confirmar
que os gates técnicos já aprovados continuam válidos foram repetidas.

| Gate | Resultado | Evidência |
|---|---|---|
| Baseline sucessor físico | `PASS` | checksum esperado, 61.440 bytes e `mtime` `2026-09-13T20:21:30.5809353Z` antes/depois |
| SQLite do baseline sucessor | `PASS` | conexão `mode=ro&immutable=1`; `integrity_check=ok`; zero FKs; coluna esperada presente |
| Sidecars operacionais | `PASS` | WAL, SHM e journal ausentes antes/depois |
| Isolamento/bootstrap/migration/cutover guards | `PASS` | `30 passed in 3.89s`, raiz temporária curta e não operacional |
| Candidato congelado | `PASS` | SHA-256 `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46` |
| Simulação aprovada | `PASS` | evidência SHA-256 `7deb142d8ad764ee3d43cb509c8252ca51129e2951c01f9eaab092a17b1ab5d6`; nominal e rollback `PASS`; cutover `false` |
| Runtime da simulação | `PASS` | manifest `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`, recuperado byte-idêntico da raiz isolada e preservado em `docs/audit` |
| Evidências anteriores de não regressão | `PASS/REUSED` | `194 passed`, frontend `5 passed`, build Vite e simulações já aprovados; não repetidos por não haver mudança de produto |

Duas tentativas iniciais da seleção direcionada foram inválidas antes dos testes por
raiz `--basetemp` inexistente/inacessível no sandbox. Elas produziram 6 aprovações e
24 erros de setup, sem falha de produto e sem abertura write-capable do banco
operacional. A execução válida fora do sandbox, em `C:\tmp`, aprovou os 30 casos.

## Sentinela final

Observação final em `2026-09-14T20:39:57.3681775-03:00`:

- SHA-256: `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
- tamanho: 61.440 bytes;
- `mtime`: `2026-09-13T20:21:30.5809353Z`;
- WAL/SHM/journal: ausentes.

Não houve restauração, normalização, escrita, substituição ou qualquer modificação do
banco operacional para registrar a decisão ou executar este gate.

## Resultado

O único bloqueio do preflight anterior — ausência de decisão HUMAN sobre a divergência
física histórica — foi resolvido pela aceitação explícita do baseline sucessor. Todos
os gates técnicos e de evidência permanecem satisfeitos. A próxima ação é uma decisão
HUMAN separada de GO/NO-GO da Fase 10.

`READY_FOR_HUMAN_CUTOVER_DECISION`

Este estado não autoriza nem executa cutover, promoção, troca do ponteiro operacional,
desativação do legado, liberação de writes ou commit.
