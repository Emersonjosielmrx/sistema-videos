# Legenda com vírgula fantasma no início — CAUSA RAIZ e fix

**Data:** 2026-07-30
**Arquivo afetado:** `bin/fx_subtitles.py` → `burn_subtitles_ass()`
**Sintoma:** legendas do recap de anime apareciam com vírgula ANTES da primeira palavra
(`,Kensuke`, `,A mulher`, `,Ele`), em TODOS os cards, independente do texto.

---

## Causa raiz (o bug REAL)

A seção `[Events]` do `.ass` gerado tinha a linha `Format:` com **9 campos**, faltando o
`MarginV`:

```
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
```

Mas cada linha `Dialogue:` escrevia **10 valores**:

```
Dialogue: 0,0:00:00.20,0:00:01.80,Cap,,0,0,0,,A mulher
                                          ^ ^ ^ ^ ^
                        Layer Start End Style Name MarginL MarginR MarginV Effect Text
```

Com o `Format` declarando só 9 colunas, o libass desalinha o parse e o valor que deveria ser
`MarginV` (o `0` antes do `,,`) é lido no lugar errado — o resultado é que **o libass injeta
uma vírgula literal no INÍCIO do campo Text na renderização**.

Consequências que confundiram o diagnóstico por dias:
- A vírgula aparecia antes de **qualquer** primeira palavra (até com texto `HHH`).
- Os **bytes do campo Text no `.ass` estavam limpos** (a vírgula nasce no parse do libass).
- `_strip_lead_punct()` (limpeza de pontuação líder) **nunca resolveu** — porque a vírgula
  não estava na string, era criada na renderização.

## Fix

Adicionar `MarginV` na linha `Format` (passa a ter 10 campos, casando com o `Dialogue`):

```
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
```

Aplicado em:
- `D:\recapd-ambientes\producao\bin\fx_subtitles.py`
- PC2 `C:\recapd-e-animes\bin\fx_subtitles.py` (backup `.bak_fmt_*`)

---

## Bug 2 (achado de quebra na mesma investigação): legenda pequena/deslocada

`burn_subtitles_ass` escrevia `PlayResX: {W}` / `PlayResY: {H}` usando os globais de
`fx_assets` (W=720, H=1280 — RETRATO dos shorts). O recap deitado é **1280x720**. Com o
PlayRes invertido, o libass escala e posiciona o texto errado (glifo caía de ~46px para 25px,
deslocado do rodapé).

**Fix:** detectar a resolução real por `ffprobe` e usar `PlayResX/Y` reais + fonte e `MarginV`
proporcionais a `vh/720`.

**Regra geral:** todo `.ass` gerado por código deve usar `PlayRes = resolução real do vídeo
alvo`, nunca uma constante global.

---

## Como validar bug visual de texto (sem depender de olho humano nem OCR de IA)

Aprendizado caro: tanto leitura humana de PNG pequeno quanto o **OCR do Gemini alucinaram**
(Gemini via vírgula até em render onde o pixel provava que não havia). Métodos confiáveis:

1. **ASCII art dos pixels** — dump da região como caracteres (`#` > 180, `.` > 60, espaço):
   é legível com 100% de certeza. Testar com texto `HHH` (impossível ter vírgula real):
   se aparecer marca isolada ~6x13px com rabo descendente em y≈640-653 ANTES da 1ª letra,
   é o artefato.
2. **Componentes conectados (blobs):** um blob fixo (mesmo tamanho independente de letra e
   fonte) isolado antes da 1ª letra = elemento injetado, não parte do glifo.
3. **YMAX, não YHIGH:** `signalstats.YHIGH` é percentil e ignora texto pequeno (dá ~54,
   parece "vídeo em branco"). Use `YMAX` (fundo escuro ≈ baixo; texto branco ≈ 250).
4. **`burn_subtitles_ass` retorna `ok=True` sem checar conteúdo** (só `exists + size>0`) e
   APAGA o `.ass` no `finally`. Pra depurar, faça monkeypatch de `pathlib.Path.unlink` para
   preservar o `.ass` e inspecione o texto cru.
5. **Parser `.ass`:** o campo Text é o índice 9 em `linha.split(",", 9)`. Split ingênuo pega
   o campo `Name` (vazio) e valida lixo.

## Prova

`burn_subtitles_ass` alimentado com vírgula líder proposital (`,Quem`, `，Ele`, `‚Essa`,
`,A mulher se chama`) → renderiza limpo e no tamanho certo. Arquivo de prova:
`PROVA_FORMAT_FIX_sem_virgula.mp4`.
