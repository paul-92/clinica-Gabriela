# SPEC-004 — Implementation Candidate Report

## Estado

`READY_FOR_SPEC004_OPERATIONAL_GATE`

Baseline Git: `19983dc5ec940b65d552bb57eb0f85ee0e9aadba`.
Candidato: `a88ef64c4baf589cd13448669ef80a910a0bcd769e630395e0914ef94ae7d511`.

## Evidence por etapa

| Etapa | Resultado | Evidence privacy-safe |
|---|---|---|
| Baseline Lock | PASS | Generation 5/canonical; manifest `e7951f...171d1`; banco `143523...bb506`; `user_version=3`; integridade ok; zero FKs |
| Harness RED | PASS | falha inicial reproduzível: `AppointmentEvent` ausente durante coleta |
| Schema Candidate | PASS | cópia isolada `user_version=4`; SHA-256 `7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07`; integridade ok; zero FKs; sem sidecars |
| Domain Core | PASS | estados, duração, intervalo semiaberto, retroatividade, timezone, autorização e transições explícitas |
| Atomicidade | PASS | fault injection no commit preservou original, impediu sucessor e evento parcial |
| Concorrência | PASS | duas conexões SQLite reais: uma reserva persistida e uma resposta `409` |
| API | PASS | PATCH/If-Match, `428`, `412`, ações explícitas e mensagens sanitizadas |
| Frontend | PASS | PATCH/action com If-Match, remarcação atômica, falta, feedback da API e ação `done` oculta da recepção |
| Regressão | PASS | Python `216 passed`; frontend `5 passed`; build Vite passou |

## Reparos e invalidação seletiva

- O RED estrutural foi corrigido pelo evento append-only e schema v4.
- O Windows não possuía base IANA; `tzdata` foi declarado e instalado no ambiente de
  desenvolvimento.
- A primeira migration isolada foi bloqueada pelo runtime freeze; o reteste desacoplou
  apenas o processo de candidato, sem tocar o pointer.
- A primeira materialização herdou WAL; a migration passou a forçar `journal_mode=DELETE`
  na cópia, produzindo artefato autocontido sem sidecars.
- Quatro testes canônicos foram invalidados pela nova tabela; o verifier foi atualizado
  para o schema v4 e a suíte completa voltou a passar.
- O primeiro build falhou com `spawn EPERM` no sandbox; fora do sandbox passou.

## Recovery e limites

O banco operacional, pointer, manifest vigente e Generation 5 não foram alterados. A
migration é forward-only e foi exercitada somente sobre cópia. Nenhum cleanup, rollback,
push, merge ou release foi executado. A promoção requer gate HUMAN e deve criar nova
Generation/manifest, backup verificado e smoke no runtime promovido; até lá o smoke
default do candidato não pode substituir silenciosamente o runtime congelado vigente.

## Riscos residuais

- O vínculo `users.psychologist_id` precisa ser preenchido explicitamente na futura
  promoção; ausência permanece fail-closed.
- Registros legados permanecem `legacy_unverified`; nenhuma autoria, sucessor ou timezone
  histórico foi inventado.
- A correção excepcional administrativa está suportada pelo desenho append-only, mas sua
  interface dedicada permanece fora do fluxo operacional normal e deverá ser validada no
  gate antes de uso.

`STOP_CONDITION = READY_FOR_SPEC004_OPERATIONAL_GATE`
