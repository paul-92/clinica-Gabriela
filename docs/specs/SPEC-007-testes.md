# SPEC-007 — Testes Automatizados

**Status:** DRAFT — especificação detalhada, pendente de validação e implementação.  
**Prioridade:** P1  
**Origem:** SPEC-001 — Auditoria  
**Dependências:** SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006, SPEC-008, SPEC-009 e SPEC-010  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir uma estratégia de testes automatizados para a Clínica Gabriela que permita validar regras de negócio, segurança, persistência, API, integrações internas e fluxos críticos antes de considerar qualquer funcionalidade concluída.

A auditoria identificou cobertura automatizada muito limitada. Esta SPEC estabelece critérios mínimos de qualidade, isolamento, dados fictícios, evidências e regressão.

Nenhuma funcionalidade deverá ser considerada homologada apenas porque “funciona na máquina do desenvolvedor”.

## 2. Princípios
- Testes devem validar comportamento, não apenas execução sem erro.
- Dados reais de pacientes não devem ser usados.
- Testes devem ser determinísticos sempre que possível.
- Falhas devem ser reproduzíveis.
- Banco de teste deve ser isolado do banco operacional.
- Testes não devem depender de ordem de execução.
- Testes de segurança e autorização são obrigatórios em rotas protegidas.
- Regressão deve proteger funcionalidades já homologadas.
- Testes devem refletir as regras definidas nas Specs, não inventar regras novas.
- Cobertura percentual é útil, mas não substitui cenários relevantes.

## 3. Escopo
A estratégia deverá contemplar:

- autenticação;
- autorização;
- usuários;
- pacientes;
- psicólogos;
- agenda;
- prontuário;
- financeiro;
- configurações;
- licenciamento;
- backup e restauração;
- arquitetura backend;
- API;
- frontend Electron/React;
- fluxos desktop legados ainda mantidos;
- migrations;
- instalador, em testes apropriados.

## 4. Estado atual
Antes da implementação deverá ser inventariado o estado real dos testes existentes.

A auditoria encontrou cobertura limitada e deverá ser confirmado:

- arquivos de teste existentes;
- frameworks utilizados;
- fixtures;
- mocks;
- banco temporário;
- testes de API;
- testes frontend;
- testes desktop;
- testes de integração;
- automação em CI, se existir.

Nenhuma cobertura será assumida sem evidência.

## 5. Pirâmide de testes
A estratégia deverá priorizar uma base ampla de testes rápidos e uma camada menor de testes mais integrados.

Estrutura conceitual:

```text
Muitos testes unitários
↓
Testes de serviço/repositório
↓
Testes de API
↓
Testes de integração
↓
Poucos testes end-to-end
```

O equilíbrio final deverá considerar custo de manutenção e risco funcional.

## 6. Testes unitários
Devem validar regras de negócio isoladas.

Exemplos:

- validação de valores;
- transições de status;
- sobreposição de agenda;
- regras de autenticação;
- permissões;
- cálculos financeiros;
- transformação de datas;
- helpers de segurança;
- regras de licenciamento.

Sempre que possível, serviços devem ser testados sem depender de UI.

## 7. Testes de repositório
Devem validar persistência e consultas.

Exemplos:

- criação;
- atualização;
- filtros;
- relacionamentos;
- constraints;
- rollback;
- consultas por período;
- exclusão/inativação;
- integridade referencial.

Esses testes deverão usar banco temporário e isolado.

## 8. Testes de serviço
Devem validar regras de negócio com dependências reais ou controladas.

Exemplos:

- agendamento com conflito;
- pagamento inválido;
- usuário inativo;
- prontuário sem paciente válido;
- cancelamento;
- estorno;
- restauração;
- backup pré-migração.

## 9. Testes de API
A API deverá possuir testes automatizados para:

- status HTTP;
- payloads;
- autenticação;
- autorização;
- validações;
- erros controlados;
- persistência;
- filtros;
- contratos principais.

Exemplo:

```text
POST /auth/login
→ 200 com credencial válida
→ 401 com credencial inválida
→ 403 ou 401 conforme regra para usuário inativo
```

## 10. Testes de autenticação
Devem cobrir no mínimo:

- login válido;
- senha inválida;
- usuário inexistente;
- usuário inativo;
- token ausente;
- token inválido;
- token expirado;
- token válido;
- endpoint `/auth/me`;
- segredo ausente ou configuração inválida.

## 11. Testes de autorização
Para cada rota protegida deverá existir pelo menos um teste de permissão.

Exemplos:

```text
admin → permitido
recepção → permitido ou bloqueado conforme regra
psicólogo → permitido ou bloqueado conforme regra
não autenticado → bloqueado
```

Não basta esconder botão na interface.

## 12. Testes de pacientes
Devem cobrir:

- criação válida;
- campos obrigatórios;
- atualização parcial;
- identificadores duplicados, se aplicável;
- inativação;
- busca;
- filtros;
- dados inválidos;
- autorização.

## 13. Testes de psicólogos
Devem cobrir:

- criação válida;
- atualização;
- status ativo/inativo;
- vínculo com agenda;
- autorização;
- dados inválidos;
- filtros e busca.

## 14. Testes de agenda
Conforme SPEC-004:

- intervalo válido;
- intervalo inválido;
- conflito do mesmo profissional;
- horários adjacentes;
- profissionais diferentes;
- edição sem conflito consigo mesmo;
- edição com conflito;
- cancelamento libera horário;
- status inválido;
- transição inválida;
- remarcação;
- concorrência;
- rollback.

## 15. Testes de prontuário
Conforme SPEC-003:

- paciente existente;
- psicólogo existente;
- vínculo correto;
- tentativa de registro órfão;
- atualização parcial;
- autorização;
- acesso indevido;
- histórico, se implementado;
- retificação, se aprovada;
- exclusão/inativação conforme regra.

## 16. Testes financeiros
Conforme SPEC-005:

- valor zero;
- valor negativo;
- precisão monetária;
- status válido;
- status inválido;
- transição inválida;
- pagamento;
- cancelamento;
- estorno;
- resumo mensal;
- filtros por período;
- rollback;
- autorização.

## 17. Testes de backup
Conforme SPEC-006:

- criação;
- integridade;
- restauração;
- falha;
- arquivo incompatível;
- backup pré-restore;
- backup pré-migração;
- concorrência;
- retenção;
- autorização.

## 18. Testes de licenciamento
Devem validar:

- licença válida;
- licença inválida;
- licença expirada;
- trial;
- ausência de licença;
- alteração indevida de arquivo;
- comportamento offline;
- erros controlados.

Nenhum segredo de emissão deverá ser exposto em fixtures.

## 19. Testes de migrations
Cada migration relevante deverá possuir estratégia de teste.

Cenários:

- banco vazio;
- banco com dados legados fictícios;
- migration para frente;
- rollback, quando suportado;
- preservação de dados;
- constraints;
- conversões;
- versionamento de schema.

## 20. Banco de testes
Testes não deverão usar:

```text
data/clinica_psicologia.db
backend/data/clinica_api.db
```

ou qualquer banco operacional real.

Utilizar banco temporário isolado por teste, módulo ou sessão conforme necessidade.

Exemplos:

```text
tmp_path / "test.db"
SQLite :memory:
```

A escolha dependerá do comportamento testado.

## 21. Isolamento
Cada teste deverá começar em estado conhecido.

Não depender de:

- dados criados por outro teste;
- ordem alfabética;
- horário imprevisível;
- arquivos locais do desenvolvedor;
- conexão com internet, salvo teste explicitamente de integração externa;
- credenciais pessoais.

## 22. Fixtures
Fixtures deverão ser pequenas, previsíveis e reutilizáveis.

Exemplos:

- admin ativo;
- recepção ativa;
- psicólogo ativo;
- paciente fictício;
- atendimento fictício;
- pagamento fictício.

Evitar fixtures gigantes que escondam o cenário testado.

## 23. Dados fictícios
Somente dados sintéticos.

Exemplo:

```text
Paciente Teste 001
CPF fictício válido para teste, se necessário
email: paciente001@example.test
```

Nunca copiar dados reais do ambiente da clínica.

## 24. Geração de dados
Quando necessário, factories poderão ser utilizadas.

A geração deverá permitir controlar campos relevantes.

Exemplo conceitual:

```python
make_patient(active=True)
make_appointment(status="scheduled")
```

Valores aleatórios sem seed devem ser evitados quando dificultarem reprodução.

## 25. Mocks
Mocks devem ser usados quando isolam dependências externas ou comportamentos lentos.

Não usar mocks para esconder defeitos do próprio domínio.

Exemplos adequados:

- relógio;
- filesystem;
- serviço externo;
- emissor de licença;
- integração futura.

## 26. Tempo
Regras dependentes de data/hora deverão usar mecanismo testável.

Evitar:

```python
datetime.now()
```

espalhado pelo domínio sem abstração quando isso impedir testes determinísticos.

Poderá ser utilizada função central ou clock injetável.

## 27. Concorrência
Cenários críticos deverão ser testados de forma controlada.

Exemplos:

- dois agendamentos simultâneos;
- duas alterações financeiras;
- backup durante escrita.

O objetivo é provar ausência de estado inconsistente.

## 28. Rollback
Toda operação transacional relevante deverá possuir teste de falha intermediária.

Exemplo:

```text
etapa 1 persistida
etapa 2 falha
→ nenhuma alteração final permanece
```

## 29. Erros controlados
Testes devem verificar não apenas que existe erro, mas que o contrato é adequado.

Exemplo:

```text
status HTTP correto
mensagem controlada
sem stack trace
sem segredo
```

## 30. Testes frontend
A interface Electron/React deverá possuir testes para componentes e fluxos críticos.

Prioridades:

- login;
- sessão;
- navegação por perfil;
- estados de loading;
- erro;
- vazio;
- agenda;
- financeiro;
- prontuário;
- indicadores;
- formulários.

Os detalhes da ferramenta deverão ser escolhidos após inventário do frontend.

## 31. Testes de contrato frontend-backend
Mudanças de API não deverão quebrar silenciosamente o frontend.

Devem ser validados:

- nomes de campos;
- tipos;
- status HTTP;
- enums;
- paginação;
- filtros;
- tratamento de erro.

## 32. Electron
Fluxos críticos do Electron deverão validar:

- inicialização;
- comunicação com backend;
- falha do backend;
- remoção de fallback inseguro;
- encerramento;
- sessão;
- comportamento offline local.

## 33. Desktop Tkinter
Enquanto o desktop legado estiver mantido, testes adequados deverão proteger regras críticas que ainda passam por ele.

Não é necessário testar cada pixel.

Priorizar:

- autenticação;
- autorização;
- acesso às funcionalidades;
- serviços chamados;
- comportamento de erro.

## 34. End-to-end
Testes E2E deverão ser poucos e focados nos fluxos mais críticos.

Exemplos:

```text
login
→ criar paciente
→ agendar atendimento
→ registrar pagamento
```

ou:

```text
backup
→ alterar dados
→ restaurar
→ validar recuperação
```

E2E não deverá substituir testes de domínio.

## 35. Instalador
Conforme SPEC-010, deverão existir testes de instalação em ambiente limpo.

Cenários:

- instalação sem Python;
- instalação sem Node;
- primeiro uso;
- criação de dados;
- reinício;
- atualização;
- preservação de banco;
- desinstalação;
- reinstalação.

Esses testes podem ser manuais controlados ou automatizados conforme viabilidade.

## 36. Smoke tests
Deverá existir um conjunto curto de smoke tests para verificar rapidamente se o sistema está operacional.

Exemplo:

```text
backend inicia
/health responde
login funciona
consulta básica funciona
frontend abre
```

## 37. Regressão
Cada bug corrigido deverá gerar, quando viável, um teste que falhava antes da correção.

Isso reduz reincidência.

Exemplo:

```text
bug: resumo mensal somava histórico
→ criar teste que comprova isolamento por mês
```

## 38. Cobertura
Cobertura deverá ser medida, mas sem meta cega.

Priorizar cobertura de:

- serviços;
- domínio;
- segurança;
- finanças;
- agenda;
- backup;
- migrations.

Uma porcentagem alta sem cenários relevantes não será suficiente.

A meta numérica deverá ser definida após baseline real.

## 39. Organização dos testes
Estrutura candidata:

```text
tests/
  unit/
  integration/
  api/
  services/
  repositories/
  security/
  migrations/
  backup/
  e2e/
```

A estrutura final deverá respeitar o projeto existente.

## 40. Nomenclatura
Nomes de teste devem descrever comportamento.

Preferir:

```python
test_login_rejects_inactive_user()
test_monthly_summary_excludes_previous_month()
test_appointment_rejects_overlap_for_same_professional()
```

Evitar:

```python
test_1()
test_function()
```

## 41. Arrange, Act, Assert
Testes deverão ser legíveis.

Estrutura recomendada:

```text
Arrange → preparar cenário
Act → executar comportamento
Assert → validar resultado
```

## 42. Velocidade
A suíte deverá permitir feedback rápido.

Separar testes lentos de testes rápidos quando necessário.

Exemplo conceitual:

```text
unit → segundos
integration → maior duração
e2e → execução seletiva
```

## 43. CI
A necessidade de pipeline CI deverá ser avaliada.

Fluxo desejado no futuro:

```text
push/PR
→ instalar dependências
→ executar testes backend
→ executar testes frontend
→ build
→ reportar falha
```

Nenhum merge automatizado é definido por esta SPEC.

## 44. Dependências de teste
Novas bibliotecas somente deverão ser adicionadas se necessárias.

Antes disso, inventariar:

- pytest;
- FastAPI TestClient/httpx;
- ferramentas frontend;
- plugins;
- coverage.

Não adicionar dependências redundantes sem motivo.

## 45. Evidências
Cada gate relevante deverá produzir evidência.

Exemplos:

- saída do pytest;
- relatório de cobertura;
- logs de smoke test;
- resultado de build;
- relatório de restore;
- screenshot somente quando realmente útil.

Não declarar “aprovado” sem evidência.

## 46. Testes esperados por Spec
| SPEC | Evidência mínima |
|---|---|
| SPEC-002 | autenticação e autorização |
| SPEC-003 | integridade clínica |
| SPEC-004 | conflitos, status e concorrência |
| SPEC-005 | precisão, período e transações |
| SPEC-006 | backup e restore |
| SPEC-008 | arquitetura e persistência única |
| SPEC-009 | fluxos principais de UI |
| SPEC-010 | instalação e atualização |

## 47. Gates de implementação
1. **Inventário:** testes, fixtures, ferramentas e cobertura atual.
2. **Isolamento:** banco temporário e configuração de testes.
3. **Factories/fixtures:** dados fictícios reutilizáveis.
4. **Segurança:** autenticação e autorização.
5. **Domínio:** pacientes, psicólogos, clínica e agenda.
6. **Financeiro:** valores, períodos e transações.
7. **Backup:** backup, restore e rollback.
8. **Migrations:** dados legados e compatibilidade.
9. **API:** contratos e erros.
10. **Frontend:** componentes e fluxos principais.
11. **Electron/Desktop:** integração crítica.
12. **E2E:** poucos fluxos essenciais.
13. **Cobertura:** baseline e relatório.
14. **CI:** se aprovado.
15. **Regressão:** suíte consolidada.

## 48. Critérios de aceitação
- **AC-001:** testes não utilizam banco operacional.
- **AC-002:** dados reais não são usados.
- **AC-003:** autenticação e autorização possuem cobertura adequada.
- **AC-004:** regras críticas de agenda possuem testes.
- **AC-005:** regras financeiras possuem testes de precisão e período.
- **AC-006:** backup possui teste de restauração.
- **AC-007:** operações transacionais possuem testes de rollback.
- **AC-008:** migrations críticas possuem teste de preservação de dados.
- **AC-009:** principais contratos de API são testados.
- **AC-010:** principais fluxos frontend possuem teste apropriado.
- **AC-011:** bugs corrigidos geram regressão quando viável.
- **AC-012:** resultados de testes podem ser reproduzidos.
- **AC-013:** nenhuma funcionalidade é declarada homologada sem evidência.

## 49. Fora do escopo
Esta SPEC não define:

- ferramenta comercial de QA;
- testes de invasão profissionais;
- pentest externo;
- certificação regulatória;
- testes de carga em escala hospitalar;
- observabilidade de produção;
- SLA;
- chaos engineering;
- device farm.

Esses itens poderão ser especificados futuramente.

## 50. Definition of Done
- [ ] Inventário de testes existente concluído.
- [ ] Banco de teste isolado configurado.
- [ ] Fixtures/factories com dados fictícios.
- [ ] Testes de autenticação implementados.
- [ ] Testes de autorização implementados.
- [ ] Testes de pacientes implementados.
- [ ] Testes de psicólogos implementados.
- [ ] Testes de agenda implementados.
- [ ] Testes de prontuário implementados.
- [ ] Testes financeiros implementados.
- [ ] Testes de backup/restauração implementados.
- [ ] Testes de migrations implementados.
- [ ] Testes de API implementados.
- [ ] Testes frontend prioritários implementados.
- [ ] Smoke tests definidos.
- [ ] Regressões relevantes adicionadas.
- [ ] Cobertura medida.
- [ ] Evidências registradas.
- [ ] Nenhum dado real presente nos testes.
- [ ] Documentação atualizada.

## 51. Estado desta SPEC
Esta SPEC define a estratégia esperada de testes automatizados, mas não representa cobertura implementada.

Os detalhes de ferramentas, baseline e meta de cobertura deverão ser definidos após inventário do projeto atual.

Nenhum gate, critério de aceitação ou item do Definition of Done foi declarado concluído.
