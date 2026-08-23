# Previa dos Modulos - Marilia Gabriela Gaspar

Este material apresenta uma visao comercial dos principais modulos do sistema.

Imagens de apoio para apresentacao:

```text
docs/PREVIA_VISUAL.md
```

## 1. Login e Controle de Acesso

Tela inicial para acesso seguro ao sistema.

Recursos:

- Login por usuario e senha.
- Senha protegida por criptografia.
- Perfis de acesso: administrador, psicologo e recepcao.
- Base preparada para limitar acesso a prontuarios e areas sensiveis.

Beneficio para a clinica:

Evita acesso livre aos dados dos pacientes e separa melhor as responsabilidades da equipe.

## 2. Dashboard

Painel principal com resumo da rotina da clinica.

Recursos:

- Quantidade de pacientes ativos.
- Atendimentos do dia.
- Valores pendentes.
- Saldo mensal.
- Situacao dos atendimentos.
- Resumo financeiro rapido.

Beneficio para a clinica:

Permite enxergar rapidamente como esta o dia, a agenda e o financeiro, sem precisar abrir varias planilhas.

## 3. Cadastro de Pacientes

Modulo para organizar os dados dos pacientes.

Recursos:

- Nome completo.
- CPF.
- Data de nascimento.
- Telefone.
- E-mail.
- Endereco.
- Contato de emergencia.
- Observacoes.
- Status ativo ou inativo.

Beneficio para a clinica:

Centraliza os dados do paciente em um unico lugar e facilita a busca durante a rotina.

## 4. Cadastro de Psicologos

Modulo para registrar profissionais da clinica.

Recursos:

- Nome do psicologo.
- CRP.
- Telefone.
- E-mail.
- Especialidade.
- Status ativo ou inativo.

Beneficio para a clinica:

Ajuda a organizar a equipe e permite filtrar agenda e atendimentos por profissional.

## 5. Agenda de Atendimentos

Modulo para controle dos horarios da clinica.

Recursos:

- Criar atendimento.
- Filtrar por data.
- Filtrar por psicologo.
- Visualizar atendimentos do dia.
- Marcar atendimento como realizado.
- Remarcar atendimento.
- Cancelar atendimento.
- Registrar observacoes do atendimento.

Beneficio para a clinica:

Reduz confusao de horarios, melhora a organizacao da recepcao e facilita o acompanhamento da rotina dos psicologos.

## 6. Prontuario e Ficha de Atendimento

Modulo para registro clinico detalhado dos atendimentos.

Recursos:

- Selecao do paciente.
- Psicologo responsavel.
- Data do atendimento.
- Queixa principal.
- Objetivos da sessao.
- Humor/estado observado.
- Evolucao clinica.
- Intervencoes e conduta.
- Encaminhamentos.
- Observacoes privadas.
- Hipoteses clinicas.
- Plano terapeutico.
- Proximos passos.
- Historico de evolucoes.
- Estrutura preparada para anexos futuros.

Beneficio para a clinica:

Organiza o acompanhamento clinico do paciente e evita perda de informacoes importantes entre as sessoes.

Observacao:

Prontuario envolve dados sensiveis. O uso correto depende tambem de boas praticas da clinica, controle de acesso, backup e cuidado com LGPD.

## 7. Financeiro

Modulo para controle financeiro basico da clinica.

Recursos:

- Lancamento de receitas.
- Lancamento de despesas.
- Controle de sessoes pagas.
- Controle de sessoes pendentes.
- Valor da sessao.
- Forma de pagamento.
- Resumo mensal.
- Saldo do periodo.

Beneficio para a clinica:

Substitui controles manuais simples e ajuda a identificar valores pendentes, despesas e resultado financeiro.

## 8. Relatorios

Modulo para acompanhar indicadores do sistema.

Recursos:

- Total de pacientes cadastrados.
- Psicologos ativos.
- Atendimentos cadastrados.
- Prontuarios registrados.
- Receitas cadastradas.
- Despesas cadastradas.
- Saldo mensal.

Beneficio para a clinica:

Ajuda o gestor a acompanhar a evolucao da clinica e tomar decisoes com base em dados.

## 9. Configuracoes

Modulo para dados basicos da clinica.

Recursos:

- Nome da clinica.
- Telefone.
- E-mail.
- Endereco.
- Valor padrao da sessao.

Beneficio para a clinica:

Permite personalizar informacoes basicas do sistema.

## 10. Backup Local

Recurso para protecao dos dados.

Recursos:

- Script de backup local.
- Banco SQLite salvo em arquivo.
- Estrutura preparada para evoluir para backup automatico.

Beneficio para a clinica:

Reduz risco de perda de dados em caso de problema na maquina.

## 11. Licenca e Teste Gratuito

Modulo de controle comercial do sistema.

Recursos:

- Licenca de teste por quantidade de dias.
- Licenca completa para cliente pagante.
- Bloqueio automatico quando o teste expira.
- Exibicao dos dias restantes na interface.

Beneficio para venda:

Permite oferecer teste gratuito controlado e converter clientes para a versao paga.

## 12. Instalacao Automatizada

Scripts para facilitar instalacao em maquinas Windows.

Recursos:

- Instalador automatico.
- Criacao de ambiente Python.
- Instalacao de dependencias.
- Inicializacao do banco.
- Instalacao do frontend quando Node.js estiver disponivel.
- Scripts para execucao diaria.

Beneficio para o cliente:

Facilita a instalacao e reduz dependencia tecnica no dia a dia.

## Resumo Comercial

O sistema foi pensado para pequenas clinicas e consultorios de psicologia que precisam organizar:

- pacientes
- agenda
- prontuarios
- pagamentos
- despesas
- relatorios
- rotina administrativa

Proposta de valor:

```text
Uma solucao local para organizar a rotina da clinica de psicologia, reduzir planilhas e centralizar agenda, prontuario e financeiro em um unico sistema.
```

## Sugestao de Demonstracao

Ordem recomendada para apresentar ao cliente:

1. Login.
2. Dashboard.
3. Cadastro de pacientes.
4. Agenda.
5. Prontuario.
6. Financeiro.
7. Relatorios.
8. Controle de licenca/teste.
9. Instalacao e uso diario.

## Frase curta para venda

```text
Sistema desktop para clinicas de psicologia com agenda, pacientes, prontuario, financeiro, relatorios e teste gratuito controlado.
```
