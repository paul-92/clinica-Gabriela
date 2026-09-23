# Arquitetura

O sistema segue uma separacao simples em camadas:

- `views`: telas Tkinter.
- `controllers`: entrada das acoes de interface.
- `services`: regras de negocio.
- `repositories`: acesso ao banco.
- `models`: entidades SQLAlchemy persistidas em SQLite.
- `database`: configuracao, criacao e dados iniciais.

As telas nao acessam o banco diretamente. Elas chamam controllers, que coordenam servicos e repositorios.

## Autoridade financeira

O backend/FastAPI é a única autoridade financeira. O modelo canônico usa centavos
inteiros, serviços transacionais, versão otimista e eventos append-only. A interface
Electron consome esse contrato; o caminho Tkinter consulta o mesmo resumo via API.

A competência financeira canônica tem granularidade mensal e é representada pelo
par inteiro `competence_year` + `competence_month`, apresentado como `YYYY-MM`.
Ela não é uma data diária e não pode ser persistida ou transportada como primeiro
dia, último dia ou outro dia artificial. Consultas e relatórios mantêm competência
mensal separada do caixa, cuja autoridade temporal continua sendo `paid_at`.

O bootstrap/seed Tkinter não registra nem cria fatos financeiros e o caminho de
ativação desktop não importa o antigo model/service/repository financeiro. Service e
repository legados falham explicitamente se chamados; os models históricos ficam
fora do runtime. Assim, não existe segunda autoridade, cálculo alternativo ou write
financeiro pelo legado.

O seed canônico do backend usa o mesmo `FinanceService` da API e um ator sintético,
inativo e exclusivo de fixture. Categoria, cobrança e despesa nascem com autoria e
com o respectivo evento financeiro append-only; não há inserção direta de fatos
financeiros pelo seed.

A migração financeira é `FORWARD_ONLY / ISOLATED_CANDIDATE / FAIL_CLOSED`.
Generation 8/canonical, ponteiro e manifestos operacionais não são alterados pela
implementação ou pelo dry-run da SPEC-005. Origem, candidato e recovery são
rejeitados antes de qualquer mutação quando resolvem dentro do runtime operacional
ou para o banco apontado pelo pointer, inclusive por caminho normalizado/alias.
A implementação baseada em `competence_date: DATE` foi substituída e revalidada pelo
executor em todas as camadas afetadas. Essa reconciliação não criou candidato
operacional e não autoriza alterar a Generation 8/canonical.
