# SPEC-004 — Operational Gate Report

- Data: 2026-09-17
- Autoridade: HUMAN/Product Owner
- Estado: `READY_FOR_SPEC004_INDEPENDENT_QUALITY_REVIEW`

## Composição e commits

- baseline aprovado: `19983dc5ec940b65d552bb57eb0f85ee0e9aadba`;
- implementação: `0defb94`;
- executor e reparos auditáveis: `2c483f4`, `bb40ca7`, `a15b1e0`, `e147dfe`,
  `587fb5b`, `0846691`, `958af84`, `9e35f48`, `ae8bbd5`, `68ea79a`, `e72878a`;
- integração do runtime: `e72878a93e5f86c9ae54090cd1e6c63ff63624a9`;
- nenhum push, merge ou release.

## Runtime promovido

- pointer final: Generation `7`, estado `canonical`;
- pointer SHA-256: `9d3300076994702b6e60d48c9c16cb0bcd5e6a38ed290e55aa663bbf2a104ba2`;
- banco SHA-256: `7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07`;
- runtime manifest SHA-256: `b2ff5b733b344b2916733acd62bfb3c05b108ca6b86c6564d96fdcc06b57b20d`;
- schema material: `backend-models-v4-spec004-agenda`;
- `user_version=4`, `integrity_check=ok`, zero violações de FK e zero sidecars.

A Generation 6 realizou a promoção do banco e o primeiro CAS. O smoke pós-CAS detectou
que o maintenance lock havia sido liberado cedo demais. Conforme
`NO_SILENT_POINTER_ROLLBACK`, não houve rollback. O recovery avançou o pointer para a
Generation 7, mantendo o mesmo banco imutável e vinculando o manifest do executor
reparado.

## Backup e recovery

- backup final pré-promoção da Generation 5: manifest
  `099112f761aa95aff054ec7d693e9cf1993b6e30b64a410ed0ac6aed9ee874b8`;
- backup pré-recovery da Generation 6: manifest
  `d2679cca7bd293c3706c72c587a3a1bf6bb8e43ad26c85f0717b32a66f5547f5`;
- backup estabilizado: manifest
  `977a131f895f67e1d75f3a42c8946686d8e3c51e23c5a7d39a1b0b41d6a07747`;
- restore isolado SHA-256: `7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07`;
- generations, pointers históricos, manifests, backups e Evidence anteriores preservados.

## Validação

- suíte Python: `216 passed`;
- testes SPEC-004/cutover direcionados durante os reparos: `27 passed`;
- frontend: `5 passed`;
- build Vite: passou (`1582 modules transformed`);
- startup pelo binding operacional default: PASS;
- `/health`: PASS;
- leitura de agenda e autorização da rota: PASS;
- write guard read-only sob maintenance lock: PASS;
- banco permaneceu inalterado durante o smoke;
- criação, conflito `409`, payload inválido `422`, ETag/If-Match `412`, remarcação
  atômica, cancelamento, `done`, `no_show`, autorização por papel, fault injection e
  dupla reserva concorrente: PASS na suíte automatizada isolada;
- auditoria read-only pós-promoção: 18 relacionamentos, zero órfãos e zero violações FK.

## Reparos e invalidações seletivas

1. Import da migration foi desacoplado da inicialização do runtime.
2. Uma tentativa de quiescência de WAL vazio alterou bytes da Generation 5 e abortou
   antes do freeze. A Generation 5 foi restaurada atomicamente de backup manifestado
   com checksum exato; Evidence: `836ba54705703342265e0c04ce9b8061416f577f69fa3fdc096bcd0028eaf53b`.
3. O freeze passou a comparar a fonte limpa normalizada com o checkout ativo e a
   manifestar os bytes realmente executados, preservando diferenças apenas de EOL.
4. O smoke pós-CAS falhou porque o maintenance lock havia sido liberado. O recovery
   forward-only criou Generation 7 e concluiu estabilização; Evidence:
   `64245f79a296945270e2b71deca096bb8a0e0f4881b0e7d57419aed85580f83f`.

## Riscos residuais

- `users.psychologist_id` legado permanece nulo e fail-closed até vinculação explícita;
- dados históricos continuam `legacy_unverified`, sem inferência retroativa;
- os smokes funcionais mutantes permaneceram isolados para não inserir dados técnicos
  no banco operacional; o runtime real recebeu smoke read-only e write-guard;
- manifests órfãos produzidos por tentativas de freeze anteriores foram preservados e
  nunca ativados.

`STOP_CONDITION = READY_FOR_SPEC004_INDEPENDENT_QUALITY_REVIEW`
