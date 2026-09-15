# SPEC-008 Fase 10 — Production Cutover Attempt

- Data: 2026-09-14
- Autorização: `HUMAN DECISION — SPEC-008 PHASE 10 PRODUCTION CUTOVER: GO`
- Resultado: `BLOCKED`
- Bloqueio: preflight fail-closed, antes da primeira mutação
- Maintenance lock, backup, promoção, switch e startup: não executados
- Commit: não executado

## Divergência material

O fingerprint HUMAN aprovado corresponde ao caminho:

`%LOCALAPPDATA%\ClinicaGabriela\runtime`

- fingerprint aprovado/observado na raiz:
  `f58389254ac21f4890d95ad00ed1039fd0820183855e90a33ea9715f7c05b5f0`.

O mecanismo `promote_candidate` valida a ACL do diretório de destino exato. Pela
separação de generations provisionada, esse destino é:

`%LOCALAPPDATA%\ClinicaGabriela\runtime\generations`

- fingerprint observado no destino exato:
  `5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91`.

As regras efetivas aparecem herdadas da raiz, mas o algoritmo homologado calcula o
fingerprint sobre a saída de `icacls`, que inclui o caminho e marcadores de herança.
Logo os fingerprints não são idênticos. A decisão HUMAN determina que nenhuma
equivalência seja inferida. Passar o fingerprint da raiz para o destino faria a
primitiva falhar; autoaprovar o fingerprint do destino violaria o gate.

## Estado preservado

- generation antes/depois: generation 1, state `legacy`;
- arquivo: `generation-0001-d0123c58c57f.db`;
- checksum: `d0123c58c57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`;
- pointer antes/depois: generation 1/state `legacy`;
- pointer SHA-256:
  `8320039f393fb55baaa877f3fceb80848d03237c6b16ef1d3cd342055d6161bf`;
- backup final: `NOT_CREATED`;
- candidato promovido: `NONE`;
- runtime iniciado: `NO`;
- health/smoke pós-cutover: `NOT_EXECUTED`;
- rollback: `NOT_REQUIRED`, pois não houve promoção ou switch;
- legado e banco-fonte: preservados;
- cutover/dual-write: não ocorreram.

## Próximo gate

Requer decisão HUMAN específica para o diretório exato de promoção, aprovando ou
rejeitando o fingerprint:

`5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91`

Alternativamente, o algoritmo de fingerprint pode ser redesenhado para medir somente
a semântica normalizada da ACL, mas isso alteraria infraestrutura/runtime congelados,
exigiria nova homologação e não pode ser feito nesta janela.

`BLOCKED`
