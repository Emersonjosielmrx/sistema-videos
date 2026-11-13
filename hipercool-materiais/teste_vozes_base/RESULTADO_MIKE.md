# Teste de bases - Mike (20/10/2026)

> **Correção (20/10, 10:40):** as bases deste teste NÃO eram as do nome. O `edge_tts_engine` (COMUM), sem a variável
> `VOZ_CLONADA`, troca as vozes "proibidas": Francisca → Thalita e Antonio → **Andrew Multilingual**. Então:
> "francisca" = Thalita, "thalita" = Thalita (por isso saíram iguais) e "antonio" = Andrew (confirmado comparando o
> som com o Andrew e o Antonio reais em `bases_reais\`). Detalhes e medições: `VARIACOES_POR_MOMENTO.md`.

## O que o dono ouviu
- Versões "francisca" e "thalita": iguais (eram a mesma voz, Thalita).
- Versão "antonio" (na verdade Andrew): mesma voz do mike, mais grossa, "como se ele imitasse um personagem
  maligno" — ideal pra partes sombrias.

## Por que (medido com RMVPE)
- O tom do clone é calibrado na Francisca real (234 Hz). A Thalita fala em 181 Hz e o Andrew em 110 Hz.
- Resultado: versão "francisca" ~5 semitons abaixo da voz natural do mike (90 Hz × 121 Hz natural); versão
  "antonio" ~13 semitons abaixo (59 Hz), mais lenta (11%) e com entonação mais reta = voz de vilão.
