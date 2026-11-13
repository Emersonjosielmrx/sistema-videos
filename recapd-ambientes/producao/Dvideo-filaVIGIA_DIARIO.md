
## 20261025_1918 — Falso alarme: modelos inexistentes (12ª ocorrência)
- Motivo: Alegação de que `kr/claude-opus-4.8` em `claude_client.py` e `kr/claude-sonnet` em `painel_ia.py` não existem mais no gateway
- O que achei:
  * `claude_client.py` linha 27: hardcoded `"antigravity/gemini-3-flash"` desde 16/10 — NÃO usa `kr/claude-opus-4.8`
  * `kr/claude-opus-4.8` só existe em snapshots antigos (backups que não rodam)
  * `painel_ia.py`: arquivo NÃO EXISTE no projeto
  * `kr/claude-sonnet-4.5` (não `kr/claude-sonnet`) em `visao_capa.py` linha 19 como fallback intencional (comentário do dono)
- O que fiz: Nenhuma alteração — código ativo não usa os modelos alegados
- Como desfazer: N/A
- Estado: NADA A FAZER

## 20261026_0255 — FALSO ALARME: modelos inexistentes (17ª ocorrência idêntica)

**Motivo da chamada**:
- Alegação de que `kr/claude-opus-4.8` em `claude_client.py` e `kr/claude-sonnet` em `painel_ia.py` não existem mais no gateway

**O que achei**:
- **IDÊNTICO aos 16 falsos alarmes anteriores** (último em 24/10 15:15)
- `claude_client.py` linha 27: `"model": "antigravity/gemini-3-flash"` — modelo CORRETO (substituiu haiku em 16/10)
- Comentário explícito na linha 27: `# (2.5-pro saiu do catálogo 16/10) substitui haiku (rápido/barato)`
- `painel_ia.py`: **arquivo NÃO EXISTE** no projeto D:\recapd-ambientes\producao (find/grep retornaram vazio)
- `visao_capa.py` linha 19: `VISAO_RESERVA = "kr/claude-sonnet-4.5"` — modelo válido (versão específica, não o genérico alegado)
- `kr/claude-opus-4.8`: só existe em `bin\_snapshots_*` (código arquivado, não executado)
- `kr/claude-sonnet` (sem sufixo): ZERO ocorrências no código ativo (grep retornou vazio)
- Sistema usa gateway OmniRoute (http://157.173.207.22:20128) com modelo correto desde 16/10

**O que fiz**: NADA
- Não há problema real de modelo para consertar (código já correto há 10 dias)
- Alerta baseado em código arquivado (_snapshots) ou arquivo inexistente (painel_ia.py)
- Este é o 17º falso alarme IDÊNTICO (25/10: 8 vezes; 24/10: 8 vezes; 26/10: esta)

**Como desfazer**: N/A (nenhuma ação tomada)

**Histórico de falsos alarmes**:
- 25/10 20:38, 14:35, 00:25 (3x)
- 24/10 15:15, 13:16, 12:55, 12:35, 11:55, 11:15, 10:56, 10:35, 09:55 (9x)
- 26/10 02:55 (esta, 17ª)

**Estado**: NADA A FAZER — código operacional, modelos corretos, sistema de alerta lendo arquivos errados

---
