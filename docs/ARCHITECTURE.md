# Arquitetura

## Estado operacional atual da SPEC-005 (2026-09-24)

`CLOSED_PASS_PROMOTED_INDEPENDENTLY_VERIFIED`: Generation 9/canonical é a
autoridade financeira operacional. O pointer, runtime manifest e banco promovido
foram conferidos na [verificação independente pós-promoção](audit/spec005-20260924-post-promotion-independent-verification.md).
Generation 8 e backups de recuperação permanecem preservados. As afirmações
posteriores neste documento sobre E011/E012 pendentes ou Generation 8 autoritativa
descrevem os checkpoints D005 em que foram escritas; não são o estado atual.

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

## Legado financeiro não resolvido — D005-09 / D005-10

O contrato futuro preserva registros incompatíveis em quarentena persistida,
separada das tabelas e consultas financeiras canônicas. R2 (`paid` sem `paid_at`
comprovado) será preservado ali, sem criar payment e sem participar de CASH,
ACCRUAL ou indicadores. A migração deverá particionar cada registro de origem,
sem perda ou duplicação, entre canônico e quarentena e provar a reconciliação por
identidade, fingerprint, valor e disposition. Os labels R1–R6 permanecem
históricos; a identificação usa manifesto D005-10 por tipo, ID e hashes. Resolução
futura terá operação autorizada, transacional e auditada. D005-10 substituiu a
dependência operacional do vínculo histórico R1–R6 por identidade técnica
`source SHA + tipo + ID + fingerprint`. O migrador isolado grava payment/4 em
`legacy_financial_quarantine`, com evento append-only; repositories, serviços,
API e UI normais consultam apenas `payments`/`expenses`. Generation 8 permanece
somente leitura e E011/E012 não foram executados.
# SPEC-005 D005-11: identidades separadas

O preflight do candidato financeiro usa `backend/cutover/spec005_execution_identity.py`.
`verify_source` confere pointer, banco, integridade, FKs e freeze contra uma cópia
histórica explícita do código operacional. `verify_manifest` confere o manifest
content-addressed e recalcula a closure dos imports do código migrador. O SHA-256
canônico de source + migration + contrato identifica a transformação. A
verificação não regenera manifests. O CLI do candidato requer esse preflight
quando há manifesto legado D005-10; a autorização E011 e a revisão independente
continuam gates separados. A Generation 8 e seu manifest ativo não são alterados.

## SPEC-005 D005-12: autoridade operacional persistida

A busca histórica após D005-11 encerrou com 111/128 arquivos do runtime manifest
recuperados byte a byte; 17 permanecem sem fonte verificável. D005-12, aprovada
por HUMAN, conserva esse limite e autoriza a identidade da fonte a partir dos
artefatos persistidos da Generation 8: pointer com SHA esperado externamente,
runtime manifest com SHA esperado, banco apontado e snapshot com o mesmo SHA,
schema, `user_version`, integridade, FKs, sidecars e maintenance lock. O runtime
manifest permanece prova da identidade do artefato, sem afirmação de que seus 128
arquivos foram reconstruídos.

`verify_persisted_source` executa essa leitura; o manifest de execução migradora
continua verificado independentemente pela closure de imports e pelos hashes dos
arquivos. `bind_transformation` vincula as duas identidades ao contrato SPEC-005 e
D005-09/D005-10/D005-11/D005-12. E011 segue suspensa até revisão independente;
E012 não foi autorizada. Nenhum desses verificadores cria candidato ou promove
Generation.
