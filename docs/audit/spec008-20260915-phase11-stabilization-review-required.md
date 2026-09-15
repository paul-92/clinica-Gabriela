# SPEC-008 Phase 11 Stabilization Report

- Execução: `spec008-phase11-20260915T010003Z`
- Resultado: `STABILIZATION_REVIEW_REQUIRED`
- Rollback automático: proibido após canonical write; não executado
- Cleanup/remoção/commit: não executados

## Estado ativo

- generation: `2`;
- pointer state: `canonical`;
- pointer SHA-256:
  `55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b`;
- banco: `canonical-verified-v2-96b27238c038.db`;
- runtime manifest:
  `d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`;
- modo write-enabled: iniciado de forma controlada e encerrado após a falha;
- runtime persistente: não deixado em execução.

## Rollback boundary

O boundary foi registrado antes do início write-enabled em
`spec008-20260915-phase11-rollback-boundary.json`, SHA-256
`7ff7e402ddd990f4e8a9f17c7fb6fb63ba375f7fc9b9bba9959ad24060ee5ba8`.

Após o bootstrap write-enabled, qualquer reversão silenciosa à Generation 1 ficou
proibida. Generation 2 e todas as evidências foram preservadas para decisão HUMAN.

## Estado inicial e escrita técnica

Estado inicial da Generation 2:

- SHA-256 `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46`;
- tamanho 61.440 bytes;
- `integrity_check=ok`;
- zero FKs;
- `user_version=0`;
- `journal_mode=delete`;
- nenhum sidecar.

A validação não criou nem alterou linhas clínicas, financeiras, pacientes ou
credenciais. Foi usado apenas o marcador técnico SQLite planejado:

`user_version: 0 → 1101 → 0`

com ativação WAL, persistência após reabertura, checkpoint e retorno a
`journal_mode=delete`. O estado lógico técnico foi restaurado, mas ocorreu escrita
física real e o checksum passou a:

`4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f`

Por isso não é seguro nem permitido fazer rollback cego do pointer.

## Validações alcançadas

Pela ordem fail-closed do executor, antes do marcador técnico foram exercitados:

- resolução do pointer para Generation 2;
- startup write-enabled;
- health;
- leituras críticas de pacientes, psicólogos, agenda, prontuários, financeiro e
  settings;
- passagem pelo write guard write-enabled com payload inválido rejeitado sem insert;
- autenticação inválida rejeitada;
- `password_reset_required` obrigatório;
- credenciais migradas desabilitadas;
- bloqueio do desktop legado por pointer canonical.

Estado após a falha, confirmado read-only:

- `integrity_check=ok`;
- zero violações de FK;
- `user_version=0`;
- `journal_mode=delete`;
- WAL/SHM/journal ausentes;
- pointer generation 2/canonical inalterado;
- Generation 1 e backup final pré-cutover preservados.

## Falha

- tipo: `sqlite3.OperationalError`;
- mensagem: `database is locked`;
- momento provável: transição entre o encerramento do lifespan write-enabled e a
  aquisição do lock exclusivo para o primeiro backup canônico;
- evidência: não foi criado diretório de backup da execução da Fase 11, portanto o
  backup canônico não começou;
- correção/retry: não executados após o boundary.

## Backup e restauração

- primeiro backup canônico pós-cutover: `NOT_CREATED`;
- checksum do backup: indisponível;
- restauração isolada: `NOT_EXECUTED`;
- backup final pré-cutover: preservado, SHA-256 do manifest
  `922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3`.

## Writers e legado

- nenhum dual-write foi habilitado;
- desktop legado permanece bloqueado pelo pointer canonical;
- Generation 1 e bancos legados não foram removidos ou alterados;
- nenhum processo de runtime permaneceu iniciado após a falha;
- maintenance lock não permanece ativo;
- nenhum sidecar está pendente.

## Evidências

- `%LOCALAPPDATA%\ClinicaGabriela\runtime\evidence\spec008-phase11-20260915T010003Z\rollback-boundary.json`;
- `%LOCALAPPDATA%\ClinicaGabriela\runtime\evidence\spec008-phase11-20260915T010003Z\stabilization-result.json`;
- SHA-256 do resultado:
  `855288410cef9e5bdb58a0cff3b6db8593f829a46b6a276a1e9a724f306b528e`;
- executor: `scripts/spec008_phase11_stabilization.py`.

## Riscos residuais e próximo requisito

1. O primeiro backup canônico pós-cutover ainda não existe.
2. A causa do lock residual precisa ser localizada sem escrever na Generation 2.
3. O checksum físico da Generation 2 mudou devido ao marcador técnico, embora
   integridade, FKs e metadados finais estejam válidos.
4. Qualquer recuperação deve preservar as escritas canônicas e não pode reverter
   silenciosamente à Generation 1.

Próximo requisito: decisão HUMAN para investigação read-only do lock e autorização
separada para repetir somente o backup canônico/restauração após comprovar ausência de
handles e estabilizar o lifecycle de conexões. Encerramento da SPEC-008 permanece
bloqueado até backup pós-cutover e monitoramento aprovados.

`STABILIZATION_REVIEW_REQUIRED`
