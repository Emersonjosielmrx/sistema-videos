# 🟢 LEIA PRIMEIRO — Projeto RECAP DE ANIME (recapd-e-animes)

> **Se você é um agente novo (inclusive modelo grátis/fraco): leia SÓ este doc.**
> Ignore o `LEIA_PRIMEIRO.md` (sem sufixo) — aquele é do projeto manhwa (hipercool), não tem a ver com anime.
> Última atualização: **2026-07-12**.

## O que este projeto faz (em 1 frase)
Pega um vídeo de **recap de anime** já postado no YouTube (que conta a HISTÓRIA de um anime),
**re-narra em PT-BR com voz própria** e **descaracteriza o visual** (espelha/corta/satura) pra
ficar diferente do original. Agora, há 2 fluxos de produtos independentes: **Deitado (16:9)** e **Short (9:16)**.

## ⛔ REGRAS CURTAS (se conflitar com qualquer outro doc, ESTAS mandam)
1. **Python é SEMPRE:** `D:\recapd-e-animes\venv\Scripts\python.exe` (venv próprio deste projeto).
2. **SEMPRE exportar `PYTHONUTF8=1`** antes de rodar (senão quebra em acento/caractere japonês).
3. **Edite só os `bin/anime_*.py`** (e `bin/anime-pipeline.py`). NÃO mexa em `bin/_SNAPSHOT_*`.
4. **NÃO apague caches** (`workspace/anime/*/audio_cache`, `narration_cache`). É o que evita gastar quota.
5. **Rode o ffmpeg/pipeline em BACKGROUND** (é pesado). Nunca com `&` no fim — use a flag de background.
6. **Nunca diga "pronto" sem PROVAR** com ffprobe (duração vídeo≈áudio) + abrir/extrair um frame.
7. **Postar / commit / apagar = só com confirmação da dona.**
7b. **MICROCORTES OBRIGATÓRIOS no SHORT (dona, 22/10):** no vertical cada fala vai numa CÓPIA com
   `narracao_curva.microcortes` (`anime_segments._fala_do_short`): pausa > 0,07 s vira 0,07 s, a fala NÃO acelera, o
   `words.json` acompanha; `CLIP_GAP_S` do vertical = 0. 23/10: a dona ouviu o teste no deitado (longo) e aprovou —
   os microcortes valem nas DUAS orientações (o deitado mantém o respiro entre falas dele). Não reintroduza respiro
   fixo entre as falas do Short.
7c. **TESTE GRADUAL de formatos e vozes (dona, 23/10):** `bin/anime_testes.py` + `config/testes_voz.json` (`ligado`,
   `fracao` 0,15). Uma parte dos Shorts de parceiro com clone vira teste: formato com várias vozes (`formatos_voz.json`,
   só uso producao/padrao_faustao) ou voz nova sozinha (personagem aprovado com encaixe 1; pessoa real fica fora). O
   `anime_auto.fazer_short` sorteia logo depois do narrador; o Short pronto é TRANSCRITO e comparado com o roteiro
   (`conferir`): formato que soou mal é refeito no solo, voz em teste que soou mal fica segurada. O postar.json leva
   `teste_voz` ("solo" = controle), `elenco` e `sintetico` (pessoa real = marca de conteúdo alterado no upload). O
   placar de 48 h (`placar_testes_voz.json`) decide quem sai mais (promovido) ou para (pausado). Vigia:
   `D:\video-fila\avaliar_testes_voz.py` (subvigia, 3 h) -> `D:\video-fila\TESTES_VOZ_RELATORIO.md`. Ensaio de um item:
   `TESTE_VOZ_FORCAR=formato:chaves_quico`. Não use a chave "formato" no postar.json (já quer dizer deitado/short).
8. **SHORT (9:16) = fonte JÁ VERTICAL/short.** O modo `--modo short` DEVE usar vídeos-fonte que já são shorts/verticais nativos do YouTube. Se o vídeo baixado NÃO for vertical (`anime_probe.is_vertical` = False), **DESCARTAR e buscar outro candidato** — NÃO cair no `reframe` (moldura de fundo borrado + imagem no meio). O `reframe` é feio/errado como produto principal e é último recurso (ou nem usar). Regra reforçada pela dona em 2026-07-12.

## 🧩 Os arquivos (cada um faz UMA coisa — de propósito, pra facilitar edição)
| Arquivo | O que faz |
|---|---|
| `bin/anime_auto.py` | **Ponto de entrada autônomo.** Separado em fluxos `--modo deitado` e `--modo short`. |
| `bin/anime_discover.py` | Acha recaps no YouTube. O `discover()` busca recaps longos, o `discover_shorts()` busca vídeos verticais ou curtos. |
| `bin/anime_fetch.py` | Baixa o mp4 + transcrição (legenda YT; senão Whisper, capado em ~25min pra não estourar RAM). |
| `bin/anime_probe.py` | Mede media properties através do FFmpeg. Valida se mp4 é vertical ou não. |
| `bin/anime_script.py` | Reescreve a transcrição crua em roteiro PT-BR próprio (via IA do gateway). |
| `bin/anime_tts.py` | Narração TTS (voz Thalita Multilingual, edge-tts keyless) com cache. Só Antonio é proibida (Francisca/Isabella liberadas 16/10). edge-tts >= 7.3.1 (o 7.2.8 leva 403). |
| `bin/anime_publish.py` | postar.json (SEO de `bin/seo_generator.py`, sem o nome da obra) + capa IA (`bin/capa_ia_anime.py`). |
| `bin/anime_compose.py` | Layout criativo pros casos verticais (apenas `--short-source-kind reframe` os ativa agora). |
| `bin/anime-pipeline.py` | Orquestrador do render. Roda 1 subprocesso por formato (deitado/short). |

## ▶️ COMO RODAR

**A) Autônomo:**
O script tenta achar novos vídeos e rodar todo o fluxo.
Você pode rodar modo `deitado`, `short` (fluxos super independentes) ou os dois num run (`ambos`).
```bash
cd /d/recapd-e-animes
PYTHONUTF8=1 D:/recapd-e-animes/venv/Scripts/python.exe bin/anime_auto.py --modo deitado --top 3 --target-lines 40
PYTHONUTF8=1 D:/recapd-e-animes/venv/Scripts/python.exe bin/anime_auto.py --modo short --target-lines 12
```

**B) Render direto (já tenho o mp4-fonte e o roteiro.txt):**
```bash
cd /d/recapd-e-animes
PYTHONUTF8=1 D:/recapd-e-animes/venv/Scripts/python.exe bin/anime-pipeline.py \
  --video-source "<caminho/source.mp4>" --script "<caminho/roteiro.txt>" \
  --titulo "Nome do Anime" --formato short --short-source-kind native
```

## ✅ VALIDAR ANTES DE FALAR "PRONTO"
```bash
ffprobe -v error -select_streams v -show_entries stream=width,height,duration -of csv=p=0 arquivo.mp4
ffprobe -v error -select_streams a -show_entries stream=duration -of csv=p=0 arquivo.mp4
```
Regra: se **áudio for >2s menor que vídeo**, tá QUEBRADO. Deitado deve ser 1280x720; short 720x1280.
Verifique se a resolução confere!

## 🌍 ORIENTAÇÃO POR PROCESSO (gotcha importante)
`fx_assets.py` decide W/H no IMPORT lendo a env **ANIME_ORIENT** (`landscape`=1280x720 / `vertical`=720x1280).
Por isso **cada formato roda num subprocesso próprio**.

## 🚀 SHORT: Nativo vs Reframe
Se a dona escolheu o roteiro de curtas (Short 9:16), o source visual baixado pelo `anime_auto.py` é analisado:
- Se for vertical nativo `h > w`, recebe um zoom para preencher 720x1280 exato (`short-source-kind native`).
- Se for 16:9 normal (`h < w`), recebe uma moldura de *fundo-borrado e imagem ao meio* para forçar os 720x1280 mantendo aspecto da imagem (`short-source-kind reframe`).
