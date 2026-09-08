# SPEC-003 — Integridade Clínica e Consistência de Dados

Status: DRAFT. Prioridade: P1.
Dependências: SPEC-002 e alinhamento com SPEC-008.

## Objetivo
Impedir persistência incoerente e perda silenciosa de dados de pacientes, psicólogos, atendimentos e prontuários.

## Requisitos
RF-001: validar campos obrigatórios de pacientes conforme regras aprovadas.
RF-002: validar cadastro profissional; obrigatoriedade/unicidade/normalização de CRP dependem de decisão de domínio.
RF-003: verificar existência de entidades relacionadas antes de persistir.
RF-004: comprovar aplicação efetiva de Foreign Keys no SQLite.
RF-005: impedir prontuários órfãos ou associados incorretamente.
RF-006: atualizações parciais preservam campos ausentes; ausente não equivale a vazio.
RF-007: operações multigravação são transacionais quando necessário.
RF-008: tratar erros de constraints sem expor tracebacks ou dados sensíveis.
RF-009: exclusão/inativação e retenção de histórico exigem política explícita; não aplicar cascata destrutiva por conveniência.
RF-010: testes e seeds usam apenas dados fictícios.

## Prontuário
Definir identidade, associação, data/hora e política de edição/retificação/versionamento de evoluções com aprovação funcional e jurídica apropriada.
Não sobrescrever histórico clínico sem política aprovada.

## Gates
1. Inventário de modelos, schemas, services, repositories e migrations.
2. Aprovação das regras de domínio.
3. Testes de integridade e Foreign Keys.
4. Validações e tratamento de erros no backend.
5. Constraints/migrations não destrutivas.
6. Preservação e atualização de prontuário.
7. Regressão com SPEC-002.

## Testes mínimos
Entidades inexistentes, FK ativa, atualização parcial, rollback, exclusão protegida e erro de constraint.
Usar banco temporário isolado.

## Fora do escopo
Conflitos de agenda, financeiro, layout, instalador, cloud e novos módulos clínicos.

## Definition of Done
Integridade comprovada por testes, migrations com backup/validação/rollback e nenhuma perda silenciosa.
