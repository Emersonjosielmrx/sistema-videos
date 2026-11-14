# Placar dos testes dos Shorts (Cortes) — 2026-11-13 14:31

Gerado por `D:\recapd-ambientes\producao\bin\placar_variantes.py` (só lê; não muda nada). Régua do FABLE_DECISOES.md: D1 só **elegíveis** (views >= 20), D3 >= 6 elegíveis por braço no mesmo canal, D16 >= 12 por braço e P >= 0,95; nunca pela nota do júri (D6). Decidir = mudar a chave em `bin\cortes_ajustes.json` para o braço vencedor (com linha no histórico).

Shorts de parceiro no ledger: 1860 | medidos (>= 48 h): 1350 | elegíveis: 648

## legenda_impacto — sem teste agora (valor fixo 'lateral')
Valor em cortes_ajustes: `lateral` | braços: centro, lateral | referência: centro
> fechado em 'lateral' pelo melhorador em 30/10 04:44 (sem views); só vídeos de antes têm braço.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| centro | 106 | 104 | 49 | 47% | 51% | 14% | 55.8 | 35% | 1.065 | 33/104 | 40% | -0.422 |
| lateral | 88 | 86 | 36 | 42% | 64% | 22% | 52.7 | 17% | 1.451 | 19/86 | 38% | -0.376 |

P(melhor que centro) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'lateral': 0.388} — decide por: ajustado+pct65

P(melhor que centro): ≥500 {'lateral': 0.876} | pct≥65 {'lateral': 0.035}

Canais com ≥ 6 elegíveis em cada braço: AssistIA Investimentos, Bicho Noturno, Dorama Noturno, Esporte Noturno, Filme Noturno, Game Noturno | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['lateral'] pior que centro

## gancho_meio — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 604 | 402 | 205 | 51% | 76% | 25% | 62.3 | 32% | 1.389 | 87/402 | 48% | -0.012 |
| B | 596 | 342 | 178 | 52% | 68% | 26% | 59.2 | 33% | 1.207 | 61/342 | 51% | 0.02 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.757} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.063} | pct≥65 {'B': 0.559}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## gancho_remotion — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> braço 'A_falhou' = sorteado B mas o render caiu no ASS (falha de RAM/PC2): não é sorteio, compare só os braços sorteados.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 590 | 377 | 185 | 49% | 74% | 31% | 61.9 | 35% | 1.375 | 73/377 | 49% | -0.023 |
| A_falhou | 23 | 23 | 11 | 48% | 64% | 9% | 54.4 | 36% | 0.804 | 8/23 | 39% | -0.685 |
| B | 564 | 321 | 178 | 56% | 71% | 21% | 60.5 | 29% | 1.199 | 63/321 | 52% | 0.089 |
| fora | 21 | 21 | 8 | 38% | 88% | 25% | 55.6 | 25% | 2.873 | 3/21 | 43% | -0.005 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'A_falhou': 0.196, 'B': 0.779, 'fora': 0.304} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'A_falhou': 0.203, 'B': 0.287, 'fora': 0.732} | pct≥65 {'A_falhou': 0.567, 'B': 0.105, 'fora': 0.329}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## fx_choque — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 612 | 372 | 187 | 50% | 73% | 26% | 59.7 | 31% | 1.292 | 77/372 | 49% | -0.038 |
| B | 583 | 367 | 195 | 53% | 71% | 26% | 62.0 | 33% | 1.324 | 70/367 | 50% | 0.047 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.682} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.337} | pct≥65 {'B': 0.646}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## mascote — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> braço 'A_falhou' = sorteado B mas falhou: não é sorteio, compare só os braços sorteados.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 572 | 347 | 178 | 51% | 75% | 26% | 59.4 | 31% | 1.314 | 65/347 | 50% | 0.02 |
| A_falhou | 30 | 30 | 10 | 33% | 60% | 0% | 59.2 | 40% | 2.556 | 9/30 | 50% | -0.278 |
| B | 590 | 359 | 194 | 54% | 70% | 27% | 62.4 | 33% | 1.238 | 73/359 | 49% | 0.011 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'A_falhou': 0.521, 'B': 0.47} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'A_falhou': 0.125, 'B': 0.139} | pct≥65 {'A_falhou': 0.766, 'B': 0.707}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## curto — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 593 | 361 | 190 | 53% | 72% | 24% | 57.5 | 29% | 1.275 | 65/361 | 52% | 0.05 |
| B | 567 | 343 | 180 | 52% | 73% | 29% | 65.0 | 35% | 1.319 | 75/343 | 48% | 0.02 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.168} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.649} | pct≥65 {'B': 0.893}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## fala_rapida — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 564 | 342 | 183 | 54% | 70% | 28% | 60.3 | 33% | 1.172 | 65/342 | 49% | 0.036 |
| B | 582 | 348 | 179 | 51% | 74% | 25% | 61.5 | 30% | 1.306 | 70/348 | 49% | -0.002 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.501} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.755} | pct≥65 {'B': 0.26}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, Manhwa Noturno, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## saudacao — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 520 | 284 | 154 | 54% | 70% | 24% | 62.0 | 32% | 1.207 | 50/284 | 52% | 0.122 |
| B | 541 | 321 | 171 | 53% | 75% | 31% | 61.4 | 32% | 1.208 | 65/321 | 50% | 0.002 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.288} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.882} | pct≥65 {'B': 0.517}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

## ninguem_esperava — PRONTO PARA DECIDIR (D3+D16)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 526 | 292 | 148 | 51% | 75% | 32% | 64.2 | 39% | 1.428 | 59/292 | 51% | 0.113 |
| B | 535 | 313 | 177 | 56% | 71% | 24% | 59.5 | 27% | 1.024 | 56/313 | 50% | 0.008 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.408} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.193} | pct≥65 {'B': 0.01}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, AssistIA Investimentos, Bicho Noturno, CartuchoReact, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Dorama Noturno, Esporte Noturno, Filme Noturno, ForjaReact, Game Noturno, HistoriasEmFrames, Inovare, InventoReact, ManhwaReact-ia, inovaremanhwabr | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['B'] pior que A

## abertura — esperando dados
Valor em cortes_ajustes: `abcd` | braços: fato, pergunta, contraste, custo | referência: fato

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

Canais com ≥ 6 elegíveis em cada braço: nenhum | ≥ 12 por braço no total: não

## horario_fraco — dá pra olhar (só indício: braço por canal)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> sorteio por CANAL (cada canal fica num braço só): não dá pra estratificar por canal; a comparação é entre canais diferentes e vale só como indício.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | à noite | acima do grupo | log(rz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 684 | 413 | 211 | 51% | 68% | 23% | 60.8 | 30% | 0.78 | 88/413 | 45% | -0.027 |
| B | 547 | 339 | 201 | 59% | 68% | 24% | 68.2 | 31% | 1.244 | 54/339 | 53% | -0.043 |

P(melhor que A) AJUSTADO pelo horário (acima da mediana do mesmo canal e período): {'B': 0.979} — decide por: ajustado+pct65

P(melhor que A): ≥500 {'B': 0.535} | pct≥65 {'B': 0.531}

Canais com ≥ 6 elegíveis em cada braço: nenhum | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ['B'] melhor que A
