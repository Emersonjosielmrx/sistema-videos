# Placar dos testes dos Shorts (Cortes) — 2026-11-13 08:48

Gerado por `D:\recapd-ambientes\producao\bin\placar_variantes.py` (só lê; não muda nada). Régua do FABLE_DECISOES.md: D1 só **elegíveis** (views >= 20), D3 >= 6 elegíveis por braço no mesmo canal, D16 >= 12 por braço e P >= 0,95; nunca pela nota do júri (D6). Decidir = mudar a chave em `bin\cortes_ajustes.json` para o braço vencedor (com linha no histórico).

Shorts de parceiro no ledger: 1835 | medidos (>= 48 h): 1316 | elegíveis: 625

## legenda_impacto — sem teste agora (valor fixo 'lateral')
Valor em cortes_ajustes: `lateral` | braços: centro, lateral | referência: centro
> fechado em 'lateral' pelo melhorador em 30/10 04:44 (sem views); só vídeos de antes têm braço.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| centro | 106 | 104 | 49 | 47% | 51% | 14% | 55.8 | 35% | 1.151 |
| lateral | 88 | 86 | 36 | 42% | 64% | 22% | 52.7 | 17% | 1.515 |

P(melhor que centro): ≥500 {'lateral': 0.876} | pct≥65 {'lateral': 0.035}

Canais com ≥ 6 elegíveis em cada braço: Esporte Noturno, Filme Noturno | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['lateral'] pior que centro

## gancho_meio — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 590 | 387 | 195 | 50% | 75% | 26% | 62.2 | 31% | 1.494 |
| B | 585 | 324 | 166 | 51% | 69% | 28% | 57.9 | 31% | 1.32 |

P(melhor que A): ≥500 {'B': 0.119} | pct≥65 {'B': 0.492}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, Bicho Noturno, CenaReact, DicasFinanceirasDaIA, Esporte Noturno, Filme Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

## gancho_remotion — PRONTO PARA DECIDIR (D3+D16)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> braço 'A_falhou' = sorteado B mas o render caiu no ASS (falha de RAM/PC2): não é sorteio, compare só os braços sorteados.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 575 | 363 | 175 | 48% | 74% | 32% | 62.1 | 36% | 1.465 |
| A_falhou | 23 | 23 | 11 | 48% | 64% | 9% | 54.4 | 36% | 0.902 |
| B | 554 | 302 | 166 | 55% | 70% | 23% | 58.9 | 26% | 1.326 |
| fora | 21 | 21 | 8 | 38% | 88% | 25% | 55.6 | 25% | 3.001 |

P(melhor que A): ≥500 {'A_falhou': 0.186, 'B': 0.19, 'fora': 0.715} | pct≥65 {'A_falhou': 0.542, 'B': 0.027, 'fora': 0.312}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, Bicho Noturno, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Esporte Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['B'] pior que A

## fx_choque — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 599 | 358 | 177 | 49% | 72% | 26% | 59.5 | 30% | 1.421 |
| B | 571 | 348 | 183 | 53% | 73% | 28% | 61.0 | 33% | 1.415 |

P(melhor que A): ≥500 {'B': 0.57} | pct≥65 {'B': 0.681}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, Bicho Noturno, CenaReact, DicasFinanceirasDaIA, Esporte Noturno, Filme Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

## mascote — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> braço 'A_falhou' = sorteado B mas falhou: não é sorteio, compare só os braços sorteados.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 556 | 334 | 169 | 51% | 75% | 28% | 59.1 | 29% | 1.437 |
| A_falhou | 30 | 30 | 10 | 33% | 60% | 0% | 59.2 | 40% | 2.807 |
| B | 581 | 339 | 181 | 53% | 70% | 28% | 61.4 | 33% | 1.324 |

P(melhor que A): ≥500 {'A_falhou': 0.128, 'B': 0.153} | pct≥65 {'A_falhou': 0.795, 'B': 0.764}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, Bicho Noturno, CenaReact, DicasFinanceirasDaIA, Esporte Noturno, Filme Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

## curto — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 582 | 338 | 177 | 52% | 72% | 25% | 56.3 | 28% | 1.406 |
| B | 553 | 333 | 171 | 51% | 73% | 30% | 64.8 | 35% | 1.411 |

P(melhor que A): ≥500 {'B': 0.609} | pct≥65 {'B': 0.916}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Bicho Noturno, CenaReact, DicasFinanceirasDaIA, Esporte Noturno, Filme Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

## fala_rapida — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 552 | 325 | 172 | 53% | 70% | 29% | 60.1 | 32% | 1.287 |
| B | 569 | 332 | 168 | 51% | 74% | 26% | 60.3 | 29% | 1.391 |

P(melhor que A): ≥500 {'B': 0.762} | pct≥65 {'B': 0.253}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, Bicho Noturno, CenaReact, DicasFinanceirasDaIA, Esporte Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

## saudacao — dados suficientes, sem diferença clara ainda
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 507 | 268 | 144 | 54% | 69% | 25% | 61.1 | 30% | 1.3 |
| B | 529 | 304 | 159 | 52% | 76% | 33% | 60.8 | 32% | 1.307 |

P(melhor que A): ≥500 {'B': 0.878} | pct≥65 {'B': 0.662}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Bicho Noturno, CenaReact, Curiosidades Noturnas, DicasFinanceirasDaIA, Esporte Noturno, HistoriasEmFrames, inovaremanhwabr | ≥ 12 por braço no total: sim

## ninguem_esperava — PRONTO PARA DECIDIR (D3+D16)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 516 | 278 | 139 | 50% | 75% | 33% | 63.4 | 37% | 1.506 |
| B | 520 | 294 | 164 | 56% | 71% | 26% | 58.8 | 26% | 1.132 |

P(melhor que A): ≥500 {'B': 0.216} | pct≥65 {'B': 0.025}

Canais com ≥ 6 elegíveis em cada braço: @CodigoInteligente-n7j, Animescomia, Bicho Noturno, CenaReact, DicasFinanceirasDaIA, Esporte Noturno, HistoriasEmFrames, InventoReact, inovaremanhwabr | ≥ 12 por braço no total: sim

**Sugestão (a dona decide):** ; ['B'] pior que A

## horario_fraco — dá pra olhar (só indício: braço por canal)
Valor em cortes_ajustes: `ab` | braços: A, B | referência: A
> sorteio por CANAL (cada canal fica num braço só): não dá pra estratificar por canal; a comparação é entre canais diferentes e vale só como indício.

| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) |
|---|---|---|---|---|---|---|---|---|---|
| A | 670 | 397 | 201 | 51% | 67% | 24% | 60.1 | 28% | 0.841 |
| B | 536 | 323 | 189 | 58% | 68% | 24% | 68.2 | 31% | 1.333 |

P(melhor que A): ≥500 {'B': 0.589} | pct≥65 {'B': 0.721}

Canais com ≥ 6 elegíveis em cada braço: nenhum | ≥ 12 por braço no total: sim
