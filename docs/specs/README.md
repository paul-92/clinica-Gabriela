# Clínica Gabriela — Índice de Specs e Roadmap de Implementação

Documentação Spec-Driven Development da Clínica Gabriela.

Este diretório reúne as especificações funcionais, técnicas, arquiteturais, de segurança, testes, interface e distribuição do projeto.

> **Regra central:** documento pronto não significa código implementado. Cada SPEC só pode avançar para `DONE` após implementação, testes, evidências e revisão compatíveis com seus critérios de aceitação.

## 1. Índice

| Spec | Assunto | Status documental | Prioridade | Próxima ação |
|---|---|---|---|---|
| SPEC-001 | Auditoria e estabilização | DONE — auditoria estática | P0/P1 | manter como baseline de riscos |
| SPEC-002 | Autenticação e autorização seguras | READY FOR IMPLEMENTATION | P0 | implementar primeiro |
| SPEC-003 | Integridade clínica | DRAFT detalhada | P1 | implementar após base de segurança |
| SPEC-004 | Agenda e atendimentos | DRAFT detalhada | P1 | implementar após segurança/arquitetura |
| SPEC-005 | Financeiro | DRAFT detalhada | P1 | implementar após segurança/arquitetura |
| SPEC-006 | Backup e recuperação | DRAFT detalhada | P1 | implementar antes de migrations críticas |
| SPEC-007 | Testes automatizados | DRAFT detalhada | P1 transversal | aplicar desde o início |
| SPEC-008 | Unificação arquitetural | DRAFT detalhada | P1 | inventário e decisão após SPEC-002 |
| SPEC-009 | Interface clínica e Design System | DRAFT detalhada | P1 | modernizar após estabilização funcional |
| SPEC-010 | Instalador Windows e distribuição | DRAFT detalhada | P1 | empacotar após arquitetura/UI estáveis |

## 2. Objetivo do roadmap

O roadmap organiza a implementação para evitar três riscos principais:

1. modernizar a interface antes de corrigir segurança e arquitetura;
2. criar novas regras em duas arquiteturas paralelas;
3. migrar dados ou empacotar o sistema antes de backup, testes e rollback estarem confiáveis.

A ordem abaixo privilegia segurança, fonte única de verdade, integridade dos dados e somente depois experiência visual e distribuição.

## 3. Fluxo de governança

Toda mudança deverá seguir:

```text
Necessidade
→ SPEC
→ critérios de aceitação
→ inventário do código atual
→ plano de implementação
→ branch de feature
→ testes primeiro quando aplicável
→ implementação
→ evidências
→ revisão
→ merge
→ atualização da SPEC
```

Não pular diretamente de uma ideia para alteração em `main`.

## 4. Estados permitidos

Estados documentais recomendados:

```text
BACKLOG
DRAFT
READY FOR IMPLEMENTATION
IN IMPLEMENTATION
READY FOR REVIEW
DONE
BLOCKED
```

Significados:

- **BACKLOG:** necessidade identificada, ainda sem detalhamento suficiente.
- **DRAFT:** especificação detalhada, mas possui decisões ou inventários pendentes.
- **READY FOR IMPLEMENTATION:** critérios suficientes para iniciar código.
- **IN IMPLEMENTATION:** branch de implementação ativa.
- **READY FOR REVIEW:** código e testes concluídos, aguardando revisão.
- **DONE:** implementação, testes e evidências aprovados.
- **BLOCKED:** impedimento externo ou decisão funcional impede avanço.

## 5. Roadmap macro

```text
FASE 0 — Auditoria
SPEC-001
    ↓
FASE 1 — Segurança
SPEC-002
    ↓
FASE 2 — Fundação arquitetural
SPEC-008
    ↓
FASE 3 — Integridade e domínios
SPEC-003
SPEC-004
SPEC-005
    ↓
FASE 4 — Resiliência e qualidade
SPEC-006
SPEC-007
    ↓
FASE 5 — Experiência
SPEC-009
    ↓
FASE 6 — Distribuição
SPEC-010
    ↓
FASE 7 — Homologação
```

A SPEC-007 é transversal: seus testes deverão acompanhar todas as fases, e não apenas começar na Fase 4.

## 6. Fase 0 — Auditoria

### SPEC-001 — Auditoria e estabilização

**Situação:** concluída como auditoria estática.

A SPEC-001 identificou o backlog que originou as demais especificações.

Principais riscos que direcionam o roadmap:

- autenticação/autorização incompletas;
- fallback inseguro no Electron;
- acesso clínico sem proteção suficiente;
- integridade referencial a validar;
- conflitos de agenda não garantidos;
- inconsistências financeiras;
- backup incompleto;
- dois bancos e duas linhas de negócio;
- cobertura de testes limitada.

### Gate da Fase 0

- [x] Auditoria estática documentada.
- [x] Riscos principais mapeados.
- [x] Specs derivadas criadas.
- [ ] Auditoria runtime completa — somente quando os ambientes de execução forem validados.

## 7. Fase 1 — Segurança

### SPEC-002 — Autenticação e autorização seguras

Esta é a primeira implementação recomendada.

Objetivos principais:

- autenticação real no FastAPI;
- token de sessão;
- `/auth/me`;
- rejeição de usuário inativo;
- 401 e 403 consistentes;
- autorização por perfil;
- proteção de rotas clínicas;
- remoção do fallback hardcoded no Electron;
- sessão frontend integrada ao backend;
- alinhamento do desktop legado enquanto existir.

### Branch recomendada

```text
feature/spec-002-auth-security
```

### Primeiro incremento recomendado

```text
teste: usuário inativo não autentica
→ implementação mínima
→ teste de token
→ login
→ rotas protegidas
→ autorização por perfil
→ Electron
→ regressão
```

### Gate da Fase 1

Só avançar estruturalmente para a próxima fase quando:

- [ ] login seguro estiver funcional;
- [ ] usuário inativo for rejeitado;
- [ ] token válido/expirado/inválido estiver testado;
- [ ] rotas privadas exigirem autenticação;
- [ ] perfis forem validados no backend;
- [ ] prontuário possuir política de acesso;
- [ ] fallback inseguro do Electron estiver removido;
- [ ] testes de regressão relevantes passarem.

## 8. Fase 2 — Fundação arquitetural

### SPEC-008 — Unificação arquitetural

Não começar pela migração de dados.

Primeiro executar o **inventário**.

Ordem recomendada:

```text
inventariar desktop
→ inventariar backend
→ comparar models
→ comparar schemas
→ comparar repositories
→ comparar services
→ comparar migrations
→ comparar bancos
→ definir fonte de verdade
→ planejar migração
```

Arquitetura alvo:

```text
Electron / React
        ↓
      FastAPI
        ↓
     Services
        ↓
   Repositories
        ↓
SQLite autoritativo
```

O Tkinter poderá permanecer temporariamente como legado, sem receber novas regras duplicadas sem justificativa.

### Branch sugerida para inventário/decisão

```text
feature/spec-008-architecture-unification
```

Se a fase inicial produzir somente documentação e matriz, poderá ser separada em branch de docs antes da implementação.

### Gate da Fase 2A — Decisão arquitetural

- [ ] dois bancos inventariados;
- [ ] entidades comparadas;
- [ ] migrations comparadas;
- [ ] funcionalidades exclusivas identificadas;
- [ ] banco autoritativo escolhido;
- [ ] estratégia de IDs definida;
- [ ] conflitos de dados mapeados;
- [ ] plano de rollback definido;
- [ ] nenhuma perda de dados presumida.

### Gate da Fase 2B — Unificação

- [ ] um único banco operacional autoritativo;
- [ ] frontend principal usa API;
- [ ] regras críticas estão nos services/backend;
- [ ] dual-write permanente inexistente;
- [ ] migrations testadas com dados fictícios;
- [ ] integridade pós-migração validada;
- [ ] rollback testado.

## 9. Fase 3 — Integridade e domínios

Após segurança e decisão arquitetural, implementar os domínios sobre a mesma fundação.

### 9.1 SPEC-003 — Integridade clínica

Prioridade alta porque envolve dados sensíveis e relacionamentos.

Sequência:

```text
inventário
→ decisões funcionais
→ testes
→ validações de entidades
→ FK
→ transações
→ histórico clínico
→ regressão
```

Gate mínimo:

- [ ] relacionamentos válidos;
- [ ] FK comprovada em runtime;
- [ ] ausência de órfãos;
- [ ] updates parciais seguros;
- [ ] rollback;
- [ ] política de edição/retificação clínica definida;
- [ ] testes com banco temporário.

### 9.2 SPEC-004 — Agenda

Implementar sobre entidades já integradas.

Sequência:

```text
intervalos
→ conflitos
→ estados
→ cancelamento
→ remarcação
→ concorrência
→ API
→ interface
```

Gate mínimo:

- [ ] conflito do mesmo profissional impedido;
- [ ] horários adjacentes permitidos;
- [ ] edição revalida conflito;
- [ ] cancelamento libera slot conforme regra;
- [ ] histórico de remarcação preservado;
- [ ] concorrência testada;
- [ ] permissões backend aplicadas.

### 9.3 SPEC-005 — Financeiro

Somente implementar cálculos após definir claramente suas regras.

Sequência:

```text
precisão monetária
→ datas
→ status
→ receitas/despesas
→ pagamentos
→ resumo por período
→ integração com agenda
→ indicadores
```

Gate mínimo:

- [ ] dinheiro não depende de `float` inadequado;
- [ ] período dos indicadores é explícito;
- [ ] resumo mensal não soma histórico inteiro;
- [ ] transições de status estão definidas;
- [ ] cancelamento/estorno têm semântica definida;
- [ ] filtros são testados;
- [ ] testes de precisão monetária passam.

## 10. Paralelismo permitido na Fase 3

SPEC-003, SPEC-004 e SPEC-005 podem ter planejamento parcialmente paralelo depois da arquitetura definida.

A implementação simultânea só deve ocorrer se:

- os contratos compartilhados já estiverem definidos;
- não houver migrations conflitantes;
- não houver duas branches alterando a mesma regra central;
- integração for revisada antes do merge.

Na dúvida, preferir execução sequencial:

```text
SPEC-003
→ SPEC-004
→ SPEC-005
```

## 11. Fase 4 — Resiliência e qualidade

### SPEC-006 — Backup e recuperação

A implementação deve começar **antes da primeira migration destrutiva ou estruturalmente crítica**.

Isso significa que partes da SPEC-006 podem ser antecipadas durante a SPEC-008.

Ordem:

```text
definir fonte de verdade
→ backup consistente
→ validação
→ restore
→ backup pré-migration
→ rollback
→ retenção
```

Gate mínimo:

- [ ] backup do banco autoritativo;
- [ ] backup atômico;
- [ ] integridade validada;
- [ ] restore real testado;
- [ ] backup pré-migration;
- [ ] rollback em falha;
- [ ] dados fictícios sobrevivem ao ciclo backup/restore.

### SPEC-007 — Testes automatizados

A SPEC-007 é transversal.

Política recomendada:

```text
cada bug corrigido
→ teste de regressão

cada regra nova
→ teste

cada migration
→ teste em banco temporário

cada rota protegida
→ teste de autenticação/autorização
```

Não esperar o final do projeto para criar testes.

Gate geral:

- [ ] testes isolados de banco operacional;
- [ ] dados fictícios;
- [ ] comportamento determinístico;
- [ ] API coberta nos fluxos críticos;
- [ ] migrations testadas;
- [ ] regressões conhecidas cobertas;
- [ ] evidências salvas.

## 12. Fase 5 — Experiência

### SPEC-009 — Interface clínica e Design System

A modernização visual começa após estabilizar contratos essenciais.

Ordem recomendada:

```text
inventário frontend
→ tokens
→ componentes base
→ login
→ shell
→ dashboard
→ pacientes
→ agenda
→ prontuário
→ financeiro
→ configurações
→ usuários
→ relatórios
```

Não redesenhar regras de negócio no React.

Gate mínimo:

- [ ] design tokens definidos;
- [ ] componentes reutilizáveis;
- [ ] login usa autenticação real;
- [ ] dashboard usa dados reais;
- [ ] loading/empty/error states;
- [ ] permissões refletidas na navegação;
- [ ] prontuário preserva privacidade;
- [ ] financeiro mostra período correto;
- [ ] 1366×768 e 1920×1080 validados;
- [ ] foco/teclado/contraste básicos validados.

## 13. Fase 6 — Distribuição

### SPEC-010 — Instalador Windows

Somente empacotar como versão candidata quando:

- backend estiver estável;
- banco autoritativo definido;
- migrations estiverem controladas;
- frontend principal estiver funcional;
- backup/restore estiverem confiáveis.

Fluxo alvo:

```text
ClinicaGabriela-Setup.exe
→ instalar
→ atalho
→ abrir
→ backend inicia
→ health OK
→ login
```

Gate mínimo:

- [ ] Windows sem Python;
- [ ] Windows sem Node.js;
- [ ] backend empacotado;
- [ ] Electron inicia e encerra backend;
- [ ] dados fora da pasta de instalação;
- [ ] upgrade preserva dados;
- [ ] migrations possuem backup;
- [ ] rollback testado;
- [ ] uninstall/reinstall testado;
- [ ] logs sanitizados;
- [ ] licença validada;
- [ ] aplicação funciona sem internet para recursos locais.

## 14. Fase 7 — Homologação

A homologação final não é uma nova feature.

É a validação integrada das Specs.

Fluxo mínimo:

```text
instalação limpa
→ configuração inicial
→ login
→ paciente
→ agenda
→ prontuário
→ financeiro
→ backup
→ fechar
→ reiniciar
→ restaurar em ambiente controlado
→ upgrade
→ regressão
```

### Evidências mínimas

- versão do build;
- commit/tag;
- resultado dos testes;
- SO utilizado;
- banco fictício utilizado;
- relatório de migration;
- relatório de backup/restore;
- smoke test;
- falhas encontradas e resoluções;
- decisões funcionais pendentes.

## 15. Dependências resumidas

```text
SPEC-001
   ↓
SPEC-002
   ↓
SPEC-008
   ├───────────────┐
   ↓               ↓
SPEC-003        SPEC-006 parcial
   ↓
SPEC-004
   ↓
SPEC-005
   ↓
SPEC-006 completa
   ↓
SPEC-009
   ↓
SPEC-010
```

A SPEC-007 acompanha todas as setas.

## 16. Estratégia de branches

Recomendação:

```text
main
└─ feature/spec-002-auth-security
└─ feature/spec-008-architecture-unification
└─ feature/spec-003-clinical-integrity
└─ feature/spec-004-agenda
└─ feature/spec-005-finance
└─ feature/spec-006-backup-recovery
└─ feature/spec-009-interface
└─ feature/spec-010-windows-installer
```

Evitar uma única branch gigantesca contendo todo o roadmap.

A SPEC-007 normalmente será implementada junto às branches das funcionalidades testadas.

## 17. Política de commits

Commits devem ser pequenos e coerentes.

Exemplos:

```text
test: cover inactive user authentication
feat: reject inactive users during login
test: cover protected patient routes
feat: enforce authentication on patient routes
```

Não agrupar segurança, agenda, interface e instalador em um mesmo commit.

## 18. Política de merge

Antes de merge:

```text
git status
→ testes
→ diff
→ revisão
→ evidências
→ autorização
```

Não fazer merge automático apenas porque a branch compila.

## 19. Dados e segurança durante desenvolvimento

Nunca utilizar dados reais de pacientes em:

- testes;
- fixtures;
- screenshots;
- commits;
- issues;
- documentação;
- logs de debug compartilhados.

Utilizar somente dados fictícios.

Não versionar:

- banco operacional;
- arquivos de licença;
- secrets;
- tokens;
- credenciais;
- `.env` de produção;
- backups com dados reais.

## 20. Definition of Done global

O projeto só poderá ser considerado pronto para entrega quando:

- [ ] SPEC-002 implementada e testada;
- [ ] fonte única de verdade estabelecida;
- [ ] integridade clínica validada;
- [ ] agenda validada;
- [ ] financeiro validado;
- [ ] backup e restore testados;
- [ ] suíte de testes crítica aprovada;
- [ ] interface principal homologada;
- [ ] instalador Windows homologado;
- [ ] upgrade sem perda de dados validado;
- [ ] licença validada;
- [ ] nenhum P0 conhecido aberto;
- [ ] evidências finais registradas.

## 21. Próxima execução

A próxima implementação recomendada é:

```text
SPEC-002 — Autenticação e Autorização Seguras
```

Antes de criar ou alterar código:

```text
git status
git branch --show-current
git log -1 --oneline
git fetch
```

Depois, a partir da base correta e após a documentação estar integrada conforme decisão do projeto, criar:

```text
feature/spec-002-auth-security
```

O primeiro incremento deverá começar por teste de autenticação de usuário inativo, seguido da implementação mínima necessária para fazê-lo passar.

## 22. Documentos

- `SPEC-001-auditoria.md`
- `SPEC-002-seguranca.md`
- `SPEC-003-integridade-clinica.md`
- `SPEC-004-agenda.md`
- `SPEC-005-financeiro.md`
- `SPEC-006-backup.md`
- `SPEC-007-testes.md`
- `SPEC-008-arquitetura.md`
- `SPEC-009-interface.md`
- `SPEC-010-instalador.md`

## 23. Estado deste roadmap

Este roadmap organiza a sequência de implementação.

Ele não declara que as funcionalidades das SPEC-002 a SPEC-010 já foram implementadas, testadas ou homologadas.

A única conclusão registrada neste conjunto é a auditoria estática da SPEC-001 e o detalhamento documental das demais especificações.
