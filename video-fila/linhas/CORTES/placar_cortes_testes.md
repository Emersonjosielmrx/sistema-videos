# Placar dos testes dos Shorts (Cortes) — 2026-11-17 20:44

Gerado por `D:\recapd-ambientes\producao\bin\placar_variantes.py` (só lê; não muda nada). Régua do FABLE_DECISOES.md: D1 só **elegíveis** (views >= 20), D3 >= 6 elegíveis por braço no mesmo canal, D16 >= 12 por braço e P >= 0,95; nunca pela nota do júri (D6). Decidir = mudar a chave em `bin\cortes_ajustes.json` para o braço vencedor (com linha no histórico).

Shorts de parceiro no ledger: 2326 | medidos (>= 48 h): 1765 | elegíveis: 968

## legenda_impacto — sem teste agora (valor fixo 'lateral')
Valor em cortes_ajustes: `lateral` | braços: centro, lateral | referência: centro
> fechado em 'lateral' pelo melhorador em 30/10 04:44 (sem views); só vídeos de antes têm braço.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| centro | 106 | 104 | 50 | 48% | 50% | 14% | 56.5 | 36% | 0.82 | 33/104 | 36% | -0.432 |
| lateral | 88 | 86 | 37 | 43% | 62% | 22% | 52.1 | 16% | 1.262 | 19/86 | 34% | -0.363 |

P(melhor que centro) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'lateral': 0.343} — decide por: ajustado+pct65

P(melhor que centro): ≥500 {'lateral': 0.862} | pct≥65 {'lateral': 0.023}

Canais com ≥ 6 elegíveis em cada braço: AssistIA Investimentos, Bicho Noturno, Dorama Noturno, Esporte Noturno, Filme Noturno, Game Noturno | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['lateral'] pior que centro

## gancho_meio — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 841 | 574 | 346 | 60% | 69% | 23% | 61.1 | 34% | 1.239 | 111/574 | 49% | 0.007 |
| B | 807 | 552 | 322 | 58% | 69% | 27% | 62.3 | 35% | 1.267 | 98/552 | 51% | 0.044 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.782} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.455} | pct≥65 {'B': 0.637}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, YouTube inovaremanhwaverseind, inovaremanhwabr | ≥ 12 por braço no total: sim

## gancho_remotion — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> braço 'A_falhou' = sorteado B mas o render caiu no ASS (falha de RAM/PC2): não é sorteio, compare só os braços sorteados.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 810 | 552 | 316 | 57% | 69% | 28% | 61.9 | 37% | 1.28 | 103/552 | 50% | 0.0 |
| A_falhou | 23 | 23 | 11 | 48% | 64% | 9% | 54.4 | 36% | 0.511 | 8/23 | 22% | -0.69 |
| B | 792 | 528 | 332 | 63% | 69% | 23% | 61.9 | 33% | 1.222 | 94/528 | 53% | 0.086 |
| fora | 21 | 21 | 8 | 38% | 88% | 25% | 55.6 | 25% | 2.643 | 3/21 | 48% | 0.055 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'A_falhou': 0.004, 'B': 0.85, 'fora': 0.435} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'A_falhou': 0.318, 'B': 0.561, 'fora': 0.822} | pct≥65 {'A_falhou': 0.532, 'B': 0.173, 'fora': 0.301}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, YouTube inovaremanhwaverseind, inovaremanhwabr | ≥ 12 por braço no total: sim

## fx_choque — PRONTO PARA DECIDIR (D3+D16)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 858 | 570 | 329 | 58% | 68% | 25% | 60.7 | 34% | 1.166 | 104/570 | 48% | -0.042 |
| B | 785 | 551 | 338 | 61% | 70% | 26% | 62.6 | 35% | 1.341 | 104/551 | 53% | 0.098 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.954} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.77} | pct≥65 {'B': 0.659}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, YouTube inovaremanhwaverseind, inovaremanhwabr | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ['B'] melhor que A

## mascote — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> braço 'A_falhou' = sorteado B mas falhou: não é sorteio, compare só os braços sorteados.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 803 | 532 | 315 | 59% | 70% | 25% | 60.3 | 33% | 1.16 | 90/532 | 50% | 0.036 |
| A_falhou | 30 | 30 | 11 | 37% | 55% | 0% | 62.3 | 46% | 1.844 | 9/30 | 37% | -0.326 |
| B | 807 | 556 | 341 | 61% | 69% | 26% | 63.0 | 36% | 1.324 | 109/556 | 52% | 0.038 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'A_falhou': 0.085, 'B': 0.761} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'A_falhou': 0.134, 'B': 0.463} | pct≥65 {'A_falhou': 0.833, 'B': 0.837}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## curto — PRONTO PARA DECIDIR (D3+D16)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 829 | 555 | 333 | 60% | 68% | 24% | 57.7 | 32% | 1.159 | 98/555 | 52% | 0.051 |
| B | 779 | 531 | 322 | 61% | 70% | 26% | 66.1 | 38% | 1.352 | 103/531 | 51% | 0.048 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.365} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.767} | pct≥65 {'B': 0.952}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, YouTube inovaremanhwaverseind, inovaremanhwabr | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ['B'] melhor que A

## fala_rapida — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 777 | 532 | 323 | 61% | 67% | 25% | 60.8 | 34% | 1.193 | 94/532 | 52% | 0.036 |
| B | 817 | 540 | 324 | 60% | 71% | 26% | 62.6 | 34% | 1.27 | 102/540 | 50% | 0.047 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.349} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.901} | pct≥65 {'B': 0.492}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, YouTube inovaremanhwaverseind, inovaremanhwabr | ≥ 12 por braço no total: sim

## saudacao — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 747 | 482 | 299 | 62% | 68% | 24% | 62.2 | 36% | 1.227 | 83/482 | 50% | 0.056 |
| B | 762 | 505 | 310 | 61% | 70% | 28% | 62.0 | 33% | 1.238 | 93/505 | 54% | 0.071 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.826} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.681} | pct≥65 {'B': 0.207}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## ninguem_esperava — PRONTO PARA DECIDIR (D3+D16)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 746 | 493 | 307 | 62% | 71% | 28% | 64.7 | 39% | 1.353 | 89/493 | 53% | 0.108 |
| B | 763 | 494 | 302 | 61% | 68% | 24% | 59.5 | 31% | 1.11 | 87/494 | 51% | 0.019 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.272} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.203} | pct≥65 {'B': 0.016}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['B'] pior que A

## abertura — esperando dados
Valor em cortes_ajustes: `abcd` | braços: fato, pergunta, contraste, custo | referência: fato

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| contraste | 15 | 0 | 0 | 0% | — | — | — | — | — | 0/0 | — | — |
| custo | 19 | 0 | 0 | 0% | — | — | — | — | — | 0/0 | — | — |
| fato | 17 | 0 | 0 | 0% | — | — | — | — | — | 0/0 | — | — |
| pergunta | 14 | 1 | 1 | 100% | 0% | 0% | 57.1 | 0% | 0.0 | 0/1 | 0% | 0.0 |

Canais com ≥ 6 elegíveis em cada braço: nenhum | ≥ 12 por braço no total: não

## horario_fraco — dá pra olhar (só indício: braço por canal)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> sorteio por CANAL (cada canal fica num braço só): não dá pra estratificar por canal; a comparação é entre canais diferentes e vale só como indício.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 918 | 635 | 384 | 60% | 66% | 22% | 61.7 | 33% | 1.151 | 125/635 | 48% | 0.025 |
| B | 779 | 517 | 338 | 65% | 68% | 24% | 65.8 | 33% | 0.936 | 77/517 | 53% | -0.049 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.955} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.783} | pct≥65 {'B': 0.465}

Canais com ≥ 6 elegíveis em cada braço: nenhum | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ['B'] melhor que A
