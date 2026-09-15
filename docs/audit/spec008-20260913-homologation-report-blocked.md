# Homologation Report — SPEC-008

- Data: 2026-09-13
- Escopo: Fase 9, janela de homologação sem cutover
- Candidato solicitado: `verified-v2`
- Recomendação técnica: `BLOCKED`
- Cutover: proibido e não executado

## Pré-validação

O artefato canônico `verified-v2` e seu pacote vinculante não foram encontrados nos
locais acessíveis pesquisados. Não foi possível obter o caminho do candidato, seu
checksum esperado, manifest `verified-v2`, freeze vigente ou inventário de artefatos
protegidos. Portanto, não é possível provar identidade exata, vínculo com o freeze,
schema, integridade, ausência de sidecars ou imutabilidade contra a baseline congelada.

Conforme o critério de aborto da SPEC-008 e a instrução HUMAN desta janela, a
homologação foi interrompida antes de qualquer teste ou escrita.

## Estado read-only observado

| Persistência legada | Tamanho | SHA-256 observado | Sidecars SQLite |
|---|---:|---|---|
| `data/clinica_psicologia.db` | 61.440 bytes | `5aa6a8d22ecbf9b8f6d4574ae49a2c611ab089aa933132ea47dd5e1c451d793b` | nenhum |
| `backend/data/clinica_api.db` | 61.440 bytes | `8f973f56654fb92f03c278f21934b976c76ba61318edd1f449dbe4584bed0aed` | nenhum |

Esses valores são observações pontuais, não uma confirmação contra o freeze, pois a
baseline vinculante não estava acessível. Nenhum banco foi aberto para escrita.

## Resultados da Fase 9

| Gate/fluxo | Resultado | Evidência/razão |
|---|---|---|
| Identificação/checksum do candidato | `BLOCK` | candidato e checksum esperado indisponíveis |
| Versão do freeze | `BLOCK` | pacote de freeze vigente indisponível |
| Schema/integridade/FKs do candidato | `NOT_RUN` | pré-validação bloqueada |
| Ausência de sidecars do candidato | `NOT_RUN` | caminho do candidato indisponível |
| Imutabilidade de históricos/snapshots/manifests | `PARTIAL` | históricos observados read-only; comparação com baseline impossível |
| Startup exclusivo no candidato | `NOT_RUN` | proibido prosseguir após `BLOCK` |
| Health check e reinício controlado | `NOT_RUN` | pré-validação bloqueada |
| Autenticação | `NOT_RUN` | pré-validação bloqueada |
| `password_reset_required` | `NOT_RUN` | pré-validação bloqueada |
| Credencial desabilitada | `NOT_RUN` | pré-validação bloqueada |
| Patients | `NOT_RUN` | pré-validação bloqueada |
| Psychologists | `NOT_RUN` | pré-validação bloqueada |
| Appointments | `NOT_RUN` | pré-validação bloqueada |
| Clinical records | `NOT_RUN` | pré-validação bloqueada |
| Payments | `NOT_RUN` | pré-validação bloqueada |
| Expenses | `NOT_RUN` | pré-validação bloqueada |
| Clinic settings | `NOT_RUN` | pré-validação bloqueada |
| Persistência após reinício | `NOT_RUN` | pré-validação bloqueada |
| Backup/restauração | `NOT_RUN` | pré-validação bloqueada |
| Smoke tests/regressão automatizada | `NOT_RUN` | pré-validação bloqueada |
| Ausência de dual-write | `NOT_RUN` | runtime do candidato não iniciado |
| Runtime legado inalterado | `PASS_OBSERVED` | nenhuma configuração/runtime foi alterada nesta execução |
| Plano de rollback pré-cutover | `REVIEW_REQUIRED` | estratégia consta na SPEC; execução não validável sem pacote/candidato |

## Falhas, correções e reinício

- Falha: material vinculante de `verified-v2` ausente ou não acessível.
- Classificação: `BLOCK`.
- Correções: nenhuma; reconstruir ou inferir o candidato violaria a exigência de
  identidade exata e de vínculo com o freeze.
- Reinício: não executado.
- Backup/restauração: não executado.

## Ausência de dual-write

Não houve inicialização do backend nem alteração de configuração nesta execução.
Assim, esta execução não introduziu dual-write. A independência funcional do candidato
continua não homologada.

## Rollback pré-cutover

A estratégia documentada permanece conceitualmente aplicável: parar a carga, fechar
conexões, preservar evidências, invalidar e descartar somente o temporário controlado,
mantendo originais e snapshots intactos. A validação operacional permanece aberta até
que o candidato e todo o pacote congelado estejam disponíveis.

## Riscos residuais e gates abertos

- identidade e checksum de `verified-v2` não comprovados;
- freeze vigente e manifests vinculantes não comprovados;
- snapshots e artefatos protegidos não comparados à baseline;
- todos os fluxos funcionais/técnicos da Fase 9 permanecem abertos;
- independência de dual-write não comprovada;
- backup/restauração e rollback operacional não exercitados;
- aceites técnico, funcional, clínico/financeiro e HUMAN permanecem abertos.

## Condição para retomada

Disponibilizar o caminho read-only do diretório protegido que contenha, no mínimo, o
candidato `verified-v2`, checksum esperado, freeze vigente, manifests de snapshot e
remap `verified-v2`, relatório de validação das Fases 5–8 e inventário/checksums dos
artefatos protegidos. A retomada deve começar novamente pela pré-validação.
