# SPEC-005 / D005-09 — contrato e plano de implementação

> Emenda normativa D005-10 (2026-09-23): a recuperação do vínculo histórico
> R1–R6 falhou. A seção antiga sobre mapa por labels fica preservada como
> histórico, mas sua precondition operacional foi substituída pelo manifesto
> de identidade técnica D005-10. Nenhum label é usado como chave de migração,
> disposition ou reconciliação. Payment/4 é a linha HUMAN indicada para
> quarentena, sujeita a hash da fonte, fingerprint e invariantes.

O fingerprint `spec005-row-v1` usa SHA-256 de JSON UTF-8 compacto com
`[versão, entity_type, [[nome_campo, tipo_SQLite, valor_tipado], ...]]`, campos
ordenados pelo nome. `REAL` usa `float.hex()`; bytes usam hexadecimal; NULL,
inteiros e texto mantêm tipo explícito. Todos os campos da linha fonte entram
no hash para detectar alteração material, mas seus valores não aparecem no
manifesto nem na Evidence. O conteúdo legado necessário para resolução futura
fica restrito no candidato, em `legacy_row_json`, com teste de restore.

Estado: `HUMAN APPROVED / CONTRACT FORMALIZED`. Implementação, E011, E012 e
promoção: `NOT AUTHORIZED / NOT EXECUTED`. Este documento especifica o trabalho
futuro; não constitui Evidence de candidato.

## Contexto e limite

HEAD `c5100dd3cc347a9263c64a52a64d6bb0967b1db5` em
`feature/spec-008-architecture-foundation`, sincronizado com o upstream. A revisão
independente D005-08 passou. Generation 8/canonical permanece fonte operacional:
pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`,
manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`,
banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`.
Integridade `ok`, zero FKs, sidecars e lock ausentes. Resíduos preexistentes do
working tree são preservados.

## Contrato mínimo da quarentena

Uma tabela separada de `payments` e `expenses` guardará apenas legado incompatível.
Campos mínimos propostos para o schema futuro:

| Campo | Finalidade e regra |
|---|---|
| `id` | Identidade interna estável, sem PII, única no candidato. |
| `source_database_sha256`, `source_generation`, `source_entity_type`, `source_record_id` | Identidade da fonte; par tipo/ID único por fonte. Tipo limitado a payment/expense. |
| `source_record_sha256` | Hash de serialização canônica e versionada da linha original inteira; detecta alteração. Não publicar material bruto. |
| `legacy_status`, `legacy_amount_text`, `legacy_currency` | Estado e valor originalmente observados; texto decimal exato preserva representação. `amount_cents` só quando a conversão exata passar. |
| `competence_year`, `competence_month` | Decisão HUMAN mensal; nunca evidencia pagamento. |
| `reason_code`, `quarantined_at`, `decision_id` | Motivo fechado, instante de entrada e autoridade. |
| `source_manifest_sha256`, `mapping_sha256`, `migration_execution_id` | Proveniência e ligação à reconciliação. |
| `resolution_state` | Inicialmente `unresolved`; transição somente pela operação futura autorizada. |

O registro deve conservar, em armazenamento restrito, os campos legados **necessários**
à futura resolução, ou referência verificável a backup imutável e retido. Um hash
sozinho não recupera o conteúdo original. A escolha de retenção será concretizada
na implementação com teste de restore; nenhum dump/PII irá para Evidence, logs ou
manifestos. Eventos de quarentena serão append-only com identidade interna, ator,
ação, instante e referência à evidência; UPDATE/DELETE sem trilha são proibidos.
Não se cria API/UI administrativa nesta etapa.

R2 terá `QUARANTINED_UNRESOLVED` / `PAID_WITH_UNKNOWN_PAID_AT`, status legado
`paid`, competência `2026/7`, valor legado e fingerprint preservados. Não terá linha
em `payments` canônicos. `paid -> paid_at` permanece obrigatório. Quarentena fica
fora de CASH, ACCRUAL, receitas, KPIs, totais, repositório, API e UI normais.

## Mapa determinístico R1–R6

O artefato D005-08 contém labels e competência, mas não vincula labels a IDs.
Antes de E011, criar fora do runtime um mapa restrito com, para cada label:
`source_database_sha256`, generation, entity type, internal source ID,
`source_record_sha256`, canonicalization version e decisão de competência.
Fingerprint monetário pode reforçar a verificação, mas não substituir ID e hash da
linha. O mapa público de Evidence registra somente labels, contagens e hash do mapa
restrito. IDs internos ou hashes de linhas podem permitir correlação e portanto
ficam fora de Evidence pública.

Procedimento: ler Generation 8 por conexão SQLite read-only/immutable após validar
pointer, manifest e hash do banco; calcular hashes sobre bytes/campos completos com
serialização tipada e versionada; identificar cada linha por tipo + ID e conferir
individualmente a associação com a revisão HUMAN original. **A associação R1–R6
não pode ser deduzida por ordenação.** Se a revisão original não contiver vínculo
comprovável suficiente, obter confirmação HUMAN sobre o mapa antes de selá-lo.
Exigir bijeção: seis labels únicos, seis chaves distintas, mesma fonte, fingerprint
igual, nenhuma linha ausente ou duplicada. Qualquer divergência: `REVIEW/BLOCK`.
Essa preparação cria apenas artefato fora do runtime; não escreve no banco fonte.

## Reconciliação e resolução

Para cada tipo (`payment`, `expense`) e para o conjunto:

`SOURCE_FINANCIAL_RECORDS = CANONICAL_MIGRATED_RECORDS + QUARANTINED_LEGACY_RECORDS`.

As chaves `(source_database_sha256, entity_type, source_record_id)` formam partição
disjunta e completa. Verificar contagem, conjunto de identidades, fingerprints,
valor legado/centavos quando exatos, status observado e disposition de cada linha.
Somar valores por tipo e disposition sem incluir quarentena em totais canônicos.
R2 conta **uma vez** na quarentena e zero vezes em `payments`. A regra atual do
migrador que exige contagem/hash de IDs iguais apenas em `payments`/`expenses`
precisa ser substituída por essa reconciliação particionada; não se deve simplesmente
eliminar R2.

Resolução futura exige evidência confiável do `paid_at` real, ou nova decisão HUMAN
que altere explicitamente o contrato. Operação restrita, autorizada e transacional:
revalidar identidade/fingerprint e estado `unresolved`; registrar ator, autorização,
referência da evidência, before state, ação e instante; criar payment canônico somente
se todos os invariantes passarem; vincular sua identidade ao registro legado e
acrescentar evento de resolução. Chave de idempotência e unicidade do vínculo
impedem segunda resolução em retry. Falha reverte payment, estado e evento juntos.
O histórico original e os eventos permanecem retidos.

## Impacto e invalidação seletiva

| Área | Classificação | Mudança futura |
|---|---|---|
| Schema/migração | REQUIRED_FOR_D00509 | Tabela e constraints de quarentena; disposição por linha; sem `paid_at` inferido. |
| Reconciliação/manifest | REQUIRED_FOR_D00509 | Partição de identidades, contagens, valores e hashes; proveniência fonte/mapa/candidato. |
| Repositories/services | REQUIRED_FOR_D00509 | Isolamento de consultas canônicas e operação interna auditável; nenhuma API/UI nova. |
| Auditoria/testes/Evidence | REQUIRED_FOR_D00509 | Eventos append-only, testes negativos, Evidence sanitizada. |
| Visão administrativa de quarentena | OPTIONAL, contrato HUMAN próprio | Consulta restrita futura. |
| Pagamento parcial, outro sistema financeiro, alteração de caixa | OUT_OF_SCOPE | Nenhuma. |

**PRESERVED:** D005-08 mensal, CASH/ACCRUAL separados, `paid -> paid_at`, testes de
conversão exata, autorização, UI e regressão não dependentes da contagem de importação.
**SELECTIVELY_INVALIDATED:** suposição E004 de que toda linha financeira entra em
payments/expenses; Evidence de contagens e hashes exclusivos dessas tabelas como
prova de completude operacional. **REVALIDATION_REQUIRED:** testes de migração R2,
recovery, reconciliação particionada, isolamento de consulta, privacidade e
proveniência E010. Resultados históricos não são apagados nem rotulados como execução
de D005-09.

## DAG de implementação futuro

| Fase | Input → ação → output | Teste | Falha / retry |
|---|---|---|---|
| Q0 contrato | D005-09 + SPEC → congelar campos/códigos → contrato verificável | revisão de rastreabilidade | divergência: STOP; editar plano é seguro |
| Q1 schema | contrato → tabela, índices, constraints e eventos → schema sintético | constraints/no-delete/FK | rollback em DB sintético; repetir em DB novo |
| Q2 mapa | fonte read-only + revisão HUMAN → vínculo individual → mapa restrito | missing/duplicate/hash/source mismatch | STOP; recalcular, nunca presumir ordem |
| Q3 migração | snapshot isolado + mapa → disposition por linha → candidato sintético | R2 quarentena, outros invariantes | STOP; novo destino, fonte intacta |
| Q4 reconciliação | fonte + candidato → partição por tipo/ID/valor → prova | count/identity/money | STOP; novo destino |
| Q5 isolamento | repositórios/serviços → excluir quarentena do domínio normal | CASH/ACCRUAL/API/KPI | rollback de código; DB sintético |
| Q6 auditoria | decisões + candidato → eventos e hashes → proveniência | append-only, replay/retry | STOP se trilha incompleta |
| Q7 testes | Q1–Q6 → suíte dirigida → Evidence técnica | negativos, privacidade | corrigir e repetir |
| Q8 regressão | suíte existente → validar integração → Evidence | Python/frontend relevantes | corrigir e repetir |
| Q9 revisão | Evidence → revisão independente D005-09 → parecer | checks independentes | finding: STOP; sem E011 |

## Testes e Evidence planejados

Testes sintéticos: R2 entra uma vez em quarentena e nunca em payment; `paid_at`
continua NULL no legado e não é fabricado; CASH, ACCRUAL, receita, KPIs, API e UI
excluem quarentena; contagens, identidades, lifecycle e valores reconciliam por tipo;
mapa duplicado/ausente, fingerprint/source hash divergentes falham antes de mutação;
retries não duplicam quarentena, payment nem evento; evento é append-only;
restore e integridade/FK passam; Evidence/logs/manifests não contêm PII; sentinela
Generation 8 permanece byte a byte. Evidence futura deve conter hashes de fonte,
mapa restrito, candidato e recovery, regras/versões, contagens por disposition,
resultados e parecer independente, sem linhas clínicas/financeiras identificáveis.

**E011 permanece bloqueada** até implementação e validação de D005-09, mapa R1–R6
verificável, disposition R2 determinística, preconditions verdes e autorização HUMAN
separada. Nenhum candidato ou migration foi produzido neste plano.
