# SPEC-002 — Autenticação e Autorização Seguras

Status: READY FOR IMPLEMENTATION. Prioridade: P0.
Branch proposta: feature/spec-002-auth-security.
Dependência: SPEC-001.

## Objetivo
Garantir autenticação real, sessão/token e autorização no backend, eliminando bypass de demonstração.

## Requisitos
- Login rejeita usuário inexistente, senha inválida e active=false.
- JWT de curta duração, assinatura e expiração verificadas.
- AUTH_SECRET externo ao Git, independente do segredo de licença.
- POST /auth/login retorna token Bearer; GET /auth/me retorna identidade autenticada.
- Rotas privadas exigem autenticação: 401 ausente/inválida/expirada.
- Permissão insuficiente retorna 403.
- Perfis existentes: admin, psychologist, reception.
- Prontuário inicialmente restrito a psychologist; admin não recebe acesso clínico automático.
- Configurações administrativas restritas a admin.
- Backend aplica permissões; ocultar menus é apenas UX.
- Electron remove fallback admin/admin123 e envia Authorization: Bearer.
- API indisponível não significa autenticação bem-sucedida.
- Demonstração, se mantida, deve ser explícita, isolada e sem dados reais.
- Logout descarta sessão; não persistir senhas.
- Desktop verifica active e aplica política de permissões.
- Licença e autenticação permanecem controles distintos.

## Plano de implementação
1. Criar branch e conferir estado do repositório.
2. Teste e correção de usuário inativo.
3. Adicionar biblioteca JWT e configuração segura.
4. Implementar criação/validação de token e dependências de autenticação.
5. Atualizar login e criar /auth/me.
6. Proteger todas as rotas privadas.
7. Implementar matriz de roles e proteger prontuário/configurações.
8. Corrigir Electron, sessão, Bearer, logout e fallback.
9. Alinhar desktop.
10. Executar testes, build e smoke/regressão.

## Aceitação
- GET /patients sem token → 401.
- Reception em clinical-records → 403.
- Psychologist autorizado → acesso permitido.
- Usuário inativo → login rejeitado.
- API indisponível + admin/admin123 → nenhum acesso real.
- Token expirado → 401.
- Nenhum segredo ou credencial sensível versionado.

## Validação
python -m pytest
npm run build
Smoke: health, login, me, rotas anônimas, roles, token expirado e licença.

## Fora do escopo
Agenda, financeiro, backup, layout, migração de banco e reformulação do licenciamento.

## Definition of Done
Todos os gates aprovados, evidências registradas, documentação atualizada e revisão de segredos.
Não fazer commit/push/merge sem autorização explícita.
