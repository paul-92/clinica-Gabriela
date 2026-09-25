# SPEC-005 D005-11 — Evidence do executor

Decisão HUMAN: `spec005-20260924-d00511-human-decision.json`. O diagnóstico do
freeze concluiu que o manifest operacional da Generation 8 descreve a baseline
SPEC-004 e que 20/128 arquivos locais divergem por evolução SPEC-005. O blocker
da Independent Re-review e os findings anteriores permanecem no histórico.

## Contrato implementado

- Fonte: `verify_source` lê pointer operacional, verifica seu hash esperado,
  Generation 8/canonical, banco apontado/snapshot SHA, schema do pointer,
  `integrity_check`, FK, ausência de sidecars/lock e o runtime manifest contra
  uma baseline histórica explícita. Não verifica o código migrador como se fosse
  código operacional antigo.
- Migrador: `spec005-migration-execution-v1`, contrato
  `SPEC-005/D005-09+D005-10+D005-11`. Manifest canônico JSON UTF-8, chaves
  ordenadas, separadores compactos e LF final; hashes dos bytes reais. AST fecha
  imports Python locais e packages a partir dos entrypoints de execução,
  migração e preflight. São 29 arquivos, incluindo config, runtime/freeze,
  migração, identidade D005-10, package imports, models e scripts importados.
  Dependência obrigatória ausente falha. BUILD exclusivo; VERIFY recalcula
  closure e bytes, sem regravar.
- Manifest atual proposto: `spec005-20260924-d00511-migration-execution-manifest-v4.json`,
  SHA-256 `33de0cbaeb3b4e96552af1495303d27a31a04a3c21d876404337b05ad7528cff`.
  Os builds anteriores sem sufixo, v2 e v3 foram preservados como drafts superados
  pela integração do preflight e do bloqueio E011 no CLI; não são baselines
  para E011.
- Binding: hash canônico da identidade da fonte, SHA do manifest migrador,
  contrato SPEC-005 e D005-09/D005-10/D005-11. O CLI exige checkpoint externo
  com SHA fornecido separadamente e compara as três identidades. Um checkpoint
  proposto não substitui revisão independente nem autorização E011.
- `scripts/spec005_candidate_migration.py` exige preflight D005-11 quando recebe
  manifesto legado e termina bloqueado mesmo após preflight enquanto a revisão
  independente D005-11 e autorização HUMAN E011 estiverem pendentes. O migrador
  aceita baseline histórica explícita e repete a verificação do freeze antes de
  qualquer criação de candidato futura.

## Validação

- D005-11 sintético: 4 testes PASS. Fonte, migração e binding coerentes passam;
  alterações em arquivo principal/dependência, arquivo ausente, dependência
  obrigatória inesperada, path/hash/contrato/bytes do manifest alterados, fonte
  ou código divergente bloqueiam. Documentação alheia ao inventário não altera
  identidade. Baseline histórica explícita passa com current code root inválido.
- D005-10 + D005-11 após integração: 31 passed.
- Regressão afetada antes da integração final: 73 passed.
- Suíte backend final: 312 passed. Frontend não executado, sem mudança causal.
- Manifest v4 BUILD e VERIFY: PASS, 29 arquivos. Nenhum commit/working tree
  global clean é requisito do verificador.

## Harness operacional e risco residual

O probe read-only reproduziu o pointer e o manifest ativo e tentou montar uma
baseline histórica temporária: cada arquivo candidato foi aceito somente se seu
SHA-256 de bytes coincidisse com a entrada operacional. A reconstrução parou
em `app/views/main_view.py`: o blob do commit de origem e conversões uniformes
de EOL não reproduzem os bytes congelados, que têm mistura histórica de finais
de linha. O probe falhou fechado; não foi inferido `SOURCE_IDENTITY_PASS` real
nem criado binding real. Uma cópia histórica íntegra desses bytes, ou outro
método verificável de reconstrução exata, é pré-condição pendente. Não se deve
atualizar ou relaxar o manifest ativo para resolver isso.

## Sentinela antes/depois

Generation 8/canonical. Pointer
`d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`;
runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`;
banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`.
`integrity_check=ok`; FK=0; sidecars=0; lock ausente. Nenhuma mutação
operacional. E011/E012 e promoção não executados. A revisão independente D005-11
permanece pendente; E011 suspensa.

`STATUS=IMPLEMENTED_AND_SYNTHETICALLY_VALIDATED / REAL_SOURCE_BASELINE_BLOCKED`
