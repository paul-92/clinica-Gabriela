# SPEC-006 — Backup e Recuperação

**Status:** DRAFT — especificação detalhada, pendente de validação funcional e implementação.  
**Prioridade:** P1  
**Origem:** SPEC-001 — Auditoria  
**Dependências:** SPEC-003, SPEC-005, SPEC-008 e SPEC-010  
**Implementação:** Não iniciada.

## 1. Objetivo
Definir as regras funcionais e técnicas de backup, restauração e recuperação da Clínica Gabriela, garantindo proteção dos dados operacionais e clínicos durante falhas, migrações, atualizações e uso normal do sistema.

A auditoria identificou que o backup atual cobre apenas o banco utilizado pelo desktop, enquanto a arquitetura possui bancos distintos. Esta SPEC estabelece que a estratégia definitiva de backup deve acompanhar a unificação arquitetural prevista na SPEC-008.

Nenhuma regra descrita aqui deve ser considerada implementada sem testes e evidências.

## 2. Princípios
- Backup não é considerado concluído apenas porque um arquivo foi copiado.
- Todo backup deve poder ser validado e restaurado.
- Restauração é parte obrigatória da estratégia.
- O sistema deve evitar perda silenciosa de dados.
- Migrações de banco exigem backup prévio e plano de rollback.
- Dados clínicos e financeiros devem receber tratamento cuidadoso por serem sensíveis.
- Arquivos de backup não devem conter segredos desnecessários.
- Logs de backup não devem expor conteúdo clínico, senhas, tokens ou chaves.
- Dados reais não deverão ser utilizados em testes automatizados.

## 3. Estado arquitetural atual
Antes da implementação deverá ser confirmado o estado real dos bancos de dados existentes.

A auditoria encontrou, conceitualmente:

- banco SQLite do desktop;
- banco SQLite do backend;
- mecanismos de negócio distribuídos entre os dois caminhos.

Enquanto houver múltiplas fontes de verdade, a estratégia de backup deverá deixar explícito quais bases são protegidas.

A solução definitiva deverá acompanhar a SPEC-008 e preferencialmente operar sobre uma única base operacional autoritativa.

## 4. Escopo do backup
O backup deverá considerar, conforme a arquitetura final:

- banco de dados operacional;
- arquivos anexados, caso existam;
- configurações necessárias para restauração;
- metadados de versão do banco;
- versão da aplicação;
- informações mínimas para validar compatibilidade;
- arquivos necessários para recuperação de licenciamento, se aplicável e seguro.

Segredos de emissão, chaves privadas ou credenciais administrativas não deverão ser incluídos automaticamente no pacote.

## 5. Tipos de backup
O sistema poderá suportar:

1. backup manual;
2. backup automático;
3. backup pré-migração;
4. backup pré-atualização;
5. backup de segurança antes de operações potencialmente destrutivas.

Os tipos finais deverão ser definidos conforme a experiência desejada para a clínica.

## 6. Backup manual
Usuários autorizados poderão disparar um backup manual.

O fluxo deverá informar:

- início da operação;
- conclusão;
- falha;
- localização do arquivo;
- data e hora;
- tamanho;
- versão da aplicação;
- resultado da validação.

A interface não deverá afirmar “backup concluído” antes da confirmação real.

## 7. Backup automático
A necessidade de backup automático deverá ser aprovada funcionalmente.

Caso adotado, deverão ser definidos:

- frequência;
- horário;
- destino;
- retenção;
- comportamento se a aplicação estiver fechada;
- comportamento em caso de falha;
- quantidade máxima de backups mantidos.

Nenhuma frequência deverá ser assumida sem decisão funcional.

## 8. Consistência do SQLite
Copiar um arquivo SQLite enquanto ele está sendo alterado pode gerar inconsistência dependendo da estratégia utilizada.

A implementação deverá utilizar método seguro para obter uma cópia consistente.

Alternativas a avaliar:

- SQLite Online Backup API;
- transação consistente;
- parada controlada de escrita;
- cópia após fechamento seguro da conexão.

A escolha deverá ser testada sob escrita concorrente.

## 9. Atomicidade
A criação do backup deverá ser atômica sempre que possível.

Fluxo conceitual:

```text
criar arquivo temporário
→ copiar/gerar backup
→ validar integridade
→ renomear para arquivo final
```

Um backup incompleto não deverá aparecer como válido.

Arquivos temporários resultantes de falha deverão ser removidos ou claramente marcados como inválidos.

## 10. Nomeação dos arquivos
Os arquivos deverão possuir nome previsível e auditável.

Exemplo:

```text
clinica-gabriela-backup-2026-09-08-143000.db
```

ou, se houver pacote:

```text
clinica-gabriela-backup-2026-09-08-143000.zip
```

O nome poderá incluir versão da aplicação ou schema, se necessário.

## 11. Local de armazenamento
O destino padrão deverá ser adequado ao Windows e separado da pasta de instalação.

Uma estrutura candidata, alinhada à SPEC-010, é:

```text
%LOCALAPPDATA%\ClinicaGabriela\backups
```

O local final deverá ser validado com o instalador e a estratégia de dados.

Backups não devem ficar em diretório que seja removido durante atualização ou desinstalação comum.

## 12. Exportação externa
A clínica poderá copiar backups para:

- pendrive;
- pasta de rede;
- armazenamento em nuvem;
- pasta definida pelo usuário.

Integrações automáticas com nuvem não fazem parte desta SPEC, salvo futura aprovação.

O sistema poderá oferecer opção de “Salvar cópia em...” sem assumir integração com serviço externo.

## 13. Retenção
A política de retenção deverá ser aprovada.

Exemplos possíveis:

- manter os últimos N backups;
- manter backups por número de dias;
- combinação diário/semanal/mensal.

Nenhuma política definitiva será aplicada sem decisão funcional.

A exclusão automática deverá ocorrer somente após confirmação de que existem backups válidos suficientes.

## 14. Validação de integridade
Um backup somente será considerado válido após verificação.

A implementação deverá avaliar:

```sql
PRAGMA integrity_check;
```

ou mecanismo equivalente.

O resultado esperado deverá ser validado.

Também deverão ser verificados:

- arquivo existe;
- tamanho maior que zero;
- banco abre corretamente;
- schema esperado está presente;
- versão é reconhecida.

## 15. Metadados do backup
Cada backup deverá possuir metadados suficientes para diagnóstico.

Exemplo conceitual:

```text
created_at
app_version
schema_version
database_size
validation_status
source_database
backup_type
```

Esses metadados poderão existir em arquivo adjacente, manifesto ou tabela controlada.

## 16. Manifesto
Caso o backup seja um pacote, deverá existir um manifesto.

Exemplo:

```json
{
  "application": "Clinica Gabriela",
  "created_at": "2026-09-08T14:30:00",
  "app_version": "x.y.z",
  "schema_version": "n",
  "validation": "ok"
}
```

O formato final poderá ser JSON.

## 17. Restauração
A restauração deverá ser tratada como operação crítica.

O fluxo deverá:

1. validar o arquivo selecionado;
2. verificar compatibilidade;
3. criar backup do estado atual;
4. bloquear escritas;
5. restaurar;
6. validar integridade;
7. reiniciar conexões;
8. confirmar sucesso;
9. oferecer rollback se algo falhar.

## 18. Backup antes de restaurar
Antes de restaurar qualquer backup, o sistema deverá criar um backup de segurança do estado atual, salvo impossibilidade técnica explicitamente informada ao usuário.

Exemplo:

```text
pre-restore-2026-09-08-144500.db
```

Isso evita perda do estado atual caso o backup selecionado esteja incorreto.

## 19. Compatibilidade
A restauração deverá verificar compatibilidade entre:

- versão do banco;
- schema;
- versão da aplicação;
- formato do backup.

Um backup incompatível não deverá ser aplicado silenciosamente.

A aplicação deverá informar quando uma migração intermediária for necessária.

## 20. Restauração de versão antiga
Restaurar um backup antigo pode exigir migração de schema após a recuperação.

Fluxo conceitual:

```text
restaurar banco antigo
→ validar
→ executar migrations
→ validar novamente
```

Cada etapa deverá possuir rollback controlado.

## 21. Falha durante restauração
Se uma restauração falhar:

- o banco atual não deverá ser destruído;
- arquivos parcialmente restaurados deverão ser isolados;
- o sistema deverá recuperar o estado anterior;
- a falha deverá ser registrada sem dados sensíveis;
- o usuário deverá receber mensagem clara.

## 22. Backup pré-migração
Toda migration potencialmente destrutiva deverá exigir backup válido antes de alterar dados.

Exemplos:

- mudança de tipo monetário;
- alteração de relacionamento;
- consolidação de bancos;
- remoção de coluna;
- alteração de enum;
- transformação de dados.

A migration não deverá prosseguir se o backup obrigatório falhar.

## 23. Backup pré-atualização
Atualizações que alterem schema deverão criar backup automático antes da primeira migration.

O processo do instalador e o backend deverão coordenar essa etapa.

A SPEC-010 deverá integrar essa regra.

## 24. Unificação arquitetural
Enquanto desktop e backend utilizarem bases diferentes, o backup atual não poderá ser tratado como proteção completa do sistema.

A SPEC-008 deverá definir a fonte de verdade final.

Após a unificação:

```text
uma base autoritativa
→ uma estratégia principal de backup
```

Caso arquivos externos permaneçam, eles deverão ser incluídos no escopo de recuperação.

## 25. Dados anexos
Se o prontuário ou outras áreas permitirem anexos no futuro, o backup deverá considerar:

- banco;
- arquivos físicos;
- vínculo entre registro e arquivo;
- validação de existência;
- restauração coordenada.

Não basta restaurar somente o banco se os anexos estiverem fora dele.

## 26. Criptografia
Devido à sensibilidade dos dados, a criptografia de backups deverá ser avaliada.

Se adotada:

- utilizar algoritmo reconhecido;
- não criar criptografia proprietária fraca;
- separar chave e backup;
- definir recuperação da chave;
- evitar senha embutida no código.

A decisão final dependerá do modelo de distribuição e segurança.

## 27. Senhas e segredos
Backups não deverão incluir:

- senha em texto puro;
- AUTH_SECRET;
- segredo de emissão de licença;
- tokens de sessão;
- credenciais administrativas reutilizáveis.

Hashes de senha existentes no banco fazem parte dos dados persistidos e poderão ser incluídos conforme o modelo.

## 28. Logs
Os logs deverão registrar apenas informações operacionais.

Permitido:

```text
backup iniciado
backup concluído
arquivo
tamanho
duração
resultado da validação
```

Evitar:

```text
nome de paciente
conteúdo de prontuário
observações clínicas
senha
token
```

## 29. Auditoria
Operações manuais de backup e restauração poderão registrar:

- usuário;
- data e hora;
- tipo de operação;
- resultado.

A necessidade de trilha detalhada deverá ser aprovada conforme o modelo de auditoria da aplicação.

## 30. Autorização
A SPEC-002 deverá controlar acesso às operações.

Matriz inicial proposta:

| Perfil | Criar backup | Restaurar | Alterar retenção |
|---|---|---|---|
| Admin | Sim | Sim | Sim |
| Recepção | Não por padrão | Não | Não |
| Psicólogo | Não | Não | Não |

A política final deverá ser aprovada.

Restauração é uma operação administrativa crítica.

## 31. Interface
A interface deverá possuir estados claros:

- pronto;
- processando;
- concluído;
- falhou;
- validando;
- restaurando;
- reinício necessário.

Operações longas não deverão aparentar travamento silencioso.

A interface deverá impedir cliques duplicados durante operação crítica.

## 32. Mensagens de erro
Exemplo inadequado:

```text
OperationalError: database is locked
```

Exemplo esperado:

```text
Não foi possível criar o backup porque o banco está ocupado. Tente novamente em alguns instantes.
```

Erros técnicos poderão ser registrados internamente, sem exposição de dados sensíveis.

## 33. Testes obrigatórios
| Cenário | Resultado esperado |
|---|---|
| Backup manual válido | Arquivo criado e validado |
| Banco vazio | Backup válido |
| Banco com dados fictícios | Backup válido |
| Escrita concorrente | Backup consistente |
| Falha de gravação | Arquivo inválido não é publicado |
| Destino sem permissão | Erro controlado |
| Disco sem espaço | Erro controlado |
| Integridade inválida | Backup rejeitado |
| Restauração válida | Dados recuperados |
| Backup incompatível | Restauração bloqueada |
| Falha no restore | Estado anterior preservado |
| Restore de versão antiga | Migração controlada |
| Pré-migração | Backup obrigatório criado |
| Usuário sem permissão | Operação rejeitada |
| Retenção | Apenas arquivos elegíveis removidos |

## 34. Teste de restauração
Um backup só terá valor operacional se puder ser restaurado.

Deverá existir teste automatizado ou de integração que execute:

```text
criar banco temporário
→ inserir dados fictícios
→ gerar backup
→ alterar/apagar dados
→ restaurar
→ validar dados originais
```

Esse teste deverá fazer parte dos critérios de homologação.

## 35. Teste de integridade
Após restauração:

- abrir banco;
- executar `PRAGMA integrity_check`;
- validar tabelas esperadas;
- consultar registros de teste;
- confirmar relacionamentos.

## 36. Teste de concorrência
Deverá ser testado backup enquanto existem leituras e escritas controladas.

O objetivo é provar que a estratégia escolhida produz uma cópia consistente.

## 37. Teste de rollback
Simular falha entre etapas da restauração e confirmar que:

- o banco anterior permanece recuperável;
- o backup de segurança existe;
- nenhuma base parcialmente restaurada fica ativa.

## 38. Gates de implementação
1. **Inventário:** bancos, paths, conexões, serviço atual de backup e instalador.
2. **Arquitetura:** definir fonte de verdade conforme SPEC-008.
3. **Escopo:** banco, anexos, configs e metadados.
4. **Backup seguro:** implementar cópia consistente e atômica.
5. **Validação:** integridade e manifesto.
6. **Retenção:** política aprovada.
7. **Restauração:** fluxo seguro com backup prévio.
8. **Compatibilidade:** schema e versões.
9. **Migrações:** backup pré-migração e rollback.
10. **Segurança:** autorização, logs e criptografia se aprovada.
11. **Interface:** feedback de estado e erros.
12. **Instalador:** integração com atualizações.
13. **Testes:** restore real, concorrência e falhas.
14. **Regressão:** executar suíte relacionada e registrar evidências.

## 39. Critérios de aceitação
- **AC-001:** backup contém todos os dados operacionais definidos no escopo.
- **AC-002:** backup é validado antes de ser considerado concluído.
- **AC-003:** restauração recupera corretamente dados fictícios de teste.
- **AC-004:** restauração não destrói o estado atual sem backup de segurança.
- **AC-005:** falha de backup não publica arquivo incompleto como válido.
- **AC-006:** falha de restauração preserva ou recupera o estado anterior.
- **AC-007:** backups incompatíveis são rejeitados de forma controlada.
- **AC-008:** migrations críticas não executam sem backup prévio válido.
- **AC-009:** usuários não autorizados não podem restaurar dados.
- **AC-010:** logs não expõem dados clínicos ou credenciais.
- **AC-011:** backup permanece fora da pasta descartável de instalação.
- **AC-012:** a solução final protege a fonte de verdade definida pela SPEC-008.

## 40. Fora do escopo
Esta SPEC não define:

- sincronização em nuvem em tempo real;
- disaster recovery geograficamente distribuído;
- replicação contínua;
- alta disponibilidade;
- backup corporativo de servidor;
- integração automática com OneDrive, Google Drive ou Dropbox;
- política jurídica definitiva de retenção;
- anonimização de prontuários.

Esses itens poderão ser tratados em Specs futuras.

## 41. Definition of Done
- [ ] Bancos e diretórios atuais inventariados.
- [ ] Fonte de verdade definida.
- [ ] Escopo completo do backup documentado.
- [ ] Estratégia consistente para SQLite implementada.
- [ ] Backup atômico implementado.
- [ ] Validação de integridade implementada.
- [ ] Manifesto/metadados definidos.
- [ ] Retenção aprovada e testada.
- [ ] Restauração segura implementada.
- [ ] Backup pré-restore implementado.
- [ ] Compatibilidade de versão validada.
- [ ] Backup pré-migração implementado.
- [ ] Rollback de migration/restauração testado.
- [ ] Autorização aplicada.
- [ ] Logs sem dados sensíveis.
- [ ] Interface com feedback adequado.
- [ ] Integração com instalador validada.
- [ ] Testes de backup e restauração concluídos.
- [ ] Teste de concorrência concluído.
- [ ] Nenhum dado real utilizado nos testes.
- [ ] Documentação atualizada.

## 42. Estado desta SPEC
Esta SPEC detalha o comportamento esperado de backup e recuperação, mas não representa implementação concluída.

A estratégia definitiva depende da arquitetura autoritativa definida na SPEC-008 e da integração com o instalador prevista na SPEC-010.

Nenhum gate ou critério de aceitação foi declarado concluído.
