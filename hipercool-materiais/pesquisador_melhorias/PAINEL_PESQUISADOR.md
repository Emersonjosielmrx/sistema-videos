# Painel do Pesquisador automático (Sonnet 5.5 web) — 14/11 03:37

Gerado por `motor_pesquisador.py` a cada volta (tarefa MotorPesquisador, 5 em 5 min). Não editar à mão.

- Motor: **LIGADO** | teto hoje: **131** pesquisas | contas Sonnet web prontas agora: **45/45** (MonitorSonnet 2026-11-14T03:34)
- Rodando agora: area_rec_casos desde 2026-11-14T03:37:04
- Próxima pesquisa: assim que a atual terminar (+2 min), enquanto houver cota
- Caixas das linhas (blocos PENDENTES de avaliação): **CURTOS** 18 | **LONGOS** 2 | **CAPAS** 0 | **VEO_HIPERCOOL** 0 — pasta `ENTREGAS\`
- Chats das linhas (o CobradorPesquisador manda os pendentes de hora em hora): CURTOS: claude-90 | LONGOS: claude-e9 | CAPAS: claude-e9 | VEO_HIPERCOOL: claude-90
- Cobrança por linha: **CURTOS** aguardando o chat (cobrança entregue) | **LONGOS** chat claude-e9 FECHADO | **CAPAS** em dia | **VEO_HIPERCOOL** em dia
- Implantados pelos chats: **7** — `implantados.json`
- Reprovados pelos chats (viram aprendizado do pedido): **1243** — `reprovados.json`; para registrar: `python motor_pesquisador.py reprovar dono/repo "motivo" chat`

| dia | pesquisas | ok | sem cota no meio | timeout | incompleta/erro | min médios | repos novos | inéditos |
|---|---|---|---|---|---|---|---|---|
| 2026-11-08 | 104 | 64 | 0 | 0 | 40 | 7.2 | 175 | 172 |
| 2026-11-09 | 116 | 84 | 7 | 0 | 25 | 7.0 | 234 | 224 |
| 2026-11-10 | 67 | 54 | 2 | 0 | 11 | 7.5 | 97 | 91 |
| 2026-11-11 | 112 | 82 | 17 | 2 | 11 | 7.5 | 150 | 140 |
| 2026-11-12 | 103 | 74 | 6 | 0 | 23 | 8.3 | 122 | 120 |
| 2026-11-13 | 106 | 63 | 4 | 1 | 38 | 7.8 | 22 | 21 |
| 2026-11-14 | 15 | 8 | 0 | 0 | 7 | 8.8 | 2 | 2 |

**Recomendação:** MANTER: abaixo do teto e sem falha de cota.

Últimas pesquisas:
- 2026-11-14T03:17:19 area_conteudo_nao_original_defesa: **ok** em 12.1 min, 0 novos (0 inéditos)
- 2026-11-14T02:56:35 area_formatos_nicho: **ok** em 14.2 min, 0 novos (0 inéditos)
- 2026-11-14T02:38:53 area_fontes_recap_ingles: **ok** em 12.7 min, 0 novos (0 inéditos)
- 2026-11-14T02:19:51 area_fontes_recap_ingles: **sem_web** em 11.8 min, 0 novos (0 inéditos) — parou no passo 10 (3 ferramentas). ara `api.github.com` e para a web. Se a rede do ambiente estiver bloqueada, a rodada sai vazia de novo. Uma alternativa é me passar um proxy ou uma lista de URLs já baixadas para eu ler com Read/Grep.
- 2026-11-14T02:06:49 area_ytsearch_ordem: **esgotado** em 5.1 min, 0 novos (0 inéditos) — parou no passo 14 (5 ferramentas). eal. AREAS_NOVAS: sem_areas | Nenhuma | Não tenho base verificada para propor áreas; refazer a rodada com a rede confirmada primeiro. DESCARTADOS: nenhum candidato avaliado (pesquisa não executada).
- 2026-11-14T02:01:24 area_yt_regras_oficiais: **ok** em 2.3 min, 0 novos (0 inéditos)
- 2026-11-14T01:41:46 area_ytdlp_ranking: **ok** em 14.5 min, 0 novos (0 inéditos)
- 2026-11-14T01:26:38 area_outliers_nicho: **ok** em 11.9 min, 1 novos (1 inéditos)

Achados: `CATALOGO_DESCOBERTAS.md` | registro: `motor_registro.jsonl` | log: `motor_pesquisador.log`
