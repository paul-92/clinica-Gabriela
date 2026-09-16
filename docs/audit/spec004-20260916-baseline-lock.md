# SPEC-004 — Baseline Lock

- Data: 2026-09-16
- Autoridade: HUMAN/Product Owner
- Parent Git observado: `30cdd7a495e09a6994c5f08ebfa75e4cc935b6a9`
- Estado: `BASELINE_LOCK_PASS`

## Baseline operacional revalidado

- Generation: `5/canonical`;
- runtime manifest SHA-256:
  `e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1`;
- banco canônico SHA-256:
  `143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506`;
- schema material: `backend-models-v3-spec003-integrity`;
- `user_version=3`, `integrity_check=ok`, zero violações de FK;
- suíte baseline: `210 passed`.

Nenhum banco, pointer, manifest, Generation ou sidecar operacional foi alterado.

## Classificação dos deltas

| Delta | Classificação | Decisão |
|---|---|---|
| fechamento/aceite da SPEC-003, contrato/decisão da SPEC-004 e índice das specs | `REQUIRED_BASELINE` | incluir no commit técnico de baseline |
| `backend/services/appointment_service.py` | `SPEC004_SCOPE` | não incluir no baseline; o conteúdo local é posterior ao blob versionado e ao arquivo de staging da SPEC-008, enquanto a composição operacional aceita registra as regras SPEC-003 em `AppointmentIntegrityService` |
| `.context/COMMANDS.md` | `PREEXISTING_UNRELATED` | preservar fora do commit |
| `.baseline-staging/`, `.forensics/`, `.homologation/` | `PREEXISTING_UNRELATED` | preservar fora do commit |

## Provenance de `appointment_service.py`

- blob em `HEAD` e cópia `.baseline-staging/appointment_service.py`:
  `ae41644c22ca3414dec10eb8c7a1c1f5f1c71059fdff2bbf126bfcc30ed9d099`;
- arquivo local observado antes do baseline lock:
  `58e52678146a4ce44e42476e8b1b8da0ea8c13fd546085e663f934cce4ab7111`;
- o delta local adiciona prechecks relacionais, tradução de `IntegrityError` e versão
  esperada, conteúdo materialmente pertencente ao domínio evolutivo da agenda;
- portanto, a revalidação recusou classificá-lo como `REQUIRED_BASELINE` e evitou sua
  incorporação silenciosa. O arquivo permanece preservado para o Harness RED e a
  implementação da SPEC-004.

## Escopo do commit

O commit de baseline contém somente documentação e Evidence privacy-safe necessárias
para tornar o gate aprovado reconstruível. Não contém secrets, PII, bancos, dependências,
artefatos temporários ou mudanças operacionais.

`BASELINE_LOCK_PASS — READY_FOR_HARNESS_RED`
