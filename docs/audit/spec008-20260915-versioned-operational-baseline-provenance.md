# SPEC-008 — Versioned Operational Baseline Provenance

- Data do registro: 2026-09-15
- Estado funcional preservado: `SPEC-008 = ACCEPTED / DONE`
- Natureza: errata append-only de provenance; nenhum requisito, migration, cutover,
  pointer, generation, backup ou Evidence histórico foi alterado.
- Parent da materialização: commit SPEC-003
  `00ee65e8dc1541783cf4c798f08b40af6b9fd266`.

## Motivo

O preflight de runtime da SPEC-003 identificou que a infraestrutura operacional já
aceita e usada pela SPEC-008 estava presente no working tree e nos artefatos
operacionais, mas ainda não possuía referência Git reproduzível. O HUMAN autorizou
seu registro separado, sem incorporar esse escopo ao commit da SPEC-003.

## Provenance material

O conjunto foi confrontado com:

- `spec008-20260915-final-closure-report.md`;
- `spec008-20260915-phase10-cutover-accepted.md`;
- `spec008-20260915-phase11-stabilization-pass.md`;
- `spec008-20260914-final-cutover-readiness-preflight.md`;
- os quatro runtime manifests content-addressed preservados;
- decisões HUMAN com seus sidecars SHA-256;
- executores e testes das fases 1, 3, 5–11.

O runtime manifest aceito
`d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398`
lista 13 arquivos. Onze arquivos ainda coincidiam byte a byte. Os dois arquivos
mistos foram reconstruídos independentemente:

| Arquivo | Reconstrução SPEC-008 | SHA-256 aceito | Resultado |
|---|---|---|---|
| `backend/database/session.py` | removido apenas o hook FK posteriormente introduzido pela SPEC-003 | `15e0e4b99527c5b129d472669a1332547415c709a0dcb6c39c96322b10a04f88` | match exato, 2.708 bytes |
| `backend/services/appointment_service.py` | removidas apenas validações relacionais/ETag da SPEC-003, preservado conflito de agenda | `ae41644c22ca3414dec10eb8c7a1c1f5f1c71059fdff2bbf126bfcc30ed9d099` | match exato, 2.660 bytes |

No commit composto, `session.py` preserva o hook FK já pertencente ao parent
SPEC-003 e acrescenta somente o delta read-only da SPEC-008. O serviço de agenda foi
registrado a partir do blob histórico byte-exato da SPEC-008; as regras SPEC-003
continuam na camada `AppointmentIntegrityService` versionada pelo commit pai.

## Classificação

- `ACCEPTED_SPEC008_OPERATIONAL_BASELINE`: infraestrutura de cutover, pointer,
  maintenance lock, runtime binding/freeze, promotion/rollback, backup/recovery,
  guards, migration transacional, credencial migrada, conflitos de agenda,
  executores, testes e Evidence privacy-safe associados.
- `SPEC003`: candidato, migration Evidence e artefatos de homologação da SPEC-003;
  excluídos deste registro.
- `OTHER_SCOPE`: `PROMPT_MESTRE_NOVO_PROJETO_SPEC_DRIVEN.txt`; excluído.
- `AMBIGUOUS_NON_SEMANTIC`: `.context/COMMANDS.md`; excluído por conter histórico
  de comandos de mais de uma SPEC e não ser necessário para reproduzir o runtime.
- Artefatos gerados `.forensics/` e `.homologation/`: preservados localmente e
  excluídos do Git; os relatórios privacy-safe correspondentes foram incluídos.

## Validação isolada

A árvore staged foi materializada em worktree destacada, sem usar arquivos não
versionados do working tree. Com pointer e runtime root reais neutralizados apenas no
processo de teste, a regressão concluiu:

`204 passed`

O primeiro ensaio observou duas falhas de bootstrap porque o ambiente padrão encontrou
o pointer operacional real, cujo checksum interno pré-marcador é uma divergência
histórica aceita e documentada. Nenhuma escrita ocorreu. O reteste isolado removeu
esse acoplamento ambiental e passou integralmente.

## Preservação

Este registro não executa novamente migrations ou cutover da SPEC-008. Generation 2,
pointer, generations anteriores, backups, manifests, Evidence e o boundary
`NO_SILENT_POINTER_ROLLBACK` permanecem inalterados.

`ACCEPTED_SPEC008_OPERATIONAL_BASELINE_VERSIONED`
