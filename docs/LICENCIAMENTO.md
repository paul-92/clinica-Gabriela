# Controle de licencas e testes gratuitos

O projeto possui um controle simples de licenca local.

## Arquivos importantes

- `license.json`: arquivo de licenca usado pelo sistema.
- `.license_secret`: chave local usada para assinar a licenca.
- `GERAR_LICENCA_TESTE.bat`: cria uma licenca de teste.
- `GERAR_LICENCA_COMPLETA.bat`: cria uma licenca completa.

## Como criar teste gratuito

Execute:

```bat
GERAR_LICENCA_TESTE.bat
```

Informe:

- nome do cliente
- quantidade de dias do teste

O sistema cria ou substitui o arquivo `license.json`.

## Como ativar cliente pagante

Execute:

```bat
GERAR_LICENCA_COMPLETA.bat
```

Informe o nome do cliente.

Esse comando gera uma licenca valida ate `2099-12-31`.

## Como o bloqueio funciona

Quando a API recebe uma requisicao, ela verifica a licenca.

Se a licenca estiver:

- ausente
- vencida
- alterada manualmente

A API retorna bloqueio `403`.

O endpoint publico:

```text
GET /license/status
```

continua disponivel para a interface mostrar a mensagem correta.

## Limite desta versao

Este controle e local e simples. Ele serve para pilotos e primeiras vendas.

Para uma protecao comercial mais forte, o ideal futuro e:

- servidor de licencas online
- vinculo com maquina
- assinatura assimetrica
- painel administrativo para clientes
- historico de ativacoes
