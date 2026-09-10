# SPEC-008 — Unificação Arquitetural e Fonte Única de Verdade

**Status:** DRAFT — especificação detalhada, pendente de inventário final e implementação.  
**Prioridade:** P1  
**Origem:** SPEC-001 — Auditoria  
**Dependências:** SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006 e SPEC-007  
**Relacionadas:** SPEC-009 e SPEC-010  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir a arquitetura-alvo da Clínica Gabriela de forma que a aplicação possua uma única fonte de verdade operacional, elimine duplicidade permanente de regras de negócio e reduza o risco de inconsistência entre desktop, backend e frontend.

A auditoria identificou caminhos paralelos de persistência e lógica, incluindo banco SQLite do desktop, banco SQLite do backend e camadas de negócio independentes.

Esta SPEC define a estratégia de convergência arquitetural sem assumir que qualquer migração já foi executada.

## 2. Problema atual
O projeto possui, em linhas gerais:

```text
Tkinter
→ serviços/repositórios desktop
→ SQLite desktop
```

e também:

```text
Electron/React
→ FastAPI
→ serviços/repositórios backend
→ SQLite backend
```

Esse desenho cria risco de:

- dados divergentes;
- regras duplicadas;
- correções aplicadas em apenas um fluxo;
- testes duplicados;
- backup incompleto;
- dificuldade de migração;
- comportamento diferente entre interfaces;
- manutenção mais cara.

## 3. Arquitetura-alvo
A arquitetura desejada é:

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

A aplicação desktop Tkinter poderá permanecer temporariamente como legado durante a transição, mas não deverá continuar como uma segunda fonte de verdade permanente.

## 4. Fonte única de verdade
A arquitetura final deverá possuir uma única base de dados operacional autoritativa.

A candidata principal é o banco utilizado pelo backend, porém essa escolha somente será definitiva após inventário comparativo entre os dois bancos atuais.

A decisão deverá considerar:

- schema;
- migrations;
- dados existentes;
- funcionalidades;
- relacionamentos;
- integridade;
- compatibilidade;
- dependências de código;
- riscos de perda.

## 5. Inventário obrigatório
Antes de qualquer migração, deverá ser produzido inventário dos dois caminhos.

Para cada lado:

- models;
- schemas;
- repositories;
- services;
- controllers;
- rotas;
- migrations;
- tabelas;
- colunas;
- constraints;
- enums;
- índices;
- dados de seed;
- funcionalidades exclusivas;
- integrações;
- arquivos anexos;
- banco utilizado.

## 6. Matriz comparativa
Deverá existir uma matriz semelhante a:

| Domínio | Desktop | Backend | Diferença | Ação |
|---|---|---|---|---|
| Usuários | Sim | Sim | verificar campos | consolidar |
| Pacientes | Sim | Sim | verificar contratos | consolidar |
| Psicólogos | Sim | Sim | verificar relacionamentos | consolidar |
| Agenda | Sim | Sim | verificar regras | consolidar |
| Prontuário | parcial | Sim | diferenças de modelo | preservar mais completo |
| Financeiro | Sim | Sim | semântica distinta | alinhar |
| Backup | Sim | parcial | cobertura diferente | redesenhar |

Nenhuma tabela ou regra deverá ser descartada sem comparação.

## 7. Critério de escolha da base autoritativa
A base final deverá ser escolhida considerando:

- completude funcional;
- qualidade de schema;
- existência de migrations;
- alinhamento com API;
- integração com Electron;
- facilidade de manutenção;
- estratégia de backup;
- instalador;
- possibilidade de migração segura.

A escolha não deverá ser feita apenas por conveniência.

## 8. Sem dual-write permanente
Não será adotado como arquitetura final:

```text
salvar no banco desktop
+
salvar no banco backend
```

Dual-write aumenta o risco de divergência.

Se houver período transitório, deverá ser curto, controlado e documentado.

## 9. Sem sincronização implícita
Não deverá existir mecanismo oculto de sincronização entre bancos como solução permanente.

Exemplo inadequado:

```text
desktop grava local
→ job copia depois para backend
```

A estratégia final deverá privilegiar gravação direta na fonte autoritativa.

## 10. Backend como autoridade de negócio
Regras de negócio deverão residir preferencialmente no backend.

A interface não deverá ser responsável por decidir:

- autorização;
- conflitos de agenda;
- integridade clínica;
- transições financeiras;
- regras de persistência;
- validações críticas.

## 11. Serviços
Services deverão concentrar regras de domínio.

Evitar:

```text
view → repository diretamente
```

quando houver regra de negócio relevante.

A cadeia preferida é:

```text
route/controller
→ service
→ repository
```

## 12. Repositories
Repositories deverão cuidar de persistência, não de decisões funcionais complexas.

Responsabilidades típicas:

- consultas;
- inserts;
- updates;
- filtros;
- relacionamentos;
- transações em apoio ao service.

## 13. Models
Models finais deverão ser unificados.

Não manter dois modelos diferentes para a mesma entidade sem justificativa transitória.

Exemplo:

```text
Patient desktop
Patient backend
```

deverá convergir para contrato coerente.

## 14. Schemas e contratos
Schemas Pydantic deverão refletir contratos de entrada e saída consistentes.

Separar adequadamente:

- Create;
- Update;
- Read;
- Internal.

Campos sensíveis não deverão ser expostos por padrão.

## 15. Migração de dados
A migração deverá ser não destrutiva.

Fluxo conceitual:

```text
backup
→ copiar para ambiente de teste
→ executar transformação
→ validar contagens
→ validar relacionamentos
→ validar amostras
→ executar testes
→ homologar
→ migrar produção
```

Nunca migrar produção diretamente como primeira tentativa.

## 16. Estratégia de transformação
Caso os schemas sejam diferentes, deverá existir mapeamento explícito.

Exemplo:

| Origem | Destino | Regra |
|---|---|---|
| desktop.patient_name | patients.name | direta |
| desktop.birth_date | patients.birth_date | normalizar formato |
| desktop.status | patients.active | mapear enum |
| desktop.notes | patients.notes | validar semântica |

Nenhum campo deverá ser descartado sem decisão documentada.

## 17. Dados conflitantes
Se os dois bancos possuírem dados diferentes para a mesma entidade, deverá existir política.

Possíveis critérios:

- mais recente;
- mais completo;
- banco escolhido como autoridade;
- revisão manual;
- regra por domínio.

A política deverá ser definida antes da migração real.

## 18. Identificadores
IDs poderão divergir entre bancos.

A migração deverá preservar relacionamentos mesmo que IDs precisem ser remapeados.

Poderá ser necessário criar tabela de correspondência:

```text
old_desktop_id
old_backend_id
new_id
```

## 19. Integridade referencial
Após migração, deverão ser validados:

- pacientes órfãos;
- atendimentos órfãos;
- registros clínicos órfãos;
- pagamentos sem vínculo;
- despesas inconsistentes;
- usuários inválidos.

A SPEC-003 deverá orientar a integridade clínica.

## 20. Migrações
A arquitetura final deverá possuir mecanismo único e previsível de migrations.

Evitar migrations paralelas independentes para dois bancos operacionais.

Cada alteração de schema deverá ser:

- versionada;
- testada;
- reversível quando possível;
- precedida de backup quando crítica.

## 21. Backend local
O backend poderá continuar rodando localmente na máquina da clínica.

Arquitetura conceitual:

```text
Electron
→ http://127.0.0.1:<porta>
→ FastAPI local
→ SQLite local
```

Não é obrigatório haver servidor remoto.

## 22. Porta
A porta do backend deverá ser gerenciada pelo aplicativo.

O usuário final não deverá precisar:

- descobrir porta;
- iniciar uvicorn;
- abrir terminal;
- editar configuração manual.

A SPEC-010 tratará do empacotamento.

## 23. Health check
O Electron deverá verificar se o backend está operacional antes de liberar a aplicação.

Exemplo:

```text
iniciar backend
→ aguardar /health
→ abrir interface
```

Se falhar:

```text
mostrar erro controlado
```

e não cair para autenticação falsa.

## 24. Remoção de fallback inseguro
O fallback de autenticação local/hardcoded identificado na auditoria deverá ser removido conforme SPEC-002.

Falha do backend não deverá ser interpretada como autorização.

## 25. Sessão
A interface deverá depender da sessão fornecida pelo backend.

Não manter duas autenticações independentes como solução final.

## 26. Tkinter durante a transição
O Tkinter poderá ser mantido temporariamente se ainda for necessário para funcionalidades não migradas.

Porém:

- não adicionar nova lógica duplicada sem necessidade;
- não criar novos módulos completos apenas no Tkinter;
- reduzir dependência progressivamente;
- registrar funcionalidades ainda legadas.

## 27. Critério para retirar Tkinter
O Tkinter poderá ser considerado elegível para retirada quando:

- funcionalidades essenciais existirem no Electron;
- backend cobrir regras de negócio;
- dados estiverem unificados;
- testes estiverem aprovados;
- instalador estiver funcional;
- backup estiver validado.

A remoção deverá ser uma decisão explícita, não automática.

## 28. Frontend principal
O Electron/React será o frontend principal alvo.

A SPEC-009 deverá modernizar a interface sobre essa arquitetura.

Não iniciar redesign completo em arquitetura ainda duplicada sem controle.

## 29. API como contrato
A API deverá se tornar o contrato central entre UI e domínio.

Benefícios:

- testes mais claros;
- regras centralizadas;
- frontend desacoplado de SQLite;
- menor duplicidade;
- futura possibilidade de outro cliente.

## 30. Acesso direto ao banco
O frontend não deverá acessar SQLite diretamente.

Views Tkinter também não deverão executar SQL diretamente.

Acesso deverá passar pelas camadas adequadas.

## 31. Configuração
Configurações deverão possuir fonte clara.

Evitar:

```text
config desktop
config backend
config Electron
```

com valores conflitantes.

Configurações comuns deverão ser centralizadas quando possível.

## 32. Diretório de dados
O banco autoritativo deverá ficar fora da pasta de instalação.

Candidato, alinhado à SPEC-010:

```text
%LOCALAPPDATA%\ClinicaGabriela\data
```

A definição final deverá considerar permissões e backup.

## 33. Logs
Logs de backend e Electron deverão possuir diretório controlado.

Evitar dados sensíveis.

Possível estrutura:

```text
%LOCALAPPDATA%\ClinicaGabriela\logs
```

## 34. Licenciamento
O licenciamento deverá ser integrado à arquitetura final sem duplicar lógica desnecessariamente.

A validação poderá ocorrer em ponto central.

O segredo de emissão não deverá acompanhar o cliente final.

## 35. Backup
A SPEC-006 dependerá da fonte de verdade definida aqui.

Após a unificação:

```text
um banco autoritativo
→ backup principal consistente
```

Isso elimina o problema atual de proteger apenas uma das bases.

## 36. Financeiro
A SPEC-005 deverá operar sobre a mesma base autoritativa.

Não permitir:

```text
agenda no backend
financeiro no desktop
```

como arquitetura permanente.

## 37. Prontuário
Registros clínicos deverão permanecer no mesmo domínio transacional da aplicação.

Isso facilita:

- integridade;
- autorização;
- backup;
- auditoria;
- restauração.

## 38. Agenda
Agenda deverá consultar a mesma fonte usada por pacientes e profissionais.

Evitar sincronização entre bancos para resolver conflitos.

## 39. Transações
Operações relacionadas deverão utilizar uma única unidade transacional sempre que pertencem ao mesmo banco.

Exemplo:

```text
criar atendimento
→ criar consequência financeira aprovada
→ commit
```

ou:

```text
falha
→ rollback
```

## 40. Tratamento de erro
Erros de banco deverão ser convertidos em respostas controladas.

Não expor detalhes internos ao frontend.

## 41. Performance
A unificação não deverá degradar significativamente a experiência local.

Após migração deverão ser avaliados:

- tempo de inicialização;
- consultas principais;
- agenda;
- prontuário;
- financeiro;
- backup.

Índices poderão ser revisados conforme evidência.

## 42. Compatibilidade
A estratégia deverá considerar dados existentes de instalações já utilizadas.

Não presumir banco novo em toda instalação.

Migrações deverão funcionar sobre estado legado suportado.

## 43. Rollback da migração
Antes da consolidação:

```text
backup completo
```

Se a migração falhar:

```text
restaurar estado anterior
```

A aplicação não deverá operar sobre base parcialmente migrada.

## 44. Validação pós-migração
Deverão ser comparados, quando aplicável:

- número de usuários;
- pacientes;
- psicólogos;
- atendimentos;
- registros clínicos;
- receitas;
- despesas;
- pagamentos;
- relacionamentos.

Diferenças devem ser explicadas.

## 45. Testes obrigatórios
Conforme SPEC-007:

- migration de banco vazio;
- migration com dados fictícios legados;
- preservação de registros;
- preservação de relacionamentos;
- rollback;
- autenticação;
- autorização;
- agenda;
- prontuário;
- financeiro;
- backup;
- startup Electron/backend.

## 46. Smoke test arquitetural
Após unificação:

```text
iniciar aplicação
→ backend inicia
→ health OK
→ login
→ criar paciente
→ agendar
→ consultar
→ reiniciar aplicação
→ dados permanecem
```

## 47. Gates de implementação
1. **Inventário:** dois bancos e duas camadas.
2. **Matriz comparativa:** entidades e regras.
3. **Escolha da autoridade:** banco e backend alvo.
4. **Plano de migração:** mapeamentos e conflitos.
5. **Backup:** proteção prévia conforme SPEC-006.
6. **Models/schemas:** consolidar contratos.
7. **Repositories/services:** consolidar negócio.
8. **Migrations:** criar transformação segura.
9. **API:** contratos finais.
10. **Electron:** remover dependências paralelas.
11. **Tkinter:** reduzir para legado controlado.
12. **Dados:** migrar em ambiente de teste.
13. **Validação:** contagens, integridade e amostras.
14. **Testes:** executar SPEC-007.
15. **Instalador:** alinhar SPEC-010.
16. **Homologação:** somente após evidências.

## 48. Critérios de aceitação
- **AC-001:** existe uma única fonte de verdade operacional.
- **AC-002:** frontend principal não acessa SQLite diretamente.
- **AC-003:** regras de negócio críticas ficam centralizadas no backend/services.
- **AC-004:** não existe dual-write permanente.
- **AC-005:** dados existentes são preservados na migração.
- **AC-006:** relacionamentos permanecem íntegros.
- **AC-007:** backup é executado antes de migração crítica.
- **AC-008:** rollback é possível em caso de falha.
- **AC-009:** Electron opera exclusivamente sobre API para fluxos migrados.
- **AC-010:** falha do backend não habilita autenticação falsa.
- **AC-011:** agenda, prontuário e financeiro compartilham a mesma fonte de dados.
- **AC-012:** aplicação reinicia e mantém dados migrados.
- **AC-013:** testes de regressão aprovados.
- **AC-014:** nenhum dado é descartado sem decisão documentada.

## 49. Fora do escopo
Esta SPEC não define:

- migração para banco remoto;
- PostgreSQL;
- arquitetura cloud;
- microsserviços;
- Kubernetes;
- multi-tenant;
- sincronização entre filiais;
- modo SaaS;
- replicação;
- alta disponibilidade.

Esses temas poderão ser avaliados futuramente.

## 50. Definition of Done
- [ ] Inventário dos dois bancos concluído.
- [ ] Models comparados.
- [ ] Schemas comparados.
- [ ] Services comparados.
- [ ] Repositories comparados.
- [ ] Migrations comparadas.
- [ ] Fonte de verdade aprovada.
- [ ] Matriz de migração documentada.
- [ ] Estratégia de IDs definida.
- [ ] Conflitos de dados tratados.
- [ ] Backup pré-migração implementado.
- [ ] Banco autoritativo consolidado.
- [ ] Regras duplicadas removidas ou isoladas como legado.
- [ ] API consolidada.
- [ ] Electron utiliza backend real.
- [ ] Fallback inseguro removido.
- [ ] Tkinter classificado como legado controlado ou removido.
- [ ] Migração testada com dados fictícios.
- [ ] Integridade pós-migração validada.
- [ ] Rollback testado.
- [ ] Testes da SPEC-007 aprovados.
- [ ] Backup da SPEC-006 validado.
- [ ] Instalador alinhado à SPEC-010.
- [ ] Documentação atualizada.

## 51. Estado desta SPEC
Esta SPEC define a arquitetura-alvo e a estratégia de convergência, mas não representa migração implementada.

A escolha definitiva da base autoritativa depende do inventário comparativo dos bancos e camadas existentes.

Nenhum gate, critério de aceitação ou item do Definition of Done foi declarado concluído.

## 52. Política de autoridade e consolidação de dados

### 52.1 Escopo e distinção de autoridades

Esta política transforma os inventários e diagnósticos read-only em critérios para
uma futura migração. Ela não autoriza criar banco, copiar registros, alterar runtime
ou executar cutover.

Ficam definidas duas autoridades distintas:

- **autoridade arquitetural:** o backend/FastAPI, com regras em services,
  persistência em repositories e acesso ao banco apenas pelo backend, será a
  autoridade operacional futura;
- **autoridade histórica dos dados:** nenhum dos dois bancos atuais possui
  precedência global. Desktop e backend são fontes históricas independentes que
  devem ser preservadas e reconciliadas por entidade e por campo.

Escolher o backend como autoridade arquitetural não autoriza preferir, sobrescrever
ou descartar automaticamente dados históricos do desktop.

### 52.2 Classificação das decisões

- **AUTO:** há evidência suficiente para executar futuramente uma regra
  determinística, auditável e não destrutiva;
- **REVIEW:** a proposta deve ser decidida ou confirmada por pessoa autorizada
  antes de produzir o valor canônico;
- **BLOCK:** o cutover não pode ocorrer enquanto a condição não for resolvida e
  documentada.

Uma mesma entidade pode conter regras AUTO e REVIEW e, ao mesmo tempo, possuir um
gate BLOCK. AUTO nunca substitui um BLOCK pendente.

### 52.3 Terceiro banco canônico

A consolidação deverá ocorrer em um terceiro banco novo, criado somente na futura
etapa de migração e nunca sobre os arquivos originais. Conceitualmente:

```text
SQLite desktop original (somente leitura) ─┐
                                           ├─ transformação validada → SQLite canônico novo
SQLite backend original (somente leitura) ─┘
```

Os dois bancos originais deverão permanecer imutáveis e disponíveis para auditoria
e rollback. O banco canônico deverá usar o schema aprovado para o runtime do
backend, passar por validações de contagem, unicidade, integridade referencial e
reconciliação, e somente então poderá receber o cutover aprovado.

Não haverá dual-write permanente nem sincronização implícita. Até o cutover, cada
origem permanece histórica; depois do cutover, somente o banco canônico será fonte
operacional.

### 52.4 Política de IDs, proveniência e remapeamento

PKs atuais são identificadores locais de cada origem, não identidades globais. A
migração futura deverá:

1. atribuir IDs canônicos novos e controlados pelo processo de migração;
2. manter mapa auditável com a chave lógica
   `source_database + source_table + source_id -> canonical_id`;
3. permitir que duas linhas equivalentes, inclusive com IDs de origem diferentes,
   apontem para um único ID canônico após matching aprovado;
4. atribuir IDs canônicos distintos quando a mesma PK numérica estiver ocupada por
   identidades diferentes;
5. remapear todas as FKs por meio do mapa, nunca por igualdade numérica direta;
6. preservar a proveniência de cada contribuição e de cada decisão de merge;
7. não usar o mapa de migração como identidade funcional permanente do sistema.

A geração de novo ID e o remapeamento de uma correspondência já aprovada são AUTO.
Qualquer ausência, multiplicidade ou contradição no mapa de uma FK obrigatória é
BLOCK.

### 52.5 Regras gerais de consolidação

- Matching identifica candidatos; não define sozinho quais valores vencerão.
- Igualdade de PK ou de quantidade de linhas não comprova identidade.
- Registros exclusivos serão preservados por padrão e receberão novo ID canônico;
  exclusividade não é motivo para descarte.
- Campos divergentes não serão sobrescritos por precedência global de banco. Cada
  resolução deverá seguir regra de campo documentada ou REVIEW.
- `created_at` não é chave de matching. Quando divergente, os valores de origem
  devem permanecer na trilha de proveniência e a escolha do valor canônico exige
  regra documentada.
- `password_hash` não é chave de identidade e hashes não serão mesclados. A política
  de credencial válida, revalidação ou redefinição deverá ser aprovada antes do
  cutover.
- Matching ausente, ambíguo ou não único não autoriza deduplicação.
- Nenhuma decisão manual poderá expor dados clínicos ou pessoais além do mínimo
  necessário e do perfil autorizado.

### 52.6 Matriz de política por entidade

| Entidade | Matching e confiança | Equivalentes | Exclusivos | Conflito de PK | Divergências de campos | ID canônico | Decisão / gate |
|---|---|---|---|---|---|---|---|
| `users` | `username` normalizado; alta; nunca usar `password_hash` ou `created_at` | Unificar somente a identidade confirmada; tratar credencial separadamente | Preservar como usuário distinto, sujeito à política de acesso | Sempre criar IDs distintos e remapear; nunca reaproveitar a PK conflitante | Perfil: REVIEW; `password_hash`: não mesclar, definir revalidação/redefinição | Novo ID por identidade aprovada | Matching único: AUTO; campos e acesso: REVIEW; colisão sem mapa ou credencial sem política: BLOCK |
| `patients` | CPF normalizado; alta quando presente, válido e único | Consolidar em um candidato canônico após validar unicidade | Preservar integralmente | IDs distintos quando identidades diferirem; equivalentes convergem após aprovação da correspondência | Dados cadastrais divergentes: REVIEW; `created_at` não decide identidade | Novo ID por paciente reconciliado | Matching único: AUTO; conflito de campo: REVIEW; CPF ausente/duplicado/contraditório: BLOCK |
| `psychologists` | CRP normalizado; alta quando presente e único | Consolidar em um candidato canônico | Preservar integralmente | Remapear para IDs distintos ou para o mesmo canônico conforme identidade aprovada | Cadastro divergente: REVIEW; `created_at` apenas proveniência | Novo ID por profissional reconciliado | Matching único: AUTO; campos: REVIEW; CRP ausente/duplicado/contraditório: BLOCK |
| `appointments` | Identidade reconciliada de paciente + psicólogo + horário; heurística | Deduplicar somente após confirmação de que representam o mesmo evento | Preservar e remapear ambas as FKs | PK nunca decide; colisões recebem IDs canônicos distintos salvo matching aprovado | Horário, duração, status e demais diferenças: REVIEW | Novo ID por evento aprovado | Exclusivo e FKs resolvidas: AUTO; candidato equivalente: REVIEW; pai/FK sem mapa ou matching ambíguo: BLOCK |
| `clinical_records` | Paciente + psicólogo + data do atendimento; heurística e clinicamente sensível | Não deduplicar automaticamente; exigir revisão clínica autorizada | Preservar integralmente com acesso e proveniência | PK nunca decide; novo ID para cada registro não deduplicado | Conteúdo clínico jamais sofre escolha automática por completude ou recência | Novo ID por registro preservado ou merge explicitamente aprovado | Preservação exclusiva: AUTO; equivalência/conteúdo: REVIEW; vínculo obrigatório sem mapa ou merge clínico ambíguo: BLOCK |
| `payments` | Paciente + agendamento opcional + vencimento + valor; heurística atualmente ambígua | Não deduplicar nem sobrescrever automaticamente | Preservar provisoriamente até reconciliação financeira | PK nunca decide; novos IDs e mapas separados | Status, liquidação, método, descrição e vínculos divergentes: REVIEW | Novo ID por lançamento aprovado | Matching destrutivo: BLOCK; revisão financeira: REVIEW; preservação sem deduplicar e com FKs resolvidas: AUTO |
| `expenses` | Data + valor + descrição + categoria; heurística | Deduplicar somente após revisão financeira | Preservar | PK nunca decide | Qualquer divergência material: REVIEW | Novo ID por despesa aprovada | Exclusivo: AUTO; candidato equivalente: REVIEW; ambiguidade financeira não resolvida: BLOCK |
| `clinic_settings` | Singleton sem chave natural confiável; inconclusivo | Não combinar por PK nem por posição | Preservar ambas as versões como fontes para decisão, não como duas configurações ativas | PK igual não comprova identidade | Seleção campo a campo ou escolha de configuração: REVIEW | Uma configuração canônica após aprovação | REVIEW obrigatório; ausência de configuração final aprovada: BLOCK |

### 52.7 Decisões automáticas permitidas

São AUTO, desde que nenhum gate BLOCK relacionado esteja aberto:

- criar novo ID canônico para cada unidade de identidade aprovada;
- registrar proveniência e mapa de IDs para as duas origens;
- preservar registros exclusivos sem deduplicação;
- aplicar matching de alta confiança quando a chave natural normalizada for
  presente e única nos dois bancos;
- remapear FKs quando a origem e o destino canônico forem unívocos;
- manter NULL em `payments.appointment_id` quando a origem já representar ausência
  legítima de vínculo;
- executar validações de contagem, unicidade, órfãos e `foreign_key_check`.

### 52.8 Revisão humana obrigatória

Exigem REVIEW:

- divergências de campos sem regra de precedência aprovada;
- política de credenciais e acesso de `users`;
- candidatos heurísticos de `appointments`, `clinical_records`, `payments` e
  `expenses`;
- qualquer possível deduplicação clínica ou financeira;
- seleção campo a campo de `clinic_settings`;
- chaves naturais inválidas que ainda possam ser resolvidas com evidência
  autorizada;
- explicação das diferenças finais de contagem e aprovação do relatório de
  reconciliação.

### 52.9 Condições de bloqueio da migração e do cutover

São BLOCK:

- colisão de PK sem mapa explícito para todos os registros envolvidos;
- chave natural obrigatória ausente, duplicada ou contraditória sem resolução;
- matching ambíguo usado para deduplicação automática;
- política de `password_hash`/credencial não aprovada para usuários que precisarão
  autenticar;
- pagamento ambíguo ainda sujeito a descarte, sobrescrita ou deduplicação;
- configuração canônica não aprovada;
- FK obrigatória sem correspondência canônica única;
- órfão ou violação de `foreign_key_check` no banco resultante;
- diferença de contagem não explicada, perda de proveniência ou registro descartado
  sem decisão documentada;
- ausência de backup verificável, rollback testado, validação, homologação ou
  aprovação formal de cutover.

### 52.10 Preservação de integridade referencial

O processo futuro deverá carregar e reconciliar primeiro as entidades pai e apenas
depois as dependentes. Devem ser preservadas e remapeadas explicitamente:

- `appointments.patient_id -> patients.id`;
- `appointments.psychologist_id -> psychologists.id`;
- `clinical_records.patient_id -> patients.id`;
- `clinical_records.psychologist_id -> psychologists.id`;
- `payments.patient_id -> patients.id`;
- `payments.appointment_id -> appointments.id`.

Cada FK não-NULL deverá resolver para exatamente um ID canônico. Antes do cutover,
deverão ser executados validação explícita das relações e
`PRAGMA foreign_key_check`, ambos sem violações. O runtime canônico deverá habilitar
enforcement de FKs por conexão conforme decisão técnica específica e testada; essa
alteração não faz parte desta tarefa.

### 52.11 Tratamento de `payments.appointment_id`

`payments.appointment_id` permanece opcional. A política é:

- NULL histórico continua NULL e não é erro nem motivo para inferir vínculo;
- valor não-NULL somente será remapeado quando o agendamento de origem resolver de
  forma unívoca para um agendamento canônico;
- é proibido preencher automaticamente um NULL por proximidade de data, valor,
  paciente ou qualquer outra heurística;
- vínculo não-NULL sem mapa único é BLOCK;
- a ambiguidade de identidade dos pagamentos impede deduplicação ou sobrescrita
  automática, mas não autoriza perda do lançamento.

### 52.12 Aprovação necessária antes da implementação

Esta política define a direção, mas a criação do banco canônico e do script de
migração depende de aprovação explícita dos seguintes artefatos futuros:

- schema canônico e mecanismo único de migrations;
- regras campo a campo para divergências;
- política de credenciais;
- workflow de revisão clínica e financeira;
- formato e retenção do mapa de IDs/proveniência;
- plano de backup, rollback, validação e cutover.

## 53. Plano de remapeamento de identidades e FKs

### 53.1 Escopo

Este plano define a representação e os gates do remapeamento futuro. Não cria mapa
concreto, não contém IDs reais, não abre os bancos de origem e não autoriza escrita
ou migração. A implementação deverá ser precedida pela aprovação dos artefatos
listados na seção 52.12.

### 53.2 Registro conceitual do mapa

Cada registro de origem deverá possuir exatamente uma entrada lógica no mapa:

| Campo | Finalidade |
|---|---|
| `source_database` | Origem controlada: `desktop_legacy` ou `backend_legacy` |
| `source_table` | Tabela na origem |
| `source_id` | PK histórica, mantida apenas no artefato protegido de migração |
| `canonical_table` | Tabela de destino aprovada |
| `canonical_id` | Novo ID; ausente enquanto REVIEW/BLOCK não estiver resolvido |
| `match_status` | Estado da análise de identidade |
| `match_confidence` | Confiança da evidência de identidade |
| `pk_relation_status` | Relação entre a PK local e a PK da outra origem, em eixo separado |
| `decision_class` | `AUTO`, `REVIEW` ou `BLOCK` |
| `decision_status` | `pending`, `approved` ou `rejected` |
| `canonical_group_ref` | Referência opaca e temporária ao candidato canônico, sem PII |
| `provenance` | Regra, versão, evidências e decisão que produziram o mapeamento |

A chave única do mapa será
`(source_database, source_table, source_id)`. `source_id` e `canonical_id` são dados
operacionais protegidos do processo e não poderão aparecer em relatórios públicos
ou de diagnóstico.

O mapa deverá ser versionado por execução de migração, imutável após aprovação e
reproduzível a partir dos mesmos snapshots e regras. Alteração de decisão gera nova
versão; não reescreve silenciosamente a evidência anterior.

### 53.3 Estados de identidade, confiança e PK

`match_status` descreve identidade, não igualdade numérica:

- `equivalent`: evidência aprovada de que registros representam a mesma entidade;
- `exclusive`: registro encontrado em somente uma origem, preservado como entidade
  própria;
- `conflicting_identity`: evidências de identidade se contradizem;
- `ambiguous`: existem múltiplos candidatos plausíveis ou evidência insuficiente
  para decisão unívoca;
- `unresolved`: análise ou decisão ainda não concluída.

`match_confidence` possui os valores:

- `high`: chave natural única e válida ou decisão humana expressa;
- `medium`: composição relacional forte, mas ainda heurística;
- `low`: evidência parcial, fraca ou sujeita a colisão;
- `none`: não há evidência utilizável.

Como colisão de PK é ortogonal à identidade, `pk_relation_status` possui:

- `not_compared`: relação numérica ainda não avaliada;
- `same_pk_same_identity`: mesma PK numérica e identidade equivalente;
- `same_pk_different_identity`: mesma PK numérica ocupada por identidades
  diferentes;
- `different_pk_same_identity`: identidade equivalente sob PKs diferentes;
- `different_pk_different_identity`: PKs e identidades diferentes;
- `no_counterpart`: não há registro correspondente na outra origem.

Assim, uma entrada pode ser `match_status=equivalent` e
`pk_relation_status=different_pk_same_identity`, enquanto outra colisão é registrada
como `same_pk_different_identity`. Uma condição não será confundida com a outra.

### 53.4 Classes de decisão aplicadas ao mapa

- **AUTO:** pode receber `canonical_id` quando a regra determinística, as
  cardinalidades e todas as dependências estiverem válidas;
- **REVIEW:** mantém `canonical_id` pendente até decisão humana aprovada. Após a
  aprovação, a decisão e a evidência são registradas na provenance;
- **BLOCK:** não recebe remapeamento definitivo e impede escrita da entidade e de
  todos os dependentes afetados.

Rejeitar um candidato de equivalência não significa descartar registros. Salvo
decisão explícita em contrário, cada origem passa a ser preservada como registro
distinto com seu próprio ID canônico.

### 53.5 Grafo real e ordem de processamento

O grafo foi derivado das FKs declaradas:

```text
patients ───────┬─> appointments ──> payments
                ├─> clinical_records
                └──────────────────> payments

psychologists ──┬─> appointments
                └─> clinical_records

users             (independente do grafo de FK)
clinic_settings   (independente; depende de REVIEW funcional)
expenses          (independente do grafo de FK)
```

Ordem segura por fases:

1. **Preparação:** schema canônico, snapshots, regras, espaço de IDs e versão do
   mapa, sem escrita de registros canônicos;
2. **raízes do grafo:** `patients` e `psychologists`;
3. **independentes:** `users`, `clinic_settings` e `expenses`; podem ser analisados
   em paralelo às raízes, mas seus REVIEW/BLOCK permanecem ativos;
4. **dependentes de primeiro nível:** `appointments` e `clinical_records`, somente
   após mapas unívocos de pacientes e psicólogos;
5. **dependente de segundo nível:** `payments`, somente após mapas de pacientes e
   appointments;
6. **validação global:** cardinalidades, contagens, unicidade, FKs, órfãos,
   `foreign_key_check` e aprovação.

`clinical_records` não depende de `appointments` no schema atual; portanto não deve
ser artificialmente serializado depois de appointments. `clinic_settings` não tem
FK, mas sua decisão humana é gate funcional do cutover.

### 53.6 Política por tipo de caso

#### Entidade equivalente

- cada entrada de origem é preservada no mapa;
- ambas apontam para o mesmo `canonical_table + canonical_id`;
- a cardinalidade esperada é N origens para 1 entidade canônica, normalmente 2:1
  nesta consolidação;
- a convergência somente é definitiva após resolver as divergências de campos;
- REVIEW ou BLOCK pendente mantém `canonical_id` não gravável.

#### Registro exclusivo

- recebe ID canônico próprio;
- mantém `match_status=exclusive`, `pk_relation_status=no_counterpart` e
  provenance da origem;
- não é descartado nem fundido por ausência na outra base;
- a cardinalidade esperada é 1:1 entre origem e entidade canônica.

#### Colisão de PK

- `same_pk_different_identity` exige IDs canônicos distintos;
- igualdade numérica nunca participa da escolha do pai canônico;
- cada origem mantém entrada e provenance próprias;
- qualquer FK é resolvida usando também `source_database` e `source_table`;
- colisão sem separação e mapa completos é BLOCK.

#### Mesma identidade com IDs diferentes

- `match_status=equivalent` e `pk_relation_status=different_pk_same_identity`;
- ambas as entradas convergem para o mesmo ID canônico após aprovação;
- dependentes de cada banco consultam o mapa dentro da respectiva origem e passam
  a apontar para esse mesmo pai canônico;
- a PK histórica de nenhuma origem é preferida.

#### Ambiguidade ou conflito de identidade

- não gera `canonical_id` definitivo;
- recebe REVIEW quando houver evidência que uma pessoa autorizada possa resolver;
- recebe BLOCK quando a decisão for necessária para uma FK, deduplicação, valor
  clínico/financeiro ou cutover;
- nenhuma escrita destrutiva, inferência por proximidade ou descarte é permitido;
- preservar separadamente é a alternativa segura, mas também deve ser decisão
  explícita quando puder criar duplicidade funcional ou financeira.

### 53.7 Regra de lookup e remapeamento de FKs

Para cada FK não-NULL, o lookup obrigatório será:

```text
(source_database da linha filha, tabela pai, valor histórico da FK)
→ exatamente uma entrada aprovada no mapa da tabela pai
→ canonical_id do pai
```

É proibido procurar o pai somente pelo número da FK ou cruzar diretamente a FK de
uma origem com a PK da outra. As regras por relação são:

| FK de origem | Pré-requisito | Valor no canônico | Gate |
|---|---|---|---|
| `appointments.patient_id` | mapa aprovado de `patients` na mesma origem | `canonical patients.id` | Sem um único pai: BLOCK |
| `appointments.psychologist_id` | mapa aprovado de `psychologists` na mesma origem | `canonical psychologists.id` | Sem um único pai: BLOCK |
| `clinical_records.patient_id` | mapa aprovado de `patients` na mesma origem | `canonical patients.id` | Sem um único pai: BLOCK |
| `clinical_records.psychologist_id` | mapa aprovado de `psychologists` na mesma origem | `canonical psychologists.id` | Sem um único pai: BLOCK |
| `payments.patient_id` | mapa aprovado de `patients` na mesma origem | `canonical patients.id` | Sem um único pai: BLOCK |
| `payments.appointment_id` | NULL histórico ou mapa aprovado de `appointments` na mesma origem | NULL ou `canonical appointments.id` | Não-NULL sem um único pai: BLOCK |

Se dois pais históricos forem equivalentes, seus dois lookups distintos resolvem
para o mesmo ID canônico. Se houver colisão de PK, a inclusão de `source_database`
no lookup impede que os filhos sejam ligados à identidade errada.

### 53.8 Regra especial de `payments.appointment_id`

- NULL histórico é copiado como NULL e não cria entrada de lookup;
- é proibido inferir appointment por paciente, data, valor ou proximidade;
- não-NULL exige exatamente uma entrada aprovada do appointment da mesma origem;
- lookup ausente, múltiplo, REVIEW pendente ou BLOCK impede escrever o pagamento;
- a ambiguidade do matching de `payments` não altera o mapa do appointment pai;
- pagamentos não serão deduplicados automaticamente, ainda que outros atributos
  coincidam.

### 53.9 Verificações de cardinalidade e completude

O mapa somente estará completo quando todas as condições abaixo forem verdadeiras:

- cada registro de cada snapshot de origem possui exatamente uma entrada pela chave
  única `(source_database, source_table, source_id)`;
- nenhuma entrada de origem aponta para mais de um ID canônico;
- todo AUTO está resolvido e todo REVIEW necessário está aprovado;
- não existe BLOCK aberto;
- todo `canonical_id` pertence à `canonical_table` declarada;
- grupo equivalente possui um único ID canônico e ao menos duas entradas de origem
  aprovadas, sem candidato incompatível no mesmo grupo;
- registro exclusivo possui exatamente um ID canônico e uma entrada de origem;
- entradas `same_pk_different_identity` apontam para IDs canônicos distintos;
- entradas `different_pk_same_identity` aprovadas apontam para o mesmo ID canônico;
- toda FK obrigatória resolve para exatamente um pai canônico;
- toda FK opcional não-NULL resolve para exatamente um pai canônico;
- NULL opcional permanece NULL e não é contado como mapa ausente;
- nenhum registro de origem foi perdido e nenhuma linha canônica existe sem
  provenance;
- contagens são reconciliáveis por fonte, tabela, status e grupo canônico;
- a redução de contagem causada por equivalência é exatamente explicada pelos
  grupos N:1 aprovados;
- a expansão causada por preservação de colisões/exclusivos é exatamente explicada
  pelas entradas 1:1;
- somas por `equivalent`, `exclusive`, `conflicting_identity`, `ambiguous` e
  `unresolved` correspondem ao total de entradas de origem de cada tabela.

### 53.10 Invariantes antes de qualquer escrita canônica

Antes do primeiro INSERT no futuro banco canônico, deverão valer:

1. os dois originais estão preservados em snapshots verificáveis e read-only;
2. schema canônico e mecanismo único de migrations estão aprovados;
3. versão das regras e normalizações está congelada para a execução;
4. espaço de IDs canônicos está reservado sem reutilizar PK histórica por
   conveniência;
5. mapa completo de todas as raízes necessárias à fase de escrita está aprovado;
6. não há REVIEW pendente nem BLOCK na entidade ou em seus ancestrais;
7. todas as divergências de campos possuem decisão reproduzível;
8. credenciais, dados clínicos, financeiros e configuração possuem políticas
   aprovadas;
9. simulação/dry-run reconcilia todas as contagens e cardinalidades;
10. toda FK não-NULL possui exatamente um destino canônico calculado;
11. nenhuma regra depende apenas de igualdade de PK, row count ou `created_at`;
12. logs e relatórios da migração não expõem PII, dados clínicos, credenciais ou
    IDs históricos fora do artefato protegido;
13. plano de rollback e critérios de abortar a transação estão aprovados.

As invariantes devem ser reavaliadas ao fim de cada fase. Falha aborta a execução e
impede banco parcialmente aprovado de receber cutover.

### 53.11 Provenance

`provenance` deverá ser metadata técnica sem PII e conter, conceitualmente:

- origem controlada, tabela e referência interna protegida ao ID histórico;
- versão do snapshot e da execução;
- versão da regra de matching e normalização;
- status e confiança da identidade;
- estado ortogonal de PK;
- classe, estado, motivo categórico e referência opaca da decisão;
- campos cuja resolução foi AUTO ou REVIEW, sem copiar seus valores para a
  metadata;
- referência ao grupo canônico e ao evento de criação do ID canônico;
- resultados agregados das validações aplicáveis.

Dados pessoais, clínicos, credenciais, hashes de senha e valores usados no matching
não pertencem à provenance. Acesso ao mapa concreto deverá ser restrito, auditado e
limitado ao período de migração e retenção aprovado.

### 53.12 Riscos e decisões ainda abertas

Permanecem abertos:

- formato físico, criptografia, controle de acesso e retenção do mapa concreto;
- algoritmo de alocação dos IDs canônicos e garantia de reprodutibilidade;
- regras campo a campo e política de credenciais;
- interface e segregação de função para REVIEW clínico e financeiro;
- tratamento aprovado dos pagamentos ambíguos e de `clinic_settings`;
- schema canônico, transação por fase e comportamento de rollback;
- validação do enforcement de FKs no runtime canônico;
- formato do relatório de reconciliação sem exposição de IDs históricos;
- critérios de homologação e autoridade responsável pela aprovação do cutover.
