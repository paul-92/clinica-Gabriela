# SPEC-010 — Instalador Windows e Distribuição

**Status:** DRAFT — especificação detalhada, pendente de inventário do empacotamento atual e implementação.  
**Prioridade:** P1  
**Origem:** necessidade de distribuição simplificada da Clínica Gabriela  
**Dependências:** SPEC-002, SPEC-006, SPEC-007, SPEC-008 e SPEC-009  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir como a Clínica Gabriela deverá ser empacotada, instalada, atualizada e executada em Windows de forma simples para o usuário final.

A experiência desejada é:

```text
ClinicaGabriela-Setup.exe
→ Instalar
→ Atalho
→ Abrir
→ Login
```

O usuário final não deverá precisar instalar Python, Node.js, npm, pip, uvicorn ou executar comandos em terminal.

## 2. Princípios
- instalação simples;
- execução local;
- backend iniciado automaticamente;
- dados persistidos fora da pasta de instalação;
- atualizações sem perda de dados;
- logs e backups em diretórios apropriados;
- nenhuma dependência de ambiente de desenvolvimento;
- nenhuma credencial demo insegura em produção;
- licença validada sem expor segredo de emissão;
- falhas de startup tratadas de forma controlada;
- possibilidade de restauração e rollback.

## 3. Plataforma alvo
Primeiro alvo:

```text
Windows 10
Windows 11
```

Arquitetura preferencial:

```text
x64
```

Outras arquiteturas somente se houver necessidade comprovada.

## 4. Arquitetura de distribuição
Arquitetura conceitual:

```text
Electron
→ inicia backend local empacotado
→ aguarda health check
→ abre interface
→ backend acessa SQLite autoritativo
```

O backend deverá ser executado como processo filho ou processo local controlado pela aplicação.

## 5. Inventário obrigatório
Antes da implementação deverá ser inventariado:

- package.json;
- electron-builder ou ferramenta equivalente;
- scripts npm;
- entrypoint Electron;
- preload;
- build React/Vite;
- backend FastAPI;
- requirements;
- arquivos estáticos;
- migrations;
- banco;
- licença;
- ícones;
- scripts BAT atuais;
- artefatos PyInstaller existentes, se houver.

## 6. Ferramenta de instalador
A solução atual do Electron deverá ser inspecionada antes de decidir.

Candidato:

```text
electron-builder
+
NSIS
```

A escolha final deverá considerar:

- maturidade;
- suporte a Windows;
- criação de atalhos;
- uninstall;
- versionamento;
- atualização futura;
- inclusão de binários auxiliares.

## 7. Empacotamento do backend
O backend Python deverá ser distribuído sem exigir Python instalado.

Candidato:

```text
PyInstaller
```

O executável deverá incluir:

- código backend;
- dependências Python;
- migrations;
- recursos necessários;
- configuração padrão segura.

## 8. Entrada do backend
Deverá existir entrypoint próprio para execução empacotada.

Exemplo conceitual:

```text
clinica-backend.exe
```

Responsabilidades:

- carregar configuração;
- preparar diretórios;
- inicializar banco;
- executar migrations;
- validar licença;
- iniciar FastAPI local;
- expor health check.

## 9. Backend local apenas
O backend deverá escutar apenas em loopback:

```text
127.0.0.1
```

Não utilizar:

```text
0.0.0.0
```

por padrão em instalação local.

## 10. Porta
A porta deverá ser controlada automaticamente.

Possíveis estratégias:

- porta fixa com detecção de conflito;
- porta dinâmica comunicada ao Electron;
- faixa reservada local.

A estratégia final deverá ser documentada.

## 11. Conflito de porta
Se a porta estiver ocupada:

```text
detectar
→ tentar estratégia permitida
→ informar Electron
```

Nunca falhar silenciosamente.

## 12. Health check
O Electron deverá aguardar confirmação do backend:

```text
GET /health
```

antes de liberar a interface.

Deverá haver timeout.

## 13. Falha do backend
Se o backend não iniciar, a aplicação deverá mostrar mensagem clara.

Exemplo:

```text
Não foi possível iniciar os serviços da Clínica Gabriela.
```

Possíveis ações:

- tentar novamente;
- abrir diagnóstico;
- fechar aplicação.

Não autenticar por fallback.

## 14. Encerramento
Ao fechar a aplicação, o Electron deverá encerrar corretamente o backend filho quando apropriado.

Evitar processos órfãos.

## 15. Instância única
A aplicação deverá evitar múltiplas instâncias operacionais acidentais.

O Electron deverá avaliar uso de single-instance lock.

Isso reduz risco de:

- conflitos de backend;
- porta duplicada;
- concorrência desnecessária;
- múltiplos processos da mesma instalação.

## 16. Diretório de instalação
Arquivos do programa deverão ficar em diretório apropriado ao instalador.

Eles não deverão conter dados clínicos persistentes.

## 17. Diretório de dados
Dados persistentes deverão ficar fora da pasta de instalação.

Candidato:

```text
%LOCALAPPDATA%\ClinicaGabriela\
```

Estrutura proposta:

```text
ClinicaGabriela
├─ data
├─ backups
├─ logs
├─ config
└─ license
```

A estrutura final deverá ser validada.

## 18. Banco
O SQLite autoritativo definido na SPEC-008 deverá ficar em:

```text
%LOCALAPPDATA%\ClinicaGabriela\data
```

ou diretório equivalente aprovado.

Não usar a pasta de instalação para banco operacional.

## 19. Atualização do aplicativo
Atualizar binários não deverá apagar:

- banco;
- backups;
- logs úteis;
- licença;
- configuração;
- anexos.

## 20. Migrations na atualização
Quando uma nova versão exigir alteração de schema:

```text
backup
→ migration
→ validação
→ iniciar aplicação
```

Em caso de falha:

```text
rollback
→ restaurar estado anterior
```

conforme SPEC-006 e SPEC-008.

## 21. Primeira execução
Na primeira execução:

```text
criar diretórios
→ criar banco
→ executar migrations
→ criar configuração
→ validar licença
→ iniciar backend
→ login
```

Seed de produção não deverá criar credenciais demo inseguras.

## 22. Credenciais iniciais
A política de primeiro usuário deverá ser definida explicitamente.

Possibilidades a avaliar:

- assistente de configuração;
- senha inicial gerada;
- usuário criado durante ativação;
- credencial temporária com troca obrigatória.

Não utilizar `admin/admin123` em produção.

## 23. Licenciamento
A instalação deverá validar licença local conforme arquitetura aprovada.

O cliente final não deverá receber segredo capaz de emitir licenças arbitrárias.

Separar:

```text
emissor
≠
validador
```

quando aplicável.

## 24. Ativação
A ativação poderá ser:

- arquivo de licença;
- chave;
- processo assistido.

A solução deverá funcionar offline se esse for o requisito operacional aprovado.

## 25. Expiração
Em caso de licença expirada:

- mensagem clara;
- dados preservados;
- nenhuma exclusão;
- comportamento definido funcionalmente.

## 26. Configuração
A configuração deverá residir em diretório persistente.

Evitar editar arquivos dentro de:

```text
Program Files
```

## 27. Segredos
Segredos não deverão ser gravados em:

- repositório;
- instalador em texto simples;
- logs;
- arquivos públicos.

A estratégia de AUTH_SECRET da SPEC-002 deverá ser compatível com distribuição local.

## 28. AUTH_SECRET
A aplicação instalada deverá possuir segredo de autenticação seguro e persistente.

Não gerar novo segredo a cada startup se isso invalidar sessões de forma indevida.

A geração e armazenamento devem ser avaliados com cuidado.

## 29. Logs
Logs deverão ajudar diagnóstico sem expor informações clínicas.

Não registrar:

- senha;
- token;
- conteúdo clínico;
- documentos;
- dados sensíveis desnecessários.

## 30. Rotação de logs
A aplicação deverá evitar crescimento infinito dos logs.

Definir política simples de:

- tamanho;
- quantidade;
- retenção.

## 31. Diagnóstico
Poderá existir opção:

```text
Exportar diagnóstico
```

contendo apenas dados técnicos seguros.

Exemplos:

- versão;
- SO;
- status backend;
- portas;
- últimas mensagens técnicas sanitizadas.

## 32. Backup
A aplicação instalada deverá integrar a SPEC-006.

Backup manual deverá ser acessível sem conhecimento técnico.

## 33. Local do backup
O backup padrão poderá ficar em:

```text
%LOCALAPPDATA%\ClinicaGabriela\backups
```

com opção de exportação externa quando aprovada.

## 34. Restore
A restauração não deverá depender de abrir SQLite manualmente.

Fluxo:

```text
selecionar backup
→ validar
→ confirmar
→ backup do estado atual
→ restaurar
→ validar
→ reiniciar serviços
```

## 35. Atualização automática
Auto-update não é requisito obrigatório da primeira versão.

Poderá ser fase futura.

A primeira versão pode utilizar atualização manual por novo instalador.

## 36. Atualização manual
Fluxo desejado:

```text
baixar nova versão
→ executar instalador
→ detectar instalação
→ atualizar binários
→ preservar dados
→ migrar banco
→ abrir aplicação
```

## 37. Downgrade
Downgrade deve ser tratado com cautela.

Versão antiga não deverá abrir banco migrado incompatível sem validação.

## 38. Versionamento
A aplicação deverá possuir versão visível.

Exemplo:

```text
1.0.0
```

Usar versionamento consistente entre:

- Electron;
- instalador;
- backend;
- metadados de build.

## 39. Build reproduzível
O processo de build deverá possuir comandos documentados.

Exemplo conceitual:

```text
build backend
build frontend
build Electron
package installer
```

Nenhuma etapa manual obscura deverá ser necessária.

## 40. Build limpo
O build deverá ser testado em ambiente limpo.

Evitar dependência acidental de:

- arquivo local não versionado;
- variável pessoal;
- Python global;
- Node global fora do esperado;
- caminho absoluto do desenvolvedor.

## 41. Artefatos
Artefatos esperados poderão incluir:

```text
ClinicaGabriela-Setup-1.0.0.exe
```

e, se necessário:

```text
latest.yml
```

para futura estratégia de update.

## 42. Assinatura de código
Assinatura digital de código é recomendada para distribuição profissional.

Entretanto, certificado comercial poderá ser tratado separadamente se ainda não disponível.

A ausência de assinatura deve ser documentada por impacto de SmartScreen.

## 43. SmartScreen
Instaladores não assinados podem gerar alertas no Windows.

Isso não deve ser confundido com erro do aplicativo.

A estratégia comercial de assinatura deverá ser avaliada antes da distribuição ampla.

## 44. Firewall
Como o backend usa loopback, não deverá exigir abertura de porta externa.

Se o instalador solicitar regra de firewall, isso deverá ser investigado e evitado quando desnecessário.

## 45. Antivírus
Binários PyInstaller/Electron podem gerar falsos positivos em alguns ambientes.

O build final deverá ser testado em máquinas limpas.

## 46. Permissões
A aplicação operacional deverá funcionar sem exigir execução como administrador.

Privilégio elevado deverá ser restrito ao instalador quando realmente necessário.

## 47. UAC
O instalador poderá solicitar UAC conforme modelo de instalação.

A aplicação diária não deverá depender de UAC.

## 48. Atalhos
O instalador deverá criar, conforme opção:

- Menu Iniciar;
- Área de Trabalho.

## 49. Desinstalação
A desinstalação deverá remover binários.

Dados do usuário não deverão ser apagados silenciosamente.

A política de remoção de dados deverá ser explícita.

## 50. Reinstalação
Reinstalar a mesma versão ou versão nova deverá detectar dados existentes.

Não sobrescrever banco por arquivo vazio.

## 51. Recuperação pós-reinstalação
Se os binários forem reinstalados e os dados persistirem, a aplicação deverá reutilizar a base compatível após validação.

## 52. Teste em máquina limpa
Teste obrigatório:

```text
Windows sem Python
Windows sem Node.js
Windows sem Git
```

Instalar e executar normalmente.

## 53. Teste de primeira instalação
Fluxo:

```text
executar setup
→ instalar
→ abrir
→ backend inicia
→ banco é criado
→ login/configuração inicial
```

## 54. Teste de restart
Após uso:

```text
fechar
→ reiniciar Windows
→ abrir
→ dados continuam presentes
```

## 55. Teste de upgrade
Cenário:

```text
versão N
→ cadastrar dados fictícios
→ instalar N+1
→ migrations
→ validar dados
```

## 56. Teste de falha de migration
Simular migration inválida:

```text
backup
→ falha
→ rollback
→ banco anterior utilizável
```

## 57. Teste de uninstall/reinstall
Cenário:

```text
instalar
→ criar dados fictícios
→ desinstalar
→ reinstalar
→ comportamento conforme política de preservação
```

## 58. Teste de porta ocupada
Simular porta padrão ocupada.

A aplicação deverá:

- detectar;
- resolver ou informar;
- não abrir frontend quebrado.

## 59. Teste de processo órfão
Encerrar a aplicação de diferentes formas e verificar se backend não permanece indevidamente.

## 60. Teste de múltipla instância
Abrir duas vezes.

A segunda instância deverá seguir comportamento definido.

## 61. Teste sem internet
Com rede externa indisponível:

- aplicativo local continua iniciando;
- login local continua operando;
- funcionalidades locais permanecem disponíveis.

Recursos online futuros podem falhar de forma controlada.

## 62. Teste de licença
Testar:

- licença válida;
- ausente;
- inválida;
- expirada;
- corrompida.

Nunca perder dados por falha de licença.

## 63. Teste de backup
Criar backup por interface e restaurar em ambiente de teste.

## 64. Teste de logs
Confirmar que logs não contêm:

- senhas;
- tokens;
- conteúdo clínico;
- segredos.

## 65. Compatibilidade com SPEC-009
O instalador deverá incluir corretamente o build final do Electron/React.

Não depender de Vite dev server em produção.

## 66. Compatibilidade com SPEC-008
O backend empacotado deverá usar somente a fonte de verdade definida.

Não distribuir dois bancos independentes como arquitetura final.

## 67. Compatibilidade com SPEC-002
Autenticação real e proteção das rotas deverão funcionar no pacote final.

Não introduzir bypass por conveniência de empacotamento.

## 68. Compatibilidade com SPEC-006
Backup e restore deverão usar os diretórios finais de produção.

## 69. Compatibilidade com SPEC-007
Todos os cenários de empacotamento críticos deverão ser reproduzíveis e evidenciados.

## 70. Scripts de build
Deverá existir um caminho documentado, por exemplo:

```text
scripts/
  build_backend.ps1
  build_frontend.ps1
  build_installer.ps1
```

ou equivalente.

A escolha final dependerá da estrutura atual.

## 71. CI
CI para build pode ser adicionada futuramente ou nesta fase se viável.

Não declarar pipeline aprovado sem execução real.

## 72. Artefato de homologação
Antes de produção deverá existir um instalador identificado como candidato.

Exemplo:

```text
ClinicaGabriela-Setup-1.0.0-rc1.exe
```

## 73. Evidências de homologação
Registrar:

- hash do instalador;
- versão;
- data do build;
- Windows testado;
- instalação limpa;
- upgrade;
- backup;
- restore;
- licença;
- testes aprovados.

## 74. Gates de implementação
1. **Inventário:** empacotamento atual.
2. **Arquitetura:** fluxo Electron/backend.
3. **Diretórios:** dados, logs, config, backups.
4. **Backend:** executável standalone.
5. **Frontend:** build de produção.
6. **Electron:** start/stop/health.
7. **Single instance:** validar.
8. **Banco:** init e migrations.
9. **Licença:** validar modelo final.
10. **Backup:** integração.
11. **NSIS/instalador:** pacote.
12. **Clean machine:** Windows sem dev tools.
13. **Upgrade:** preservação.
14. **Rollback:** migration.
15. **Uninstall/reinstall:** política de dados.
16. **Logs:** privacidade.
17. **Testes:** SPEC-007.
18. **Homologação:** evidências finais.

## 75. Critérios de aceitação
- **AC-001:** aplicação instala por executável único ou fluxo equivalente simples.
- **AC-002:** usuário final não precisa instalar Python.
- **AC-003:** usuário final não precisa instalar Node.js.
- **AC-004:** backend inicia automaticamente.
- **AC-005:** Electron aguarda health check.
- **AC-006:** falha do backend não habilita fallback inseguro.
- **AC-007:** banco fica fora da pasta de instalação.
- **AC-008:** upgrade preserva dados.
- **AC-009:** migration crítica possui backup.
- **AC-010:** rollback funciona em falha controlada.
- **AC-011:** reinstall não sobrescreve dados existentes sem autorização.
- **AC-012:** aplicação funciona sem internet para recursos locais.
- **AC-013:** logs não expõem dados sensíveis.
- **AC-014:** licença inválida não apaga dados.
- **AC-015:** aplicação funciona em Windows limpo sem ferramentas de desenvolvimento.
- **AC-016:** atalhos e desinstalação funcionam.
- **AC-017:** versão do aplicativo é identificável.
- **AC-018:** instalador homologado possui evidências de teste.

## 76. Fora do escopo
Esta SPEC não exige:

- macOS;
- Linux;
- Microsoft Store;
- atualização automática obrigatória;
- servidor cloud;
- sincronização online;
- Kubernetes;
- Docker no cliente;
- Active Directory;
- instalação multiusuário em servidor corporativo;
- assinatura digital comercial obrigatória na primeira entrega;
- MDM;
- deploy corporativo via SCCM/Intune.

## 77. Definition of Done
- [ ] Empacotamento atual inventariado.
- [ ] Arquitetura final de distribuição aprovada.
- [ ] Diretórios persistentes definidos.
- [ ] Backend standalone construído.
- [ ] Frontend de produção construído.
- [ ] Electron inicia backend automaticamente.
- [ ] Health check integrado.
- [ ] Encerramento do backend validado.
- [ ] Single-instance validado.
- [ ] SQLite autoritativo usado.
- [ ] Migrations integradas.
- [ ] Backup pré-migration integrado.
- [ ] Rollback testado.
- [ ] Política de primeiro usuário definida.
- [ ] Credenciais demo removidas de produção.
- [ ] Licenciamento validado.
- [ ] Segredos protegidos.
- [ ] Logs sanitizados.
- [ ] Instalador Windows construído.
- [ ] Atalhos funcionam.
- [ ] Desinstalação funciona.
- [ ] Dados sobrevivem a upgrade.
- [ ] Política de dados após uninstall validada.
- [ ] Reinstalação validada.
- [ ] Máquina limpa sem Python testada.
- [ ] Máquina limpa sem Node.js testada.
- [ ] Teste sem internet aprovado.
- [ ] Teste de porta ocupada aprovado.
- [ ] Teste de licença aprovado.
- [ ] Backup/restore aprovado.
- [ ] Testes da SPEC-007 aprovados.
- [ ] Artefato de homologação gerado.
- [ ] Evidências registradas.
- [ ] Documentação atualizada.

## 78. Estado desta SPEC
Esta SPEC define o modelo de instalação e distribuição, mas não representa um instalador já implementado ou homologado.

A implementação deverá partir do inventário real do Electron, backend, scripts e configuração de build do repositório.

Nenhum gate, critério de aceitação ou item do Definition of Done foi declarado concluído.
