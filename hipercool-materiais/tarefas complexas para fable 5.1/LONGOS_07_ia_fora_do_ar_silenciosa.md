# 07 — IA fora do ar sem ninguém ver (qualidade cai em silêncio)
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Fato (28/10 ~22h):** `antigravity/gemini-3.8-flash-tiered` no OmniRoute não respondeu nem "ok" em 120–150 s (2
testes); `gemini-fila` respondeu em 2 s; `antigravity/gemini-3-flash` em 1 s. O longo usa o "tiered" no resumo de
abertura e nas falas de personagem (`anime-pipeline.py`, `GEMINI_TEXTO_VIDEO`) e, quando falha, **segue sem** — o vídeo
sai pior e nada avisa. Memória: "Argon sem cota vira Flash-Lite calado".

**Onde olhar:** `D:\recapd-ambientes\producao\bin\claude_client.py` (`generate_text`, `_texto_video`, reserva
`TEXTO_VIDEO_RESERVA`), OmniRoute na VPS 157 (memórias "OmniRoute na 157", "Filas do OmniRoute"), `avisos.py`.

**O que falta:** saúde por modelo (latência/erro) com troca automática para o que está vivo, registro de "este vídeo
saiu sem X porque a IA Y falhou" no `render.json`/painel, e não postar vídeo que perdeu partes importantes.

**Como medir:** % de longos com resumo/personagens/capítulos realmente presentes.

## Fable — resultado
**29/10 03:55 — feito (detalhe e "não fazer" em `FABLE_DECISOES.md` D7).**
- Causa do silêncio: `claude_client._post` repete 3× o timeout (240 s) = até 12 min preso num modelo travado, e o
  pipeline trata "vazio" como "segue sem" sem registrar. Medido agora: tiered 2,5 s, gemini-fila 5,3 s, 3-flash 4,6 s,
  agy 29,7 s; Argon pela :20128 > 60 s (o vídeo usa a :20133 com teto de 120 s, já tratado no `_texto_video`).
- Novo: `claude_client.generate_text_vivo` (cadeia, 1 tentativa por modelo, saúde em `workspace/ia_saude.json`,
  pula 15 min quem falhou) + `registrar_faltou` (`faltou.json` na pasta do vídeo + Telegram importante). Ligado no
  resumo de abertura e nas falas de personagem do `anime-pipeline.py`. Testado ao vivo: modelo inexistente → 0,8 s →
  próximo da cadeia responde.
- Fica para quem cuida do painel: ler `faltou.json` das pastas do longo e mostrar "saiu sem resumo/falas" no :8790 e
  no `render.json` do vídeo (não achei `render.json` no pipeline; o `faltou.json` é o registro).
- Capítulos (`capitulos.json`) e mascote ainda "seguem sem" calados: mesmo padrão, chamar `registrar_faltou` nos
  `except` das linhas ~373/375 (mascote) e onde os capítulos são gerados — não mexi porque não medi esses modelos.
