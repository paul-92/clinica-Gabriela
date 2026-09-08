# SPEC-010 — Instalador Windows e Distribuição Cliente

Status: DRAFT — especificação conceitual; implementação não iniciada.
Prioridade: P1. Dependências: SPEC-002, SPEC-008 e SPEC-009.

## Objetivo
ClinicaGabriela-Setup.exe → Instalar → Atalho → Abrir → Login.
Sem Python, Node, pip, npm, terminal ou inicialização manual de API.

## Arquitetura proposta
Electron/React + backend FastAPI empacotado + SQLite local.
Avaliar PyInstaller para backend e electron-builder/NSIS para distribuição após inspecionar scripts e configuração existentes.

## Requisitos
- Um aplicativo inicia backend automaticamente e aguarda health check.
- Backend restrito a 127.0.0.1, com tratamento de porta e falhas.
- Encerramento controla processo filho; single instance.
- Separar arquivos instaláveis de dados persistentes.
- Diretório candidato: %LOCALAPPDATA%\ClinicaGabriela\data, config, license, logs, backups.
- Banco e licença não ficam em diretório substituível de instalação.
- Inicialização e migrations idempotentes e não destrutivas.
- Atualizações preservam dados; backup antes de migrações sensíveis.
- Desinstalação não apaga dados silenciosamente; remoção explícita e confirmada.
- Logs sem senhas, tokens ou conteúdo clínico sensível.
- Mensagens amigáveis de erro e diagnóstico para suporte.
- Operação local offline; recursos online futuros são escopo separado.
- Preservar licenciamento e revisar modelo de assinatura para distribuição.
- Credenciais padrão de demonstração não podem ser mecanismo de acesso de produção.
- Ícone, nome e identidade alinhados à SPEC-009.

## Segurança de licença
Avaliar separação entre geração de licenças pelo fornecedor e validação pelo cliente. Não distribuir segredo de emissão por conveniência.

## Gates
1. Inventário de scripts, Electron, backend e dependências.
2. Definição de runtime, diretórios e ciclo de vida.
3. Empacotamento do backend.
4. Integração Electron/backend.
5. Empacotamento e instalador.
6. Persistência, licença e migrations.
7. Logs, falhas, shutdown e single instance.
8. Clean install em Windows sem ferramentas de desenvolvimento.
9. Restart, upgrade, uninstall/reinstall e rollback.
10. Documentação e evidências de release.

## Aceitação
Instalação em poucos cliques, funcionamento sem dependências de desenvolvimento, persistência após reinício/atualização, dados preservados na desinstalação padrão e testes em máquina limpa.

## Fora do escopo
Atualização automática, cloud, troca de banco e novas regras de negócio.
