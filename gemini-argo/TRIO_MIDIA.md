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
- **O Gemini também está DENTRO do `gera_imagem.gerar_imagem()`** (14/11): quem chama o Flow direto passa por ele —
  foto na hora do Veo (`foto_na_hora.py`, fotos-base do dono) e capas com referência do recapd
  (`capa_ia_anime._gerar_com_ref`, capa do parceiro + Maria). O `cliente.py` passa `GEMINI_JA_TENTOU=1` pro
  gera_imagem não repetir. Só entra com `quantidade=1` e sem conta fixa do Flow.
- **Foto de referência e foto inicial SEM navegador (14/11):** o arquivo sobe no content-push do Google (o mesmo do
  app) e o caminho vai em msg[3]. Até 10 referências; foto grande/webp/png vira jpg ≤ 2048 px antes de subir.
  Testado: foto na hora do dono APROVADA de 1ª (rosto 0,66; o Flow tinha dado 0,02 no mesmo cenário hoje); vídeo
  animando essa foto passou no porteiro completo (validação + "mesmo rosto" em 5 quadros, 0,59-0,62); capa de
  parceiro + Maria em 26 s. `GEMINI_VIDEO_FOTO=0` manda só os vídeos COM foto direto pro Flow.
- O vídeo do Gemini sai com 10 s e é cortado na duração pedida (`FLOW_DURATION`, 8 s). O porteiro do robô aprova
  (`validar_video`: 720x1280, 8,08 s, com áudio).
- Vídeo feito pelo Gemini imprime `GEMINI_VIDEO_OK`: o robô NÃO desconta os 20 créditos do Flow da conta.
- **Flow inteiro sem crédito**: antes o ciclo parava; agora, se o Gemini tem conta, o robô roda com a sessão virtual
  `gemini` (`VEO_SO_GEMINI=1`: o worker só tenta o Gemini e, se não entregar, sai com "sem crédito" e o prompt volta
  pra fila). A sessão `gemini` não entra no `sessoes_status.json` nem no `creditos_contas.json`.

## Várias referências (capas) — o que foi visto e ajustado (14/11)

As capas do recapd mandam até 8 referências (capa do parceiro + pose + corpo + até 3 mulheres + herói + fundo do
banco `capas_referencias`) e o prompt cita cada uma pela POSIÇÃO ("the FIRST/SECOND... reference").
- **Ordem preservada:** os uploads vão em paralelo (4 de cada vez) mas o pedido sai na ordem das refs (testado).
- **Upload reaproveitado por conta:** o caminho do content-push vale 1 dia; a conta reaproveita o que ELA subiu nas
  últimas 20 h (`uploads_midia.json`). 8 refs: 3,7 s na 1ª vez, 0 s na 2ª. Não reaproveita entre contas de
  propósito (funciona, mas não ligamos contas).
- **Referência que não existe** é pulada com aviso e o pedido segue com as outras; nenhuma existindo = erro do
  PEDIDO (não castiga a conta). Antes 1 caminho errado mandava tudo pro Flow sem deixar motivo no log.
- **Mais de 10 refs:** só as 10 primeiras, com aviso no log.
- **PNG:** convertido com PIL em memória (o ffmpeg com timeout de 60 s caiu 2x com o PC carregado e jogava fora a
  imagem já gerada).
- **Bloqueio do Argon não para a mídia:** o "bloqueada" do Argon (3 erros de TEXTO) não vale aqui. Em 14/11
  11h35-11h58 uma oscilação de rede bloqueou 10 de 12 contas no Argon e a mídia parou junto. Falha de rede agora
  castiga a conta só 3 min (antes 30 min, que esvaziava a fila).
- **Recusa:** a capa A real (biquíni + rostos reais do vídeo) foi recusada pelo Gemini em 14/11; a B (pose + Maria)
  passou. Recusa cai no Flow com as mesmas referências — não tentar driblar o filtro.
- Texto copiado das referências: com o prompt da produção (que proíbe texto) não apareceu; prompt curto sem essa
  proibição copia ("OUTSIDE / AT HOME").
- Dado do banco (não do Gemini): "Lee Hiona" e "Lee Hyona" (mesma mulher, nome escrito diferente) passaram como 2
  mulheres diferentes no `capa_longo_v2._banco_mulheres`.

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
  `cron_gerar_video_llm.py.bak_antes_gemini_14nov`, `gera_imagem.py.bak_antes_gemini_14nov`,
  `foto_na_hora.py.bak_antes_gemini_14nov` (este não foi alterado; o Gemini entra pelo gera_imagem).

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

## 16/11 — celulares entram na produção (`D:\projeto celular sub controle\celular_midia.py`)
- Imagem: Gemini HTTP -> Flow HTTP -> Flow tela -> **celular** (app Gemini; só sem referência e 9:16). `CELULAR_IMAGEM=0`.
- Vídeo: Gemini HTTP -> **celular (S20 Ultra)** -> Flow (o vídeo do Flow está quebrado). Só sem foto e 9:16; corta em 8 s.
  `CELULAR_VIDEO=0`. Ver LEIA_PRIMEIRO.md da pasta dos celulares.
