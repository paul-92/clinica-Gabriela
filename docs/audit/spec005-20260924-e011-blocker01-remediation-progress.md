# SPEC-005 E011 — BLOCKER-01 remediation progress
Status: REMEDIATED_BY_EXECUTOR / PENDING_INDEPENDENT_REREVIEW. E011 remains suspended. This is executor evidence, not an Independent Review PASS.

## Trust chain and exploit

The E011 caller supplied the checkpoint path and SHA. The checkpoint supplied the review path, SHA and independently verified status. The CLI checked internal consistency and PASS fields. The independent rereview reproduced a self-fabricated PASS reaching the migration call boundary without a first write. Hashes proved integrity of caller-selected bytes, not reviewer authority.

The existing E011 authorization gate pins the earlier D005-13 review and human authorization. It does not approve the v6 migration and transformation identities. No canonical, independently controlled review registry for those identities was found in the repository.

## Provisioned authority protocol

The canonical authority is `docs/audit/spec005-e011-independent-review-authority.json`, fixed by the CLI contract and absent in the real repository. A separate reviewer command, `python -m scripts.spec005_provision_e011_review --review <review-file>`, validates a review subject, creates `docs/audit/spec005-e011-review-<SHA256>.json` with exclusive creation, then creates the authority registry with exclusive creation. The E011 CLI never calls this command and accepts no authority location argument. It resolves the fixed registry, verifies the content-addressed artifact, and checks SPEC, E011, Source, Migration version and digest, Transformation, contract, QUALITY_GATE_PASS and BLOCKER-01 closure against the exact checkpoint and operational source. A checkpoint-provided review path and SHA must match the independently resolved authority; they confer no authority themselves.

Only the independent reviewer may provision the real authority after independently verifying the final identities. The implementation executor provisioned only synthetic authority inside isolated test fixtures. The real canonical registry and real PASS review remain absent. Existing authority cannot be overwritten by the provisioner. Supersession requires a separately reviewed successor and explicit archival/replacement of the canonical registry outside E011; no invocation flag selects it.

This is protocol separation of duties, not protection against a malicious local user with full filesystem control. Such a user could alter both registry and artifact. No signature, PKI, HMAC, OS ACL or external attestation is claimed. Tampering with the reviewed artifact alone fails by digest. The trust anchor is the independently provisioned, fixed-location registry and the reviewer workflow, not the caller's checkpoint.

Implementation executor, Independent Review authority and E011 invocation are separate roles. The implementation executor has not issued an approval artifact. No E011, E012, candidate, or promotion was run.

## Identities

- Source Identity: `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`; read-only operational reconfirmation PASS before and after.
- v6 Migration Manifest: `b0bc52392cb40bd4e4c19d8c89651452a3651b6adbaa88cbc3ba87e505cff36b`, historical and superseded for future E011.
- v6 Transformation Identity: `41b1c6f91fae82530f3a28bbb8baa348f4209212bb49f43a6a36e6d1ff6b81c3`, historical and superseded for future E011.
- v7 Migration Manifest: `5f31063560441aab1ee3da571e1fc45563a32d88a569c2ce2d47b15634003fea`; 29 files; historical/superseded because CLI bytes changed.
- v7 Transformation Identity: `f71d774208c6660ff7a03ea2fa73958348d29ec7626857e4e03a6fa4897bd410`; historical/superseded.
- v8 Migration Manifest: `d4efc92187d615c3d04808c140dfa6d1a24501cd935ac2fcf8683c88ce73f968`; 29 files; build and separate verify PASS; executor verified, pending independent review.
- v8 Transformation Identity: `6d6d93d2769bc2370f632d3f82f574ed586940a1974bf916636e34d0e2ce6bd8`; executor calculated and bound to Source, v8 migration, SPEC contract, decisions and E011 authorization gate; pending independent review.

## Adversarial results and validation

A/F self-fabricated PASS without canonical authority: BLOCK. B Source mismatch: BLOCK. C Migration mismatch: BLOCK. D Transformation mismatch: BLOCK. E artifact tamper: BLOCK. G wrong scope: BLOCK. H PENDING: BLOCK. I FAIL: BLOCK. J pre-provisioned synthetic PASS bound to exact identities: reached intercepted pre-write boundary; no candidate created. The full E011 CLI positive harness mocks source/manifest verification with synthetic identities; those verifiers have separate regression tests. Real E011 was never run.

Pytest permission root cause: directories created with mode 0700 by Python/pytest were inaccessible in the managed Windows environment. A test-process-only `os.mkdir` mode override to 0777 and a short explicit pytest base temp under the system Temp directory (`s5b01t`, `s5b01reg`, `s5b01full`) allowed isolated fixtures without ACL mutation or production code changes. An initial long project-local path also exceeded practical Windows path limits for content-addressed filenames.

Targeted trust tests: 13 passed. Affected SPEC-005 regression: 46 passed before the extra wrong-SPEC case. Full Python/backend suite after that case: 328 passed. Source and sentinel after: Generation 8/canonical, pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`, runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`, DB `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`, integrity `ok`, FK 0, sidecars 0, maintenance lock absent. Before values matched. No staging, commit or push.
