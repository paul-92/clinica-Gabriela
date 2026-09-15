# Cutover Readiness Report — SPEC-008

- Data: 2026-09-13
- Execução: `spec008-20260911-phase1-001`
- Escopo: preflight/readiness da Fase 10; cutover não autorizado
- Classificação: `BLOCKED`
- Promoção, troca da fonte operacional e cutover: não executados

## Resumo executivo

O candidato `verified-v2` e sua cadeia protegida permanecem tecnicamente íntegros.
Também foi comprovada, de forma não destrutiva, a capacidade básica de backup e
restauração das duas fontes atuais. O cutover não está pronto para decisão HUMAN,
porque ainda não existe um mecanismo implementado e testado para promoção e troca
atômica do ponteiro, nem um mecanismo que bloqueie e comprove todos os writers.
Além disso, o runtime homologado está em uma árvore de trabalho não commitada e não
possui um release/code manifest congelado que garanta correspondência reproduzível
com o runtime que seria iniciado depois da promoção.

## Evidências do candidato e freeze

| Verificação | Resultado | Evidência privacy-safe |
|---|---|---|
| Candidato exato | `PASS` | candidato físico único vinculado ao remap `verified-v2` |
| SHA-256 esperado/observado | `PASS` | `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46` |
| Freeze vigente | `PASS` | `spec008-20260911-phase1-001-freeze-v7` |
| Schema | `PASS` | `backend-models-v2-credential-reset` |
| Remap lifecycle | `PASS` | `verified`; versão termina em `verified-v2` |
| Cadeia de manifests | `PASS` | freeze, MigratorToolManifest, snapshots, provenance e relatório v2 coerentes |
| Snapshot desktop | `PASS` | manifest tipado, checksum, schema, integridade e FKs |
| Snapshot backend | `PASS` | manifest tipado, checksum, schema, integridade e FKs |
| Candidato SQLite | `PASS` | `integrity_check=ok`; FK violations `0` |
| Sidecars do candidato | `PASS` | WAL/SHM/journal pendentes `0` |
| Gate das Fases 7–8 v2 | `PASS` | relatório v2 vinculado ao freeze-v7 |

Os artefatos protegidos foram abertos somente para leitura. Nenhum byte foi
regenerado, promovido ou substituído.

## Fonte operacional atual e quiescência

O launcher do backend não define `BACKEND_DATABASE_PATH`. Sem override persistente,
o backend resolve sua fonte para `backend/data/clinica_api.db`. O desktop mantém uma
fonte separada e fixa em `data/clinica_psicologia.db`.

No instante do preflight:

- não havia listener nas portas 8000, 8765 ou 5173;
- não havia processo identificado pelo caminho do ambiente virtual deste projeto;
- os dois bancos legados não possuíam sidecars SQLite;
- tamanho, timestamps e checksums observados permaneceram inalterados durante as
  verificações e backups.

Isso é apenas uma observação pontual, não uma garantia de quiescência. Não existe
maintenance mode, lock interprocesso, mutex, bloqueio de launchers ou verificação
autoritativa de handles capaz de impedir que desktop, API ou processo auxiliar volte
a escrever durante a janela. Gate: `BLOCK`.

## Diretórios, ACLs e capacidade

- Pacote protegido, raiz de migration, diretórios operacionais e repositório existem.
- Todos retornaram owner e regras ACL legíveis; as ACLs são herdadas, não isoladas.
- Candidato, fontes atuais e eventual destino local estão no volume NTFS `C:`.
- Espaço livre observado: aproximadamente 112 GB para artefatos de 61.440 bytes.
- Não foi feito write probe no pacote protegido.

As condições físicas são suficientes para testes, mas o diretório final de promoção,
seu nome versionado, ACL mínima e política de retenção ainda não foram definidos.
Gate: `BLOCK`.

## Backup e restauração pré-cutover

Foi executado backup não destrutivo, via SQLite Backup API, das fontes desktop e
backend para arquivos isolados. Para ambas:

- a origem manteve o mesmo checksum;
- o backup retornou `integrity_check=ok`;
- a restauração retornou zero violações de FK;
- o tamanho observado foi 61.440 bytes.

A capacidade técnica existe, porém o script operacional atual de backup cobre apenas
o banco desktop e usa cópia de arquivo. Não há comando de final backup coordenado das
duas fontes, manifest com checksums, barreira de writers e validação automática.
Gate operacional: `BLOCK`.

## Promoção atômica no Windows

A SPEC exige arquivo canônico versionado no mesmo volume, sem reutilizar ou
sobrescrever nomes históricos, seguido de troca atômica de configuração. O código
atual possui primitivas atômicas apenas para manifests; não possui implementação de
promoção do banco ou de troca/reversão do ponteiro operacional.

O mecanismo a implementar e testar deve:

1. copiar o candidato validado para um nome versionado novo no diretório canônico;
2. fsync/fechar e revalidar checksum antes da publicação;
3. publicar no mesmo volume NTFS por operação atômica do Windows, sem overwrite de
   legado ou destino existente;
4. trocar um ponteiro/configuração persistente validado por substituição atômica;
5. manter o valor anterior registrado para reversão igualmente atômica;
6. recusar volumes diferentes, sidecars, destino preexistente ou ACL divergente.

Como destino, formato do ponteiro e implementação não existem, o passo `PROMOTE` não
é executável com segurança. Gate: `BLOCK`.

## Runtime homologado versus runtime pós-cutover

A homologação utilizou o código presente na árvore atual, incluindo a correção de
conflitos de agenda. Foram registrados checksums dos componentes críticos no
preflight, mas a árvore contém alterações não commitadas e não existe release/code
manifest assinado ou congelado para o futuro startup.

Também não há configuração pós-cutover persistente que force o mesmo caminho e
desative o runtime desktop legado. Portanto, não é possível provar hoje que o código,
configuração e entrypoint pós-promoção seriam exatamente os homologados. Gate:
`BLOCK`.

## Plano operacional ordenado

### Caminho nominal

`QUIESCE → FINAL BACKUP → REVALIDATE → PROMOTE → START → HEALTH → SMOKE → VERIFY → ACCEPT`

1. **QUIESCE** — abrir manutenção; impedir novos launches; parar API, desktop,
   Electron e jobs; adquirir lock exclusivo; provar ausência de handles/writers e
   sidecars. Qualquer writer resulta em `NO-GO`.
2. **FINAL BACKUP** — executar SQLite Backup API das duas fontes quiescidas; gerar
   manifest com tamanho/checksum; restaurar cópias isoladas; exigir integridade e FKs.
3. **REVALIDATE** — repetir checksum do candidato, freeze-v7, cadeia, schema,
   contagens, remap, provenance, `integrity_check`, FKs e sidecars; comparar originais
   ao estado esperado para a janela.
4. **PROMOTE** — somente após implementação/aprovação: publicar arquivo versionado no
   mesmo volume e trocar atomicamente o ponteiro, preservando ponteiro anterior.
5. **START** — iniciar uma única instância do runtime congelado em modo de verificação
   sem writes e confirmar que abriu exclusivamente o canônico.
6. **HEALTH** — exigir processo estável e `GET /health` aprovado dentro do timeout.
7. **SMOKE** — executar testes read-only: schema, contagens, autenticação bloqueada
   para credenciais migradas, listagens permitidas e settings, sem seed ou mutation.
8. **VERIFY** — confirmar caminho efetivo, checksum de código/configuração, um único
   banco aberto, zero sidecars inesperados, zero FKs e ausência de writes nos legados.
9. **ACCEPT** — obter aceite HUMAN operacional explícito; somente decisão posterior
   poderá liberar writes.

### Caminho de falha

`FAIL → QUIESCE → ROLLBACK → RESTORE → START → HEALTH → VERIFY`

1. **FAIL** — registrar etapa, código de razão e checksums sem PII; não liberar writes.
2. **QUIESCE** — parar a instância canônica e manter todos os writers bloqueados.
3. **ROLLBACK** — reverter atomicamente o ponteiro ao valor anterior registrado.
4. **RESTORE** — se necessário e antes de writes canônicos, restaurar somente a fonte
   anterior a partir do final backup validado; nunca sobrescrever evidência.
5. **START** — iniciar uma única instância do runtime anterior aprovado.
6. **HEALTH** — exigir health check dentro do timeout; falha escala para HUMAN.
7. **VERIFY** — conferir caminho efetivo, integridade, FKs, checksums, ausência de
   sidecars e permanência do canônico sem writes.

Após qualquer write no canônico, o rollback cego ao legado é proibido. Deve-se
bloquear writes e escalar para HUMAN para reconciliação/forward recovery.

## Critérios objetivos de GO/NO-GO

### GO — todos obrigatórios

- autorização HUMAN separada e explícita para cutover;
- maintenance lock implementado, testado e adquirido;
- zero writers, handles incompatíveis e sidecars;
- final backup duplo, manifests e restores aprovados;
- candidato/freeze/cadeia/checksums/schema/contagens/FKs íntegros;
- destino canônico versionado e ACL aprovados;
- promoção e ponteiro atômicos implementados, testados e reversíveis;
- runtime/release/configuração pós-cutover congelados e iguais aos homologados;
- smoke read-only e rollback ensaiados com os mesmos entrypoints;
- responsáveis de cutover e rollback disponíveis.

### NO-GO / rollback automático antes de writes

- checksum, freeze, schema, contagem, remap ou provenance divergente;
- qualquer writer, handle, lock ou sidecar pendente;
- backup ou restore sem integridade/FKs;
- destino existente, volume diferente, espaço ou ACL insuficiente;
- falha de promoção, ponteiro, startup, health ou smoke;
- runtime efetivo diferente do manifest congelado;
- abertura simultânea de legado e canônico;
- ausência de responsável operacional ou autorização válida.

### HUMAN obrigatório

- qualquer write detectado no canônico antes do aceite;
- necessidade de reconciliar writes pós-cutover;
- ambiguidade sobre fonte operacional ou processo escritor;
- mudança de candidato, freeze, código, configuração, destino ou plano;
- decisão de liberar writes, encerrar rollback window ou remover legado.

## Gates abertos e classificação

1. manutenção/lock de writers não implementado;
2. destino canônico e ACL final não definidos;
3. promoção atômica de banco não implementada;
4. ponteiro persistente, troca e reversão atômicas não implementados;
5. final backup coordenado com manifest não implementado;
6. desktop legado ainda possui fonte fixa e pode voltar a escrever;
7. runtime pós-cutover não congelado em artefato reproduzível;
8. modo de startup/verificação estritamente read-only não implementado;
9. janela de rollback, responsáveis e tratamento operacional ainda não formalizados.

Classificação final: `BLOCKED`.

Nenhuma ação de cutover foi executada. Uma futura autorização HUMAN de cutover não
deve ser emitida até que estes gates sejam resolvidos e este preflight seja repetido.
