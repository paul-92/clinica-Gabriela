# SPEC-005 — revisão independente D005-11/D005-12 (2026-09-24)

## Escopo e estado

Revisão sem autoridade de reparo. Branch `feature/spec-008-architecture-foundation`, HEAD `c5100dd3cc347a9263c64a52a64d6bb0967b1db5`, upstream `origin/feature/spec-008-architecture-foundation`. Working tree já continha alterações de D005-09 a D005-12; foram preservadas. Handoff canônico, SPEC-005, decisões D005-09 a D005-12, Evidence do executor, manifests, código e runtime foram confrontados. E011/E012 não executadas.

## Verificações independentes

- Leitura direta dos bytes operacionais: Generation 8/canonical, pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`, runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519` (128 entradas), banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`, schema `backend-models-v2-credential-reset`, `user_version=5`, `integrity_check=ok`, zero violações FK, zero sidecars, maintenance lock ausente.
- Serialização canônica independente da identidade da fonte: `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`.
- Manifest migrador v5: SHA dos bytes `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`; 29 entradas em ordem, JSON canônico, cada SHA de arquivo coincide e a closure recalculada coincide. Manifest v4 preservado, SHA `33de0cbaeb3b4e96552af1495303d27a31a04a3c21d876404337b05ad7528cff`.
- Binding recalculado sem chamar o binder: `03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0`, incluindo fonte, manifest migrador, SPEC-005 e D005-09/10/11/12.
- Em cópias temporárias: pointer, SHA esperado de pointer/manifest/banco, Generation, snapshot, arquivo migrador, dependência e dependência ausente bloquearam; arquivo alheio à closure não invalidou. Trocas isoladas de fonte, SHA migrador, contrato e identidade da transformação bloquearam. BUILD em destino existente bloqueou. O SHA do snapshot copiado coincidiu com o SHA operacional; `verify_persisted_source` compara esse SHA antes de retornar, e a migração chama essa verificação antes de escrever o candidato quando recebe a identidade D005-12. Testes do executor exercem schema, integridade e FK adulterados em fixtures.
- Runtime normal ainda verifica o manifest contra o código em `backend/config.py`; o CLI do candidato permanece explicitamente bloqueado após preflight. D005-09/D005-10: classificação de payment/4 em quarentena, centavos inteiros, ciclo de pagamento e reconciliação continuam cobertos pela suíte. Nenhuma mudança de frontend com impacto causal.
- Testes D005-10/11/12 e guardas de runtime: **45 passed**. Suíte backend completa no estado final do CLI: **315 passed**. Primeira tentativa sandboxed falhou por `PermissionError` do pytest ao criar fixtures; repetição permitida com fixtures temporárias passou. `git diff --check`: passou (avisos de conversão LF/CRLF). Não há lint configurado.

## Achado

**MAJOR-01 — contagem de recuperação histórica não sustentada no estado atual.** O contrato, handoff, decisão D005-12, Evidence e identidade da fonte persistem `PARTIAL_111_OF_128`, 17 não recuperadas. Uma verificação independente dos 128 SHA do manifest ativo contra os bytes atuais e `git show <source_commit>:<path>` (incluindo conversão uniforme LF→CRLF do blob) encontrou **126 correspondências exatas e 2 sem correspondência** (`app/views/main_view.py`, `backend/database/seed.py`); todos os 128 blobs do commit foram lidos com sucesso. Portanto, a afirmação atual de que 17 entradas seguem sem fonte verificável não é reproduzível com as fontes hoje acessíveis. Isto não prova 128/128, nem altera a identidade operacional, mas deixa a provenance da recuperação e o campo semântico da identidade D005-12 desatualizados. Escopo: Evidence e contrato de autoridade histórica D005-12, não a integridade dos três artefatos operacionais. Próximo gate: reconciliação humana/técnica da contagem, seguida de nova revisão independente; nenhum reparo nesta revisão.

## Resultado e sentinela

BLOCKERS=0; MAJORS=1; MINORS=0; OBSERVATIONS=0. `QUALITY_GATE_FAIL`; `E011_READINESS=NOT_READY`. D005-11 e D005-12 não recebem estado `INDEPENDENTLY_VERIFIED` como fechamento total. A baseline histórica integral segue não comprovada. E011/E012/promotion não executadas.

Sentinela antes e depois idêntica: Generation 8/canonical; pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integridade ok, FK=0, sidecars=0, lock ausente. Apenas este artifact e o handoff foram alterados; sem stage, commit ou push.
