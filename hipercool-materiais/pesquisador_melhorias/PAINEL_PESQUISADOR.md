# Painel do Pesquisador automático (Sonnet 5.5 web) — 20/11 12:21

Gerado por `motor_pesquisador.py` a cada volta (tarefa MotorPesquisador, 5 em 5 min). Não editar à mão.

- Motor: **LIGADO** | teto hoje: **131** pesquisas | contas Sonnet web prontas agora: **45/45** (MonitorSonnet 2026-11-20T12:15)
- Rodando agora: area_android_adb_automacao_upload desde 2026-11-20T12:21:47
- Próxima pesquisa: assim que a atual terminar (+2 min), enquanto houver cota
- Caixas das linhas (blocos PENDENTES de avaliação): **CURTOS** 49 | **LONGOS** 0 | **CAPAS** 0 | **VEO_HIPERCOOL** 28 — pasta `ENTREGAS\`
- Chats das linhas (o CobradorPesquisador manda os pendentes de hora em hora): CURTOS: fable melhorias | LONGOS: claude-f1 | CAPAS: claude-f1 | VEO_HIPERCOOL: fable melhorias
- Cobrança por linha: **CURTOS** chat fable melhorias FECHADO | **LONGOS** em dia | **CAPAS** em dia | **VEO_HIPERCOOL** chat fable melhorias FECHADO
- Implantados pelos chats: **9** — `implantados.json`
- Reprovados pelos chats (viram aprendizado do pedido): **1304** — `reprovados.json`; para registrar: `python motor_pesquisador.py reprovar dono/repo "motivo" chat`

| dia | pesquisas | ok | sem cota no meio | timeout | incompleta/erro | min médios | repos novos | inéditos |
|---|---|---|---|---|---|---|---|---|
| 2026-11-14 | 107 | 55 | 0 | 0 | 52 | 8.3 | 19 | 18 |
| 2026-11-15 | 104 | 44 | 0 | 2 | 58 | 8.0 | 10 | 10 |
| 2026-11-16 | 104 | 69 | 7 | 0 | 28 | 6.0 | 28 | 27 |
| 2026-11-17 | 106 | 81 | 2 | 0 | 23 | 6.6 | 71 | 70 |
| 2026-11-18 | 112 | 81 | 2 | 1 | 28 | 6.0 | 56 | 56 |
| 2026-11-19 | 110 | 74 | 3 | 1 | 32 | 6.6 | 38 | 38 |
| 2026-11-20 | 59 | 42 | 2 | 1 | 14 | 6.9 | 23 | 22 |

**Recomendação:** COTA: 2 pesquisa(s) hoje acabaram sem cota no meio — o motor espera a hora de volta das contas.

Últimas pesquisas:
- 2026-11-20T11:28:51 area_gemini_web_sessao_cookie: **sem_cota_no_meio** em 20.9 min, 0 novos (0 inéditos) — parou no passo 39 (15 ferramentas). e ler como o Orbit trata a renovação da sessão, antes de escrever a resposta. API Error: Request rejected (429) · [claude-web/claude-sonnet-5-5] [429]: Rate limited by Claude Web API (reset after 1s) API Error: Request rejected (429) · [claude-web/claude-sonnet-5-5] [429]: Rate limited by Claude Web API (reset after 1s) | próxima às 12:19 (volta da cota)
- 2026-11-20T10:56:34 area_gemini_web_sessao_cookie: **timeout** em 25.3 min, 0 novos (0 inéditos) — parou no passo 36 (13 ferramentas). v, que só faz a requisição inicial com os cookies. Falta ver como ele trata a renovação do `__Secure-1PSIDTS` e o erro 401. Vou procurar isso no código e fazer mais buscas, sem repetir o que já temos.
- 2026-11-20T10:34:22 area_gemini_web_sessao_cookie: **ok** em 16.6 min, 1 novos (1 inéditos)
- 2026-11-20T10:17:49 area_camera_3d_painel: **ok** em 11.6 min, 0 novos (0 inéditos)
- 2026-11-20T10:01:34 area_camera_3d_painel: **ok** em 10.9 min, 0 novos (0 inéditos)
- 2026-11-20T09:52:31 area_camera_3d_painel: **ok** em 5.7 min, 1 novos (0 inéditos)
- 2026-11-20T09:38:12 area_android_adb_automacao_upload: **erro_proxy** em 8.7 min, 0 novos (0 inéditos) — parou no passo 50 (18 ferramentas). scas focadas no upload e no Gemini, com saída segura para cp1252. Vou rodar mais uma bateria de buscas curtas, com saída em UTF-8 segura e 7 s entre elas. API Error: Claude Web stream protocol error API Error: Claude Web stream protocol error
- 2026-11-20T09:22:12 area_camera_3d_painel: **ok** em 8.3 min, 0 novos (0 inéditos)

Achados: `CATALOGO_DESCOBERTAS.md` | registro: `motor_registro.jsonl` | log: `motor_pesquisador.log`
