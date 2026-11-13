# 04 — Melhorador A/B que funcione com poucos vídeos
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Objetivo:** o melhorador automático (substitui o chat) escolhe e testa mudanças e só aplica o que ganhou de verdade.

**Onde olhar**
- Longo: `D:\recapd-ambientes\producao\colab\melhorador_longo.py` + `melhorador_longo.json` (alavancas, experimento:
  videos_por_lado, nota_min, views_fator), prompt `D:\video-fila\linhas\LONGOS\PROMPT_MELHORADOR.md`. A/B: `cliente.py
  _variante_do_experimento` → `ANIME_LONGO_OVERRIDE` → `anime-pipeline._cfg_longo`. Está DESLIGADO (controle.json) até
  a dona dar o sinal.
- Cortes: `D:\recapd-ambientes\producao\bin\cortes_melhorador.py` (modo SOMBRA), `linhas\CORTES\SOMBRA.md`, `LICOES.md`.
- Motor antigo parado: `melhoria_continua.py` (memória "Melhorias contínuas").

**Problema:** saem poucos longos por dia, cada um com obra/canal/horário diferentes; views têm variância enorme. Com
3 vídeos por lado o "vencedor" é sorte. Faltam: controle por canal/obra/horário, prior bayesiano, parar cedo, e usar
sinais mais rápidos que views (retenção aos 30 s, CTR — frentes 01/02).

**Onde parei / limite:** montei o fluxo (abre experimento, alterna A/B, julga por nota + views) mas não validei a
estatística; não sei o tamanho de efeito real das alavancas.

**Como medir:** simular com o histórico (`colab\longos_postados.json`, painel) quantos vídeos cada teste precisa.

## Fable — resultado
**29/10 (Fable).** O desenho estatístico está em `CORTES_01` (seção "Fable — resultado", item 2) e vale igual para o
longo, com uma diferença: saem poucos longos, então a métrica tem de ser a mais rápida e menos ruidosa —
**`pct_media`/`dur_media` do lote do Studio** (chega em 48 h, desvio ~18 pts) em vez de views (desvio do log ≈ 1,2;
com 3 por lado é sorte, como você viu). Regras: excluir vídeo sem impressões (não mostrado = não mede nada);
normalizar por canal (mediana do canal nas 4 semanas); prior Beta(2,2) por alavanca; parar cedo só com P(B>A) ≥ 0,95
e n ≥ 8 elegíveis por lado; uma alavanca por vez no longo (sem fatorial: não há volume). Com 2 longos/dia elegíveis
isso dá ~8 dias por alavanca — é o custo real; o que não cabe nisso não é testável, é gosto da dona.
