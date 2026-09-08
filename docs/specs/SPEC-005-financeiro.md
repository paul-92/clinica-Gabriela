# SPEC-005 — Financeiro

**Status:** DRAFT — especificação detalhada, pendente de validação funcional e implementação.  
**Prioridade:** P1  
**Origem:** SPEC-001 — Auditoria  
**Dependências:** SPEC-002, SPEC-003 e SPEC-008  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir as regras funcionais e técnicas do módulo financeiro da Clínica Gabriela, garantindo consistência entre receitas, despesas, pagamentos, períodos de apuração e indicadores apresentados na aplicação.

A implementação deverá corrigir ambiguidades identificadas na auditoria, especialmente a diferença entre valores históricos acumulados e indicadores apresentados como mensais.

Nenhuma regra descrita nesta SPEC deve ser considerada implementada sem testes e evidências.

## 2. Princípios
- O backend é a autoridade final sobre regras financeiras.
- Valores monetários não devem utilizar lógica sujeita a erro de ponto flutuante.
- Indicadores mensais devem considerar explicitamente o período selecionado.
- Cancelamentos, estornos e exclusões não devem apagar histórico de forma silenciosa.
- Receitas e despesas devem possuir status e datas com significado definido.
- A interface não pode exibir um valor como “mensal” quando a consulta representa todo o histórico.
- Regras de autorização devem respeitar a SPEC-002.
- Dados financeiros reais da clínica não devem ser utilizados em testes automatizados.

## 3. Escopo funcional
O domínio financeiro deverá tratar, conforme o modelo existente:

- receitas;
- pagamentos;
- despesas;
- situação do pagamento;
- data de competência;
- data de vencimento, quando existente;
- data de pagamento, quando existente;
- vínculo com atendimento ou paciente, quando aplicável;
- forma de pagamento, quando prevista;
- observações;
- cancelamento, estorno ou inativação;
- indicadores e resumos por período.

Antes da implementação, os modelos, schemas, repositories, services, rotas, migrations e interfaces existentes deverão ser inventariados.

## 4. Representação monetária
Valores financeiros deverão possuir precisão adequada para moeda.

Não utilizar `float` como representação de negócio quando isso puder causar erros de arredondamento.

A implementação deverá avaliar a melhor estratégia compatível com SQLite e SQLAlchemy, priorizando uma das abordagens:

1. `Decimal` com coluna numérica adequada; ou
2. armazenamento em unidade inteira mínima, como centavos.

A estratégia escolhida deverá ser única e consistente em todo o domínio.

Exemplo:

```text
R$ 123,45
```

não deverá ser tratado internamente de forma que possa resultar em:

```text
123.449999999
```

## 5. Regras de valor
Valores deverão ser validados conforme o tipo de lançamento.

Regra inicial proposta:

- receitas normais: valor maior que zero;
- despesas normais: valor maior que zero;
- estornos ou ajustes: devem usar operação ou status explícito, em vez de valor negativo arbitrário.

Valores iguais a zero deverão ser rejeitados, salvo se houver regra funcional específica aprovada.

Valores negativos não deverão ser aceitos como atalho para cancelamento ou estorno.

## 6. Status financeiros
Os status atuais deverão ser inventariados antes da implementação.

Estados conceituais possíveis para receitas ou pagamentos incluem:

- Pendente;
- Pago;
- Cancelado;
- Estornado;
- Vencido, caso seja calculado ou persistido;
- Parcial, somente se pagamentos parciais forem aprovados.

Os nomes finais deverão respeitar os enums e contratos existentes.

Strings arbitrárias não deverão ser aceitas.

## 7. Transições de status
A matriz definitiva será criada após o inventário.

Proposta conceitual:

| Origem | Destino | Condição |
|---|---|---|
| Pendente | Pago | Pagamento confirmado |
| Pendente | Cancelado | Cobrança cancelada |
| Pago | Estornado | Estorno autorizado |
| Pago | Pendente | Somente se houver regra explícita de correção |
| Cancelado | Pago | Não permitido sem reabertura explícita |

Transições incoerentes deverão ser rejeitadas pelo backend.

## 8. Datas financeiras
Cada data deve possuir significado claro.

A implementação deverá identificar e separar, quando aplicável:

- data de criação;
- competência;
- vencimento;
- pagamento;
- cancelamento;
- estorno.

Não utilizar uma única data para representar conceitos diferentes sem decisão explícita.

## 9. Competência e período
Os indicadores financeiros deverão usar uma regra de período claramente definida.

A competência mensal deverá ser baseada em um campo aprovado, por exemplo:

- data do pagamento;
- data da competência;
- data do atendimento;
- data de criação.

A decisão deve ser funcional, não arbitrária.

Até a aprovação, nenhum indicador deverá ser rotulado como “receita mensal” sem indicar qual data define o mês.

## 10. Correção do resumo mensal
A auditoria identificou que o resumo utilizado pela interface pode somar registros históricos enquanto a apresentação sugere um resultado mensal.

A implementação deverá corrigir esse comportamento.

Regra obrigatória:

```text
Indicador mensal = somente registros pertencentes ao período solicitado
```

Um resumo de setembro de 2026 não poderá incluir automaticamente valores de agosto, julho ou meses anteriores.

O período deverá ser informado de forma explícita ao serviço ou derivado de uma seleção clara da interface.

## 11. Intervalos de consulta
Consultas por período deverão utilizar limites bem definidos.

Exemplo conceitual para setembro de 2026:

```text
início: 2026-09-01 00:00:00
fim exclusivo: 2026-10-01 00:00:00
```

Preferir intervalos com fim exclusivo para reduzir erros de horário final do dia.

## 12. Receita
Uma receita deverá possuir origem compreensível e status consistente.

Quando vinculada a atendimento, o relacionamento deverá ser validado.

Não criar registros financeiros órfãos para atendimentos ou pacientes inexistentes quando esses vínculos forem obrigatórios no modelo.

A relação entre atendimento realizado, cancelado, falta e cobrança dependerá de aprovação funcional e integração com a SPEC-004.

## 13. Despesas
Despesas deverão possuir:

- valor válido;
- data ou competência;
- descrição ou categoria conforme o modelo existente;
- status, se aplicável.

Despesas canceladas não deverão desaparecer silenciosamente do histórico.

Categorias deverão ser validadas se o sistema possuir catálogo ou enum.

## 14. Pagamentos
O ato de marcar uma cobrança como paga deverá definir, no mínimo:

- status;
- data de pagamento;
- valor;
- forma de pagamento, quando aplicável.

A implementação deverá impedir estados contraditórios, por exemplo:

```text
status = PAGO
data_pagamento = nula
```

caso a regra de negócio exija data de pagamento.

## 15. Pagamentos parciais
Pagamentos parciais não serão assumidos como suportados.

Antes de implementar parcelamento ou pagamento parcial, deverá haver decisão funcional explícita.

Se não forem suportados, o sistema deverá impedir combinações que aparentem pagamento parcial.

## 16. Cancelamento
Cancelar uma cobrança ou despesa deverá preservar rastreabilidade.

O cancelamento não deverá ser implementado por exclusão física silenciosa.

Campos como:

- cancelado_em;
- cancelado_por;
- motivo;

poderão ser avaliados durante o inventário.

## 17. Estorno
Estorno deve ser diferente de cancelamento.

Conceitualmente:

```text
Cancelamento = cobrança deixou de ser válida antes da liquidação
Estorno = valor previamente pago foi revertido
```

A regra final deve ser validada com a clínica.

Um estorno não deverá apagar o pagamento original.

## 18. Exclusão física
Registros financeiros utilizados operacionalmente não deverão ser excluídos fisicamente por padrão.

Qualquer exclusão excepcional deverá possuir autorização e regra explícitas.

Histórico financeiro deve permanecer auditável.

## 19. Integração com agenda
A SPEC-004 definirá os estados do atendimento.

A SPEC-005 não deverá assumir automaticamente que:

- atendimento realizado gera cobrança;
- falta gera cobrança;
- cancelamento elimina cobrança;
- remarcação cria nova cobrança.

Essas regras precisam de decisão funcional.

A implementação deverá evitar acoplamento implícito antes dessa aprovação.

## 20. Indicadores
Indicadores poderão incluir, conforme aprovação e dados disponíveis:

- receitas do período;
- despesas do período;
- saldo do período;
- valores pendentes;
- valores pagos;
- quantidade de pagamentos;
- inadimplência;
- distribuição por forma de pagamento;
- distribuição por categoria de despesa.

Nenhum indicador deverá misturar períodos ou status incompatíveis.

## 21. Saldo
O saldo deverá possuir fórmula explícita.

Proposta:

```text
saldo = receitas consideradas no período - despesas consideradas no período
```

A definição de “receita considerada” depende da regra aprovada: paga, competência, caixa ou outra.

A interface deverá deixar claro se o indicador representa:

- caixa realizado;
- competência;
- valores previstos.

## 22. Regime financeiro
A clínica deverá decidir se os principais indicadores utilizam:

- regime de caixa;
- regime de competência;
- ambos, em visões separadas.

Nenhuma dessas opções deverá ser presumida como regra definitiva durante a implementação.

## 23. Filtros
Consultas financeiras deverão suportar filtros coerentes com o modelo existente, podendo incluir:

- período;
- status;
- paciente;
- profissional;
- forma de pagamento;
- categoria;
- tipo de lançamento.

Filtros deverão ser aplicados no backend quando influenciam regras ou volume de dados.

## 24. Autorização
A autorização deverá respeitar a SPEC-002.

Matriz inicial sujeita a aprovação:

| Perfil | Visualizar financeiro | Criar/alterar | Cancelar/estornar |
|---|---|---|---|
| Admin | Sim | Sim | Sim |
| Recepção | Sim* | Sim* | Sim* |
| Psicólogo | Restrito ou não | Restrito ou não | Não por padrão |

`*` O nível de acesso da recepção deverá ser aprovado.

Dados financeiros não deverão ficar expostos apenas porque a interface possui uma rota acessível.

## 25. API
Preservar endpoints existentes quando possível.

Operações equivalentes podem incluir:

```text
GET /finance/payments
POST /finance/payments
PUT/PATCH /finance/payments/{id}

GET /finance/expenses
POST /finance/expenses
PUT/PATCH /finance/expenses/{id}

GET /finance/summary
```

Os contratos finais deverão respeitar o backend existente.

## 26. Erros controlados
Erros técnicos não deverão ser expostos ao usuário.

Exemplo inadequado:

```text
IntegrityError
```

Exemplo esperado:

```text
O valor informado deve ser maior que zero.
```

ou:

```text
Não é possível estornar um pagamento que ainda está pendente.
```

## 27. Testes obrigatórios
| Cenário | Resultado esperado |
|---|---|
| Receita com valor zero | Rejeitada |
| Receita com valor negativo | Rejeitada |
| Despesa com valor zero | Rejeitada |
| Despesa com valor negativo | Rejeitada |
| Status inválido | Rejeitado |
| Transição inválida | Rejeitada |
| Pagamento válido | Persistido |
| Cancelamento | Histórico preservado |
| Estorno válido | Histórico preservado |
| Estorno de pendente | Rejeitado |
| Resumo mensal | Considera apenas o período |
| Meses diferentes | Não são somados indevidamente |
| Filtro por status | Resultado consistente |
| Falha na persistência | Sem registro parcial |
| Usuário sem permissão | Rejeitado |

## 28. Casos de aceitação para período
Dado:

```text
Agosto: R$ 1.000,00
Setembro: R$ 2.000,00
```

Ao solicitar setembro:

```text
Resultado esperado: R$ 2.000,00
```

e não:

```text
R$ 3.000,00
```

Esse caso deverá possuir teste automatizado.

## 29. Casos de precisão
Operações monetárias deverão ser testadas para evitar erros de ponto flutuante.

Exemplo:

```text
0,10 + 0,20 = 0,30
```

O resultado financeiro não poderá apresentar resíduos de representação binária.

## 30. Transações
Operações que alteram múltiplos registros relacionados deverão ser atômicas.

Se qualquer etapa falhar:

```text
ROLLBACK
```

Nenhum estado parcial deverá permanecer persistido.

## 31. Migrações
Qualquer mudança de tipo monetário, status ou datas deverá utilizar migração segura.

Antes de migrar:

- inventariar dados existentes;
- criar backup;
- validar conversão;
- testar rollback;
- garantir que registros legados não sejam silenciosamente truncados ou arredondados de forma incorreta.

A SPEC-006 deverá ser considerada antes de migrações destrutivas.

## 32. Interface
A interface Electron/React deverá consumir os valores reais do backend.

Não exibir:

- gráficos fictícios como dados reais;
- valores históricos com rótulo mensal;
- status locais diferentes do backend;
- totais calculados apenas no frontend quando a regra pertence ao domínio.

Estados de loading, vazio e erro deverão ser explícitos.

## 33. Gates de implementação
1. **Inventário:** modelos, schemas, repositories, services, rotas, migrations e interfaces.
2. **Decisões funcionais:** caixa/competência, status, cancelamento, estorno, parcial, integração com agenda.
3. **Testes de domínio:** demonstrar as inconsistências existentes.
4. **Precisão monetária:** definir representação única.
5. **Validações:** valores, datas, status e relacionamentos.
6. **Período:** corrigir consultas mensais e filtros.
7. **Transições:** pagamentos, cancelamentos e estornos.
8. **Transações:** rollback e consistência.
9. **Autorização:** aplicar SPEC-002.
10. **API:** contratos e erros.
11. **Interface:** indicadores e filtros reais.
12. **Regressão:** executar testes relacionados e registrar evidências.

## 34. Critérios de aceitação
- **AC-001:** valores inválidos não são persistidos.
- **AC-002:** cálculos monetários mantêm precisão adequada.
- **AC-003:** resumo mensal considera somente o período solicitado.
- **AC-004:** status inválidos ou transições incoerentes são rejeitados.
- **AC-005:** cancelamentos e estornos preservam histórico.
- **AC-006:** filtros por período e status retornam dados consistentes.
- **AC-007:** operações financeiras não deixam estado parcial após erro.
- **AC-008:** usuários sem permissão não acessam operações protegidas.
- **AC-009:** a interface não apresenta valor acumulado como mensal.
- **AC-010:** migrações financeiras preservam dados existentes.

## 35. Fora do escopo
Esta SPEC não define:

- contabilidade fiscal;
- emissão de nota fiscal;
- integração bancária;
- Pix automático;
- conciliação bancária;
- emissão de boleto;
- gateway de pagamento;
- folha de pagamento;
- integração com sistemas contábeis;
- cobrança automática por WhatsApp;
- regras tributárias.

Esses itens deverão ser tratados em Specs próprias se forem necessários.

## 36. Definition of Done
- [ ] Domínio financeiro atual inventariado.
- [ ] Regime de caixa/competência aprovado.
- [ ] Representação monetária definida e testada.
- [ ] Valores inválidos rejeitados.
- [ ] Status e transições aprovados.
- [ ] Datas financeiras com significado definido.
- [ ] Resumo mensal corrigido.
- [ ] Filtros por período testados.
- [ ] Cancelamento preserva histórico.
- [ ] Estorno preserva histórico.
- [ ] Transações e rollback testados.
- [ ] Autorização aplicada no backend.
- [ ] API retorna erros controlados.
- [ ] Interface usa dados reais e períodos corretos.
- [ ] Migrações testadas com backup e rollback.
- [ ] Testes automatizados implementados.
- [ ] Regressão executada.
- [ ] Nenhum dado financeiro real utilizado nos testes.
- [ ] Documentação atualizada.

## 37. Estado desta SPEC
Esta SPEC detalha o comportamento esperado do módulo financeiro, mas não representa implementação concluída.

As decisões de negócio ainda pendentes — especialmente regime de caixa/competência, pagamentos parciais, cancelamentos, estornos, cobrança de faltas e integração com a agenda — deverão ser aprovadas antes da codificação definitiva.

Nenhum gate ou critério de aceitação foi declarado concluído.
