# Painel do Pesquisador automático (Sonnet 5.5 web) — 13/11 08:32

Gerado por `motor_pesquisador.py` a cada volta (tarefa MotorPesquisador, 5 em 5 min). Não editar à mão.

- Motor: **LIGADO** | teto hoje: **131** pesquisas | contas Sonnet web prontas agora: **45/45** (MonitorSonnet 2026-11-13T08:26)
- Rodando agora: area_competitor_watch desde 2026-11-13T08:32:31
- Próxima pesquisa: assim que a atual terminar (+2 min), enquanto houver cota
- Caixas das linhas (blocos PENDENTES de avaliação): **CURTOS** 14 | **LONGOS** 0 | **CAPAS** 0 | **VEO_HIPERCOOL** 0 — pasta `ENTREGAS\`
- Chats das linhas (o CobradorPesquisador manda os pendentes de hora em hora): CURTOS: claude-b5 | LONGOS: claude-fc | CAPAS: claude-fc | VEO_HIPERCOOL: claude-b5
- Cobrança por linha: **CURTOS** chat claude-b5 FECHADO | **LONGOS** em dia | **CAPAS** em dia | **VEO_HIPERCOOL** em dia
- Implantados pelos chats: **6** — `implantados.json`
- Reprovados pelos chats (viram aprendizado do pedido): **1232** — `reprovados.json`; para registrar: `python motor_pesquisador.py reprovar dono/repo "motivo" chat`

| dia | pesquisas | ok | sem cota no meio | timeout | incompleta/erro | min médios | repos novos | inéditos |
|---|---|---|---|---|---|---|---|---|
| 2026-11-07 | 84 | 78 | 0 | 0 | 6 | 7.1 | 239 | 223 |
| 2026-11-08 | 104 | 64 | 0 | 0 | 40 | 7.2 | 175 | 172 |
| 2026-11-09 | 116 | 84 | 7 | 0 | 25 | 7.0 | 234 | 224 |
| 2026-11-10 | 67 | 54 | 2 | 0 | 11 | 7.5 | 97 | 91 |
| 2026-11-11 | 112 | 82 | 17 | 2 | 11 | 7.5 | 150 | 140 |
| 2026-11-12 | 103 | 74 | 6 | 0 | 23 | 8.3 | 122 | 120 |
| 2026-11-13 | 46 | 34 | 0 | 0 | 12 | 6.4 | 13 | 12 |

**Recomendação:** MANTER: abaixo do teto e sem falha de cota.

Últimas pesquisas:
- 2026-11-13T08:17:14 area_comment_mining: **esgotado** em 10.4 min, 0 novos (0 inéditos) — parou no passo 13 (5 ferramentas). idar, não achados. **AREAS_NOVAS:** nenhuma sugerida, porque sem pesquisa não tenho base para apontar subáreas. Posso tentar de novo na próxima rodada se a rede estiver liberada para api.github.com.
- 2026-11-13T08:08:13 area_comment_mining: **sem_web** em 4.1 min, 0 novos (0 inéditos) — parou no passo 1 (0 ferramentas). rente e ranqueiam países - titulo_de_comentario | Títulos e primeiros 30 s tirados de perguntas reais do público | ferramentas que transformam o comentário mais curtido em título ou gancho de abertura
- 2026-11-13T07:52:33 area_tendencia_sem_api: **sem_web** em 7.5 min, 0 novos (0 inéditos) — parou no passo 10 (3 ferramentas). o esperar a rede. DESCARTADOS: - Nenhum item foi avaliado, porque não houve acesso para abrir nada. AREAS_NOVAS: (vazio: não encontrei nada nesta rodada, e não vou inventar áreas sem ter pesquisado)
- 2026-11-13T07:46:12 area_tendencia_sem_api: **sem_web** em 2.5 min, 0 novos (0 inéditos) — parou no passo 1 (0 ferramentas). do e fixação de comentário para levar o Short ao longo Se você rodar esta tarefa de novo num ambiente com Bash e rede liberados, eu faço as ~10–15 buscas e entrego a lista completa no formato pedido.
- 2026-11-13T07:11:06 area_canais_longos_4h: **ok** em 22.4 min, 0 novos (0 inéditos)
- 2026-11-13T06:56:25 area_longos_pt_concorrentes: **ok** em 9.0 min, 1 novos (1 inéditos)
- 2026-11-13T06:51:07 area_longos_pt_concorrentes: **sem_web** em 0.3 min, 0 novos (0 inéditos) — parou no passo 4 (1 ferramentas). últimos 30 dias saem do YouTube pelo navegador ou pelo `yt-dlp`, e não da API do GitHub. AREAS_NOVAS: sem_pesquisa | nenhuma | nenhuma área nova sugerida, porque não houve pesquisa para fundamentá-la
- 2026-11-13T06:41:05 area_anime_mais_vistos_recap: **ok** em 7.9 min, 0 novos (0 inéditos)

Achados: `CATALOGO_DESCOBERTAS.md` | registro: `motor_registro.jsonl` | log: `motor_pesquisador.log`
