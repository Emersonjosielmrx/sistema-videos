# Trio de imagem e vídeo (14/11/2026)

Pedido da dona: "o Gemini como primeiro, o Flow sem navegador como fallback e o Flow com navegador como terceiro;
usar o Gemini e não o Argon, para não consumir crédito do Argon".

## Ordem

| | 1º | 2º | 3º |
|---|---|---|---|
| **Imagem** (`D:\flow-imagens\cliente.py` → `gerar()`) | Gemini sem navegador | Flow HTTP (fábrica de tokens) | Flow pela tela |
| **Vídeo** (`D:\veo\beta\gera_auto.py` → `gerar()`) | Gemini sem navegador | Flow nos notebooks/HTTP | Flow pela tela |

- Todos os projetos que pedem imagem passam pelo `cliente.gerar()` (capas do hipercool/historias/recapd, cenas do
  historias, arte do manhwa-react, fundo de CTA do Veo, carrossel do MS Energy). Nada mudou neles.
- Pedido com **foto de referência** (imagem) ou **foto inicial** (vídeo, animar foto) pula o Gemini: o HTTP do Gemini
  ainda não anexa arquivo.
- O vídeo do Gemini sai com 10 s e é cortado na duração pedida (`FLOW_DURATION`, 8 s). O porteiro do robô aprova
  (`validar_video`: 720x1280, 8,08 s, com áudio).
- Vídeo feito pelo Gemini imprime `GEMINI_VIDEO_OK`: o robô NÃO desconta os 20 créditos do Flow da conta.
- **Flow inteiro sem crédito**: antes o ciclo parava; agora, se o Gemini tem conta, o robô roda com a sessão virtual
  `gemini` (`VEO_SO_GEMINI=1`: o worker só tenta o Gemini e, se não entregar, sai com "sem crédito" e o prompt volta
  pra fila). A sessão `gemini` não entra no `sessoes_status.json` nem no `creditos_contas.json`.

## Não gasta o Argon

O pedido usa o modelo flash (imagem) / `8c46e95b1a07cecc` (vídeo), nunca o 4 Argon; as cotas de imagem e vídeo do app
são separadas da de texto (conferido: conta que gerou vídeo seguiu com o Argon). Ordem das contas
(`gemini_midia_http.candidatas`): 1º as SEM cota de texto do Argon (crédito parado), 2º as que o Argon não está usando,
a que menos gerou hoje antes. Fila própria em `midia_contas.json` — falha de mídia nunca tira conta do Argon. Cookie
morto: a conta sai da fila e o zelador do Argon renova (`marcar_cookies`, o mesmo que o Argon faria).

## Regras de segurança

- No máx. 2 contas tentadas por pedido; conta ocupada por outro pedido não conta e passa pra próxima livre. Nunca varre
  a lista (regra do IP, CLAUDE.md). Cada conta fala pela mesma saída que o Argon já usa.
- 1 pedido por conta por vez, entre processos (`travas_midia\<conta>.lock`).
- Cota de vídeo lida antes de gastar (`MyzX6c`, sem custo): esgotada sai da fila até a hora exata que o Google informa.
- Vídeo que não fica pronto em 240 s desiste e passa pro Flow (o motivo vai pro `midia.log`).
- A conversa do vídeo é apagada depois de baixar (`GzXR5e`); a imagem usa chat temporário (não fica no histórico).

## Desligar

- `GEMINI_MIDIA=0` (tudo), `GEMINI_IMAGEM=0` ou `GEMINI_VIDEO=0` → volta ao Flow como antes.
- Backups: `cliente.py.bak_antes_gemini_14nov`, `gera_auto.py.bak_antes_gemini_14nov`,
  `cron_gerar_video_llm.py.bak_antes_gemini_14nov`.

## Medido (13-14/11)

| | Flow | Gemini sem navegador |
|---|---|---|
| Imagem | mediana 47 s, p75 154 s (426 imagens) | 12-24 s; 3 em paralelo em 19 s |
| Vídeo | 59-97 s quando dá certo; às vezes trava 30 min; 20 créditos | 64-105 s (tudo, com corte); 0 crédito |
| Limite | ~50 vídeos/mês por conta (créditos) | ~2-4 vídeos por conta, volta em ~2 h 30 |

## Testes

- `D:\veo\beta\teste_trio_gemini_a_seco.py` — 4 cenários da cadeia do vídeo sem gerar nada (todos OK 14/11).
- `python -X utf8 -I gemini_midia_http.py estado` — uso por conta e próximas da fila.
- Log: `D:\gemini-argo\midia.log`. No cliente: linhas `[gemini]`; no robô do Veo: `[gemini]` e `[gerar] video feito
  pelo Gemini`.
