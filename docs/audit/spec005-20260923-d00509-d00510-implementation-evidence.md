# SPEC-005 — Evidence D005-09 / D005-10

Estado: `IMPLEMENTATION_EXECUTOR_VERIFIED`. Revisão independente: `PENDING`.
E011 e E012: `NOT EXECUTED`. Nenhum candidato operacional foi criado.

## Contrato e identidade

- D005-09: quarentena persistida para legado incompatível.
- D005-10: labels R1–R6 permanecem históricos; `MAP_RECOVERY=FAILED` é preservado.
- Identidade: SHA-256 do banco + tipo + ID interno + fingerprint `spec005-row-v1`.
- Manifesto sem PII: `spec005-20260923-d00510-legacy-source-identity-manifest.json`,
  SHA-256 `b8f8d9df278ab377dcf4da8c3911338379766812346c7cec40c8fe21907c65a6`.
- Hash da fonte: `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`.

## Resultado

Classificação read-only da Generation 8: seis registros, cinco elegíveis a
`CANONICAL_MIGRATED` e payment/4 destinado a `QUARANTINED_UNRESOLVED` com
`PAID_WITH_UNKNOWN_PAID_AT`. `paid_at` não foi inferido. A migração sintética
produziu dois payments canônicos, três expenses canônicas e uma linha de
quarentena, com integridade/FKs/recovery válidos. A reconciliação compara conjuntos
disjuntos de identidades, contagens, fingerprint, origem, status, competência e
valores por registro, além dos totais exatos. A linha original fica em armazenamento
restrito para resolução futura; Evidence e manifesto não contêm seu conteúdo.

Repositórios, serviços e API normais usam `payments`/`expenses`; a quarentena
possui tabela e eventos separados, sem rota ou UI. Fixture sintética confirmou
que a linha quarantined não aparece em pagamentos nem no total canônico pago.

## Validação

- Testes D005-10 direcionados: `7 passed`.
- Regressão afetada SPEC-005/API/autoridade/migração: `38 passed`.
- Migração canônica sintética após ajuste de schema: `14 passed`.
- Suíte backend completa final: `288 passed`.
- Adversariais: identidade ausente/duplicada, fingerprint e hash de fonte
  divergentes, valor alterado e retry para destino existente: bloqueados.
- `compileall` e `git diff --check`: PASS.
- Frontend tests/build: não executados; nenhuma rota, contrato normal de API ou
  arquivo frontend foi alterado.

## Invalidação seletiva

E004: hipótese anterior de contagem/hash exclusivamente em `payments`/`expenses`
`SELECTIVELY_INVALIDATED → REVALIDATED` pela partição canônico/quarentena.
E010: provenance e privacidade dependentes de identidade
`SELECTIVELY_INVALIDATED → REVALIDATED` pelo manifesto e testes D005-10.
Evidence histórica D005-08, CASH/ACCRUAL, autorização e UI não dependentes dessa
hipótese permanecem preservadas.

## Sentinela operacional antes/depois

- Generation: `8/canonical`.
- Pointer: `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`.
- Manifest: `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`.
- Database: `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`.
- Integrity: `ok`; FK violations: `0`; sidecars: `0`; lock: ausente.
- Mutação operacional: nenhuma. Stage/commit/push: nenhum.

Próximo gate: revisão independente D005-09/D005-10. Esta Evidence não é um
parecer independente e não autoriza E011.

## Remediação após Independent Review — 2026-09-23

O parecer independente anterior foi `QUALITY_GATE_FAIL` (`BLOCKERS=0`,
`MAJORS=3`, `OBSERVATIONS=1`). Esse resultado histórico permanece válido para a
versão revisada naquela ocasião. A remediação abaixo é verificação do executor;
**não** declara Independent Review PASS.

| Alegação anterior → finding | Remediação | Revalidação do executor |
|---|---|---|
| Proveniência do manifesto aceita geração e hash do runtime autodeclarados → MAJOR-01 | Antes da classificação/carga com identidade D005-10, o migrador lê o pointer operacional, valida banco e freeze pelo mecanismo existente e exige igualdade exata de SHA do banco, geração e SHA do runtime manifest. O snapshot só é aceito se seus bytes correspondem ao banco apontado. | Manifestos com geração, runtime SHA ou database SHA falsos bloqueiam antes do candidato; fixture coerente passa. |
| Reconciliação comparava subconjunto canônico → MAJOR-02 | Projeções semânticas esperada/observada incluem todos os campos materialmente migrados dos pagamentos e despesas: identidade, vínculos, valor, estado, competência, datas, categoria e textos financeiros. Excluem timestamps gerados e eventos sem equivalente na origem. A projeção da quarentena inclui identidade, valor legado e centavos, estado, competência, motivo, proveniência, JSON original e `paid_at` desconhecido. Hashes SHA-256 das projeções e partição de identidades são comparados antes do recovery. | Mutações após carga em valor, estado, competência, data, vínculo, descrição, categoria, identidade, provenance, motivo e JSON legado são detectadas; candidato intacto passa. |
| Caminho padrão parava no freeze do working tree → MAJOR-03 | Harness subprocessado cria runtime isolado coerente com `LOCALAPPDATA` público, pointer, banco e freeze reais; remove overrides de banco/config dos testes. Percorre bootstrap normal, validação de freeze, fonte, manifesto e classificação. A barreira de produção permanece intacta. | Runtime coerente classifica 6 registros, com 1 em quarentena. Manifesto legado falso, freeze adulterado e pointer incorreto falham. O working tree real continua sujeito ao freeze operacional existente. |
| Constraints declarativas divergiam do schema criado pelo migrador → OBSERVATION-01 | Check constraints de proveniência, geração, ID, decisão e eventos foram alinhadas em `backend/models/finance.py`. | Teste compara constraints declarativas à DDL do migrador. |

Validação dirigida final: `26 passed` (D005-10, projeções, provenance, freeze e
schema). Regressão afetada final: `69 passed`. Suíte backend completa final:
`307 passed`. E004 foi revalidada somente nas hipóteses de
completude/partição/carga; E010 somente em provenance, privacidade e rastreabilidade
dependentes da identidade. Evidence histórica D005-08, CASH/ACCRUAL e UI permanecem.

E011/E012 e candidato operacional: **não executados**. Generation 8, pointer e
manifesto operacionais não foram alterados. Estado: `IMPLEMENTED / REMEDIATED /
VALIDATED_BY_IMPLEMENTATION_EXECUTOR`, sujeito a nova revisão independente.
