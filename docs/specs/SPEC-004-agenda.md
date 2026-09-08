# SPEC-004 — Agenda e Gestão de Atendimentos

**Status:** DRAFT — especificação detalhada, pendente de validação funcional e implementação.  
**Prioridade:** P1  
**Origem:** SPEC-001 — Auditoria  
**Dependências:** SPEC-002, SPEC-003 e SPEC-008  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir regras de agendamento, conflitos, duração, remarcação, cancelamento e transições de status no backend único. A interface auxilia o usuário, mas o backend é a autoridade final. Nenhuma regra descrita aqui deve ser considerada implementada sem testes e evidências.

## 2. Princípios e entidades
Todo atendimento deve referenciar paciente e profissional existentes. O modelo deve possuir ou permitir derivar data, início, fim ou duração, status e informações complementares. Os nomes e contratos atuais serão preservados quando possível. Não utilizar dados reais de pacientes em testes.

## 3. Validações de domínio
- Rejeitar paciente ou profissional inexistente, impedindo registros órfãos.
- Confirmar critérios de profissional apto antes de implementar restrições adicionais.
- Rejeitar datas inválidas, duração menor ou igual a zero e fim anterior ou igual ao início.
- Inventariar o formato atual de datas, horários e timezone antes de alterar schemas.
- A duração padrão, exceções, horários de funcionamento, intervalos obrigatórios e permissão de agendamentos retroativos dependem de aprovação funcional.

## 4. Sobreposição de horários
Um profissional não poderá possuir dois atendimentos que ocupem a agenda em intervalos sobrepostos. A regra conceitual é:

```text
novo_inicio < existente_fim
AND novo_fim > existente_inicio
```

Exemplos para o mesmo profissional:

| Existente | Novo | Resultado |
|---|---|---|
| 09:00–10:00 | 09:30–10:30 | Conflito |
| 09:00–10:00 | 09:00–10:00 | Conflito |
| 09:00–10:00 | 08:30–09:01 | Conflito |
| 09:00–10:00 | 09:59–11:00 | Conflito |
| 09:00–10:00 | 10:00–11:00 | Permitido |

Profissionais diferentes poderão atender no mesmo horário, salvo futura regra de recursos compartilhados. A edição deve ignorar o próprio registro e repetir a validação quando profissional, data, início, fim ou duração mudarem.

## 5. Status e transições
Inventariar enums e comportamentos atuais antes de definir a matriz definitiva. Estados conceituais incluem agendado, realizado, cancelado, falta e remarcado, caso este último seja adotado. Não aceitar strings ou transições arbitrárias.

Proposta inicial sujeita a aprovação:

| Origem | Destino | Condição |
|---|---|---|
| Agendado | Realizado | Atendimento concluído |
| Agendado | Cancelado | Cancelamento autorizado |
| Agendado | Falta | Não comparecimento registrado |
| Agendado | Remarcado | Conforme estratégia de histórico aprovada |
| Estado encerrado | Outro estado | Somente mediante regra explícita de correção/reabertura |

A matriz deverá definir quais estados ocupam agenda. Cancelamentos liberam o horário; atendimentos realizados e faltas preservam histórico. A política de correção de registros encerrados ainda precisa ser aprovada.

## 6. Cancelamento, falta e realização
Cancelar deve preservar o registro, alterar o estado e liberar o horário, sem exclusão física silenciosa. Motivo, data e responsável poderão exigir campos adicionais, sujeitos a inventário. Falta e cancelamento são eventos distintos. Consequências financeiras pertencem à SPEC-005. Realizar um atendimento não deve criar automaticamente uma evolução clínica vazia.

## 7. Remarcação e histórico
Remarcar não deverá destruir silenciosamente o horário anterior. Avaliar histórico de alterações ou preservação do atendimento anterior com novo registro relacionado. A estratégia final dependerá do modelo atual, da SPEC-008 e da aprovação funcional. Transferir um atendimento para outro profissional exige validar conflitos do profissional de destino.

## 8. Concorrência e transações
A verificação de disponibilidade na interface não é suficiente. Duas operações simultâneas para o mesmo profissional e horário não poderão resultar em dupla reserva. A implementação deverá definir estratégia transacional adequada ao SQLite e testar concorrência real, rollback e falhas de persistência. Não presumir que uma consulta prévia isolada garante exclusividade.

## 9. Timezone
Datas e horários deverão ter interpretação consistente. O horário local da clínica poderá ser adotado inicialmente, mas o formato persistido e as conversões deverão ser inventariados. Evitar misturar UTC, horário local e strings ambíguas. Nenhuma migração será criada sem análise dos dados existentes.

## 10. Autorização
A agenda deverá respeitar a SPEC-002. Matriz funcional inicial, sujeita à aprovação:

| Perfil | Visualizar | Criar | Alterar | Cancelar |
|---|---|---|---|---|
| Admin | Sim | Sim | Sim | Sim |
| Psicólogo | Sim | Sim* | Sim* | Sim* |
| Recepção | Sim | Sim | Sim | Sim |

`*` Restrições por profissional e escopo de acesso deverão ser definidas. A autorização deve ser aplicada no backend, não apenas por botões ocultos.

## 11. Exclusão e rastreabilidade
A exclusão física de atendimentos utilizados operacionalmente não será o comportamento padrão. Preferir estados e histórico. Qualquer exclusão excepcional exige regra e autorização explícitas. Registrar alterações relevantes de forma suficiente para identificar o que mudou e quando; campos adicionais de auditoria serão avaliados conforme o modelo existente.

## 12. API e mensagens
Preservar contratos existentes quando possível. Operações equivalentes a GET, POST e PUT/PATCH de appointments deverão aplicar as mesmas regras. Retornar erros controlados, como “Este profissional já possui um atendimento nesse horário”, sem expor stack traces ou detalhes internos. Códigos HTTP e formato de erro serão alinhados ao padrão do backend.

## 13. Testes obrigatórios
| Cenário | Resultado esperado |
|---|---|
| Paciente inexistente | Rejeitado |
| Profissional inexistente | Rejeitado |
| Intervalo inválido | Rejeitado |
| Horário livre | Permitido |
| Mesmo horário, mesmo profissional | Rejeitado |
| Sobreposição parcial ou total | Rejeitada |
| Horários adjacentes | Permitidos |
| Mesmo horário, profissionais diferentes | Permitido |
| Edição causando conflito | Rejeitada |
| Edição sem alterar horário | Permitida |
| Edição do próprio registro | Não conflita consigo mesmo |
| Atendimento cancelado | Não bloqueia horário |
| Transição inválida | Rejeitada |
| Remarcação | Histórico preservado |
| Concorrência | Sem dupla reserva |
| Falha de persistência | Sem registro parcial |

Usar bancos temporários isolados e dados fictícios. Testar API, domínio e integração, além de regressão das SPEC-002 e SPEC-003.

## 14. Gates de implementação
1. **Inventário:** modelos, schemas, repositories, services, rotas, enums, migrations, desktop e Electron/React.
2. **Decisões funcionais:** duração, disponibilidade, estados, transições, remarcação e histórico.
3. **Testes de domínio:** demonstrar lacunas antes das correções.
4. **Integridade:** validar paciente, profissional e relacionamentos.
5. **Intervalos:** proteger criação e edição contra conflitos.
6. **Estados:** implementar matriz aprovada.
7. **Histórico:** cancelamento, falta, realização e remarcação.
8. **Concorrência:** transações, rollback e dupla reserva.
9. **API:** contratos e erros consistentes.
10. **Interface:** integrar às regras reais do backend.
11. **Regressão:** executar testes relacionados e registrar evidências.

## 15. Critérios de aceitação
- **AC-001:** 09:30–10:30 é rejeitado quando o mesmo profissional possui 09:00–10:00.
- **AC-002:** 10:00–11:00 é permitido após atendimento que termina às 10:00.
- **AC-003:** paciente inexistente não gera atendimento persistido.
- **AC-004:** profissional inexistente não gera atendimento persistido.
- **AC-005:** alteração que gere conflito é rejeitada.
- **AC-006:** cancelamento libera o horário e preserva o registro.
- **AC-007:** transição não permitida é rejeitada.
- **AC-008:** remarcação preserva rastreabilidade do horário anterior.
- **AC-009:** operações concorrentes não produzem atendimentos conflitantes válidos.

## 16. Fora do escopo
Preço, cobrança de faltas, relatórios financeiros, prontuário clínico, layout final, WhatsApp, Google Calendar, agendamento online, teleconsulta e integrações externas. Esses itens pertencem a outras Specs ou a escopos futuros.

## 17. Definition of Done
- [ ] Modelo e contratos atuais inventariados.
- [ ] Status e transições aprovados.
- [ ] Duração e disponibilidade confirmadas.
- [ ] Paciente e profissional validados.
- [ ] Criação e edição protegidas contra conflitos.
- [ ] Próprio registro ignorado na edição.
- [ ] Horários adjacentes permitidos.
- [ ] Cancelamentos liberam horário.
- [ ] Remarcação preserva histórico.
- [ ] Concorrência e rollback testados.
- [ ] Autorização aplicada no backend.
- [ ] Erros controlados e testes automatizados.
- [ ] Regressão executada e evidências registradas.
- [ ] Documentação atualizada, sem dados reais de pacientes.

## 18. Estado desta SPEC
Esta especificação detalha o comportamento esperado, mas não representa implementação concluída. As decisões funcionais pendentes deverão ser aprovadas antes de codificar regras definitivas. Nenhum gate ou critério de aceitação foi declarado concluído.
