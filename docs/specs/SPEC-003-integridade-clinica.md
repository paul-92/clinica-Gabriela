# SPEC-003 — Integridade Clínica e Consistência de Dados

Status: ACCEPTED / DONE. Prioridade: P1.

Dependências: SPEC-002 e Generation 2/canonical resultante da SPEC-008.

Autoridade das decisões: HUMAN.

Data do gate final e aceite HUMAN: 2026-09-16.
Política-base: conservadora, não destrutiva e sem inferência de dados históricos.

## 1. Objetivo e invariantes

Impedir persistência incoerente e perda silenciosa de dados, preservando IDs e conteúdo
da Generation 2/canonical. Esta SPEC não autoriza alteração retroativa da SPEC-008.

- Não inventar, apagar ou corrigir automaticamente CPF, CRP, autoria, atendimento ou
  associação histórica ausente.
- Não aplicar cascade delete a conteúdo clínico ou fatos financeiros sujeitos a retenção.
- Campo ausente não equivale a `NULL`, string vazia ou valor padrão.
- Last-write-wins silencioso é proibido.
- Prontuário finalizado é imutável; correção posterior é append-only.
- FKs devem estar habilitadas e comprovadas em toda conexão SQLite operacional.
- Todo `IntegrityError` deve causar rollback e ser traduzido para resposta sanitizada.
- Testes, seeds e evidências usam somente dados fictícios/privacy-safe.
- A política provisória de retenção é `NO_AUTOMATIC_DELETION`.

## 2. Contrato funcional aprovado

### 2.1 CPF

**D-CPF-01 — opcionalidade.** CPF é opcional no cadastro. Quando informado, deve
cumprir integralmente o contrato de normalização, validação e unicidade.

**D-CPF-02 — normalização e validação.** A representação canônica contém exatamente
11 dígitos. Pontuação e espaços são removidos antes da validação e os dígitos
verificadores devem ser válidos.

**D-CPF-03 — unicidade.** CPF informado é único sobre o valor canônico normalizado.
Duplicidade retorna conflito de domínio; não existe exceção silenciosa.

**D-CPF-04 — legado.** CPF legado inválido deve ser preservado como
`legacy_unverified`. É proibido apagá-lo, corrigi-lo ou substituí-lo por valor inventado.
O registro permanece legível e aceita alterações não relacionadas ao CPF. Alteração do
CPF não pode resultar em outro valor inválido. Operações futuras que declararem CPF
válido como precondição devem ser bloqueadas enquanto o estado for `legacy_unverified`.

### 2.2 CRP

**D-CRP-01 — aptidão.** É permitido cadastro administrativo provisório sem CRP apto.
Psicólogo sem identidade profissional válida/apta não pode criar novos fatos clínicos
nem atuar clinicamente.

**D-CRP-02 — representação.** Adotar representação canônica estruturada suficiente
para `regional + número`. Regras sobre inscrições múltiplas e natureza
principal/secundária permanecem fora do contrato até validação profissional específica;
a implementação não pode inferi-las.

**D-CRP-03 — unicidade e conflitos.** A identidade profissional canônica normalizada
é única. Conflitos entram em estado `REVIEW` e nunca são deduplicados, mesclados ou
resolvidos automaticamente.

### 2.3 Inativação e exclusão

**D-DEL-01 — entidades.** `Patient`, `Psychologist` e `User` permanecem inativáveis.
Agenda e financeiro usam seus próprios estados de domínio, sem reutilizar `active`.

**D-DEL-02 — exclusão física.** Exclusão física somente é permitida para cadastro
comprovadamente nunca utilizado e sem dependências clínicas ou financeiras. Prontuário
finalizado e fatos financeiros não podem ser fisicamente excluídos pelo fluxo normal.
Nenhuma cascata destrutiva é autorizada.

**D-DEL-03 — efeito da inativação.** Inativação bloqueia novos fatos operacionais e
preserva consulta histórica. Retificação clínica autorizada continua possível quando
necessária à correção do histórico e é exceção controlada, não novo fato clínico.

### 2.4 Prontuário

**D-REC-01 — ciclo de vida.** O ciclo aprovado é `DRAFT → FINALIZED`. Rascunho pode
ser editado. Finalizado é imutável e a transição não é reversível pelo fluxo normal.

**D-REC-02 — retificação.** Após finalização, correção ocorre somente por retificação
append-only. Cada retificação preserva o conteúdo anterior e registra identidade do
autor, timestamp, motivo e referência à versão ou registro anterior.

**D-REC-03 — exclusão.** Prontuário finalizado nunca pode ser fisicamente excluído pelo
fluxo normal. Rascunho pode ser excluído apenas enquanto não finalizado, mediante regra
auditável e ausência de dependência que exija preservação.

**D-REC-04 — autoria e atendimento.** Registrar a identidade do usuário responsável e
do psicólogo profissional. `appointment_id` é opcional; quando presente, deve referenciar
atendimento existente e coerente com paciente e psicólogo. Registros históricos recebem
estados explícitos como `author_unknown` quando necessário. É proibido inferir autoria
ou vínculo histórico.

### 2.5 Retenção

**D-RET-01 e D-RET-02 — política provisória.** Não será fixado nesta SPEC prazo jurídico
de 5, 20 ou outro número de anos. Prazo, marco inicial, anonimização e exceções LGPD
ficam registrados como `EXTERNAL_POLICY_PENDING`.

Até validação jurídica/profissional formal aplica-se `NO_AUTOMATIC_DELETION`:

- prontuários, retificações e histórico clínico não são eliminados automaticamente;
- fatos financeiros sujeitos a retenção não são eliminados automaticamente;
- pedidos de eliminação entram em workflow futuro de análise;
- pedido de eliminação nunca dispara cascade delete;
- a pendência externa não bloqueia as proteções de integridade desta SPEC.

### 2.6 Integridade relacional

**D-REL-01 — referências inativas.** Novos vínculos com entidades inativas são
rejeitados. Histórico existente é preservado. Retificação clínica autorizada é exceção
controlada.

**D-REL-02 — persistência e erros.** Aplicar simultaneamente precheck explícito de
existência, atividade e coerência; FKs em toda conexão SQLite; captura de
`IntegrityError` com rollback; e mensagens sem traceback, PII ou conteúdo clínico.

| Condição | HTTP |
|---|---:|
| Entidade alvo ou referência inexistente | `404` |
| Conflito de unicidade, estado ou regra de domínio | `409` |
| Payload, formato ou valor inválido | `422` |
| Falha interna não classificada | `500` sanitizado |

### 2.7 Atualizações

**D-UPD-01 — atualização parcial.** `PATCH` representa atualização parcial. Campo
ausente preserva o valor atual. `NULL` somente limpa campo explicitamente nullable.
`PUT` será mantido temporariamente para compatibilidade e marcado como deprecado,
conservando sua semântica observável até migração documentada.

**D-UPD-02 — concorrência.** Adotar concorrência otimista com versão persistida exposta
por ETag e precondição `If-Match`. Versão obsoleta ou precondição de concorrência não
satisfeita retorna uniformemente `412 Precondition Failed`; `409 Conflict` fica reservado
a conflitos de unicidade, estado ou regra de domínio. Last-write-wins silencioso é proibido.

### 2.8 Migration

**D-COMP-01 — evolução canônica.** Somente migration forward-only, precedida de backup
e dry-run e seguida de validação e estratégia de recuperação. IDs e conteúdo da
Generation 2/canonical serão preservados. Estados como `legacy_unverified` e
`author_unknown` serão usados quando necessários.

## 3. Requisitos funcionais consolidados

- RF-001: validar CPF conforme D-CPF-01 a D-CPF-04.
- RF-002: validar identidade e aptidão profissional conforme D-CRP-01 a D-CRP-03.
- RF-003: verificar existência, atividade e coerência das entidades relacionadas.
- RF-004: comprovar aplicação efetiva de FKs em toda conexão SQLite.
- RF-005: impedir prontuários órfãos ou associados incorretamente.
- RF-006: implementar PATCH com distinção entre ausente, `NULL` e vazio.
- RF-007: tornar transacionais as operações multigravação.
- RF-008: tratar constraints com rollback e erros sanitizados.
- RF-009: aplicar as regras aprovadas de inativação, exclusão e retenção.
- RF-010: preservar prontuário finalizado e implementar retificação append-only.
- RF-011: aplicar concorrência otimista sem sobrescrita silenciosa.
- RF-012: usar somente dados fictícios em testes, seeds e evidências.

## 4. Plano de execução para implementação futura

### 4.1 Alterações de schema

- `patients`: CPF nullable; estado de verificação; controle de concorrência.
- `psychologists`: regional e número canônicos; estado de aptidão/revisão; ausência
  provisória de CRP; controle de concorrência.
- `clinical_records`: estado `DRAFT`/`FINALIZED`, usuário autor, psicólogo autor,
  `appointment_id` nullable, timestamps, versão e metadados de finalização.
- Estrutura append-only para versões/retificações, com predecessor, autor, timestamp e
  motivo.
- Trilha de auditoria mínima para finalização, retificação e exclusão autorizada de
  rascunho, sem conteúdo sensível em logs operacionais.
- Índices e constraints únicas canônicas de CPF e CRP.
- Nenhum `ON DELETE CASCADE` em relações clínicas/financeiras.

### 4.2 Migrations necessárias

1. Inventário e preflight read-only da Generation 2.
2. Backup verificável antes de qualquer write.
3. Dry-run sobre cópia isolada.
4. Criação forward-only das novas tabelas, colunas, índices e constraints.
5. Backfill somente de estados determinísticos:
   - CPF inválido → `legacy_unverified`;
   - autoria histórica ausente → `author_unknown`;
   - prontuário histórico → estado imutável aprovado no BLOCK-003-02;
   - CRP não comprovadamente normalizável → `REVIEW`.
6. Validar contagens, IDs, conteúdo, FKs, unicidade e integridade SQLite.
7. Promover somente após gates técnicos e HUMAN aplicáveis.

Não fazer backfill inferencial de `appointment_id`, usuário autor ou identidade
profissional.

### 4.3 Models, schemas, services, repositories e API

- Models: nulabilidade, estados, versões, autoria, retificações e constraints.
- Schemas: contratos create/read/patch/finalize/rectify, validators e nullability explícita.
- Services: prechecks, aptidão, transições, coerência, exclusão protegida e retenção.
- Repositories: transações, rollback, dependências e concorrência, sem regra clínica.
- API: PATCH, finalização e retificação; PUT temporário deprecado; erros uniformes.
- Sessão SQLite: hook de conexão para `PRAGMA foreign_keys=ON`, com prova fail-closed.
- Autorização: vínculo entre usuário e psicólogo quando aplicável, sem inferência histórica.

### 4.4 Compatibilidade temporária

- Preservar leitura, IDs e conteúdo dos registros legados.
- Manter `PUT` temporariamente, sem quebra ou mudança silenciosa.
- Introduzir versão/ETag na resposta, atualizar clientes e só depois exigir precondição.
- Expor estados legados aos clientes autorizados.
- Sincronizar frontend/API antes de remover compatibilidade.

### 4.5 Estratégia para dados legados

- Preservar valores originais e classificar incerteza.
- Nunca registrar PII ou conteúdo clínico nas evidências.
- Não normalizar em massa CPF/CRP sem análise de colisão privacy-safe.
- Resolver conflitos de CRP por `REVIEW` humano.
- Manter autoria e atendimento desconhecidos como estados explícitos.
- Não alterar Generation 1, bancos legados, backups ou artefatos da SPEC-008.

### 4.6 Testes necessários

- CPF: opcionalidade, normalização, dígitos, NULL/vazio, duplicidade e legado.
- CRP: provisório, normalização, aptidão, unicidade, REVIEW e bloqueio clínico.
- Inativação: bloqueio de novos fatos e preservação de consulta/retificação.
- Exclusão: nunca usado, dependências, fatos protegidos, rascunho e ausência de cascata.
- Prontuário: ciclo, imutabilidade, retificação, autoria, predecessor e coerência.
- FK: pragma por conexão, referências inexistentes e `foreign_key_check=0`.
- Transação: rollback integral em `IntegrityError` e multigravação.
- HTTP: `404/409/422/500` e mensagens sanitizadas.
- PATCH: ausente versus NULL, pós-merge e compatibilidade PUT.
- Concorrência: versão válida/obsoleta e ausência de last-write-wins.
- Migration: fixture Generation 2, preservação, repetibilidade e recovery.
- Regressão: autenticação, autorização, agenda, financeiro, frontend e SPEC-002/SPEC-008.

Todos os testes de banco usam cópias temporárias isoladas.

### 4.7 Rollback e recovery

- O rollback primário é abortar antes da promoção quando qualquer gate falhar.
- Após promoção e novas escritas, rollback cego de pointer é proibido.
- Recovery pós-write é forward recovery ou restauração seguida de reconciliação autorizada.
- Backup deve ter checksum, manifest, contagens e teste de restauração isolada.
- Scripts devem falhar fechados, preservar origem e não reutilizar destino parcial.
- A boundary `NO_SILENT_POINTER_ROLLBACK` da SPEC-008 permanece vigente.

### 4.8 Evidence e critérios de aceite

Evidence privacy-safe obrigatória:

- manifest da decisão de domínio e versão da SPEC;
- inventário pré/pós, checksum do backup e prova de restauração;
- relatórios de dry-run/migration e schema diff esperado;
- contagens, preservação de IDs e ausência de associações inventadas;
- `integrity_check=ok`, `foreign_key_check=0` e FK ativa por conexão;
- testes, matriz HTTP, imutabilidade/retificação e concorrência;
- estado da compatibilidade PUT/clientes e pendências externas.

Aceite exige ausência de perda silenciosa, associação inventada, órfão, cascata
destrutiva, vazamento em erros/evidências ou sobrescrita concorrente silenciosa.

### 4.9 Sequência de execução

1. Congelar contrato, inventário e fixtures privacy-safe.
2. Confirmar o registro de resolução dos BLOCKs na seção 5.
3. Especificar schema e migration forward-only.
4. Escrever testes de contrato e migration primeiro.
5. Executar backup e dry-run em cópia isolada.
6. Implementar FK, transação e tratamento de erros.
7. Implementar CPF/CRP e integridade relacional.
8. Implementar PATCH e concorrência otimista.
9. Implementar ciclo de prontuário e retificações.
10. Implementar inativação/exclusão protegida e retenção conservadora.
11. Atualizar clientes e manter compatibilidade PUT.
12. Executar regressão, auditoria privacy-safe e ensaio de recovery.
13. Solicitar gate HUMAN separado para migration/promoção real.

## 5. BLOCKs reavaliados e resolvidos

### BLOCK-003-01 — RESOLVED / HUMAN

Representação canônica mínima aprovada: `regional + número`, normalizados separadamente
para dígitos e usados conjuntamente como identidade profissional determinística. A
representação adequada à exibição pode ser preservada. Regras de inscrição
principal/secundária, múltiplas inscrições, situações especiais e validação externa
perante Conselho ficam como `EXTERNAL_POLICY_PENDING` e não autorizam atuação clínica
sem estado interno de aptidão.

### BLOCK-003-02 — RESOLVED / HUMAN

Prontuários anteriores à SPEC-003 serão `LEGACY_PRESERVED`, distintos de `FINALIZED`,
com conteúdo integral preservado, sobrescrita destrutiva proibida, autoria ausente como
`author_unknown`, sem `appointment_id` inferido e somente retificação append-only.

### BLOCK-003-03 — RESOLVED / HUMAN

Exclusão física exige simultaneamente: estado `DRAFT`, nunca ter sido `FINALIZED`, não
ser `LEGACY_PRESERVED`, não possuir dependência que exija preservação e operação pelo
autor ou perfil administrativo explicitamente autorizado. A exclusão gera evento
auditável apenas com metadados necessários, sem replicar conteúdo clínico. `FINALIZED`
e `LEGACY_PRESERVED` nunca são excluíveis pelo fluxo normal.

### EXTERNAL_POLICY_PENDING

Prazo de retenção, marco inicial, anonimização, exceções LGPD e workflow de eliminação
dependem de validação jurídica/profissional futura. Não bloqueiam
`NO_AUTOMATIC_DELETION` nem as demais proteções desta SPEC.

## 6. Gates

1. Contrato de domínio aprovado — **PASS em 2026-09-15**.
2. BLOCKs prévios resolvidos — **PASS por decisão HUMAN**.
3. Testes de contrato escritos — **PASS**.
4. Backup e dry-run aprovados — **PASS em candidato isolado**.
5. Migration forward-only validada em cópia isolada — **PASS**.
6. Implementação de integridade e prontuário — **PASS em código/candidato**.
7. Regressão com SPEC-002 e compatibilidade com SPEC-008 — **PASS: 204 testes**.
8. Evidence privacy-safe completa — **PASS para candidato**.
9. Gate HUMAN separado antes de migration/promoção real.

## 7. Fora do escopo

- Definir prazo jurídico definitivo de retenção.
- Inventar regras para inscrições CRP múltiplas/principal/secundária.
- Resolver conflitos gerais de agenda da SPEC-004 ou regras contábeis da SPEC-005.
- Alterar ou reabrir a baseline da SPEC-008.
- Cloud, layout, instalador e novos módulos clínicos.

## 8. Definition of Done

- Decisões D-* implementadas e comprovadas por testes.
- Migration forward-only com backup, dry-run, validação e recovery ensaiado.
- IDs e conteúdo canônicos preservados.
- FKs efetivas em toda conexão e zero violações.
- Prontuários finalizados imutáveis e retificações append-only auditáveis.
- Nenhuma exclusão automática ou cascata destrutiva.
- Erros e evidências sanitizados.
- Compatibilidade temporária documentada e testada.
- Pendências externas mantidas como `EXTERNAL_POLICY_PENDING`.
- Aceite HUMAN de implementação e promoção registrado separadamente.

## 9. Fechamento formal

Em 2026-09-16, o HUMAN/Product Owner aceitou o resultado do Final Independent Quality /
Closure Re-Review (`QUALITY_GATE_PASS`) e autorizou o fechamento formal desta SPEC como
`ACCEPTED / DONE`.

O estado operacional aceito é a Generation 5/canonical, vinculada ao runtime manifest
content-addressed `e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1`.
A cadeia completa, os dois `QUALITY_GATE_FAIL`, as remediações, revalidações, riscos e
ativos de recovery estão consolidados em
`docs/audit/spec003-20260916-final-closure-report.md`.

Este aceite não autoriza migration, nova promoção, alteração de pointer, rollback,
cleanup destrutivo, push, merge ou release. Generations anteriores, backups, manifests,
Evidence, histórico de pointers, relatórios de Quality Gates e artefatos de recovery
permanecem preservados.

`ACCEPTED/DONE ≠ DESTRUCTIVE CLEANUP`

`SPEC-003 CLOSED — ACCEPTED/DONE`
