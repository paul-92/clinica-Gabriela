# SPEC-009 — Interface Clínica e Design System

**Status:** DRAFT — especificação detalhada de interface, pendente de validação visual e implementação.  
**Prioridade:** P1  
**Origem:** evolução funcional e visual da Clínica Gabriela  
**Dependências:** SPEC-002, SPEC-004, SPEC-005, SPEC-007 e SPEC-008  
**Relacionada:** SPEC-010  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir a experiência visual, a navegação, os componentes reutilizáveis e os padrões de interação da Clínica Gabriela, consolidando o Electron/React como interface principal da aplicação.

A nova interface deverá modernizar a experiência sem alterar ou duplicar regras de negócio que pertencem ao backend.

Nenhum mockup ou componente descrito nesta SPEC deve ser considerado implementado sem evidência no código e validação visual.

## 2. Princípios
- Electron/React é o frontend principal alvo.
- O backend continua sendo autoridade de autenticação, autorização, validações e regras de negócio.
- A interface deve ser clínica, acolhedora, elegante e profissional.
- Clareza é mais importante que excesso de informação.
- Componentes devem ser consistentes entre telas.
- Estados de loading, vazio, erro e sucesso devem ser explícitos.
- A interface não deve exibir dados fictícios como se fossem dados reais.
- A navegação deve respeitar o perfil do usuário.
- Acessibilidade e legibilidade devem ser consideradas desde o início.

## 3. Direção visual
A identidade visual deverá seguir uma linguagem suave, contemporânea e acolhedora.

Paleta conceitual:

- verde sálvia;
- verde sálvia claro;
- creme/off-white;
- rosa blush;
- bege quente;
- texto em verde floresta escuro;
- branco para superfícies;
- cinzas suaves para elementos secundários.

A paleta final deverá ser definida em tokens.

## 4. Marca
A identidade visual poderá utilizar como referência:

```text
MG
coração / puzzle
elementos botânicos
```

O uso deverá ser elegante e discreto.

Evitar:

- excesso de elementos decorativos;
- fundos muito carregados;
- aparência infantil;
- contraste insuficiente;
- poluição visual.

## 5. Tipografia
A interface poderá combinar:

- fonte elegante para títulos;
- fonte de alta legibilidade para corpo e dados.

A escolha final deverá considerar disponibilidade no pacote da aplicação e compatibilidade com Windows.

Não depender de fonte externa carregada pela internet.

## 6. Hierarquia tipográfica
Definir pelo menos:

```text
Display
Heading 1
Heading 2
Heading 3
Body
Body small
Label
Caption
```

Cada nível deverá possuir tamanho, peso e altura de linha consistentes.

## 7. Tokens de design
O design system deverá concentrar valores reutilizáveis.

Exemplo conceitual:

```text
color.primary
color.surface
color.background
color.success
color.warning
color.error
color.text.primary
color.text.secondary
radius.sm
radius.md
radius.lg
spacing.1
spacing.2
spacing.3
shadow.card
```

Evitar valores arbitrários repetidos em cada componente.

## 8. Grid e espaçamento
A interface deverá utilizar espaçamento consistente.

Recomenda-se escala previsível, por exemplo baseada em múltiplos pequenos.

Cards e seções deverão possuir respiro suficiente, especialmente em telas clínicas.

## 9. Bordas e formas
Direção desejada:

- cantos arredondados;
- bordas suaves;
- sombras discretas;
- cards com separação visual leve;
- botões com destaque controlado.

Evitar excesso de sombra forte ou efeito “3D”.

## 10. Responsividade
A aplicação é desktop, mas deverá adaptar-se a resoluções diferentes.

Alvos mínimos propostos:

```text
1366 x 768
1920 x 1080
```

Também deverão ser testadas escalas do Windows:

```text
100%
125%
```

A interface não deverá quebrar em resoluções comuns de notebooks.

## 11. Estrutura principal
A aplicação deverá utilizar layout consistente:

```text
Sidebar
Topbar
Conteúdo principal
Área contextual / modal quando necessário
```

A sidebar deverá permanecer visualmente estável entre telas.

## 12. Sidebar
A navegação lateral poderá incluir, conforme autorização:

- Dashboard;
- Agenda;
- Pacientes;
- Prontuários;
- Financeiro;
- Relatórios;
- Configurações;
- Usuários.

Itens devem ser exibidos conforme perfil e política da SPEC-002.

Esconder item não substitui autorização backend.

## 13. Estado ativo
O item selecionado deverá possuir destaque claro.

Exemplo:

```text
fundo sálvia claro
ícone em verde escuro
texto em destaque
```

## 14. Topbar
A barra superior deverá poder exibir:

- título da tela;
- nome do usuário;
- perfil;
- acesso a sessão;
- ações contextuais;
- notificações futuras, se houver.

Não sobrecarregar com informações secundárias.

## 15. Ícones
Preferir ícones lineares, simples e consistentes.

A biblioteca atual poderá ser aproveitada se compatível.

Não misturar estilos de ícones diferentes sem motivo.

## 16. Dashboard
O Dashboard deverá entregar visão rápida da operação.

Blocos possíveis:

- atendimentos do dia;
- próximos atendimentos;
- pacientes ativos;
- receitas do período;
- despesas do período;
- pendências;
- ações rápidas.

Os dados exibidos devem vir do backend.

## 17. KPIs
Cards de KPI deverão conter:

```text
título
valor
contexto temporal
indicador opcional
```

Exemplo adequado:

```text
Receitas — Setembro
R$ 8.450,00
```

Exemplo inadequado:

```text
Receita mensal
R$ 8.450,00
```

quando o backend estiver retornando acumulado histórico.

A SPEC-005 governa a semântica financeira.

## 18. Ações rápidas
O Dashboard poderá oferecer:

- Novo paciente;
- Novo atendimento;
- Registrar pagamento;
- Abrir prontuário.

As ações deverão respeitar permissões.

## 19. Agenda
A tela de Agenda deverá permitir visualização clara dos atendimentos.

Visões possíveis:

- dia;
- semana;
- lista.

A implementação final dependerá da complexidade aprovada.

## 20. Card de atendimento
Cada atendimento poderá apresentar:

- horário;
- paciente;
- profissional;
- status;
- observação curta permitida;
- ações contextuais.

Não exibir informação clínica sensível desnecessária na agenda.

## 21. Estados visuais da agenda
Status poderão possuir representação visual distinta:

- agendado;
- concluído;
- cancelado;
- falta;
- remarcado.

As cores devem reforçar, não substituir, o texto.

## 22. Conflitos
A interface poderá alertar sobre conflito, mas a regra final pertence ao backend.

Exemplo:

```text
Este horário já está ocupado para o profissional selecionado.
```

## 23. Pacientes
A tela de Pacientes deverá possuir:

- busca;
- filtros;
- lista ou tabela;
- ação de cadastro;
- acesso ao perfil;
- status ativo/inativo, se aplicável.

## 24. Lista de pacientes
Cada linha/card poderá exibir:

- nome;
- telefone;
- idade ou nascimento, se pertinente;
- último atendimento;
- status.

Evitar exibir excesso de dados sensíveis na visão geral.

## 25. Perfil do paciente
O perfil poderá conter:

- dados pessoais;
- contatos;
- histórico de atendimentos;
- vínculo com prontuário;
- informações administrativas.

Organizar em seções ou abas.

## 26. Prontuário
A interface de prontuário deverá ser mais reservada e orientada à leitura e registro clínico.

Estrutura proposta:

```text
Cabeçalho do paciente
Evoluções
Anexos
Plano de metas
Documentos
```

Somente se esses recursos existirem ou forem aprovados.

## 27. Evoluções
As evoluções deverão priorizar legibilidade.

Cada registro poderá exibir:

- data;
- profissional;
- conteúdo;
- estado;
- histórico/retificação quando aprovado.

Evitar edição silenciosa de conteúdo clínico histórico.

A SPEC-003 governa as regras.

## 28. Notas privadas
Campos privados devem ser visualmente diferenciados e protegidos por autorização.

A interface não deverá pressupor acesso amplo.

## 29. Financeiro
A tela Financeiro deverá separar claramente:

- resumo;
- receitas;
- despesas;
- pagamentos;
- filtros;
- período.

## 30. Resumo financeiro
KPIs possíveis:

- receitas;
- despesas;
- saldo;
- pendentes;
- pagos.

Sempre exibir o período associado.

## 31. Gráficos
Gráficos poderão incluir:

- evolução mensal;
- receitas x despesas;
- distribuição por forma de pagamento;
- distribuição por categoria.

Gráfico não deverá ser exibido com dados simulados em ambiente operacional.

## 32. Filtros financeiros
Deverão ser fáceis de usar:

- período;
- status;
- paciente;
- profissional;
- categoria;
- forma de pagamento.

O backend deverá aplicar regras de negócio e filtros relevantes.

## 33. Relatórios
A tela de Relatórios poderá centralizar visões consolidadas.

Não duplicar regra de cálculo no frontend.

Relatórios ainda não suportados pelo backend deverão aparecer como indisponíveis, não simulados.

## 34. Configurações
A tela deverá agrupar configurações de forma simples.

Exemplos:

- dados da clínica;
- preferências;
- backup;
- licença;
- sistema.

Ações críticas devem ser destacadas.

## 35. Usuários
A gestão de usuários deverá existir somente para perfis autorizados.

A tela poderá conter:

- nome;
- login;
- perfil;
- status;
- última atualização;
- ações.

Nunca exibir hash ou senha.

## 36. Login
A tela de login deverá ser simples e elegante.

Elementos:

- marca;
- usuário;
- senha;
- botão entrar;
- estado de carregamento;
- mensagem de erro controlada.

Sem fallback silencioso para credencial hardcoded.

## 37. Sessão
A interface deverá lidar com:

- sessão válida;
- token expirado;
- logout;
- falha de backend;
- reautenticação.

## 38. Loading
Componentes devem possuir estado de carregamento.

Evitar tela congelada sem feedback.

Possíveis padrões:

- skeleton;
- spinner;
- botão com estado busy.

## 39. Estado vazio
Toda lista deverá possuir empty state útil.

Exemplo:

```text
Nenhum atendimento encontrado para este período.
```

Quando permitido, poderá incluir ação:

```text
Novo atendimento
```

## 40. Erro
Mensagens devem ser humanas e controladas.

Exemplo:

```text
Não foi possível carregar os pacientes.
Tente novamente.
```

Evitar stack trace ou erro técnico bruto.

## 41. Sucesso
Ações concluídas poderão gerar confirmação discreta.

Exemplo:

```text
Paciente salvo com sucesso.
```

Evitar excesso de popups.

## 42. Modais
Modais deverão ser usados apenas quando realmente necessários.

Adequados para:

- confirmação crítica;
- formulário curto;
- ação contextual.

Evitar modais profundos ou encadeados.

## 43. Confirmações críticas
Ações como:

- cancelar atendimento;
- estornar pagamento;
- restaurar backup;
- desativar usuário;

deverão exigir confirmação apropriada.

## 44. Formulários
Formulários deverão possuir:

- label sempre visível;
- ajuda contextual quando necessário;
- validação clara;
- indicação de obrigatório;
- estado de erro por campo;
- foco previsível.

## 45. Validação
A interface poderá validar formato básico, mas o backend continua como autoridade.

Exemplo:

```text
campo obrigatório
formato de email
data inválida
```

Regras críticas continuam no backend.

## 46. Máscaras
Máscaras poderão ser usadas para:

- telefone;
- CPF;
- datas;
- moeda.

Não devem corromper o valor enviado à API.

## 47. Acessibilidade
A interface deverá considerar:

- contraste;
- foco visível;
- navegação por teclado;
- labels;
- tamanho mínimo de clique;
- não depender apenas de cor;
- leitura confortável.

## 48. Teclado
Fluxos administrativos frequentes deverão ser utilizáveis com teclado.

Exemplos:

- Tab;
- Enter;
- Esc;
- atalhos futuros aprovados.

## 49. Feedback de foco
Campos e botões focados devem possuir indicação visual clara.

## 50. Contraste
A paleta sálvia/blush não deverá reduzir a legibilidade.

Textos principais devem usar contraste adequado sobre fundos claros.

## 51. Tabelas
Tabelas deverão ser usadas quando comparação entre linhas for importante.

Devem possuir:

- cabeçalho;
- alinhamento;
- loading;
- vazio;
- ações;
- paginação se necessária.

## 52. Cards
Cards são preferíveis para resumos, KPIs e agrupamentos.

Não transformar toda informação tabular em cards sem necessidade.

## 53. Tooltips
Tooltips podem explicar ícones menos óbvios.

Não esconder instruções essenciais apenas em tooltip.

## 54. Datas
Datas deverão seguir padrão brasileiro na apresentação:

```text
08/09/2026
```

Sem alterar o formato interno da API.

## 55. Horários
Horários deverão seguir padrão:

```text
14:30
```

A regra de timezone permanece com o domínio.

## 56. Moeda
Valores deverão ser apresentados como:

```text
R$ 1.234,56
```

A precisão vem da SPEC-005.

## 57. Privacidade
Dados clínicos não devem aparecer em:

- notificações genéricas;
- logs frontend;
- tooltips desnecessários;
- dashboard amplo;
- mensagens de erro.

## 58. Segurança visual
A interface deverá evitar ações que pareçam disponíveis quando o usuário não tem autorização.

Porém, autorização real deve ocorrer no backend.

## 59. Design system reutilizável
Deverão existir componentes comuns.

Exemplos:

```text
Button
Input
Select
Textarea
DatePicker
Card
KpiCard
Table
Modal
Drawer
Badge
Tabs
Toast
EmptyState
ErrorState
Skeleton
PageHeader
SidebarItem
```

## 60. Variantes de botão
Definir pelo menos:

- primary;
- secondary;
- ghost;
- danger.

Evitar criar estilos exclusivos para cada tela.

## 61. Badges
Badges devem ser usados para status.

Exemplos:

- Ativo;
- Inativo;
- Agendado;
- Pago;
- Cancelado.

Texto sempre presente.

## 62. Componentes de domínio
Além dos componentes genéricos, poderão existir:

- AppointmentCard;
- PatientCard;
- FinancialSummary;
- ClinicalTimeline;
- UserRoleBadge.

## 63. Organização do frontend
A organização deverá separar:

```text
components
pages
features
services/api
hooks
types
styles/tokens
```

A estrutura final deverá respeitar o frontend existente e evitar reorganização desnecessária sem benefício.

## 64. API client
Chamadas HTTP deverão ser centralizadas.

Evitar `fetch` espalhado por componentes sem padrão.

O client deverá tratar:

- base URL;
- token;
- erros;
- timeout;
- parsing.

## 65. Estado da aplicação
O estado global deverá ser usado somente quando necessário.

Exemplos:

- sessão;
- usuário;
- permissões;
- tema futuro.

Dados locais de tela podem permanecer locais.

## 66. Falha do backend
Se o backend local não iniciar:

```text
Não foi possível iniciar os serviços da Clínica Gabriela.
```

A interface deverá oferecer ação controlada de tentar novamente ou fechar.

Não autenticar localmente como fallback.

## 67. Modo offline
A aplicação é local e poderá funcionar sem internet.

Isso não significa funcionar sem backend local.

Recursos dependentes de internet futura devem ser claramente separados.

## 68. Performance visual
A interface deverá evitar:

- renderizações pesadas;
- tabelas gigantes sem paginação/virtualização;
- múltiplas chamadas redundantes;
- animações excessivas.

## 69. Animações
Animações devem ser discretas e funcionais.

Exemplos:

- transição de modal;
- hover;
- loading.

Evitar animações que atrasem tarefas administrativas.

## 70. Consistência
A mesma ação deverá parecer igual em toda aplicação.

Exemplo:

```text
Salvar
```

não deverá ser verde numa tela, rosa em outra e azul em outra sem significado.

## 71. Tema
O primeiro release poderá utilizar apenas tema claro.

Dark mode não é requisito obrigatório desta SPEC.

## 72. Landing/identidade
Caso exista tela institucional ou inicial, poderá usar:

```text
Marilia Gabriela Gaspar
Psicóloga — CRP 11/20433
```

somente se essa informação estiver aprovada para uso no produto.

A área operacional deverá permanecer funcional e objetiva.

## 73. Referências visuais
Os mockups e imagens de referência fornecidos para o projeto deverão ser tratados como direção visual, não como implementação pixel-perfect obrigatória.

O design final deverá preservar:

- suavidade;
- elegância;
- acolhimento;
- verde sálvia;
- blush;
- branco/creme;
- tipografia limpa;
- cards arredondados;
- ícones lineares.

## 74. Inventário antes da implementação
Antes de redesenhar, deverá ser inventariado:

- páginas existentes;
- componentes;
- rotas;
- estado global;
- client HTTP;
- estilos;
- bibliotecas;
- ícones;
- dependências;
- telas ainda não conectadas ao backend.

## 75. Estratégia de migração visual
A modernização deverá ocorrer por áreas.

Sequência proposta:

1. tokens e layout;
2. login;
3. shell/sidebar/topbar;
4. dashboard;
5. pacientes;
6. agenda;
7. prontuário;
8. financeiro;
9. configurações;
10. usuários;
11. relatórios.

A ordem poderá mudar conforme dependências funcionais.

## 76. Não duplicar frontend
Não construir uma nova interface completa separada da atual sem estratégia de substituição.

Preferir evolução controlada do Electron/React existente.

## 77. Testes
Conforme SPEC-007, deverão ser testados:

- renderização;
- loading;
- vazio;
- erro;
- permissões;
- login;
- formulários;
- navegação;
- contratos com API;
- fluxos críticos.

## 78. Testes visuais
Poderão ser utilizados screenshots de referência e revisão manual.

O objetivo é detectar regressões evidentes, não exigir pixel perfect em toda alteração.

## 79. Smoke test visual
Fluxo mínimo:

```text
abrir aplicação
→ login
→ dashboard
→ pacientes
→ agenda
→ prontuário
→ financeiro
→ logout
```

Sem erros visuais graves ou rotas quebradas.

## 80. Gates de implementação
1. **Inventário:** frontend atual.
2. **Tokens:** cores, tipografia, spacing, radius.
3. **Componentes base:** buttons, inputs, cards, states.
4. **Shell:** sidebar, topbar e layout.
5. **Login:** sessão real.
6. **Dashboard:** dados reais.
7. **Pacientes:** lista e perfil.
8. **Agenda:** visual e estados.
9. **Prontuário:** privacidade e histórico.
10. **Financeiro:** período e indicadores corretos.
11. **Configurações/Usuários:** permissões.
12. **Responsividade:** 1366×768 e 1920×1080.
13. **Acessibilidade:** contraste, foco e teclado.
14. **Testes:** conforme SPEC-007.
15. **Build:** Electron funcional.
16. **Homologação visual:** evidências e aceite.

## 81. Critérios de aceitação
- **AC-001:** Electron/React é a interface principal implementada.
- **AC-002:** layout é consistente entre telas.
- **AC-003:** design system possui tokens reutilizáveis.
- **AC-004:** navegação respeita perfil do usuário.
- **AC-005:** backend continua responsável pelas regras críticas.
- **AC-006:** loading, vazio e erro existem nas telas principais.
- **AC-007:** interface não usa fallback inseguro de autenticação.
- **AC-008:** dashboard não apresenta dados fictícios como reais.
- **AC-009:** financeiro exibe período e semântica corretos.
- **AC-010:** prontuário não expõe conteúdo sensível indevidamente.
- **AC-011:** telas funcionam em 1366×768 e 1920×1080.
- **AC-012:** navegação por teclado e foco básico funcionam.
- **AC-013:** componentes reutilizáveis reduzem duplicação.
- **AC-014:** smoke test visual principal é aprovado.

## 82. Fora do escopo
Esta SPEC não define:

- aplicativo mobile;
- portal público;
- website institucional completo;
- teleconsulta;
- chat;
- integração WhatsApp;
- dark mode obrigatório;
- customização de tema por usuário;
- white-label;
- animações avançadas;
- redesign completo do Tkinter.

## 83. Definition of Done
- [ ] Frontend atual inventariado.
- [ ] Design tokens definidos.
- [ ] Paleta validada.
- [ ] Tipografia validada.
- [ ] Componentes base implementados.
- [ ] Sidebar e topbar implementadas.
- [ ] Login modernizado e integrado ao backend real.
- [ ] Dashboard usa dados reais.
- [ ] Pacientes modernizado.
- [ ] Agenda modernizada.
- [ ] Prontuário modernizado.
- [ ] Financeiro modernizado.
- [ ] Configurações modernizadas.
- [ ] Usuários respeitam permissões.
- [ ] Loading/empty/error states implementados.
- [ ] Responsividade desktop validada.
- [ ] Acessibilidade básica validada.
- [ ] Testes frontend implementados.
- [ ] Smoke test visual aprovado.
- [ ] Build Electron aprovado.
- [ ] Nenhum dado fictício apresentado como real.
- [ ] Documentação atualizada.

## 84. Estado desta SPEC
Esta SPEC define a direção de interface e design system, mas não representa redesign implementado.

A implementação deverá ocorrer sobre o Electron/React existente, após inventário do frontend e respeitando a arquitetura definida na SPEC-008.

Nenhum gate, critério de aceitação ou item do Definition of Done foi declarado concluído.
