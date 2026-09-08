# SPEC-006 — Backup e Recuperação

Status: BACKLOG — especificação detalhada pendente. Prioridade: P1.

## Objetivo preliminar
Garantir backup restaurável de todos os dados operacionais e recuperação segura.

## Achado de origem
O script atual copia somente o SQLite desktop, não o banco da API.

## Questões a especificar
- Fonte de verdade após SPEC-008.
- Consistência de backup SQLite e arquivos associados.
- Destino, retenção, integridade e proteção.
- Restauração testada e rollback.
- Backup antes de migrations/atualizações.
- Erros, logs e proteção de dados clínicos.

Não considerar cópia de arquivo como recuperação homologada sem teste de restauração.
