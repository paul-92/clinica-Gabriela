# SPEC-008 Final Closure Report

- Data do aceite: 2026-09-15
- Autoridade: `HUMAN`
- Estado final: `SPEC-008 = ACCEPTED / DONE`
- Classificação de fechamento: `SPEC-008 CLOSED — ACCEPTED/DONE`
- Escopo do relatório: privacy-safe; sem PII, conteúdo clínico, credenciais ou IDs reais
- Commit, limpeza, nova migração e alteração do estado canônico: não executados

## 1. Resultado executivo

A SPEC-008 atingiu seu objetivo técnico: existe uma única fonte operacional canônica,
Generation 2, consumida pelo backend; o caminho desktop legado está bloqueado após a
promoção; não existe dual-write; a migração e as contagens foram validadas; o cutover
foi aceito; e o primeiro backup canônico pós-cutover foi restaurado e validado em
ambiente isolado.

Não há pendência funcional ou técnica pertencente ao escopo aprovado da SPEC-008.
Retenção, observabilidade operacional contínua, manutenção e eventual descarte futuro
são atividades posteriores e não reabrem este aceite.

## 2. Fases e resultados

| Fase | Resultado final | Evidência consolidada |
|---|---|---|
| 1 — inventário e proveniência | `PASS` | inventários privacy-safe, snapshots e cadeia de proveniência produzidos |
| 2 — freeze/reconciliação | `PASS` | freeze vinculante e regras congeladas |
| 3 — dry-run | `PASS` | execução isolada, contagens explicadas e gates avaliados |
| 4 — review/remap | `PASS / HUMAN APPROVED` | RemapManifest `verified-v2` e transição aprovada pelo HUMAN |
| 5–8 — construção, migração transacional e validação | `PASS` | candidato canônico, schema, integridade, FKs, segurança e rollback pré-write validados |
| 9 — homologação | `PASS / VERIFIED-V2` | BLOCK inicial corrigido; fluxos críticos e candidato homologados |
| 10 — cutover | `CUTOVER_ACCEPTED` | promoção versionada, pointer Generation 2/canonical e smoke read-only aceitos |
| 11 — estabilização | `STABILIZATION_PASS` | lifecycle corrigido, backup canônico e restauração isolada aprovados |

## 3. Decisões HUMAN principais

O HUMAN aprovou explicitamente:

- contrato de execução, freeze e transição do RemapManifest para `approved`;
- baseline sucessor conhecido, preservando a baseline histórica e a classificação
  forense correspondente;
- raiz de runtime, binding do runtime manifest e fingerprints ACL exatos;
- diretório exato de promoção e retomada do cutover;
- cutover real, promoção da Generation 2 e pointer canônico;
- boundary após a primeira escrita canônica, proibindo rollback silencioso;
- investigação read-only da falha de lock e retry exclusivo do backup/restauração;
- `STABILIZATION_PASS`, janela pós-cutover e encerramento técnico da SPEC-008;
- política de retenção não destrutiva registrada neste fechamento.

## 4. BLOCKs relevantes e resoluções

| BLOCK/condição | Resolução |
|---|---|
| Imutabilidade histórica e alteração física do baseline | investigação forense; baseline histórico preservado; baseline sucessor explicitamente aceito pelo HUMAN |
| Infraestrutura de cutover incompleta | maintenance lock, backup coordenado, promoção versionada, pointer persistente, runtime congelado e guards implementados/testados |
| Homologação inicial bloqueada | falhas corrigidas; candidato `verified-v2` revalidado e homologado |
| ACL/destino de promoção não aprovados | raiz e diretório `runtime/generations` aprovados por fingerprint exato pelo HUMAN |
| Tentativas de cutover interrompidas antes da mutação | execução permaneceu fail-closed; preconditions corrigidas e cutover posterior aceito |
| Lock na Fase 11 | causa-raiz confirmada no lifecycle do pool/journal; shutdown/dispose movido antes da operação técnica; regressões passaram |
| Primeiro backup canônico ausente | retry HUMAN aprovado adquiriu lock exclusivo com `timeout=0`, criou backup completo e validou restauração isolada |

Nenhum BLOCK material permanece aberto no escopo da SPEC-008.

## 5. Estado canônico final

- Generation ativa: `2 / canonical`;
- pointer SHA-256:
  `55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b`;
- Generation 2 SHA-256:
  `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`;
- `integrity_check=ok`;
- violações de FK: `0`;
- `user_version=0`;
- journal final: `delete`;
- sidecars pendentes: zero;
- dual-write: desabilitado;
- desktop legado: bloqueado pelo guard canônico;
- rollback boundary: `NO_SILENT_POINTER_ROLLBACK`.

O pointer mantém intencionalmente em seu conteúdo o checksum físico anterior ao
marcador técnico. O arquivo do pointer permanece byte a byte inalterado e não deve ser
modificado apenas para alinhar checksums. Essa divergência conhecida é parte do estado
aceito, não um gate de fechamento.

## 6. Backups e capacidade de recuperação

Primeiro backup canônico pós-cutover:

- execução: `spec008-phase11-backup-retry-20260915T125755Z`;
- banco SHA-256:
  `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`;
- manifest SHA-256:
  `70ba5acb0e7838629f39866720c138209ffc243c5e1127ed952fc7734aadafa1`;
- provenance SHA-256:
  `b0418ade215e8ea0b694b3b7892b287e59bbd79f10f8359bcd6794d3feaafdb9`;
- restauração isolada: `PASS`;
- checksum, schema, contagens e configurações SQLite: idênticos ao contrato;
- restauração: `integrity_check=ok`, zero violações de FK e zero sidecars.

O backup final pré-cutover permanece preservado, com manifest SHA-256
`922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3`.
Generation 1 permanece preservada, SHA-256
`d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`.

Esses artefatos mantêm capacidade de auditoria e recuperação. Qualquer rollback após
escritas canônicas exige decisão HUMAN própria e não pode ser silencioso.

## 7. Riscos residuais aceitos

1. A enumeração de handles do Windows é parcialmente limitada sem debug privilege.
   O risco foi mitigado pela aquisição autoritativa do lock SQLite exclusivo,
   fail-closed e com `timeout=0`, além da ausência observável de handles/sidecars.
2. O checksum físico registrado historicamente dentro do pointer difere do checksum
   físico pós-marcador da Generation 2. O pointer foi deliberadamente preservado.
3. Generation 1 e os bancos legados continuam presentes para retenção e recuperação,
   mas permanecem fora do caminho operacional; controles devem impedir reativação ou
   escrita acidental.
4. Monitoramento contínuo, testes periódicos de restore e revisão de retenção passam a
   ser responsabilidades operacionais.

O HUMAN aceita esses riscos residuais no encerramento técnico.

## 8. Política de retenção

Este fechamento não autoriza limpeza destrutiva. Devem ser preservados:

- Generation 1 e banco(s) legado(s);
- backup final pré-cutover e primeiro backup canônico pós-cutover;
- snapshots e freezes;
- RemapManifests e Review Ledgers;
- manifests e provenance;
- relatórios forenses, de homologação, cutover e estabilização;
- demais evidências necessárias para auditoria e recuperação.

Remoção, arquivamento definitivo ou mudança dessa política requer decisão e atividade
próprias, fora da SPEC-008.

## 9. Itens transferidos para operação/manutenção futura

Os seguintes itens são deliberadamente posteriores e não constituem pendência da SPEC:

- monitoramento contínuo de startup, banco, constraints, latência e fluxos críticos;
- testes periódicos de backup e restauração;
- gestão de capacidade, retenção, arquivamento e disaster recovery;
- eventual melhoria da visibilidade de handles/processos no Windows;
- decisão específica sobre alinhamento futuro dos metadados históricos do pointer;
- eventual desativação física/remoção do legado mediante autorização própria;
- manutenção evolutiva do schema, frontend, API e runtime canônico.

## 10. Aceite final

O HUMAN aprovou formalmente a janela de estabilidade pós-cutover e o encerramento
técnico. Todas as condições do escopo foram atendidas, ou foram explicitamente aceitas
como risco residual/atividade operacional futura.

`SPEC-008 = ACCEPTED / DONE`

`SPEC-008 CLOSED — ACCEPTED/DONE`
