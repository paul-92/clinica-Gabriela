# Cutover Readiness Report v2 — SPEC-008

- Data: 2026-09-13
- Escopo: implementação e preflight da infraestrutura da Fase 10
- Candidato: `verified-v2`
- Classificação final: `BLOCKED`
- Cutover real: não executado e não autorizado

## Resultado executivo

Os oito componentes de infraestrutura foram implementados e validados em fixtures e
cópias isoladas. A simulação final aprovou tanto o caminho nominal quanto rollback e
restore após falha injetada antes de writes. Entretanto, o preflight final detectou
mudança física no banco histórico backend durante a janela de implementação. Como a
imutabilidade histórica é gate obrigatório, o processo foi interrompido e permanece
`BLOCKED` até decisão HUMAN.

Nenhuma tentativa de restaurar, sobrescrever ou normalizar o banco histórico foi
realizada.

## Candidato e cadeia protegida

| Gate | Resultado |
|---|---|
| Checksum do candidato | `PASS` — `96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46` |
| Freeze | `PASS` — `spec008-20260911-phase1-001-freeze-v7` |
| Schema | `PASS` — `backend-models-v2-credential-reset` |
| Remap | `PASS` — lifecycle `verified`, versão `verified-v2` |
| Integridade | `PASS` — `integrity_check=ok` |
| FKs | `PASS` — zero violações |
| Sidecars do candidato | `PASS` — zero |
| Cadeia de snapshots/manifests/provenance | `PASS` |

O candidato, snapshots, freeze e manifests protegidos permaneceram somente leitura.

## Estado dos oito BLOCKs originais

1. **Maintenance lock — `IMPLEMENTED/PASS`**
   - criação exclusiva `O_EXCL`, ownership por token e release autenticado;
   - integração fail-closed no backend e desktop;
   - `BEGIN EXCLUSIVE` mantido sobre cada fonte da janela;
   - teste prova que writer concorrente recebe `database is locked`;
   - sidecar preexistente impede aquisição do lock.

2. **Destino versionado e ACL — `IMPLEMENTED/HUMAN_PARAMETER_PENDING`**
   - nome content-addressed inclui versão e prefixo do checksum;
   - destino preexistente é recusado;
   - promoção exige mesmo volume;
   - ACL é vinculada por fingerprint exato fornecido externamente, sem inferir uma
     política de segurança não aprovada;
   - caminho e fingerprint reais ainda exigem aprovação HUMAN separada.

3. **Promoção atômica Windows — `IMPLEMENTED/PASS_IN_SIMULATION`**
   - cópia para temporário no diretório de destino, flush/fsync, checksum e SQLite;
   - publicação por hard link atômico fail-existing no mesmo NTFS;
   - falha remove apenas temporário/destino incompleto da fixture;
   - nenhum nome histórico é reutilizado.

4. **Ponteiro persistente — `IMPLEMENTED/PASS_IN_SIMULATION`**
   - JSON canônico versionado;
   - geração monotônica e cadeia de predecessor;
   - compare-and-swap do checksum atual;
   - histórico imutável e substituição atômica por `os.replace`;
   - rollback cria nova geração, sem apagar história;
   - ponteiro ausente, corrompido, adulterado ou concorrente falha fechado.

5. **Final backup coordenado — `IMPLEMENTED/PASS_IN_SIMULATION`**
   - exige ownership do maintenance lock e lock SQLite exclusivo de todas as fontes;
   - recusa WAL não vazio, SHM incoerente ou sidecar pré-quiescência;
   - cópia ocorre somente sob exclusão, seguida de fsync, integridade, FKs e manifest;
   - mudança da origem durante backup aborta;
   - manifest privacy-safe contém checksums, tamanhos e resultados.

6. **Proteção do desktop legado — `IMPLEMENTED/PASS`**
   - entrypoint desktop recusa iniciar com maintenance lock;
   - recusa iniciar quando o ponteiro persistente está em estado `canonical`;
   - backend write-enabled também recusa startup/manutenção.

7. **Runtime content-addressed — `IMPLEMENTED/PASS`**
   - manifest final:
     `runtime-manifest-b9cdc844a2b578afa05bc66efcf32f5a55675d1fb0ae3f150923d79c9d46a904.json`;
   - checksum: `b9cdc844a2b578afa05bc66efcf32f5a55675d1fb0ae3f150923d79c9d46a904`;
   - ponteiro vincula o checksum do runtime;
   - startup verifica o manifest e cada arquivo; mudança de bytes falha fechado.

8. **Verificação pós-promoção read-only — `IMPLEMENTED/PASS`**
   - exige maintenance lock ativo;
   - engine abre SQLite com `mode=ro&immutable=1`;
   - bootstrap não cria schema, não migra e não executa seed;
   - middleware externo bloqueia POST/PUT/PATCH/DELETE antes de licença/autenticação;
   - teste de SQL direto comprova impossibilidade de INSERT.

## Testes e simulações

- Testes direcionados intermediários: `36 passed`, depois `15 passed` e `27 passed`.
- Regressão final antes do preflight: `192 passed`.
- Frontend: `5 passed`.
- Build Vite: `PASS`, 1.582 módulos.
- Simulação final v5: `PASS`.
- Evidência v5:
  `spec008-20260913-cutover-simulation-v5.json`.
- SHA-256 da evidência v5:
  `93532d285c67a9c8cb3a92668fcfe684792dd1326039fb657ed6e46bd5026e31`.

### Caminho nominal simulado

`QUIESCE → FINAL BACKUP → REVALIDATE → PROMOTE → START → HEALTH → SMOKE → VERIFY → ACCEPT`

Resultado: `PASS`. O ACCEPT foi apenas marcador da fixture; não houve aceite nem
cutover real.

### Caminho de falha simulado

`FAIL → QUIESCE → ROLLBACK → RESTORE → START → HEALTH → VERIFY`

Falha injetada: `START_FAILURE_BEFORE_WRITES`. Resultado: ponteiro retornou a
`legacy`, restore íntegro, startup read-only aprovado, health aprovado, zero FKs e
banco sem alteração.

## Falhas técnicas corrigidas

- limite de caminho do Windows para manifests content-addressed: simulações movidas
  para raiz curta não operacional;
- ordem de middleware inicialmente permitia a licença responder antes do guard
  read-only: guard tornou-se camada externa;
- fsync em handle read-only no Windows: corrigido para handle apropriado;
- compatibilidade de `BACKEND_DATA_DIR`: restaurada;
- SQLite WAL cria sidecars vazios pertencentes ao próprio lock: sidecars anteriores
  continuam proibidos e WAL durante lock somente é aceito com tamanho zero;
- lock apenas cooperativo: reforçado com exclusão SQLite real e teste concorrente.

## BLOCK novo — imutabilidade histórica

Baseline observada antes da implementação:

- `backend/data/clinica_api.db`
- SHA-256: `8f973f56654fb92f03c278f21934b976c76ba61318edd1f449dbe4584bed0aed`
- timestamp UTC: `2026-07-06T14:45:25.6521364Z`

Estado detectado no preflight final:

- SHA-256: `d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757`
- timestamp UTC: `2026-09-13T20:21:30.5809353Z`
- tamanho: 61.440 bytes
- `integrity_check=ok`
- violações de FK: zero
- sidecars: zero

A comparação agregada read-only com o snapshot backend mostrou as mesmas contagens
nas oito tabelas, integridade aprovada e zero FKs. Isso não elimina a divergência
física nem autoriza considerar o histórico imutável.

A causa provável é contaminação da suíte por restauração da configuração global para
o runtime padrão, seguida de conexão SQLite, mas a causa exata não foi comprovada.
Corrigir ou restaurar o banco agora seria uma escrita destrutiva/proibida e exige
decisão HUMAN.

O banco desktop manteve checksum, tamanho e timestamp anteriores.

## Riscos residuais e gates HUMAN

- decidir o tratamento do banco histórico backend fisicamente alterado;
- aprovar ou rejeitar eventual restauração a partir de snapshot/backup validado;
- aprovar caminho canônico real e fingerprint ACL exato;
- definir responsáveis e duração da rollback window;
- somente após resolver a imutabilidade, repetir regressão em ambiente impedido de
  alcançar bancos operacionais e repetir o preflight completo;
- autorização de cutover continua sendo decisão HUMAN separada.

## Classificação final

`BLOCKED`

Não houve promoção real, criação/troca de ponteiro real, desativação de legado,
cutover ou commit.
