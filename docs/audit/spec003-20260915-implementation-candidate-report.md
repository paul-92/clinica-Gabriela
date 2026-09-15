# SPEC-003 — Implementation Candidate Report

- Data: 2026-09-15
- Autoridade do contrato e resolução dos BLOCKs: HUMAN
- Estado: `IMPLEMENTATION_CANDIDATE_VALIDATED`
- Migração operacional: não executada
- Pointer operacional: não alterado
- Commit: não executado
- Classificação da Evidence: privacy-safe

## Decisões e BLOCKs

As decisões D-CPF-*, D-CRP-*, D-DEL-*, D-REC-*, D-RET-*, D-REL-*, D-UPD-* e
D-COMP-01 estão registradas no contrato da SPEC-003. Os três BLOCKs foram resolvidos:

- CRP canônico mínimo: `regional + número`; regras profissionais adicionais são
  `EXTERNAL_POLICY_PENDING`.
- Prontuários históricos: `LEGACY_PRESERVED`, com `author_unknown` e sem associação
  inferida.
- Exclusão: somente DRAFT elegível, pelo autor ou perfil administrativo explicitamente
  autorizado, gerando evento apenas com metadados.

Não surgiu novo `HUMAN_DECISION_REQUIRED` no escopo de implementação do candidato.

## Implementação

- CPF opcional, normalizado, validado e único quando presente.
- Estado `legacy_unverified` para CPF histórico inválido.
- CRP estruturado por regional/número, unicidade composta, estados provisório/apto/review.
- Prechecks de entidades ativas e coerência em agenda, prontuário e pagamentos.
- Foreign Keys habilitadas em todas as conexões SQLAlchemy SQLite.
- Rollback e tradução sanitizada de `IntegrityError`.
- PATCH parcial, ETag/If-Match e `412` para versão obsoleta.
- PUT preservado temporariamente e marcado como deprecado.
- Prontuário DRAFT/FINALIZED/LEGACY_PRESERVED.
- Retificação append-only; base finalizada/preservada não é sobrescrita.
- Exclusão de DRAFT protegida com evento auditável sem conteúdo clínico.
- Migration forward-only explícita, não ligada ao startup.

## Testes

- Testes dirigidos de identificadores, FK, migration e agenda: `25 passed`.
- Testes de lifecycle clínico: `8 passed`.
- Regressão final: `204 passed in 27.34s`.
- Frontend: `npm run build` — PASS.
- Compilação Python: PASS.
- `git diff --check`: PASS; apenas avisos esperados de LF/CRLF.

## Candidato e dados

Artefato validado:

`.homologation/spec003-domain-integrity-candidate-v2/`

- Generation 2 fonte SHA-256:
  `4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`
- Backup pré-SPEC-003 SHA-256:
  `bf669be2208ec6f819e3c9b8687160c957d67a8d04948e0a387160926b8d2f7b`
- Candidato SPEC-003 SHA-256:
  `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506`
- Contagens antes/depois: idênticas em todas as tabelas de domínio.
- `integrity_check=ok`.
- `foreign_key_check=0`.
- Schema do candidato versus models: PASS.
- Prontuários históricos classificados `LEGACY_PRESERVED`: 2.
- Autoria histórica `author_unknown`: 2.
- CPF histórico `legacy_unverified`: 1.
- CRP histórico em `REVIEW`: 1.
- Origem operacional inalterada: sim.

As contagens são agregadas; nenhum valor identificável ou conteúdo clínico integra este
relatório.

## Gate operacional

A Generation 2 continua ativa (`generation=2`, `state=canonical`) e com checksum
inalterado. Não houve promoção porque o código alterado ainda não possui commit/runtime
manifest congelado autorizado, e o contrato proíbe commit sem autorização específica.
Promover banco v3 contra runtime antigo, ou runtime novo sem manifest válido, seria uma
operação insegura e incompatível com os guards vigentes.

O candidato está pronto para a etapa futura de empacotamento/freeze do runtime,
promoção versionada e troca atômica do pointer sob maintenance lock. Essa etapa deve
preservar `NO_SILENT_POINTER_ROLLBACK` e não remover backups/generations anteriores.

`SPEC003_IMPLEMENTATION_CANDIDATE_VALIDATED`
