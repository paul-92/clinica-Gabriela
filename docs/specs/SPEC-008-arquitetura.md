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
