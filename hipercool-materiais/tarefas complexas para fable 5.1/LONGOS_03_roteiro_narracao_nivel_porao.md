# 03 — Roteiro e narração do longo no nível do Porão Manhwa
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Objetivo:** o roteiro/narração dos nossos longos com o jeito que faz o Porão ter 482 mil views num vídeo de 3h43.

**Onde olhar**
- Análise pronta: `D:\video-fila\linhas\LONGOS\referencias\1TXD66c_ofg\ANALISE.md` e `LINHA_DO_TEMPO.md`
  (feita por `D:\video-fila\linhas\LONGOS\engenharia_reversa.py`; mais vídeos chegam pelo campo do painel).
- Roteiro: `D:\recapd-ambientes\producao\bin\anime_script.py` (prompt), `bin\anime-pipeline.py` (`_resumo_longo`,
  `_falas_personagem`, `_marcar_falas_mascote`), config `config\longo.json` (cta, resumo, personagens).
- Voz: `bin\anime_tts.py` (clone RVC, revezamento de narradores `_inicios_blocos`), `colab\teste_narradores.json`.

**O que a análise mostrou (e nós não fazemos):** abertura em "metralhadora" (~50 cortes/238 palavras no 1º min);
CTA de tribo nos primeiros 10 s ("taverneiro de respeito"); mini-gancho a cada 15–20 min; vocabulário do público
(boladão, sigma, mitada); narrador como "amigo do discord" (quebra da 4ª parede); tom que alterna épico e deboche.

**Onde parei / limite:** listei como candidatos de A/B no `linhas\LONGOS\ESTADO.md`, sem implementar. O difícil:
reescrever o prompt do roteiro para soar humano e engraçado sem virar caricatura, e a voz clonada entregar o deboche
(eu não ouço o áudio — não consigo julgar entonação).

**Como medir:** retenção aos 30 s e 1 min (frente 01) e views 48 h, A/B pelo melhorador (frente 04).

## Fable — resultado
**29/10 (Fable) — sem dado para decidir ainda; o que dá para fazer com honestidade:**
- Os 13 longos do hipercool medidos têm no máximo 8 views (ER_03) e os longos do recapd ainda não têm medida de
  retenção lida (o lote traz `pct_media`/`dur_media` por vídeo — a tabela do modo avançado também lista os longos;
  o "aos 30 s / 1 min" só vem da curva por vídeo, frente 01). Antes de mexer no estilo do roteiro, o longo precisa
  do mesmo diagnóstico dos Shorts: ele está sendo MOSTRADO (impressões de miniatura, agora lidas em lote) e com que
  CTR? Um longo com 20 impressões não tem retenção para medir, e reescrever o prompt não muda isso.
- O que o Porão faz e é barato de testar como A/B no `config\longo.json` (um fator por vez, medido por `pct_media`
  e `dur_media` do lote): (1) **densidade da abertura** — resumo com 12–14 frases de ≤ 8 palavras em 60 s (hoje 5–8
  frases "de trailer") = a "metralhadora"; é só `rcfg min/max` + "frase curta" no prompt do `_resumo_longo`;
  (2) **mini-gancho a cada 15–20 min** — já existe a frase de expectativa (T4 dos Cortes) e o `ANIME_MASCOTE_FALAS`:
  injetar 1 frase "e o pior ainda estava por vir" no `roteiro_tempos` a cada 900 s; (3) **CTA de tribo nos 10 s**
  — 1 linha no prompt. Vocabulário ("boladão", "sigma") e deboche: não testar sem ouvir — a dona reprova voz pelo
  ouvido (CCV item 4) e um prompt "engraçado" vira caricatura sem controle; deixar para quando houver curva de
  retenção e um narrador clonado aprovado por ela.
- Regra para não repetir o erro dos Cortes: só comparar longos que RECEBERAM impressões (≥ 200 de miniatura ou
  ≥ 50 views no período).
