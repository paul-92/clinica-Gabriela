# SPEC-003 — Operational Promotion and Stabilization Report

- Data: 2026-09-15
- Resultado: `SPEC003_PROMOTION_STABILIZED`
- Estado alvo: `READY_FOR_SPEC003_QUALITY_CLOSURE_GATE`
- Evidência privacy-safe: nenhum conteúdo clínico, CPF, CRP, credencial ou nome real.

## Provenance versionada

| Papel | Commit |
|---|---|
| Implementação funcional SPEC-003 | `00ee65e8dc1541783cf4c798f08b40af6b9fd266` |
| Baseline operacional aceito SPEC-008 | `ebc8604d5e97230ccfe86ecb65a593fcfddf9fb5` |
| Runtime/integrador forward-only utilizado | `9c983aff8be9eca7b482953453c3a8c375a75ada` |

O runtime foi materializado em worktree limpa e validado sem depender do working tree
principal. O manifest registra as três referências, a migration, o candidato, Python
3.12.10 e o hash de `requirements.txt`.

## Freeze

- manifest: `runtime-manifest-6974153d6a29fb2b888dfae53e6b168ae38387a9c577c6da03e32a397635a836.json`;
- SHA-256: `6974153d6a29fb2b888dfae53e6b168ae38387a9c577c6da03e32a397635a836`;
- runtime protocol label compatível com o loader SPEC-008:
  `backend-models-v2-credential-reset`;
- schema físico explicitamente vinculado no mesmo manifest:
  `backend-models-v3-spec003-integrity`, `PRAGMA user_version=3`;
- verificação de todos os arquivos congelados: `PASS`.

## Promoção e recovery forward-only

A promoção inicial criou o banco versionado e avançou o pointer de Generation 2 para
Generation 3. O primeiro smoke detectou que `PatientRead` revalidava destrutivamente
um CPF histórico `legacy_unverified`, contrariando `D-CPF-04`. O executor registrou
`POST_SWITCH_FAILURE`, liberou o maintenance lock e respeitou
`NO_SILENT_POINTER_ROLLBACK`.

A correção separou validação de entrada (`PatientCreate`/`PatientUpdate`) da leitura
histórica (`PatientRead`) e recebeu teste de regressão. Após `205 passed` sobre a
worktree limpa, a recuperação avançou por CAS de Generation 3 para Generation 4,
apontando ao mesmo banco homologado e ao novo runtime manifest.

| Item | Resultado |
|---|---|
| Generation final | `4 / canonical` |
| Pointer final SHA-256 | `ace795b20122c478fb862b84ec74de8bbafb929ea23a84cde4fb90680700146a` |
| Banco promovido SHA-256 | `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506` |
| Maintenance lock após estabilização | ausente |
| Sidecars nas três generations preservadas | zero |

Generation 1 e Generation 2 permanecem preservadas. Nenhum cleanup ou rollback foi
executado.

## Testes e smoke

- regressão do baseline operacional isolado: `204 passed`;
- runtime SPEC-003 final, worktree exata `9c983af…`: `205 passed`;
- correção de CPF legado + bootstrap: `21 passed`;
- startup/health no runtime congelado: `PASS`;
- GETs de pacientes, psicólogos, agenda, prontuários, financeiro e settings: HTTP 200;
- write guard durante smoke controlado: `PASS`;
- checksum antes/depois do smoke: inalterado.

Cobertura da suíte SPEC-003:

- CPF opcional, normalização, validação e leitura `legacy_unverified`;
- CRP canônico e validação regional+número;
- PATCH: distinção entre ausente e `NULL`;
- concorrência otimista/ETag e resposta uniforme `412` no contrato de rotas/services;
- FK por conexão, rejeição de órfãos e relações ativas;
- lifecycle `DRAFT → FINALIZED`, imutabilidade, `LEGACY_PRESERVED` e retificação
  append-only;
- exclusão somente de draft elegível e evento de auditoria sem conteúdo sensível;
- autenticação, usuário inativo e autorização de rotas.

## Backup e recovery

- backup pré-recovery manifest SHA-256:
  `a6950e532efa0b9b35ab69b287270a2d59f8d1fa19855780cba1433fa9049004`;
- backup inicial Generation 4 manifest SHA-256:
  `7d13cd4e1a4df981b79d2b4b24c3a0709120209891b6ebac214eddba5036dfa6`;
- restauração isolada SHA-256:
  `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506`;
- restore: `integrity_check=ok`, zero violações de FK e zero sidecars.

## Integridade final

- `integrity_check=ok`;
- `foreign_key_check=0`;
- `user_version=3`;
- contagens preservadas para pacientes, psicólogos, agenda, prontuários, pagamentos,
  despesas e usuários;
- tabelas de retificação/auditoria presentes e inicialmente vazias;
- manifest/runtime verification: `PASS`.

## Evidence operacional

- sucesso: `runtime/evidence/spec003-promotion-20260915T210259Z.json`, SHA-256
  `f3f048437f3406ce997dc52e20f017d6e1d061015465d869bf880b808b1aae6a`;
- falha preservada: `runtime/evidence/spec003-promotion-20260915T205904Z.json`, SHA-256
  `e29169a718f27092abd093809427fc0cc72e0837a21317fdfee35cfb267b6e59`.

## Riscos residuais

1. O campo `schema_version` do pointer permanece com o label de protocolo legado
   exigido pelo loader imutável da SPEC-008; o schema físico v3 e `user_version=3`
   estão registrados no manifest composto. Uma evolução futura do protocolo pode
   eliminar essa compatibilidade temporária.
2. O runtime de smoke foi encerrado após a validação; operação persistente deve usar
   exclusivamente a worktree/artefato correspondente ao manifest congelado.
3. Qualquer recovery posterior a novos fatos reais continua sujeito a
   `NO_SILENT_POINTER_ROLLBACK`.

`READY_FOR_SPEC003_QUALITY_CLOSURE_GATE`
