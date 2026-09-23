# Desenvolvimento em uma máquina Windows nova

Este fluxo cria dados **sintéticos**. Nunca use o banco clínico, a licença real,
Generation 8/canonical, o pointer ou o manifest operacional para desenvolver.

## Pré-requisitos e clone

- Windows com PowerShell 5.1 ou superior.
- Baseline validada: Python **3.12.10** com `venv` e `pip`.
- Baseline validada: Node.js **24.19.0** e npm (também em `.nvmrc`).

Estas versões são baseline reproduzível, não uma afirmação de suporte exclusivo.
Versões diferentes geram aviso; o suporte delas ainda requer validação própria.
- Git; acesso à internet para a primeira instalação de pacotes.

```powershell
git clone https://github.com/paul-92/clinica-Gabriela.git
cd clinica-Gabriela
git switch feature/spec-008-architecture-foundation
git status --short --branch
git log -1 --oneline
```

O clone recupera somente o que foi publicado. Antes da publicação autorizada dos
commits locais, a branch remota ainda não inclui a reconciliação D005-08 nem este
fluxo DEV. Confirme branch, HEAD e SPEC antes de comparar com o handoff.

## Bootstrap isolado

Escolha uma pasta nova, absoluta, **fora do repositório e do runtime operacional**.
Os scripts recusam uma pasta existente com conteúdo que não tenha marcador DEV.

```powershell
$dev = 'C:\dev\clinica-gabriela-sintetico'
& .\scripts\bootstrap-dev.ps1 -DevRoot $dev -DryRun
& .\scripts\bootstrap-dev.ps1 -DevRoot $dev
```

O bootstrap copia apenas código e contratos permitidos para `$dev\workspace`, sem
Git, bancos, licenças ou dependências instaladas do source. Cria `.venv` em `$dev`,
instala Python a partir de `requirements.txt` e `requirements-dev.lock`, executa
`npm ci` em `$dev\workspace\frontend` e cria o banco sintético em `$dev\backend`.
O build e todos os caches de validação também ficam em `$dev`. O script não gera licença.

## Configuração local

Veja `.env.example`. Ele é documentação, não é carregado automaticamente. Para
fluxos autenticados, gere `AUTH_SECRET` aleatório com pelo menos 32 bytes e defina
credenciais próprias para um administrador **somente DEV**. Configure-as no processo
local antes da primeira inicialização que precise desse acesso; não registre os
valores no Git ou no histórico do terminal.

Os scripts fixam `BACKEND_DATABASE_PATH`, `BACKEND_DATA_DIR`, `CLINICA_RUNTIME_ROOT`
e `CLINICA_OPERATIONAL_POINTER` para a pasta DEV **somente nos processos que eles
iniciam**. Se já houver overrides operacionais no terminal, os scripts falham.
`CLINICA_RUNTIME_MANIFEST_DIR`, `CLINICA_RUNTIME_CODE_ROOT` e demais variáveis
operacionais não são necessárias para desenvolvimento normal.

Para iniciar a API manualmente, configure as mesmas variáveis DEV em um novo
terminal e trabalhe em `$dev\workspace` antes de `python -m backend.main`. Não use `run_all.bat` ou instaladores
gerais como substitutos deste isolamento.

## Validação

```powershell
& .\scripts\validate-dev.ps1 -DevRoot $dev -GuardsOnly
& .\scripts\validate-dev.ps1 -DevRoot $dev
```

A validação verifica a origem do banco e depois executa `compileall`, testes Python,
testes frontend e build Vite. O banco DEV é requisito: a validação nunca o cria
silenciosamente. A porta padrão da API é `127.0.0.1:8000`; Vite usa
`127.0.0.1:5173`. Portas ocupadas devem ser resolvidas antes de iniciar os apps.

## Recuperação de contexto

Leia `AGENTS.md`, `CLINICA_GABRIELA_PROJECT_HANDOFF.txt`,
`docs/specs/SPEC-005-financeiro.md` e Evidence relevante. Redescubra `git status`,
HEAD, upstream e worktrees. O estado real verificado prevalece sobre documentos
históricos. `.context/PROJECT_CONTEXT.md` e `.context/AI_HANDOFF.md` contêm o
snapshot inicial e estão marcados como legados.

## Falhas comuns

- `DevRoot` rejeitado: use caminho absoluto novo, fora do repositório e de
  `%LOCALAPPDATA%\ClinicaGabriela\runtime`; remova overrides de ambiente antigos.
- `npm ci` falhou: confira Node 24.19.0, npm, rede e lockfile; não copie
  `node_modules` de outra máquina.
- Falhas ACL em OneDrive/temp: use pasta DEV local com permissões normais.
- Rotas licenciadas retornam 403 sem licença local válida. O bootstrap não copia
  nem gera licença operacional; o health check público e testes isolados continuam
  disponíveis.

## Estado de publicação

O commit funcional D005-08 existe localmente em
`1ead29c39ba5a6153ec589fc33bc889253b7a171`. O clone remoto ainda não
contém esse commit nem o fluxo DEV até uma publicação futura autorizada.
