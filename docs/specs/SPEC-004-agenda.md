# SPEC-004 — Agenda e Gestão de Atendimentos

**Status:** BASELINE FUNCTIONAL APPROVED — READY FOR ORCHESTRATED IMPLEMENTATION

**Prioridade:** P1

**Dependências:** contratos aceitos da SPEC-002 e SPEC-003; infraestrutura operacional aceita da SPEC-008

**Implementação:** não iniciada

**Autoridade:** HUMAN/Product Owner

**Data do gate:** 2026-09-16

## 1. Objetivo e autoridade

Definir o contrato vinculante de agendamento, conflito, duração, remarcação,
cancelamento, falta, realização, autorização, concorrência e rastreabilidade no backend
único. A interface auxilia; o backend é a autoridade final.

Este gate aprova requisitos e plano. Não autoriza implementação, migration, alteração do
banco operacional, Generation, pointer, runtime, promoção, cleanup, push, merge ou
release. `HUMAN é autoridade, não orquestrador.`

## 2. Contratos herdados e invariantes

A execução reutiliza, sem duplicar, autenticação/autorização da SPEC-002; referências
ativas e coerentes, FKs, rollback, erros sanitizados, PATCH, ETag/If-Match e versionamento
da SPEC-003; e manifests, migrations forward-only, backup, recovery, pointer e guards da
SPEC-008.

- `409 = DOMAIN_CONFLICT`;
- `412 = PRECONDITION / OPTIMISTIC CONCURRENCY FAILURE`;
- `422 = INVALID PAYLOAD / DOMAIN VALUE`;
- `NO_SILENT_POINTER_ROLLBACK`;
- `NO_AUTOMATIC_DELETION`;
- nenhum dado real de paciente em teste ou Evidence;
- nenhum requisito é implementado sem verifier e Evidence;
- dado histórico desconhecido não é inferido ou corrigido silenciosamente.

## 3. Decisões HUMAN vinculantes

### D1 — Duração

A duração padrão é 50 minutos. Duração diferente é permitida quando informada
explicitamente e deve ser inteira e positiva. Não criar expediente, intervalo obrigatório
ou buffer automático.

### D2 — Estados canônicos

Os estados são `scheduled`, `done`, `canceled` e `no_show`. `rescheduled` não é estado
terminal canônico. Valor fora do conjunto é `422`.

### D3 — Remarcação

Remarcar preserva o original e cria sucessor relacionado, atomicamente. O evento registra
autoria, instante, motivo e relação original/sucessor. O horário histórico nunca é
sobrescrito silenciosamente.

### D4 — Correção excepcional

Estados encerrados não reabrem no fluxo normal. Correção excepcional é exclusiva de admin
autorizado, exige motivo e evento append-only e não apaga histórico.

### D5 — Autorização

Aplicar least privilege no backend conforme seção 7. O frontend não é autoridade de
segurança.

### D6 — Retroatividade, expediente e intervalos

Não impor expediente, intervalo ou buffer artificial. Agendamento retroativo somente
quando autorizado pelo contrato operacional, com autoria, instante e motivo auditáveis.
Até existir autorização operacional explícita, nova reserva retroativa é rejeitada com
`409`, sem impedir leitura ou preservação do histórico.

### D7 — Timezone

O timezone da clínica é configuração explícita. Novos instantes têm interpretação
inequívoca nesse timezone. Timestamps históricos não são convertidos silenciosamente.
Legado cuja semântica temporal não possa ser demonstrada é preservado e classificado como
temporalmente não verificado.

## 4. Intervalos, conflitos e ocupação

O intervalo é semiaberto `[início, fim)`, com `fim = início + duração`:

```text
novo_inicio < existente_fim
AND novo_fim > existente_inicio
```

- conflito é avaliado para o mesmo profissional;
- profissionais diferentes podem atender simultaneamente;
- intervalos adjacentes são permitidos;
- edição ignora o próprio registro e revalida profissional, início e duração;
- remarcação valida o horário e profissional do sucessor;
- referência inexistente retorna `404`;
- referência inativa/inapta ou conflito retorna `409`;
- data, duração, status ou timezone inválido retorna `422`.

| Estado | Ocupa horário | Efeito |
|---|---:|---|
| `scheduled` | Sim | reserva ativa |
| `done` | Sim | preserva fato realizado |
| `no_show` | Sim | preserva fato e impede reuso retroativo |
| `canceled` | Não | preserva registro e libera horário |

Na remarcação, o original recebe `canceled` com evento `rescheduled` e o sucessor é criado
como `scheduled` na mesma transação. O evento distingue cancelamento de remarcação.

## 5. Matriz definitiva de transições

| Origem | Destino/ação | Permitido | Condição |
|---|---|---:|---|
| novo | `scheduled` | Sim | referências válidas, intervalo válido e livre |
| `scheduled` | `done` | Sim | admin ou psicólogo responsável |
| `scheduled` | `no_show` | Sim | admin, psicólogo responsável ou recepção |
| `scheduled` | `canceled` | Sim | admin, recepção ou psicólogo responsável |
| `scheduled` | remarcar | Sim | cria sucessor; ator autorizado |
| `scheduled` | editar reserva | Sim | versão atual e nova validação |
| `done` | fluxo normal | Não | encerrado |
| `no_show` | fluxo normal | Não | encerrado |
| `canceled` | fluxo normal | Não | encerrado |
| encerrado | correção excepcional | Somente admin | motivo e evento append-only |

Transição inválida é `409`. Versão obsoleta é `412`, mesmo se uma releitura também puder
revelar conflito de domínio.

## 6. Remarcação, histórico e auditoria

A operação de remarcação deve, em uma transação:

1. carregar o original sob `If-Match`;
2. autorizar o ator e validar referências, timezone, duração e conflito;
3. criar o sucessor relacionado;
4. marcar o original como `canceled`;
5. registrar evento append-only com tipo, IDs, ator, instante e motivo;
6. confirmar tudo ou reverter tudo.

Falha deixa original, sucessor e histórico inalterados. Motivo não deve conter dado
clínico desnecessário; logs e Evidence não reproduzem observações do paciente.

## 7. Matriz definitiva de autorização

| Ação | Admin | Psicólogo | Recepção |
|---|---:|---:|---:|
| visualizar agenda | todas | somente própria | todas |
| criar | sim | somente própria | sim |
| editar `scheduled` | sim | somente própria | sim |
| remarcar | sim | somente própria | sim |
| cancelar | sim | somente própria | sim |
| marcar `done` | sim | somente própria | não |
| marcar `no_show` | sim | somente própria | sim |
| correção excepcional | sim, auditada | não | não |
| excluir fisicamente | não no fluxo normal | não | não |

“Própria” exige vínculo material entre identidade autenticada e `psychologist_id`. Na
ausência desse vínculo, negar; não inferir por nome, username ou CRP.

## 8. Concorrência e transações

- consulta prévia isolada não garante exclusividade;
- criação, edição e remarcação adotam estratégia serializável compatível com SQLite;
- exatamente uma de duas reservas concorrentes conflitantes pode persistir;
- atualização é condicional por versão, não apenas read-check-write;
- PATCH exige `If-Match`; ausência retorna `428` e versão obsoleta `412`;
- PUT permanece temporariamente compatível/deprecado conforme SPEC-003, mas o novo
  frontend não o usa para contornar concorrência;
- lock interno não é exposto como traceback;
- falha de persistência não deixa registro, evento ou vínculo parcial.

## 9. API, timezone e legado

GET, POST, PATCH e ações explícitas de cancelar, realizar, registrar falta e remarcar
aplicam as mesmas regras. Respostas de recurso expõem versão e ETag. Erros são estáveis e
sanitizados, sem PII, SQL ou traceback. Remarcação é ação atômica, nunca uma sequência
frontend de PATCH + POST.

O timezone é identificador IANA configurado. Identificador inválido ou horário novo
ambíguo/inexistente retorna `422`. Datas legadas naive não são convertidas em massa sem
Evidence. Alteração futura do timezone não reinterpreta o passado.

## 10. Schema e migration previstos

O desenho físico será validado por testes antes da migration. O contrato prevê:

- remover `rescheduled` do domínio canônico novo e adicionar `no_show`;
- constraint de duração positiva e validação de estados;
- relação imutável original/sucessor sem cascade destrutivo;
- tabela append-only de eventos com tipo, atendimento, sucessor opcional, ator,
  timestamp, motivo e metadados mínimos;
- classificação temporal legada apenas se o inventário demonstrar necessidade;
- índice composto para profissional/início/status e índices do histórico;
- preservar `version` e `updated_at` da SPEC-003;
- timezone na configuração, sem reescrita do legado.

Migration somente forward-only, com backup e dry-run. IDs e conteúdo são preservados.
`rescheduled` legado é inventariado conservadoramente; não inferir sucessor, motivo ou
autor. Migration não é executada neste gate.

## 11. Impact map

- **DATABASE:** constraints, índices, relação de sucessão e eventos.
- **MODEL:** enum, evento, sucessor e classificação temporal.
- **REPOSITORY:** conflito por intervalo, update condicional e transação.
- **SERVICE:** autorização, transições, remarcação, retroatividade e timezone.
- **SCHEMA:** duração positiva, estados e payloads de ação/motivo.
- **API:** ETag, If-Match, ações e códigos `409/412/422`.
- **FRONTEND:** PATCH com ETag, remarcação real, ações por papel e feedback.
- **TESTS:** domínio, API, autorização, concorrência, rollback e migration.
- **RUNTIME:** candidato, manifest, backup, smoke, promoção autorizada e recovery.

## 12. Harness Plan

1. Fixtures SQLite fictícias e isoladas, com FKs habilitadas.
2. Testes parametrizados de intervalos, duração, estados e transições.
3. Testes API autenticados para cada célula da autorização.
4. Duas conexões reais coordenadas para corrida de criação, edição e remarcação.
5. Fault injection em cada write/commit da remarcação para provar rollback.
6. Testes de ETag/If-Match, `409`, `412`, `422` e compatibilidade PUT.
7. Inventário/migration em cópia, incluindo `rescheduled` e timestamps legados.
8. Build e integração frontend/API sem fallback mascarando o backend.
9. Regressão SPEC-002/003 e guards/runtime SPEC-008.
10. Smoke no caminho operacional default, sem override de banco ou manifest.
11. Verifiers privacy-safe de órfãos, overlaps, estados, versões e eventos.

## 13. Evidence Plan e recovery

Cada unidade produz Evidence content-addressed, privacy-safe e reproduzível: baseline
commit/status/manifest/Generation/pointer/schema; matriz requisito → código → teste;
resultados red/green; relatório agregado de concorrência; dry-run, hashes de backup e
candidato; build; smoke default; regressão e riscos residuais. Não registrar nomes, CPF,
CRP, observações, tokens ou outro dado sensível.

Recovery reutiliza maintenance lock, backup verificado, candidato isolado, promoção
versionada, histórico de pointer e manifest da SPEC-008. Após primeiro write canônico,
aplica-se `NO_SILENT_POINTER_ROLLBACK`: preservar writes/Evidence e parar para decisão
HUMAN. Não há cleanup destrutivo automático.

## 14. Critérios de aceite

- **AC-001:** 09:30–10:30 conflita com 09:00–10:00 do mesmo profissional (`409`).
- **AC-002:** 10:00–11:00 após 09:00–10:00 é permitido.
- **AC-003:** referências inexistentes não persistem atendimento (`404`).
- **AC-004:** duração não positiva ou valor inválido retorna `422`.
- **AC-005:** edição conflitante é rejeitada e não conflita consigo.
- **AC-006:** cancelamento preserva registro/evento/ator e libera horário.
- **AC-007:** `done`/`no_show` preservam ocupação; transição inválida é `409`.
- **AC-008:** remarcação cria sucessor, cancela original e registra evento atomicamente.
- **AC-009:** falha de remarcação não deixa alteração parcial.
- **AC-010:** concorrência não cria reservas conflitantes válidas.
- **AC-011:** versão obsoleta é `412`; conflito de agenda é `409`.
- **AC-012:** autorização é aplicada no backend, inclusive recepção ≠ `done`.
- **AC-013:** frontend usa PATCH/If-Match e apresenta erros sanitizados.
- **AC-014:** timezone explícito não converte silenciosamente legado.
- **AC-015:** migration preserva IDs/conteúdo e não inventa histórico.
- **AC-016:** regressão SPEC-002/003/008, build e smoke default passam.

## 15. Plano incremental de execução

1. **Baseline lock:** commit limpo aprovado, hashes e ausência de dependência local.
2. **Harness red:** materializar AC-001–016 antes das correções.
3. **Schema candidate:** migration apenas em cópia; parar diante de inferência/perda.
4. **Domain core:** estados, intervalos, transições, autorização e erros.
5. **Atomicity:** remarcação e update condicional com fault injection.
6. **Concurrency:** corrida SQLite até comprovar uma única reserva válida.
7. **API:** ações, ETag/If-Match, PUT compatível e mensagens sanitizadas.
8. **Frontend:** integração, least privilege visual e feedback.
9. **Regression candidate:** suíte, build, smoke default e Evidence.
10. **Operational gate:** preparar, sem promover sem autorização HUMAN.

Cada unidade segue `IMPLEMENT → VERIFY → DIAGNOSE → REPAIR → REVERIFY → NEXT READY`,
com READY, precondições, verifier, Evidence e stop condition explícitos.

## 16. Baseline reconciliation

Baseline operacional aceito:

- Generation `5/canonical`;
- manifest `e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1`;
- banco SHA-256 `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506`;
- schema material `backend-models-v3-spec003-integrity`, `user_version=3`;
- SPEC-003 `ACCEPTED/DONE`, sem reabertura.

No gate, `HEAD=30cdd7a495e09a6994c5f08ebfa75e4cc935b6a9`, mas há alteração local não
versionada em `backend/services/appointment_service.py` e Evidence/documentação pendente
da SPEC-003. Nada disso é incorporado à SPEC-004 por inferência.

A execução futura começa de commit imutável, limpo e aprovado contendo este contrato.
Antes de implementar, o orquestrador compara commit e manifest, classifica cada delta e
para diante de modificação local não atribuível. O conteúdo sujo atual não é baseline.
Não se altera pointer, manifest ou SPEC-003 para alinhar o checkout. O campo histórico
`schema_version` do pointer permanece preservado; a autoridade material é manifest mais
`user_version` e inspeção física.

## 17. Stop conditions

Parar em decisão de produto nova; baseline sem commit/hash limpo; divergência não
explicada entre código/manifest/pointer/banco; inferência de timezone, sucessor, ator,
motivo ou estado histórico; risco de dupla reserva/write parcial/perda de histórico;
falha de autorização, backup, integridade, FK, migration, build, regressão ou smoke; ou
mutation/promoção sem autoridade. Após write canônico, `NO_SILENT_POINTER_ROLLBACK`.

## 18. Estado do gate

As decisões HUMAN materiais foram registradas. Não há decisão de produto indispensável
pendente. SQL, nomes finais de rotas e decomposição interna são decisões técnicas, desde
que preservem o contrato.

`READY_FOR_SPEC004_ORCHESTRATED_IMPLEMENTATION`
