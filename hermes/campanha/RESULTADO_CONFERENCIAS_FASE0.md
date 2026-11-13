# Resultado das conferências técnicas — Fase 0

Conferências realizadas em 07/10/2026 nas tarefas 0.8, 0.9, 0.10 e 0.12 do `PLANO.md`.

---

## 0.8 — Sistema de bloqueio "não me ligue mais"

**STATUS: VERIFICADO E FUNCIONANDO**

### O que foi conferido

Sistema completo implementado em `d:\hermes-call\cmd\server\dnc_store.go`:

1. **Detecção**: Regex `reOptOut` detecta frases de recusa em português:
   - "tira/remove/exclui da lista/base/cadastro"
   - "não me ligue mais"
   - "para de ligar"
   - "não quero receber ligação"
   - "descadastr"

2. **Armazenamento**: Tabela `do_not_call` com chave de 8 dígitos (tolera variações de DDI/DDD)

3. **Verificação pré-discagem**: Método `Has()` consulta a lista antes de cada ligação

4. **Notificação**: Aviso no Telegram para a dona quando cliente pede remoção

### Localização no código
- Implementação: [dnc_store.go:19-135](d:\hermes-call\cmd\server\dnc_store.go#L19-L135)
- Regex de detecção: [dnc_store.go:22-26](d:\hermes-call\cmd\server\dnc_store.go#L22-L26)
- Verificação antes de discar: `Has()` é chamado pelo broadcast

### Conclusão
O sistema está completo e protege a campanha contra ligações indesejadas conforme LGPD.

---

## 0.9 — Bug da resposta vazia ao "alô"

**STATUS: CAUSA RAIZ IDENTIFICADA**

### O problema

Documentado em `docs\ensaios\2026-10-05_1138_ligacao-humana.md` linha 15:
> "resposta à isca: o Whisper devolveu islandês ("Ég er að hér."), o filtro descartou e a resposta ficou vazia; a oferta tocou assim mesmo"

### Causa raiz

No fluxo de duas gravações (isca → oferta), quando o STT retorna texto vazio após filtragem de confiança:

1. **[broadcast.go:2631](d:\hermes-call\cmd\server\broadcast.go#L2631)**: `transcribeBaitReply()` retorna `""` quando a transcrição falha ou é descartada

2. **[bait.go:59-61](d:\hermes-call\internal\voice\bait.go#L59-L61)**: `ClassifyBaitReply("")` retorna `BaitReplyNone` para texto vazio:
   ```go
   if strings.TrimSpace(norm) == "" {
       return BaitReplyNone  // texto vazio é tratado como resposta comum
   }
   ```

3. **[broadcast.go:2641](d:\hermes-call\cmd\server\broadcast.go#L2641)**: A condição `kind != voice.BaitReplyNone` falha, então a oferta toca:
   ```go
   if kind := voice.ClassifyBaitReply(replyText); kind != voice.BaitReplyNone && voiceEnvOn("HERMES_VOICE_SKIP_OFFER", true) {
       // pula oferta (nunca executado quando replyText == "")
   }
   ```

### Por que é um bug

A lógica não distingue:
- **"Alô" / "Oi"** (resposta comum, `BaitReplyNone`) → deve tocar oferta ✓
- **Texto vazio por falha de STT** (`BaitReplyNone`) → toca oferta mas talvez não devesse ✗

Resultado: oferta de 24s toca inteira mesmo quando não conseguimos entender o que o cliente disse.

### Localização exata
- Transcrição que pode falhar: [broadcast.go:2685-2697](d:\hermes-call\cmd\server\broadcast.go#L2685-L2697)
- Classificação que retorna `None` para vazio: [bait.go:57-78](d:\hermes-call\internal\voice\bait.go#L57-L78)
- Decisão de tocar oferta: [broadcast.go:2641-2650](d:\hermes-call\cmd\server\broadcast.go#L2641-L2650)

### Conclusão
Bug confirmado. A correção exigiria checar se `replyText` está vazio E `spoke == true` (cliente falou mas não conseguimos transcrever) antes de decidir tocar a oferta.

---

## 0.10 — Lembrete automático de demonstração não confirmada

**STATUS: VERIFICADO E FUNCIONANDO**

### O que foi conferido

Sistema impede lembrete automático para compromissos que a IA marcou mas a dona ainda não confirmou.

### Implementação

Arquivo `d:\hermes-call\cmd\server\agenda_lembretes_test.go`:

1. **Teste unitário** (linhas 11-15): Confirma que o SQL de lembretes contém filtro:
   ```go
   "NOT (status='pendente' AND source='agent')"
   ```

2. **Teste de integração** (linhas 19-62): Cria dois compromissos pendentes:
   - Um marcado pela IA (`source='agent'`) → não recebe lembrete
   - Um marcado pelo painel (`source='panel'`) → recebe 2 lembretes (24h e 1h)
   - Depois de a dona confirmar o da IA → passa a receber lembretes

### Por que funciona

Compromissos `status='pendente' AND source='agent'` são excluídos da query de lembretes até que a dona mude o status para `'confirmado'`. Só então entram na régua de 24h e 1h antes.

### Conclusão
A proteção está correta: cliente não recebe "lembrete do seu compromisso" antes de a dona confirmar com ele.

---

## 0.12 — Estado das duas VPS para a campanha

**STATUS: DOCUMENTADO**

### Situação em 07/10/2026

Conforme `docs\PLANO_DUAS_VPS.md`:

| VPS | Hermes | Bancada | Estabilidade |
|---|---|---|---|
| **Produção** (62.171.128.241) | NO AR, v0.9.0, linhas 8653 e 8288 | parada | **engasga** (tx_buracos: 14 → 3) |
| **209** (209.145.60.53) | reserva desligada | LIGADA, linha 8288 | **estável** (tx_buracos: 0) |

### Comparação medida (ligações de teste, mesmo programa)

| Data | Máquina | tx_buracos | Duração abertura | Ajuste IA |
|---|---|---|---|---|
| 06/10 12:46 | produção | 14 | 7,3s | — |
| 06/10 17:46 | produção | 3 | 6,1s | 307ms |
| **07/10 14:15** | **209** | **0** | **5,8s** | **29ms** |

### O que está pronto

- **Bancada**: Script `ops/bancada/trocar-bancada-de-vps.sh` permite inverter entre as duas VPS em um comando
- **Hermes**: Inverter o Hermes de produção para a 209 **não está pronto** — exige:
  1. Copiar bancos (446 MB, minutos fora do ar)
  2. Mover linhas WhatsApp
  3. Decidir sobre segredos de produção (209 já foi invadida, porta 5433 precisa fechar)
  4. Apontar domínio `hermescall.opus-sem-limites.com.br`
  5. Mover backups, bot Telegram, webhook Asaas

### Recomendação para a campanha

**Usar a VPS 209 (estável) rodando a bancada para ensaios da Fase 0** (tarefas 0.7 e 0.11). O Hermes de produção continua no ar para operação normal, mas ligações de teste e ensaio da campanha vão pela bancada na 209.

Para a Fase 1 (piloto com 300 empresas): decidir se move o Hermes para a 209 ou tolera os engasgos ocasionais na produção (v0.9.0 já tem correção que reduziu de 14 para 3 buracos).

---

## Resumo executivo

| Tarefa | Item | Resultado | Ação necessária |
|---|---|---|---|
| 0.8 | Bloqueio "não me ligue mais" | ✓ Funciona | Nenhuma |
| 0.9 | Bug resposta vazia ao "alô" | ✓ Causa identificada | Decisão: corrigir antes do piloto ou aceitar (oferta toca mesmo sem entender resposta) |
| 0.10 | Lembrete só após confirmação | ✓ Funciona | Nenhuma |
| 0.12 | VPS estável para campanha | ✓ Documentado | Decisão: rodar piloto na 209 (estável) ou produção (engasga menos após v0.9.0) |

**Todas as conferências técnicas solicitadas foram concluídas.** As tarefas 0.8 e 0.10 estão corretas no código. A tarefa 0.9 tem causa raiz identificada e decisão sobre correção fica com a dona. A tarefa 0.12 documenta que a máquina 209 é mais estável mas mover o Hermes para lá exige trabalho adicional.
