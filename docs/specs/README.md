# Clínica Gabriela — Índice de Specs

Pacote de documentação preparado em 08/09/2026 a partir das especificações desta conversa.
Este pacote não foi publicado no GitHub. A criação da branch foi recusada pela integração (403).
Nenhuma implementação ou teste é declarado como executado por este pacote.

| Spec | Assunto | Status |
|---|---|---|
| 001 | Auditoria | DONE — auditoria estática |
| 002 | Segurança | READY FOR IMPLEMENTATION |
| 003 | Integridade clínica | DRAFT |
| 004 | Agenda | BACKLOG |
| 005 | Financeiro | BACKLOG |
| 006 | Backup | BACKLOG |
| 007 | Testes | BACKLOG |
| 008 | Arquitetura | DRAFT |
| 009 | Interface | DRAFT — baseline visual |
| 010 | Instalador | DRAFT |

## Ordem recomendada
SPEC-002 → SPEC-008 (inventário/decisão) → SPEC-003/004/005 → SPEC-006/007 → SPEC-009 → SPEC-010 → homologação.

As dependências podem ser trabalhadas em paralelo quando não houver risco de duplicação ou perda de dados.

## Governança
Necessidade → Spec → Critérios de aceitação → Plano → Implementação → Testes → Evidências → Revisão → Done.

Não confundir documento pronto com código implementado. Preservar main, dados, segredos e licenciamento.
Conferir estado atual do repositório antes de executar qualquer plano. Não fazer commit, push ou merge sem autorização explícita.

## Próxima execução
SPEC-002: criar feature/spec-002-auth-security, conferir estado atual e iniciar pelo teste de usuário inativo.

## Documentos
Os arquivos SPEC-001 a SPEC-010 estão nesta pasta. SPEC-004 a SPEC-007 são placeholders honestos de backlog, não especificações completas.
