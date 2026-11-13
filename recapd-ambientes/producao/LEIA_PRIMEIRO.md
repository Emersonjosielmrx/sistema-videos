# 🟢 LEIA PRIMEIRO — comece por aqui (Hipercool)

> Documento único de entrada. Se você é um agente novo, **leia só este + os "docs ativos" abaixo**.
> Última atualização: **2026-07-03**.

## ⛔ REGRAS (curtas — se conflitar com qualquer outro doc, ESTAS mandam)
1. **Trabalhe só em `D:\hipercool-inferior-fix`.** Ignore `-inferior`, `-BOM`, `-dev`, `-test`, `hipercool-videos`.
2. **Edite só `bin/*.py` da raiz.** NUNCA os `bin/_SNAPSHOT_*` / `bin/_VERSAO_CORRENTE_*` (são backups).
3. **NÃO apague caches** (`workspace/narration_cache`, `workspace/censura_cache`, cache de TTS) — é o que evita gastar token. Ver `workspace/CACHES_LEIA.md`.
4. **Os handoffs em `_HANDOFFS_FEITOS/` são coisas JÁ FEITAS.** NÃO reimplemente. Não confie em doc antigo que fale de "tarja"/"CENSURA_MODO" (censura velha).
5. **Nunca diga "pronto" sem provar** (ffprobe + extrair frames/mosaico).
6. **Python:** `D:\hipercool-videos\venv\Scripts\python.exe`. Rode ffmpeg/pipeline em **background**.
7. Postar / commit / apagar arquivo = **só com confirmação da dona**.

## ✅ ESTADO ATUAL (o que já está FEITO — não refazer)
- **Censura:** na IMAGEM do painel — NIVEL1_EXODIA_FOSCO (leve) e NIVEL2_TOTAL_BLUR (forte), em `bin/censura_visual.py`, plugada no `bin/hiper-pipeline.py` (só com `--censura`). **Está boa, NÃO mexer.** `effects_engine.censurar_video` (tarja) = legado.
- **Efeitos que mexem no painel (T15, 46 aprovados):** integrados em `bin/panel_effects.py` (facezoom, dollypush, breathing…), ligados por `PANEL_FX=1`.
- **Parallax 2.5D real (depth):** `bin/parallax_engine.py` + 706 depth maps cacheados. Ligado por `PARALLAX=1`. ✅ **Parallax é PRIORIDADE** no pipeline (roda primeiro; `PANEL_FX` é o fallback `if not ok`). Aparece só nos painéis elegíveis (`vale_parallax` pula texto/plano/+18) — por isso não é em todos, é o esperado. (Pendência antiga de "dar prioridade" já resolvida no commit 58606ef.)
- **Mascote:** 14 poses em `workspace/assets/overlays/elemental/fx_mascot_*.mov`, ligada por `MASCOTE_OVERLAY=1`.
- **CTA like/subscribe pequenos:** overlays no canto via `elemental_transitions` (`ELEMENTAL_TRANS=1`). Os cards de LIKE full-screen que ficavam no meio eram vídeos em `overlays/transitions/` (removidos pela dona).
- **Postagem:** só o `_CENSURADO_ULTIMO.mp4`. Fluxo em `POSTAGEM_YOUTUBE_PLAYBOOK.md`.

## 📌 PENDÊNCIAS conhecidas
- **Parallax:** priorizar sobre o PANEL_FX (pra o efeito 3D aparecer de fato).
- **split-shorts.py:** ffmpeg crasha (código 1) ao cortar alguns shorts censurados (ex.: cap7 parte03, cap9 parte07) — investigar o comando na linha ~199.

## 🧰 FERRAMENTAS (use ANTES de investigar do zero)
- **`bin/doctor.py [--cap <slug>]`** — raio-x: pasta certa, python/ffmpeg, caches, cobertura de depth, assets, flags, últimos vídeos.
- **`bin/smoketest.py [--cap <slug>]`** — testa a cadeia de render (censura/efeitos/parallax) em ~1 min, sem LLM/TTS. Rode depois de mexer no código.
- **`run_cap.bat <pasta-paineis> "<titulo>" <teste|final>`** — render de 1 capítulo com TUDO ligado certo (1 comando).
- **`--preset teste|final|night`** no `hiper-pipeline.py` — liga todas as flags de efeito de uma vez (não precisa setar 15 env vars).
- **`SINTOMA_CAUSA_FIX.md`** — tabela sintoma→causa→conserto.
- No fim de cada render sai `📊 Efeitos: parallax=X panel-fx=Y mascote=Z memes=W` — se algo deu 0, tem pista.

## 📖 DOCS ATIVOS (só estes)
- `_LEIA_FLUXO_PRODUCAO_E_CENSURA.md` — fluxo de produção + censura + **como aproveitar cache** (seção 1.5).
- `_VERSAO_CORRENTE_LEIA.md` — versão corrente / snapshots.
- `POSTAGEM_YOUTUBE_PLAYBOOK.md` + `COMO_POSTAR_CAPITULO_NOVO.md` — postagem.
- `workspace/CACHES_LEIA.md` — mapa dos caches (não apagar).
- `TAXONOMIA_EFEITOS_3_CATEGORIAS.md` / `REGRAS_LOWERTHIRD_E_MASCOTE.md` — efeitos/mascote (referência).
- `PLANO_AGENTE_PARALLAX_MOVIMENTO_REAL.md` / `PROMPT_AGENTE_PARALLAX_TESTAR_E_LIGAR.md` — parallax (em andamento).
- `MONETIZACAO_OST_INFO.md` — música sem copyright (`--no-copyright-ost`).
- `GUIA_OPERACAO_SCRAPE_SPLIT.md` / `CHECKLIST_VIDEO.md` — operação.

Tudo mais em `_HANDOFFS_FEITOS/` é **histórico** — só leia se precisar entender uma decisão passada.
