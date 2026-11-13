# 11 — Fonte de vídeo (yt-dlp, legenda, proxies)
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Fatos de 28/10:** yt-dlp avisa "No supported JavaScript runtime… some formats may be missing" (falta deno/node para o
YouTube); a legenda automática pelo proxy Webshare caiu em "Sign in to confirm you're not a bot" e depois 429; o IP de
casa entra em pausa (memória "yt-dlp sem rajada"); o arsenal de falas de séries (`hipercool-materiais\bin\arsenal_memes.py`)
anda devagar pela pausa.

**Onde olhar:** `D:\recapd-ambientes\producao\bin\ytdlp_vez.py` (vez/pausa/proxy), `anime_fetch.py`
(`download_video` — agora `-S res,vcodec:h264`, `fetch_captions`), `estoque_fontes.py`, `hipercool-materiais\bin\
fontes_drive.py`, `cookies.txt` (não mexer em cookie sem a dona).

**O que falta:** runtime JS para o yt-dlp; legenda sem depender do proxy marcado (Whisper com tempo já é o reserva na
engenharia reversa); estoque de fontes com folga para nunca faltar vídeo.

## Fable — resultado
**29/10 (Fable) — runtime JS: conferido, NÃO aplicado (regra da dona "yt-dlp: não mexer em opção/cookie").**
- Fato: o PC1 tem **Node v24.15.0** em `C:\Program Files\nodejs\node.exe`; não tem deno. yt-dlp **2026.10.26** (venv
  do recapd e Python do sistema; o do Veo é 2026.08.19) só habilita o deno por padrão e aceita
  `--js-runtimes node:"C:\Program Files\nodejs\node.exe"`. É isso que tira o aviso "No supported JavaScript runtime…
  some formats may be missing" — e os formatos que faltam são justamente os bons (o `-S res,vcodec:h264` cai em
  resolução menor sem o runtime).
- Como aplicar sem tocar em NENHUM script (1 arquivo, vale para todos os projetos e para o `ytdlp_vez`, que só
  controla a vez): criar `C:\Users\Haylla\AppData\Roaming\yt-dlp\config` com a linha
  `--js-runtimes node:"C:\Program Files\nodejs\node.exe"`. yt-dlp lê esse arquivo em toda chamada. Para desfazer:
  apagar o arquivo. Decisão da dona (é "opção do yt-dlp"); eu não criei. Atualizar o yt-dlp do `D:\veo\venv`
  (2026.08) para a mesma versão evita comportamento diferente entre projetos.
- Legenda pelo proxy caindo em "not a bot"/429: não depende de código nosso — o IP de datacenter da Webshare é
  marcado. O reserva certo já existe (Whisper com tempo); sugestão: para parceiro, usar primeiro o `legenda_tempos`
  do Whisper e só pedir legenda ao YouTube para o longo (1 chamada por obra, pelo IP de casa dentro da vez).
- Estoque com folga: o `estoque_fontes.py` + `fontes_drive.py` (Drive) já guardam; o gargalo é a pausa do IP.
  Métrica para acompanhar: `ytdlp_vez` pausas/dia (log) × Shorts que ficaram sem fonte no dia (anime_metrics FALHA
  "Baixar").
