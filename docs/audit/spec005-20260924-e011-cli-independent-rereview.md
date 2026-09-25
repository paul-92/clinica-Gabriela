# SPEC-005 E011 — revisão independente do CLI e identidades v6 (2026-09-24)

## Contexto

Branch `feature/spec-008-architecture-foundation`, HEAD `c5100dd3cc347a9263c64a52a64d6bb0967b1db5`, upstream `origin/feature/spec-008-architecture-foundation`; working tree preexistente modificada, preservada. Revisão sem autoridade de reparo. Cadeia: autorização HUMAN E011 reconfirmada → E011 bloqueada antes da escrita → remediação do CLI pelo executor → v5 substituída para E011 futura → v6 e nova identidade da transformação → esta revisão independente. E011, E012 e promotion não executadas.

## Identidades verificadas

- Manifest v5 preservado: SHA `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`. Transformation Identity antiga `03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0` preservada historicamente; ambas substituídas para E011 futura.
- Source Identity recalculada pela serialização canônica: `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`; `SOURCE_IDENTITY_INVALIDATED=NO`.
- Manifest v6: 29 entries e 29 paths únicos, inventário idêntico à closure determinística, entrypoint incluído, SHA de todos os arquivos participantes coincidente. SHA dos bytes do manifest e `verify_manifest` independente: `b0bc52392cb40bd4e4c19d8c89651452a3651b6adbaa88cbc3ba87e505cff36b`. Em cópia isolada dos 29 arquivos, VERIFY passou; após adicionar bytes ao CLI copiado, VERIFY falhou fechado. BUILD do executor e VERIFY desta revisão são operações distintas.
- Transformation Identity recalculada independentemente da serialização canônica com source, migration v6, contrato SPEC-005, D005-09/10/11/12/13 e SHA do gate HUMAN E011: `41b1c6f91fae82530f3a28bbb8baa348f4209212bb49f43a6a36e6d1ff6b81c3`.
- Checkpoint v6 contém source, migration v6, transformation, SHA do gate, E011 não executada, E012 e promotion falsas; status ainda `PENDING_INDEPENDENT_IDENTITY_REREVIEW`. Quality gate e HUMAN são representados indiretamente pelo SHA do gate. O checkpoint não se autodeclara executado/promovido.

## CLI e teste adversarial

O STOP histórico incondicional foi removido. Sem `identity-manifest`, manifest migrador, pointer, runtime manifest dir ou binding checkpoint, o CLI bloqueia. Autoridade histórica bloqueia; a autoridade persistida D005-12, hashes de fonte/migrador/transformação e o gate E011 fixado no código são verificados. Gate ausente/adulterado, quality gate FAIL e MAJOR-01 OPEN bloqueiam. Alteração isolada de source, migration SHA ou transformation SHA bloqueia. Checkpoint v6 atual pendente bloqueia. Não há flags force/skip/ignore, bypass por ambiente ou caminho permissivo explícito. E012, promotion, pointer e runtime manifest ativo não receberam operação de escrita no CLI.

**BLOCKER-01 — revisão independente v6 autofabricável pelo chamador.** O CLI aceita `--binding-checkpoint` e `--binding-sha256` juntos, ambos controlados pelo chamador. Para o parecer v6, o próprio checkpoint informa `independent_identity_review_artifact`, `independent_identity_review_sha256` e `status=E011_IDENTITY_INDEPENDENTLY_VERIFIED`. O CLI confere consistência de bytes e alguns campos `PASS`, mas não vincula esse parecer a uma autoridade independente externa ou a um digest previamente confiável. Em harness isolado, foram produzidos apenas um JSON de parecer `PASS` e um checkpoint com seus hashes coerentes; com os 29 arquivos v6 reais copiados, identidades reais e fonte operacional lida somente em modo read-only, o CLI atravessou o gate e alcançou a chamada `migrate_finance_candidate`. Essa chamada foi interceptada para lançar uma exceção antes de qualquer escrita; candidato não criado. Portanto, a revisão independente pode ser simulada por quem controla os argumentos e artifacts locais. O teste positivo do executor também usa um parecer criado no próprio fixture e substitui os verificadores de manifest, source e transformation por mocks; ele não detecta essa ausência de vínculo de autoridade. A condição `NO_AUTHORIZATION_BYPASS_FOUND` não foi satisfeita.

O checkpoint v6 atual ainda bloqueia E011. O finding descreve a possibilidade de substituí-lo por um checkpoint autoconsistente fornecido ao CLI; não houve tal substituição na working tree real. Sem reparo nesta revisão.

## Validação e sentinela

Testes direcionados CLI/D005-10/11/12: **37 passed**. Source, migration e transformation mismatch bloquearam em verificações adversariais independentes; tamper do arquivo participante bloqueou VERIFY. `py_compile`: PASS. `git diff --check`: PASS, com avisos LF/CRLF preexistentes. A suíte completa de 318 passed foi executada pelo executor no estado final do código; não repetida nesta revisão porque o finding está no gate de autoridade e foi reproduzido por harness direcionado, sem nova alteração de código.

Sentinela read-only antes/depois: Generation 8/canonical; pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integrity `ok`, FK=0, sidecars=0, maintenance lock ausente.

BLOCKERS=1; MAJORS=0; MINORS=0; OBSERVATIONS=0. `QUALITY_GATE_RESULT=QUALITY_GATE_FAIL`; `CLI_BLOCKER_STATUS=OPEN`; `E011_READINESS=NOT_READY`. Migration Identity v6 e Transformation Identity foram reproduzidas independentemente, mas o gate de autorização não foi aprovado. Nenhuma alteração de código, source operacional, stage, commit, push, E011, E012 ou promotion. Mutação do repositório limitada a este parecer e ao handoff.

`STOP_CONDITION=SPEC005_E011_IDENTITY_INDEPENDENT_REREVIEW_FAIL`; `NEXT_READY=REMEDIATION_OR_HUMAN_DECISION_REQUIRED`.
