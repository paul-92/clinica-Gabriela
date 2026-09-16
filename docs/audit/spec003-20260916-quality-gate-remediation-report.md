# SPEC-003 — Quality Gate Remediation Report

- Data: 2026-09-16
- Resultado: `READY_FOR_SPEC003_INDEPENDENT_RE_REVIEW`
- Autoridade: remediação seletiva do `CLOSURE_BLOCK` identificado pelo Independent Review
- Evidence: privacy-safe; nenhum dado pessoal, clínico, financeiro ou credencial

## Falha reproduzida e root cause

O runtime congelado `9c983aff8be9eca7b482953453c3a8c375a75ada` foi extraído em ambiente
limpo e executado com o layout operacional real, sem
`CLINICA_RUNTIME_MANIFEST_DIR`. O import normal, `scripts/run_api.ps1` e
`scripts/run_all.ps1` falharam procurando o manifest em
`%LOCALAPPDATA%\ClinicaGabriela\runtime-manifests`, um nível acima do diretório
aprovado `%LOCALAPPDATA%\ClinicaGabriela\runtime\runtime-manifests`.

Classificação: `ROOT_CAUSE_CONFIRMED`.

O smoke anterior mascarava a falha ao injetar explicitamente
`CLINICA_RUNTIME_MANIFEST_DIR`.

## Correção forward-only

- `backend/config.py`: o default passou de `pointer_path.parent.parent` para
  `pointer_path.parent`.
- `scripts/spec003_operational_promotion.py`: o smoke default remove o override
  do diretório de manifests e testa o contrato operacional normal.
- `scripts/run_api.ps1`: falhas do supervisor agora resultam em falha do launcher.
- Testes antigos de bootstrap foram isolados de pointers operacionais reais.
- Foram adicionados testes do layout padrão, import normal e launchers PowerShell.

Commits forward-only, sem reescrita:

- correção e regressões: `4329cb3326c60244c427afd84dd51589c9cb4f31`;
- integração/provenance final: `8e2d162854db84ac9352ca1a96a911870eb6a1f3`.

Nenhum push, merge ou release foi executado.

## Regressão

- testes dirigidos na árvore de desenvolvimento: `22 passed`;
- suíte completa pré-commit: `210 passed`;
- suíte completa sobre extração limpa de `4329cb3...`: `210 passed`;
- suíte completa sobre worktree limpa do runtime final `8e2d162...`:
  `210 passed in 19.67s`;
- resultado final: `0 FAILED`.

## Runtime/freeze final

- runtime integration/remediation commit:
  `8e2d162854db84ac9352ca1a96a911870eb6a1f3`;
- manifest SHA-256:
  `e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1`;
- manifest anterior:
  `6974153d6a29fb2b888dfae53e6b168ae38387a9c577c6da03e32a397635a836`;
- Evidence do quality gate anterior:
  `12e4c3762d9ec73ffd670487c2e4b3940e1bc9d8`;
- implementação funcional:
  `00ee65e8dc1541783cf4c798f08b40af6b9fd266`;
- baseline operacional:
  `ebc8604d5e97230ccfe86ecb65a593fcfddf9fb5`;
- schema físico registrado: `backend-models-v3-spec003-integrity`;
- `database_user_version=3`;
- banco esperado SHA-256:
  `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506`.

O manifest foi gerado e verificado a partir de worktree limpa e foi instalado de
forma content-addressed no diretório de manifests. O pointer não foi alterado.

## Startup e launchers

- `run_api.ps1`, runtime final e banco isolado: startup `PASS`;
- `GET /health`: HTTP 200, `{"status":"ok"}`;
- `CLINICA_RUNTIME_MANIFEST_DIR` estava ausente no startup default;
- override explícito: `PASS`, validado separadamente;
- `run_api.ps1` e `run_all.ps1`: resolução default coberta por regressão
  isolada; ambos alcançam a validação posterior de porta sem erro de manifest;
- `run_all.ps1` não abriu Electron no smoke para evitar efeito interativo; o
  caminho de launcher foi validado de forma isolada e segura.

## Estado operacional antes/depois

| Item | Antes | Depois |
|---|---|---|
| Generation | `4/canonical` | `4/canonical` |
| Pointer SHA-256 | `ace795b20122c478fb862b84ec74de8bbafb929ea23a84cde4fb90680700146a` | inalterado |
| Banco SHA-256 | `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506` | inalterado |
| Schema | `backend-models-v3-spec003-integrity` | inalterado |
| `user_version` | `3` | `3` |
| `integrity_check` | `ok` | `ok` |
| `foreign_key_check` | `0` | `0` |
| Generations preservadas | `3` | `3` |
| Sidecars anômalos | `0` | `0` |
| Maintenance lock | ausente | ausente |

Não houve migration, promoção de banco, rollback, alteração de schema,
troca de pointer ou nova Generation. `NO_SILENT_POINTER_ROLLBACK` foi preservado.

## Riscos e boundary

- O pointer operacional continua vinculado ao manifest anterior, conforme a
  instrução de preservar Generation 4/pointer. O novo freeze está disponível para
  o Independent Re-Review, mas não foi ativado por troca de pointer.
- O label v2 do pointer permanece `NON_MATERIAL_METADATA`.
- `EXTERNAL_POLICY_PENDING` permanece fora desta remediação.

`READY_FOR_SPEC003_INDEPENDENT_RE_REVIEW`
