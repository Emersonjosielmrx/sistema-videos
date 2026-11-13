#!/usr/bin/env python3
"""hiper-pipeline.py — ORQUESTRAÇÃO do pipeline de vídeo hipercool.

════════════════════════════════════════════════════════════════════════════
MAPA (feito pra manutenção rápida / modelo grátis)
════════════════════════════════════════════════════════════════════════════
Este arquivo agora só ORQUESTRA. A lógica pesada foi pra módulos menores:

  narration.py    -> narração via Claude/visão (gerar_recap, descrição de painéis,
                    falas de personagem, revisão de coerência).
  tts_stage.py    -> geração de voz + cache (tts_panel, cache por similaridade).
  effects_engine  -> montagem visual (fachada; ver fx_*.py). Vídeo/legenda/trilha.
  hp_common.py    -> caminhos do projeto + log() (compartilhado por todos).

O que SOBROU aqui: run_pipeline (o fluxo painel->áudio->clip->concat), run_batch,
main (CLI) e _burn_webm_overlays (helper de overlay do próprio fluxo).

Uso:
    python bin/hiper-pipeline.py --panels-dir workspace/panels/x/ --titulo "..."
    python bin/hiper-pipeline.py --url <chapter_url> --titulo "Manhwa cap X"
    python bin/hiper-pipeline.py --slug nome --titulo "..."
    Flags úteis: --audio-only (só TTS, p/ fábrica de áudio), --censura,
                 --subtitles --karaoke, --max-panels N, --skip-notify, --dry-run
════════════════════════════════════════════════════════════════════════════
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# bin/ no path pra importar helpers locais
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _tts_filter import clean_for_tts
import gemini_tts
import gemini_llm
import _tg_safe
import random

import effects_engine
import fx_acabamento
import fx_parallax
import tts_cache

# ── base compartilhada + módulos extraídos ──
from hp_common import (PROJECT_DIR, CACHE_DIR, VIDEOS_DIR, TMP_DIR,
                       WATERMARK_HANDLE, MAX_PANELS_DEFAULT, log)
# narração IA (Claude/visão)
from narration import gerar_recap, gerar_recap_fusao, _revisar_coerencia, personagens_anteriores
# geração de voz + cache
from tts_stage import tts_panel, _tts_cache_key, TTS_CACHE_DIR

# fração dos cortes com transição sorteada que viram transição gl-transitions (dona 02/11)
GL_TRANS_CHANCE = float(os.environ.get("HIPER_GL_TRANS_CHANCE", "0.5"))

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)


# Adiciona bin/ ao path pra importar helpers locais
sys.path.insert(0, str(Path(__file__).resolve().parent))


VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


TMP_DIR.mkdir(parents=True, exist_ok=True)


TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

APROVACOES = Path(r"D:\postador-de-videos\config\aprovacoes.json")  # chave = caminho real em minúsculas


def _limpar_sessoes_velhas(horas=12):
    """tmp/session_<epoch> de render que morreu no meio (o render que termina apaga a sua)."""
    for d in TMP_DIR.glob("session_*"):
        try:
            velha = int(d.name.split("_", 1)[1]) < time.time() - horas * 3600
        except ValueError:
            continue
        if velha:
            shutil.rmtree(d, ignore_errors=True)


def _impactos_do_roteiro(recap):
    """Índices (base 0) das falas que o editorial marcou como momento forte.

    É o que dá a CURVA da narração (elenco.curva_climax): chegando nesses pontos a voz acelera e
    sobe, e logo depois respira. O dono pediu em 16/10: "eles vão acelerando conforme vai chegando
    ao clímax, como narração de futebol". O editorial já vem no roteiro antes de gravar as vozes."""
    ed = (recap or {}).get("_editorial") or {}
    return [i["fala"] for i in (ed.get("impactos") or []) if isinstance(i.get("fala"), int)]


def conferir_imagem_censurada(panel, cpanel, nivel, score):
    """Pergunta à visão se o painel JÁ CENSURADO ainda mostra algo. True = tem de virar fosco.

    Ideia do dono (16/10): olhar as IMAGENS em vez de varrer o vídeo pronto. No cap 3 a análise do
    vídeo abriu 350 quadros em 9,1 min, enquanto os painéis de risco eram 41 — e aqui dá pra
    corrigir ANTES de renderizar, o que poupa a segunda passada inteira (41 min naquele capítulo).

    Só vale a pena em painel de MOSAICO com risco: fosco já cobre tudo e painel limpo não precisa.
    Sem resposta do modelo não reprova nada — quem barra no escuro continua sendo a análise do
    vídeo pronto. HIPER_CONFERIR_IMAGENS=0 desliga."""
    if os.environ.get("HIPER_CONFERIR_IMAGENS", "1") == "0":
        return False
    if nivel != "local" or not Path(cpanel).exists():
        return False
    try:
        import censura_visual as cv
        import revisao_video
        if score < cv.LIMIAR_DUVIDA:
            return False
        # 3 opiniões (o padrão). Medido em 16/10: cada opinião leva ~9 s, e no cap 3 sobravam 7
        # painéis pra conferir depois que a regra de score alto + mosaico pequeno já mandou 4 pro
        # fosco de graça. Dá ~3 min por capítulo, contra 9 min da análise do vídeo MAIS os 41 min
        # da segunda passada que ela provoca. Subir pra 5 opiniões triplicaria isso sem ganho
        # medido: o painel 100 do cap 3 passou nas duas doses e quem o pegou foi a regra por número.
        vezes = int(os.environ.get("HIPER_OPINIOES_IMAGEM", "3"))
        return revisao_video.exposto(str(cpanel), vezes=vezes) is True
    except Exception as e:  # noqa: BLE001 — conferência que falha não derruba o render
        log(f"    [!] conferência da imagem falhou ({str(e)[:70]})")
        return False


def _limpar_versoes_anteriores(pastas, output_suffix, manter):
    """Depois de um render bom: apaga das pastas do capítulo/idioma os renders anteriores (superados,
    incompletos ou de render que falhou) com .meta/.capa/.folha. Fica o que tem aprovação no postador:
    o catálogo e o backup no Drive acham o postado pelo caminho."""
    try:
        aprov = json.loads(APROVACOES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log("  [!] aprovacoes.json ilegível: versões anteriores ficam")
        return
    padrao = re.compile(rf"^hipercool_.+_\d{{8}}_\d{{4}}{re.escape(output_suffix)}(_CENSURADO)?(_ULTIMO)?\.mp4$")
    manter = {Path(m).resolve() for m in manter}
    for pasta in pastas:
        for mp4 in list(pasta.glob("hipercool_*.mp4")):
            real = mp4.resolve()
            if real in manter or not padrao.match(mp4.name) or str(real).casefold() in aprov:
                continue
            # A limpeza é o ÚLTIMO passo e nunca pode derrubar um render que já deu certo: no cap 2
            # de 16/10 o vídeo saiu validado e o pipeline morreu aqui com o arquivo em uso (o
            # postador/backup estava lendo), rc != 0, e a fila marcou o capítulo inteiro como
            # "falhou". Arquivo preso fica pra próxima rodada.
            presos = []
            for f in list(pasta.iterdir()):
                if f.name.startswith(mp4.stem + "."):
                    try:
                        f.unlink(missing_ok=True)
                    except OSError as e:  # em uso por outro processo, só-leitura...
                        presos.append(f"{f.name} ({type(e).__name__})")
            if presos:
                log(f"  [!] versão anterior em uso, fica pra próxima: {', '.join(presos[:3])}")
            else:
                log(f"  versão anterior apagada: {mp4.name}")


def _burn_webm_overlays(video_in, overlays, video_out):
    """Sobrepõe vídeos WebM (legendas HyperFrames) no vídeo principal com timing.

    overlays: lista de {"webm": path, "start": float, "end": float}
    Usa chromakey (fundo preto -> transparente) + overlay com enable='between(t,start,end)'.
    """
    if not overlays:
        return False

    # Limitar a 20 overlays simultâneos (ffmpeg tem limite de inputs)
    overlays = overlays[:20]

    inputs = ["-i", str(video_in)]
    for ov in overlays:
        inputs += ["-i", ov["webm"]]

    # Cadeia de overlays: cada WebM é sobreposto na janela de tempo
    # Usar chromakey para remover fundo preto dos WebMs
    parts = []
    cur = "[0:v]"
    for idx, ov in enumerate(overlays, start=1):
        out = f"[vhf{idx}]"
        # Chromakey remove preto, overlay no centro-inferior
        parts.append(
            f"[{idx}:v]chromakey=0x000000:0.15:0.1,scale=1080:1920:force_original_aspect_ratio=decrease[hfov{idx}];"
            f"{cur}[hfov{idx}]overlay=0:0:"
            f"enable='between(t,{ov['start']:.2f},{ov['end']:.2f})'{out}"
        )
        cur = out

    filter_complex = ";".join(parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", cur, "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        "-c:a", "copy",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log(f"  [X] burn_webm_overlays falhou: {str(e)[:200]}")
        return False


# ─── Pipeline principal ──────────────────────────────────────────────────────
def run_pipeline(panels_dir, titulo, max_panels=MAX_PANELS_DEFAULT,
                 skip_notify=False, dry_run=False, skip_credits=1, animated=False,
                 start_panel=0, fusao=False, narrator_gender="F", subtitles=False,
                 branding=True, karaoke=False, censura=False, # Argumentos existentes
                 force_llm=False, force_tts=False,
                 hyperframes_karaoke=False, output_suffix="", # Novo output_suffix
                 audio_only=False, acabamento=None, skip_final=0, idioma=None):
    """Executa a pipeline completa a partir de painéis já cortados.

    skip_credits: pula os N primeiros painéis (geralmente créditos/capa/avisos).
    start_panel: offset no início (pra gerar PARTES seguintes do mesmo capítulo).
                 Aplicado DEPOIS dos filtros (créditos/pequenos/brancos), então
                 part 1 = start_panel=0, part 2 = start_panel=55, etc.
    acabamento: pós-concat do fx_acabamento (legenda ASS, gancho, impactos, SFX por
                palavra, loudness, passe final único). None = env HIPER_ACABAMENTO (padrão 1).
    skip_final: descarta os N últimos painéis (propaganda/Discord do grupo de scan no fim
                do capítulo — senão a narração "dubla" o anúncio e o CTA cai em cima dele).
    """
    if acabamento is None:
        acabamento = os.environ.get("HIPER_ACABAMENTO", "1") != "0"
    panels_dir = Path(panels_dir)
    # Mesma seleção do vídeo longo 16:9 (hp_paineis): créditos, pequenos, brancos, fim, offset, limite.
    # cover_panel = 1ª imagem original (capa/créditos): vira SÓ o fundo borrado da abertura.
    import hp_paineis
    panel_files, cover_panel = hp_paineis.selecionar_paineis(panels_dir, max_panels, skip_credits,
                                                             skip_final, start_panel)
    if not panel_files:
        log("[X] Nenhum painel encontrado!")
        return None

    n = len(panel_files)
    log(f"Pipeline: {titulo} ({n} painéis)")

    if dry_run:
        log("  [DRY-RUN] Mostrando o que seria feito:")
        log(f"  1. Gerar narração ({n} locuções) com visão dos painéis")
        log(f"  2. TTS pra {n} painéis (Gemini 3.1 Flash)")
        log(f"  3. {n} clips Ken Burns -> concat -> MP4")
        log(f"  4. Notificar Telegram: {'sim' if not skip_notify else 'não'}")
        return None

    # 1. Narração IA (com cache — reusar locuções já geradas)
    narration_cache_dir = PROJECT_DIR / "workspace" / "narration_cache"
    narration_cache_dir.mkdir(parents=True, exist_ok=True)
    slug = panels_dir.name if hasattr(panels_dir, 'name') else Path(panels_dir).name
    narration_cache_file = hp_paineis.arquivo_narracao(panels_dir, n, skip_credits, skip_final, start_panel, fusao)

    import json as _json
    if narration_cache_file.exists() and not force_llm:
        # caches antigos foram gravados em cp1252 — lê tolerando os dois
        recap = fx_acabamento._ler_json(narration_cache_file)
        log(f"  [OK] Narração [CACHE]: {recap.get('titulo_video', titulo)}")
    else:
        recap = None
        if force_llm: log("  [!] --force-llm ativo, ignorando cache de narração.")
        if fusao:
            # Híbrido: tenta fusão (1 chamada). Se bloquear (conteúdo +18), cai pro 2-passos.
            recap = gerar_recap_fusao(titulo, panel_files, narrator_gender=narrator_gender)
            if not recap:
                log("  Fusão indisponível -> fluxo 2-passos (visão neutra + narração)")
        if not recap:
            # ficha de personagens: mesmos nomes (= mesmas vozes) dos capítulos anteriores da obra
            m_oc = re.match(r"^(.+)-cap(\d+)$", Path(panels_dir).name)
            conhecidos = personagens_anteriores(m_oc.group(1), int(m_oc.group(2))) if m_oc else None
            if conhecidos:
                log(f"  personagens dos capítulos anteriores: {', '.join(p for p, _g, _n in conhecidos[:8])}")
            recap = gerar_recap(titulo, panel_files, narrator_gender=narrator_gender, conhecidos=conhecidos)
        if not recap:
            log("[X] Falha na geração de narração")
            return None
        # quem fala cada fala (marca de gênero em 1ª pessoa; HIPER_REVISAR_FALANTES=0 desliga, falantes.restaurar desfaz)
        import falantes
        falantes.revisar(recap["locucoes"], recap.get("descriptions", []))
        # Salvar no cache
        narration_cache_file.write_text(_json.dumps(recap, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"  [OK] Narração: {recap.get('titulo_video', titulo)} [salvo no cache]")

    locucoes = recap["locucoes"]
    descriptions = recap.get("descriptions", [])

    # 1b. Revisão de coerência narrativa — ajusta conexões entre locuções do narrador.
    # Roda UMA VEZ e salva o resultado no narration_cache (flag _revised). Senão o texto
    # do narrador mudava a cada run -> furava o cache de áudio (regerava ~38 falas à toa).
    if not recap.get("_revised"):
        locucoes = _revisar_coerencia(locucoes, titulo)
        recap["locucoes"] = locucoes
        recap["_revised"] = True
        try:
            narration_cache_file.write_text(_json.dumps(recap, ensure_ascii=False, indent=2), encoding="utf-8")
            log("  [OK] Narração revisada salva no cache (estável p/ próximos runs)")
        except Exception as e:
            log(f"  [!] não consegui salvar revisão no cache: {e}")

    # 1b-ter. EDITORIAL ANTES DAS VOZES. A curva do clímax (elenco.curva_climax) acelera a voz chegando
    # nos impactos que o editorial marca — mas o editorial só rodava no acabamento, DEPOIS das vozes.
    # Em roteiro novo a curva nunca entrava: no cap 5 (16/10) as 60 falas do narrador saíram todas em
    # "+5%", o editorial apareceu no log 13 min depois da última voz. Mesma chamada, só mais cedo; o
    # acabamento reaproveita o que ficou salvo no cache.
    if not (recap.get("_editorial") or {}).get("fonte") == "llm":
        try:
            fx_acabamento.editorial(recap, titulo, narration_cache_file)
        except Exception as e:  # noqa: BLE001 — sem editorial a voz sai reta, como antes
            log(f"  [!] editorial antes das vozes falhou: {str(e)[:120]}")
    if not idioma:
        log(f"  curva do clímax: impactos nas falas {_impactos_do_roteiro(recap) or 'nenhum (voz reta)'}")

    # 1b-bis. Versão em OUTRA LÍNGUA: troca só o roteiro (tradução em cache) — painéis, censura,
    # recortes e efeitos continuam os do português. A censura usa as falas em pt (locucoes_pt).
    # 1a-bis. ELENCO FIXO da obra (bin/elenco.py): apelido/genérico ("Rapaz" que é o protagonista) vira o nome
    # oficial -> a voz do personagem não troca. Vale também nas outras línguas: a tradução só troca o TEXTO da fala,
    # o campo persona continua o nome em português (e a voz da língua varia por esse nome: idiomas._perfil).
    import elenco
    obra_elenco = elenco.obra_de(panels_dir)
    if not idioma:
        locucoes = elenco.normalizar(obra_elenco, locucoes)
        log(f"  voz do português: motor {elenco.motor()} (config/fila.json tts_motor)")
    locucoes_pt = locucoes
    if idioma:
        import idiomas
        recap = idiomas.traduzir_recap(recap, idioma, narration_cache_file)
        locucoes = elenco.normalizar(obra_elenco, recap["locucoes"])

    # 1c. Detecção +18 por VISÃO (só com --censura): decide quais painéis ganham versão
    # censurada na IMAGEM (censura_visual). O texto ("cena intensa") só entra se a visão faltar.
    cens_det = {}       # índice do painel -> (score, tipo)
    cens_scores = {}    # índice do painel -> score +18 (0..1), pra close nunca cair em painel sugestivo
    cens_origens = {}
    if censura and not audio_only:
        import censura_visual
        scores, textos, fluidos = [], [], []
        for k, p in enumerate(panel_files):
            txt_k = locucoes_pt[k].get("text", "") if k < len(locucoes_pt) else ""
            desc_k = descriptions[k] if k < len(descriptions) else ""
            textos.append(effects_engine.is_nsfw_panel(desc_k, txt_k))
            fluidos.append(effects_engine.is_fluido_panel(desc_k, txt_k))
            s, origem = censura_visual.detectar_score(p)
            if s is None:
                s = censura_visual.LIMIAR_NSFW if textos[k] else 0.0
                origem = "texto"
            scores.append(s)
            cens_scores[k] = s
            cens_origens[origem] = cens_origens.get(origem, 0) + 1
        # Reforço depois da advertência do YouTube (16/10): painel abaixo da dúvida em que a visão vê parte
        # exposta (cap 10 panel_005, score 0,44, saiu com o seio à mostra) e os painéis que a análise do vídeo
        # pronto reprovou antes (censura_visual.forcar_fosco) entram na lista.
        scores, subiram = censura_visual.reforcar_scores(panel_files, scores)
        for k in subiram:
            cens_scores[k] = scores[k]
        if subiram:
            log(f"  Censura: a visão/lista de forçados pôs {len(subiram)} painel(is) a mais: {subiram}")
        for k, s in enumerate(scores):
            if s >= censura_visual.LIMIAR_DUVIDA:
                cens_det[k] = (s, None, textos[k])
                continue
            # 4ª camada (16/10): fluido corporal. O Sightengine só pontua ato e nudez, então rosto
            # com líquido branco (cap 10 painel 12, score 0,32) e mãos com fluido (painel 7, 0,02)
            # passavam inteiros — em close de 6 s, com o narrador dizendo o que era. Aqui o painel só
            # vai PERGUNTAR ao Gemini; quem decide censurar continua sendo a visão.
            if fluidos[k]:
                cens_det[k] = (max(s, censura_visual.LIMIAR_DUVIDA), None, textos[k])
                continue
            # 3ª camada (V8): parte apagada em branco pelo autor + vizinho +18 forte
            viz = max([scores[j] for j in (k - 1, k + 1) if 0 <= j < len(scores)] or [0.0])
            if viz >= censura_visual.LIMIAR_NSFW and censura_visual.mancha_branca_frac(panel_files[k]) >= 0.05:
                cens_det[k] = (censura_visual.LIMIAR_DUVIDA, "branco", textos[k])
        log(f"  Censura: {len(cens_det)}/{len(panel_files)} painéis +18 {sorted(cens_det)} "
            f"(detector: {cens_origens})")
        if set(cens_origens) - {"sightengine"}:
            log("  [!] Sightengine indisponível em parte dos painéis — detecção mais fraca, "
                "revise a folha de quadros do censurado antes de postar")

    cens_jobs = []
    ultimo_2p5d = -9  # índice do último clip com parallax (pra não repetir em sequência)
    ultimo_close = -9
    ultimo_meme = -99
    ultimo_modo, ultimo_modo_i = None, -9  # modo do clip anterior (variedade de movimento)
    modos_usados = {}

    def _cens_job(idx, panel, clip, fn, antes, kw):
        """Guarda como refazer o clip deste painel (mesma função/params) a partir da imagem censurada."""
        if idx in cens_det:
            score, tipo, texto = cens_det[idx]
            cens_jobs.append({"i": idx, "panel": panel, "clip": clip, "fn": fn, "antes": antes,
                              "kw": kw, "score": score, "tipo": tipo, "texto": texto})

    # 2. TTS + clips (com efeitos visuais do effects_engine)
    clips = []
    clip_texts = []  # texto da narração por clip (pra legendas) — alinhado com clips
    clip_personas = []  # persona por clip (pra name tag) — alinhado com clips
    clip_infos = []  # dict por clip (pro fx_acabamento: voz, atraso do foley, SFX) — alinhado com clips
    _limpar_sessoes_velhas()
    session_tmp = TMP_DIR / f"session_{int(time.time())}"
    session_tmp.mkdir(parents=True, exist_ok=True)
    efx = effects_engine.EffectsManager()
    efx.variante = idioma  # fx_parallax: espelho por língua (None no pt)

    for i, (panel_path, loc) in enumerate(zip(panel_files, locucoes)):
        wav_path = session_tmp / f"audio_{i:03d}.wav"
        clip_path = session_tmp / f"clip_{i:03d}.mp4"

        # Determinar pacote de evento: transição + SFX + overlay (clip todo) + luma (no corte)
        transition_type, sfx_file, overlay_video, luma_transition = \
            effects_engine.get_event_package(i, descriptions, [l.get("text", "") for l in locucoes])
        # Transição gl-transitions (dona 02/11, REALCE_TRANSICAO=0 desliga): no lugar da transição sorteada, do
        # último quadro do clip anterior pro começo deste. Nunca encostando em painel sensível: os clips sem
        # censura são os mesmos no vídeo censurado, e a transição levaria o quadro sem censura do vizinho.
        gl_trans = None
        ant_loc = clip_infos[-1].get("loc") if clip_infos and clip_infos[-1].get("tipo") == "fala" else None
        if (transition_type and ant_loc is not None and not audio_only and random.random() < GL_TRANS_CHANCE
                and fx_parallax.realce_visual and fx_parallax.realce_visual.disponivel("transicao")
                and all(k not in cens_det and cens_scores.get(k, 0.0) < 0.25 for k in (i, ant_loc))):
            gl_trans, transition_type = random.choice(fx_parallax.realce_visual.TRANSICOES), None

        # Voz sensual DESLIGADA (sensual sempre False no TTS — ver tts_stage). A censura
        # usa a detecção por visão do passo 1c (cens_det), não este flag.
        is_sensual = False

        # Propaganda/créditos do scan no MEIO do capítulo: não vira clip (nem narração do anúncio).
        if effects_engine.is_propaganda(descriptions[i] if i < len(descriptions) else "", loc.get("text", "")):
            log(f"  [pula] painel {i} é propaganda do scan: {(descriptions[i] if i < len(descriptions) else '')[:70]}")
            continue

        text_to_narrate = loc.get("text", "").strip()

        # FÁBRICA DE ÁUDIO: só gera TTS (enche o cache) e pula o build do clip.
        # A fase de vídeo (ffmpeg) roda depois, em paralelo, reusando este cache.
        if audio_only:
            if text_to_narrate:
                persona_lower = (loc.get("persona") or "narrador").lower()
                tts_gender = None if persona_lower in ("narrador", "narradora", "narrator") else loc.get("gender")
                ok = elenco.falar(obra_elenco, text_to_narrate, wav_path, loc.get("persona", "Narrador"), tts_gender, force_tts,
                                  indice=i, impactos=_impactos_do_roteiro(recap), total=len(locucoes))
                if ok and elenco.usa_gemini(loc.get("persona", "Narrador")):
                    time.sleep(3.0)  # respiro anti-quota entre chamadas reais
            continue

        if not text_to_narrate:
            # Painel SEM NARRAÇÃO INTENCIONAL: clip rápido SEM SFX de transição
            log(f"  ⚡ Painel {i} sem narração, gerando clip rápido (sem SFX)")
            flash_kw = dict(duration=0.8, transition_type=transition_type, sfx_file=None)  # << SFX=None
            ok_flash = effects_engine.build_flash_clip(panel_path, clip_path, i, efx, **flash_kw)
            if ok_flash:
                clips.append(clip_path)
                clip_texts.append("")
                clip_personas.append("")
                clip_infos.append({"tipo": "rapido", "loc": i, "sfx": False})
                _cens_job(i, panel_path, clip_path, effects_engine.build_flash_clip, (), flash_kw)
            continue # Próximo painel

        # Painel COM NARRAÇÃO: tentar TTS
        # REGRA FIRME: Narrador SEMPRE usa a mesma voz (gender=None -> Kore).
        # Ignorar gender do LLM para manter consistência.
        persona_lower = (loc.get("persona") or "narrador").lower()
        tts_gender = None if persona_lower in ("narrador", "narradora", "narrator") else loc.get("gender")
        if idioma:  # outra língua: voz edge-tts (grátis, sem cota) no idioma
            ok = idiomas.falar(text_to_narrate, wav_path, loc.get("persona", "Narrador"), tts_gender, idioma)
        else:  # português: voz fixa do elenco da obra, motor edge ou Gemini (config/fila.json tts_motor)
            ok = elenco.falar(obra_elenco, text_to_narrate, wav_path, loc.get("persona", "Narrador"), tts_gender, force_tts,
                                  indice=i, impactos=_impactos_do_roteiro(recap), total=len(locucoes))

        if not ok:
            # Painel com narração ESPERADA, mas TTS FALHOU: clip rápido COM SFX (indica erro)
            log(f"  [!] TTS falhou pra painel {i} (mas tinha narração), gerando clip rápido (com SFX)")
            flash_kw = dict(duration=0.8, transition_type=transition_type, sfx_file=sfx_file)  # << SFX normal
            ok_flash = effects_engine.build_flash_clip(panel_path, clip_path, i, efx, **flash_kw)
            if ok_flash:
                clips.append(clip_path)
                clip_texts.append("")
                clip_personas.append("")
                clip_infos.append({"tipo": "rapido", "loc": i, "sfx": bool(sfx_file)})
                _cens_job(i, panel_path, clip_path, effects_engine.build_flash_clip, (), flash_kw)
            continue # Próximo painel

        # Se chegou aqui, TTS foi OK e tinha narração.

        # Delay entre requests TTS (só se não veio do cache)
        # A cada 10 painéis TTS reais, pausa 10s extras pra evitar quota em lote
        if idioma or not elenco.usa_gemini(loc.get("persona", "Narrador")):
            time.sleep(0.3)
        elif not (TTS_CACHE_DIR / f"{_tts_cache_key(clean_for_tts(loc['text']), elenco.voz(obra_elenco, loc.get('persona', 'Narrador'), loc.get('gender'))[1])}.wav").exists():
            time.sleep(3.0)
        else:
            time.sleep(0.3)  # Breath mesmo em cache pra não sobrecarregar ffmpeg

        # Clip com efeitos (movimentos variados + cor + vinheta)
        # Detectar impacto/tensão pra aplicar camera shake
        desc = descriptions[i] if i < len(descriptions) else ""
        is_impact = effects_engine.is_impact_panel(desc)
        is_tension = effects_engine.is_tension_panel(desc)
        efx.clima = effects_engine.detect_mood_from_text(f"{desc} {text_to_narrate}")  # cor/vinheta por clima
        # cena engraçada: um meme de áudio (sfx_memes/comedia) no lugar do SFX, no máx. 1 a cada 8 clips
        if efx.clima == "funny_lighthearted" and i - ultimo_meme >= 8 and random.random() < 0.5:
            meme = effects_engine.pick_meme("comedia")
            if meme:
                sfx_file, ultimo_meme = meme, i
                log(f"    [meme] {Path(meme).name}")

        # Foley contextual (som do que ACONTECE na cena: campainha, porta, passos...).
        # Mixado no áudio ANTES do build (build_clip deriva a duração do áudio).
        # O modo gap (pausa antes da voz) vs junto é controlado por HIPER_FOLEY_GAP.
        # NÃO no 1º clip de conteúdo: foley longo (ex: gulp/beber) logo após o intro
        # soava como "chuva" e atrapalhava a abertura.
        foley_file, foley_sit = effects_engine.pick_foley(desc, text_to_narrate)
        if foley_file and i == 0:
            foley_file, foley_sit = None, None
        voice_wav, voice_delay = wav_path, 0.0
        if foley_file:
            foley_wav = session_tmp / f"foley_{i:03d}.wav"
            wav_path = Path(effects_engine.prepare_foley_audio(wav_path, foley_file, foley_wav))
            if wav_path == foley_wav and effects_engine.FOLEY_GAP_MODE:
                voice_delay = effects_engine.FOLEY_GAP_S  # voz entra depois do foley

        # overlay_video / luma_transition vêm do get_event_package (pacote de evento)
        tag = "  [SHAKE]" if is_impact else ("  [TENSION]" if is_tension else "")
        ov_tag = f"  [ovl:{Path(overlay_video).stem}]" if overlay_video else ""
        lt_tag = f"  [luma:{Path(luma_transition).stem}]" if luma_transition else ""
        fl_tag = f"  [foley:{foley_sit}]" if foley_file else ""
        log(f"  Clip {i+1}/{n}{'  [animated]' if animated else ''}{tag}{ov_tag}{lt_tag}{fl_tag}...")
        # balão de fala no quadro: o tremor não pode impedir a leitura (impacto = tranco curto; tensão = sem)
        com_balao = fx_parallax.tem_balao(panel_path) if (is_impact or is_tension) else False
        if is_impact:
            build_fn = effects_engine.build_clip_with_shake
            build_kw = dict(transition_type=transition_type, sfx_file=sfx_file,
                            overlay_video=overlay_video, luma_transition=luma_transition)
            if com_balao:
                build_kw.update(shake_intensity=6, shake_dur=0.7)
        elif is_tension and not com_balao:
            # Shake suave em tensão (intensidade menor)
            build_fn = effects_engine.build_clip_with_shake
            build_kw = dict(shake_intensity=5, shake_freq=8,
                            transition_type=transition_type, sfx_file=sfx_file,
                            overlay_video=overlay_video, luma_transition=luma_transition)
        elif animated:
            build_fn = effects_engine.build_clip_animated
            build_kw = dict(transition_type=transition_type, sfx_file=sfx_file)
        else:
            build_fn = effects_engine.build_clip
            build_kw = dict(transition_type=transition_type, sfx_file=sfx_file,
                            overlay_video=overlay_video, luma_transition=luma_transition)
        # Efeitos com o personagem RECORTADO / closes (fx_parallax, tudo local, sem API):
        #   reação no rosto -> CLOSE (punch-in no rosto); impacto -> salto + linhas de velocidade;
        #   tensão -> parallax com tremor; deslocamento -> personagem ANDA (ou câmera segue);
        #   normal -> parallax (nunca 2 seguidos), close de vez em quando, ou câmera até o personagem.
        # Close nunca em painel +18/sugestivo (o detector de rosto já confundiu lingerie com rosto).
        # O censurado refaz com o MESMO recorte/rosto (mascara_de = painel original).
        if not animated and fx_parallax.LIGADO:
            fala_pt = locucoes_pt[i].get("text", "") if i < len(locucoes_pt) else ""
            sugestivo = (i in cens_det or cens_scores.get(i, 0.0) >= 0.25
                         or effects_engine.is_nsfw_panel(desc, fala_pt))
            eleg = fx_parallax.elegivel(panel_path)[0]
            rosto = None if sugestivo else fx_parallax.rosto_principal(panel_path)
            reacao = effects_engine.is_reacao_panel(desc, fala_pt)
            modo = None
            if is_impact and eleg:
                modo = "impacto" if random.random() < 0.85 else None
            elif rosto and reacao and i - ultimo_close >= 2 and random.random() < 0.70:
                modo = "close"
            elif (not sugestivo and i - ultimo_close >= 2 and effects_engine.is_poder_panel(desc, fala_pt)
                  and fx_parallax.brilho_principal(panel_path)):
                modo = "poder"
            elif (not sugestivo and i - ultimo_close >= 2 and effects_engine.is_objeto_panel(desc, fala_pt)
                  and fx_parallax.objeto_principal(panel_path)):
                modo = "objeto"
            elif is_tension and eleg:
                modo = "tensao" if random.random() < 0.7 else None
            elif eleg and effects_engine.is_movimento_panel(desc, fala_pt):
                modo = "andar" if fx_parallax.pode_andar(panel_path) else "foco"
            elif eleg and i - ultimo_2p5d > 1 and random.random() < fx_parallax.CHANCE:
                modo = "andar" if fx_parallax.pode_andar(panel_path) and random.random() < 0.5 else "parallax"
            elif rosto and i - ultimo_close >= 3 and random.random() < 0.40:
                modo = "close"
            elif eleg:
                modo = "foco" if random.random() < 0.75 else None
            elif not eleg and not sugestivo and fx_parallax.profundidade_vale(panel_path):
                modo = "profundidade"
            if idioma and fx_parallax.cache_ligado():  # outra língua: o movimento que já está no cache sai quase de graça
                guardados = fx_parallax.modos_guardados(panel_path, i)
                if guardados and modo not in guardados:
                    modo = random.choice(guardados)
            # Variedade (16/10): "nunca 2 seguidos" só valia pro parallax — 'foco' nem atualizava o
            # controle e 'profundidade' não olhava nada, então saíam foco-foco e 3 profundidades em
            # sequência (cap 10 clips 51 e 52). Em clip colado no anterior, troca pelo outro movimento
            # de câmera; se não der, deixa o painel parado (que também é variedade).
            if modo and modo == ultimo_modo and i - ultimo_modo_i <= 1 and modo in ("foco", "profundidade", "parallax"):
                alternativa = {"foco": "profundidade", "profundidade": "foco", "parallax": "foco"}[modo]
                pode = (fx_parallax.profundidade_vale(panel_path) if alternativa == "profundidade"
                        else eleg and not sugestivo)
                modo = alternativa if pode else None
            if modo:
                build_fn = fx_parallax.build_clip_parallax
                build_kw = dict(transition_type=transition_type, sfx_file=sfx_file, overlay_video=overlay_video,
                                luma_transition=luma_transition, mascara_de=panel_path, modo=modo,
                                texto=text_to_narrate)
                if modo in ("parallax", "andar", "impacto", "tensao", "profundidade"):
                    ultimo_2p5d = i
                if modo in ("close", "objeto", "poder"):
                    ultimo_close = i
                ultimo_modo, ultimo_modo_i = modo, i
                modos_usados[modo] = modos_usados.get(modo, 0) + 1
                log(f"    [2.5D] {'close' if modo in ('close', 'objeto', 'poder') else 'personagem recortado'}: {modo}")
        ok = build_fn(panel_path, wav_path, clip_path, i, efx, **build_kw)
        if ok:
            if gl_trans and fx_parallax.realce_visual.transicao_inicio(clip_path, clips[-1], nome=gl_trans,
                                                                       dur=0.4, semente=i):
                log(f"    [transição gl] {gl_trans}")
            _cens_job(i, panel_path, clip_path, build_fn, (wav_path,), build_kw)
            clips.append(clip_path)
            clip_texts.append(loc.get("text", ""))
            clip_personas.append(loc.get("persona", ""))
            clip_infos.append({"tipo": "fala", "loc": i, "texto": loc.get("text", ""),
                               "persona": loc.get("persona", ""), "voz_wav": str(voice_wav),
                               "atraso": voice_delay, "foley": bool(foley_file), "sfx": bool(sfx_file)})
        else:
            log(f"  [!] Clip {i} falhou, pulando")

    if modos_usados:
        log(f"  efeitos 2.5D/close: {sum(modos_usados.values())}/{len(clips)} clips {modos_usados}")
        log(f"  cache 2.5D: {fx_parallax.CACHE_STATS}")

    # memes que INTERROMPEM: emoção forte no fim da fala -> o vídeo para, o meme entra em tela cheia com o som
    # dele e a narração segue. Decide pela fala em pt (as línguas recebem nos mesmos pontos). Entra antes da
    # cópia da lista censurada, então o censurado tem o mesmo clip no mesmo lugar.
    _cfg_memes = {}
    try:
        _cfg_memes = json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8")).get("memes") or {}
    except (OSError, ValueError):
        pass
    if acabamento and clips and _cfg_memes.get("ligado", True) and _cfg_memes.get("interrompe_s", 60):
        try:  # enfeite: erro aqui nunca derruba o render
            import fx_assets
            import fx_clips
            import fx_memes
            falas, t_acum = [], 0.0
            for k, (c, inf) in enumerate(zip(clips, clip_infos)):
                d = fx_acabamento.duracao(c) or 0.0
                if inf.get("tipo") == "fala" and inf.get("loc") is not None:
                    lp = locucoes_pt[inf["loc"]].get("text", "") if inf["loc"] < len(locucoes_pt) else ""
                    falas.append((k, lp, t_acum, t_acum + d))
                t_acum += d
            inter = fx_memes.escolher_interrupcoes(falas, intervalo_s=_cfg_memes.get("interrompe_s", 60))
            for k, meme in reversed(inter):  # de trás pra frente: inserir não desloca os índices que faltam
                mclip = session_tmp / f"_meme_{k:03d}.mp4"
                if fx_memes.montar_clip_meme(meme, mclip, fx_assets.W, fx_assets.H, fx_assets.FPS, fx_clips.CLIP_CRF):
                    clips.insert(k + 1, mclip)
                    clip_texts.insert(k + 1, "")
                    clip_personas.insert(k + 1, "")
                    clip_infos.insert(k + 1, {"tipo": "meme", "sfx": True})
                    log(f"  [memes] interrompe depois do clip {k + 1}: {Path(meme['file']).name} "
                        f"({meme.get('duration', 0):.1f}s)")
        except Exception as e:  # noqa: BLE001
            log(f"  [!] memes que interrompem: pulados ({type(e).__name__}: {str(e)[:120]})")
    # CTA do fim (18/10): pedido de like/comentário falado num clip À PARTE depois do último painel — nunca na
    # narração (o capítulo entra inteiro no compilado, que ganha o dele uma vez só no fim: hiper-longo.py).
    # Fundo = o último painel seguro (sem +18, sem propaganda): o clip é o mesmo no normal e no censurado.
    if acabamento and branding and clips and not idioma and os.environ.get("HIPER_CTA_FIM", "1") != "0":
        try:  # enfeite: erro aqui nunca derruba o render
            import narration as _narr
            tinha_cta = bool((recap.get("_cta_fim") or {}).get("texto"))
            cta = _narr.gerar_cta_fim(recap, titulo)
            if cta and not tinha_cta:
                narration_cache_file.write_text(json.dumps(recap, ensure_ascii=False, indent=2), encoding="utf-8")
            seguros = []
            for k in range(len(panel_files) - 1, -1, -1):
                d_k = descriptions[k] if k < len(descriptions) else ""
                t_k = locucoes_pt[k].get("text", "") if k < len(locucoes_pt) else ""
                if (k not in cens_det and cens_scores.get(k, 0.0) < 0.25 and not effects_engine.is_propaganda(d_k, t_k)
                        and not effects_engine.is_nsfw_panel(d_k, t_k)):
                    seguros.append(panel_files[k])
            # painel com personagem (o de recorte do 2.5D); painel só de balão/fundo branco fica de reserva
            fundo = next((p for p in seguros[:20] if fx_parallax.elegivel(p)[0]), seguros[0] if seguros else None)
            wav_cta, clip_cta = session_tmp / "audio_cta.wav", session_tmp / "clip_cta.mp4"
            if (cta and fundo and elenco.falar(obra_elenco, cta["texto"], wav_cta, "Narrador", None, force_tts)
                    and effects_engine.build_clip(fundo, wav_cta, clip_cta, len(panel_files), efx)):
                clips.append(clip_cta)
                clip_texts.append(cta["texto"])
                clip_personas.append("Narrador")
                clip_infos.append({"tipo": "fala", "loc": None, "texto": cta["texto"], "persona": "Narrador",
                                   "voz_wav": str(wav_cta), "atraso": 0.0, "foley": False, "sfx": False, "cta": True})
                log(f"  [OK] CTA do fim depois do último painel (fundo: {Path(fundo).name})")
            elif cta:
                log("  [!] CTA do fim ficou de fora (sem painel seguro pro fundo, ou a voz/o clip falhou)")
        except Exception as e:  # noqa: BLE001
            log(f"  [!] CTA do fim: pulado ({type(e).__name__}: {str(e)[:120]})")
    # pra capa sensual (fx_acabamento._capa_sensual): descrição + fala (no idioma do vídeo) de cada painel
    capa_info = {str(p): {"desc": descriptions[k] if k < len(descriptions) else "",
                          "fala": locucoes[k].get("text", "") if k < len(locucoes) else "",
                          "persona": locucoes_pt[k].get("persona") if k < len(locucoes_pt) else None,
                          "genero": locucoes_pt[k].get("gender") if k < len(locucoes_pt) else None}
                 for k, p in enumerate(panel_files)}

    if audio_only:
        state_dir = PROJECT_DIR / "workspace" / "factory_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        marker = state_dir / f"{panels_dir.name}.audio_ready"
        marker.write_text(f"{datetime.now().isoformat()} n={n}\n", encoding="utf-8")
        log(f"  [OK] ÁUDIO PRONTO ({n} painéis, TTS no cache). Marcador: {marker.name}")
        return "AUDIO_ONLY_DONE"

    if not clips:
        log("[X] Nenhum clip gerado!")
        return None

    # 2b. Intro hook + outro CTA (branding) — opcional.
    # Com o acabamento, o gancho e o CTA entram POR CIMA do 1º/último painel (ASS):
    # tela parada de título/"inscreva-se" é tempo morto e derruba a retenção.
    if branding and not acabamento:
        intro_path = session_tmp / "_intro.mp4"
        title_card = recap.get("titulo_video", titulo)
        if effects_engine.build_intro_clip(title_card, cover_panel, intro_path,
                                           sfx_file=effects_engine.SFX_DIR / "riser.wav"):
            clips.insert(0, intro_path)
            clip_texts.insert(0, "")
            clip_personas.insert(0, "")
            clip_infos.insert(0, {"tipo": "intro", "sfx": True})
            log("  [OK] Intro adicionado")
        outro_path = session_tmp / "_outro.mp4"
        if effects_engine.build_outro_clip(outro_path,
                                           sfx_file=effects_engine.SFX_DIR / "bass_hit.wav"):
            clips.append(outro_path)
            clip_texts.append("")
            clip_personas.append("")
            clip_infos.append({"tipo": "outro", "sfx": True})
            log("  [OK] Outro (CTA) adicionado")

    # 2b-bis. Abertura (com acabamento): ~3 s de montagem rápida da 2ª metade do capítulo — nunca
    # painel +18 nem propaganda — com o gancho do editorial por cima (prende quem chega).
    if branding and acabamento and os.environ.get("HIPER_TEASER", "1") != "0":
        excl = set(cens_det) | {k for k, d in enumerate(descriptions) if effects_engine.is_propaganda(d)}
        escolhidos = fx_parallax.escolher_teaser(panel_files, excl)
        teaser = session_tmp / "_teaser.mp4"
        if escolhidos and fx_parallax.build_teaser(escolhidos, teaser,
                                                   sfx_file=effects_engine.SFX_DIR / "dramatic_riser.wav"):
            clips.insert(0, teaser)
            clip_texts.insert(0, "")
            clip_personas.insert(0, "")
            clip_infos.insert(0, {"tipo": "intro", "sfx": True})
            log(f"  [OK] Abertura: montagem de {len(escolhidos)} painéis ({', '.join(p.name for p in escolhidos)})")

    # 2c. Censura na IMAGEM: refaz SÓ os clips +18 a partir do painel censurado (só as partes
    # explícitas), com a mesma função/params -> mesma duração -> o censurado recebe o MESMO
    # áudio, legendas, gancho e impactos do principal (no fx_acabamento), nítidos por cima.
    clips_cens = list(clips)
    cens_info = []
    cens_conferir = []  # painéis +18 que a visão liberou mesmo com score forte (vão pro meta)
    cens_ok = bool(censura) and acabamento
    if censura and not acabamento:
        log("  [!] Versão censurada exige o acabamento (HIPER_ACABAMENTO=1) — não será gerada")
    if cens_ok and cens_jobs:
        log(f"  Censura na imagem: {len(cens_jobs)} painéis +18...")
        for job in cens_jobs:
            nome = Path(job["panel"]).name
            cpanel = session_tmp / f"{Path(job['panel']).stem}_cens.jpg"
            try:
                nivel, det = censura_visual.censurar_imagem(job["panel"], cpanel, job["score"],
                                                            tipo=job["tipo"], texto_nsfw=job["texto"])
            except Exception as e:  # noqa: BLE001
                log(f"    [!] {nome}: censura falhou ({str(e)[:120]}) -> fosco")
                try:
                    censura_visual.censurar_fosco(job["panel"], cpanel)
                    nivel, det = "fosco", "fallback após erro"
                except Exception as e2:  # noqa: BLE001
                    log(f"    [X] {nome}: fosco também falhou ({str(e2)[:120]}) — censurado NÃO será gerado")
                    cens_ok = False
                    break
            if conferir_imagem_censurada(job["panel"], cpanel, nivel, job["score"]):
                # o mosaico não resolveu: vira fosco agora, antes de renderizar, e fica marcado
                # pro próximo render do capítulo já sair assim
                censura_visual.censurar_fosco(job["panel"], cpanel)
                censura_visual.forcar_fosco(job["panel"], "conferência da imagem censurada")
                nivel, det = "fosco", "mosaico não resolveu (conferência da imagem)"
            log(f"    {nome} -> {nivel} (score={job['score']:.2f}{', ' + det if det else ''})")
            if nivel == "intacto":
                # A visão manda (o Sightengine erra muito em manhwa: mão, casal vestido). Mas se o
                # score é de nudez forte, o painel fica marcado pra conferência na folha.
                if job["score"] >= censura_visual.LIMIAR_NSFW:
                    cens_conferir.append({"painel": nome, "clip": job["i"],
                                          "score": round(job["score"], 2), "motivo": det})
                    log(f"    [!] {nome}: score {job['score']:.2f} e saiu INTACTO — confira na folha")
                continue
            cclip = Path(str(job["clip"])[:-4] + "_cens.mp4")
            ok_c = job["fn"](cpanel, *job["antes"], cclip, job["i"], efx, **job["kw"])
            d0 = fx_acabamento.duracao(job["clip"])
            d1 = fx_acabamento.duracao(cclip) if ok_c and cclip.exists() else 0.0
            if abs(d0 - d1) > 0.05:
                log(f"    [X] {nome}: clip censurado com duração {d1:.2f}s != {d0:.2f}s — censurado NÃO será gerado")
                cens_ok = False
                break
            k = clips_cens.index(job["clip"])
            clips_cens[k] = cclip
            cens_info.append({"painel": nome, "clip": k, "nivel": nivel, "detalhe": det,
                              "score": round(job["score"], 2)})
        if cens_ok:
            log(f"  [OK] Censura na imagem: {len(cens_info)} clips trocados "
                f"({', '.join(f'{n}={sum(c['nivel'] == n for c in cens_info)}' for n in ('local', 'fosco', 'branco'))})")

    # 3. Concat com transições (xfade entre clips)
    slug = re.sub(r"[^a-z0-9]+", "-", titulo.lower().strip())[:60]
    ts = datetime.now().strftime("%Y%m%d_%H%M")

    # Pasta do capítulo: workspace/videos/<obra>/capNN/<idioma>/normal|censurado (nada solto na raiz).
    # Convenção: o vídeo novo tem o output_suffix e depois "_ULTIMO" no nome. Os anteriores só saem
    # depois que este fica pronto (_limpar_versoes_anteriores, no fim): se o render cair, o bom continua.
    destino = hp_paineis.pasta_video(panels_dir, idioma)
    dir_normal = destino / "normal" if destino != VIDEOS_DIR else destino
    dir_cens = destino / "censurado" if destino != VIDEOS_DIR else destino
    dir_normal.mkdir(parents=True, exist_ok=True)
    dir_cens.mkdir(parents=True, exist_ok=True)

    out_name = f"hipercool_{slug}_{ts}{output_suffix}_ULTIMO.mp4"
    out_mp4 = dir_normal / out_name
    out_cens = dir_cens / (out_mp4.stem.replace("_ULTIMO", "") + "_CENSURADO_ULTIMO.mp4")
    # pt: a versão NORMAL (sem censura, só pro dono assistir) sai UMA vez por capítulo. Render de revisão (o
    # capítulo já tem normal na pasta) faz só a censurada e não mexe na normal que existe (dono, 16/10).
    so_cens_pt = censura and not idioma and destino != VIDEOS_DIR and any(dir_normal.glob("*_NORMAL_ULTIMO.mp4"))
    if so_cens_pt:
        log("  pt: o capítulo já tem a versão normal — este render faz só a censurada")

    log(f"  Concatenando {len(clips)} clips com transições + SFX...")
    concat_mp4 = session_tmp / "_concat.mp4" if acabamento else out_mp4
    ok = effects_engine.concat_with_transitions(clips, concat_mp4, descriptions=descriptions)
    if not ok:
        log("[X] Concat falhou!")
        return None
    concat_cens = None
    if cens_ok and cens_info:
        concat_cens = session_tmp / "_concat_cens.mp4"
        if not effects_engine.concat_with_transitions(clips_cens, concat_cens, descriptions=descriptions):
            log("[X] Concat da versão censurada falhou — censurado NÃO será gerado")
            concat_cens, cens_ok = None, False

    # 3a. ACABAMENTO (porte do manhwa-react): editorial, tempo por palavra, SFX por
    # palavra/impacto, trilha nivelada + loudness, ASS, punch-in, upscale — 1 encode.
    # Se falhar, cai no fluxo antigo (trilha -> legenda PNG -> upscale) sem perder o vídeo.
    acab = None
    if acabamento:
        log("  Acabamento: editorial + tempo por palavra + sons + master + ASS + passe final...")
        try:
            acab = fx_acabamento.finalizar(concat_mp4, out_mp4, clips, clip_infos, recap, titulo,
                                           panels_dir, narration_cache_file, panel_files, session_tmp,
                                           legendas=subtitles, idioma=idioma,
                                           video_concat_cens=concat_cens,
                                           out_cens=out_cens if concat_cens else None,
                                           capa_info=capa_info, so_censurado=bool(idioma) or so_cens_pt,
                                           clips_censurados=[k for k, (a, b) in enumerate(zip(clips, clips_cens))
                                                             if a != b])
        except Exception as e:  # noqa: BLE001
            log(f"  [X] Acabamento falhou: {str(e)[:400]} -> fluxo antigo")
            import shutil
            shutil.copy2(concat_mp4, out_mp4)
        if acab:
            def _painel_do_clip(k):
                loc = clip_infos[k].get("loc") if k < len(clip_infos) else None
                return panel_files[loc] if loc is not None and loc < len(panel_files) else None
            for rel in (acab.get("validacao"), (acab.get("censurado") or {}).get("validacao")):
                fx_acabamento.descontar_pretos_da_arte(rel, acab.get("fronteiras"), _painel_do_clip)

    # 3b. Adicionar trilha sonora dinâmica (muda conforme clima)
    trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
    if acab:
        pass  # trilha já mixada (nivelada + ducking) pelo acabamento
    elif trilhas_dir.exists() and (trilhas_dir / "moods.json").exists():
        log("  Adicionando trilha dinâmica...")
        out_with_music = out_mp4.with_name(out_mp4.stem + "_music.mp4")
        effects_engine.add_dynamic_music(
            out_mp4, recap.get("locucoes", []), out_with_music,
            trilhas_dir, music_volume=0.08
        )
        if out_with_music.exists() and out_with_music.stat().st_size > 0:
            out_mp4.unlink()
            out_with_music.rename(out_mp4)
            log("  [OK] Trilha dinâmica adicionada")
    else:
        # Fallback: trilha única
        trilha_path = PROJECT_DIR / "workspace" / "assets" / "trilha.mp3"
        if trilha_path.exists():
            log("  Adicionando trilha sonora...")
            out_with_music = out_mp4.with_name(out_mp4.stem + "_music.mp4")
            effects_engine.add_background_music(out_mp4, trilha_path, out_with_music,
                                                music_volume=0.08)
            if out_with_music.exists() and out_with_music.stat().st_size > 0:
                out_mp4.unlink()
                out_with_music.rename(out_mp4)
                log("  [OK] Trilha adicionada")

    # 3c. Legendas queimadas estilo Shorts (Ponto F) — opcional via --subtitles
    # (com acabamento a legenda já saiu em ASS no passe final)
    if subtitles and clip_texts and not acab:
        log("  Gerando legendas (estilo Shorts)...")
        # Duração real de cada clip -> timing cumulativo das legendas
        entries = []
        for clip, txt in zip(clips, clip_texts):
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(clip)],
                    capture_output=True, text=True, timeout=10)
                dur = float(r.stdout.strip())
            except Exception:
                dur = 3.0
            entries.append((txt, dur))

        # Filtrar legendas: só narrador/narradora (falas de personagens já
        # estão nos balões do manhwa, legenda é redundante e tampa)
        narrator_entries = []
        t_cursor = 0.0
        for (txt, dur), persona in zip(entries, clip_personas):
            start = t_cursor
            t_cursor += dur
            pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip().lower()
            if pclean in ("narrador", "narradora") and txt.strip():
                narrator_entries.append((txt, dur, start))

        if narrator_entries:
            # Karaokê (palavra ativa amarela) ou estáticas (brancas)
            if hyperframes_karaoke:
                # MODO HYPERFRAMES: renderiza via Playwright/GSAP
                import render_karaoke
                log(f"  Karaokê HyperFrames (Playwright+GSAP)...")
                subs = []
                for idx, (txt, dur, start) in enumerate(narrator_entries):
                    webm_path = session_tmp / f"_hfk_{idx:03d}.webm"
                    result = render_karaoke.render_karaoke(
                        txt, str(webm_path), duration=dur,
                        width=1080, height=1920, font_size=65, stroke=8)
                    if result and Path(result).exists():
                        # Converter WebM -> overlay no vídeo principal
                        # O WebM do Playwright não tem canal alpha real (fundo sólido)
                        # Então usamos a mesma abordagem de overlay com timing
                        subs.append({"webm": str(result), "start": start,
                                     "end": start + dur})
                # Se tiver WebMs, sobrepor via ffmpeg (filter_complex com movie+overlay)
                if subs:
                    log(f"  Queimando {len(subs)} overlays karaokê HyperFrames...")
                    out_hfk = out_mp4.with_name(out_mp4.stem + "_hfk.mp4")
                    _burn_webm_overlays(out_mp4, subs, out_hfk)
                    if out_hfk.exists() and out_hfk.stat().st_size > 0:
                        out_mp4.unlink()
                        out_hfk.rename(out_mp4)
                        log(f"  [OK] Karaokê HyperFrames queimado ({len(subs)} frases)")
                    else:
                        log("  [!] HyperFrames karaokê falhou, mantendo vídeo sem karaokê")
                else:
                    log("  [!] Nenhum WebM de karaokê gerado")
                # O karaokê HyperFrames já foi queimado no vídeo (overlays webm).
                # Zera subs pra que name tags + watermark (PNG) sigam num burn_subtitles
                # limpo — senão os dicts {"webm":...} causam KeyError 'png'.
                subs = []
            elif karaoke:
                subs = effects_engine.render_subtitles_progressive(
                    [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                    offsets=[s for _, _, s in narrator_entries])
                log(f"  Karaokê: {len(subs)} PNGs gerados (limite 150)")
            else:
                subs = effects_engine.render_subtitles(
                    [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                    offsets=[s for _, _, s in narrator_entries])
        else:
            subs = []

        # Name tags: nome do personagem que fala (acima da legenda).
        # DESATIVADO por padrão (v6+): as personas vinham GENÉRICAS (Homem/Mulher/Colega)
        # e apareciam na tela como se fossem legenda — era pra ser info interna.
        # Reative com SHOW_NAME_TAGS=1 (idealmente só quando houver nomes reais).
        t_cursor = 0.0
        for (txt, dur), persona in zip(entries, clip_personas):
            if os.environ.get("SHOW_NAME_TAGS", "0") != "1":
                break
            start = t_cursor
            t_cursor += dur
            pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip()
            if (pclean and txt.strip()
                    and pclean.lower() not in ("narrador", "narradora", "narrator", "personagem")):
                npng = session_tmp / f"_name_{int(start*100):05d}.png"
                res = effects_engine.render_name_tag(pclean, npng)
                if res:
                    _, nx, ny = res
                    subs.append({"png": str(npng), "x": nx, "y": ny,
                                 "start": start, "end": min(start + dur, start + 1.8)})
        # Watermark do canal (fixo no topo) junto com as legendas
        if branding:
            total_dur = sum(d for _, d in entries)
            wm = effects_engine.render_watermark(WATERMARK_HANDLE, session_tmp, total_dur)
            if wm:
                subs.append(wm)
        out_subs = out_mp4.with_name(out_mp4.stem + "_subs.mp4")
        if subs and effects_engine.burn_subtitles(out_mp4, subs, out_subs):
            out_mp4.unlink()
            out_subs.rename(out_mp4)
            log(f"  [OK] Legendas + watermark queimados")
        else:
            log("  [!] Falha ao queimar legendas (mantendo vídeo sem legenda)")
        for s in subs:
            try:
                Path(s["png"]).unlink()
            except Exception:
                pass

    # 3c-bis. Upscale 720p -> 1080p (Full HD de entrega) — o acabamento já entrega 1080p
    if not acab:
        log("  Upscalando 720p -> 1080p...")
        upscaled = out_mp4.with_name(out_mp4.stem + "_hd.mp4")
        if effects_engine.upscale_to_fullhd(out_mp4, upscaled):
            out_mp4.unlink()
            upscaled.rename(out_mp4)
            log(f"  [OK] Upscale 720->1080p feito")
        else:
            log("  [!] Upscale falhou (mantendo 720p)")

    # outra língua com censura: o acabamento nem gera o normal (só a censurada)
    size_mb = out_mp4.stat().st_size / (1024 * 1024) if out_mp4.exists() else 0.0
    if out_mp4.exists():
        log(f"  vídeo normal: {out_mp4.name} ({size_mb:.1f} MB)")

    # Salvar meta
    meta = {
        "titulo": titulo,
        "titulo_video": recap.get("titulo_video", titulo),
        "tags": recap.get("tags", []),
        "panels_count": len(clips),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file": out_name,
        "size_mb": round(size_mb, 1),
        "idioma": idioma or "pt",
        # painel de cada clip (None = abertura/meme/cartão): a análise do vídeo pronto (revisao_video) usa
        # com acabamento.fronteiras pra dizer QUAL painel apareceu sem censura e forçar o fosco nele
        "clip_paineis": [panel_files[ci["loc"]].name if ci.get("loc") is not None and ci["loc"] < len(panel_files)
                         else None for ci in clip_infos],
    }
    if acab:
        meta["acabamento"] = acab
    meta_path = out_mp4.with_suffix(".meta.json")
    if out_mp4.exists():
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3d. Versão CENSURADA (a do YouTube): montada no acabamento com os clips +18 trocados.
    # O meta dela registra o que foi censurado e onde (postar_hipercool exige isso).
    if censura and acab and cens_ok:
        import shutil
        if cens_info:
            val_c = (acab.get("censurado") or {}).get("validacao")
        else:
            shutil.copy2(out_mp4, out_cens)  # nenhum painel precisou de censura
            val_c = acab.get("validacao")
        if out_cens.exists() and val_c is not None:
            offs, durs = acab.get("fronteiras", []), acab.get("duracoes", [])
            meta_c = json.loads(json.dumps(meta))
            meta_c["file"] = out_cens.name
            meta_c["size_mb"] = round(out_cens.stat().st_size / (1024 * 1024), 1)
            meta_c["acabamento"].pop("censurado", None)
            meta_c["acabamento"]["validacao"] = val_c
            limpos = [p for k, p in enumerate(panel_files) if k not in cens_det]
            texto_capa = (acab.get("editorial") or {}).get("gancho") or meta["titulo_video"]
            capa_c = fx_acabamento.gerar_capa(limpos or panel_files, texto_capa,
                                              fx_acabamento._obra_e_cap(titulo, panels_dir)[1],
                                              out_cens.with_suffix(".capa.jpg"), info=capa_info)
            meta_c["acabamento"]["capa"] = str(capa_c) if capa_c else None
            meta_c["censura"] = {
                "metodo": "imagem-local",
                "detector": cens_origens,
                "paineis": cens_info,
                "janelas": [[offs[ci["clip"]], offs[ci["clip"]] + durs[ci["clip"]]]
                            for ci in cens_info if ci["clip"] < len(offs)],
                # score de nudez forte que a visão liberou: ninguém censurou, olhe na folha
                "conferir": cens_conferir,
            }
            out_cens.with_suffix(".meta.json").write_text(
                json.dumps(meta_c, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"  [OK] Versão censurada: {out_cens.name} ({len(cens_info)} painéis censurados na imagem)")
        else:
            log("  [X] Versão censurada não foi gerada")

    # 4. Notify
    if not skip_notify and out_mp4.exists():
        log("  Enviando pro Telegram...")
        caption = (
            f"🎬 {_tg_safe.b(recap.get('titulo_video', titulo))}\n"
            f"📊 {len(clips)} painéis | {size_mb:.1f} MB\n"
            f"🏷 {', '.join(recap.get('tags', [])[:5])}"
        )
        _tg_safe.send_video(str(out_mp4), caption=caption)

    # Outra língua: só a censurada fica (o dono não quer a versão sem censura nos idiomas). A fila lê
    # o caminho (relativo a workspace/videos) desta linha "[OK] Vídeo final".
    final = out_mp4
    if (idioma or so_cens_pt) and out_cens.exists() and out_cens.with_suffix(".meta.json").exists():
        for ext in (".mp4", ".meta.json", ".capa.jpg"):  # sobra do normal deste render (se houve)
            out_mp4.with_suffix(ext).unlink(missing_ok=True)
        final = out_cens
    shutil.rmtree(session_tmp, ignore_errors=True)
    if not final.exists():
        log("[X] Nenhum vídeo final: a censurada falhou e o normal não foi produzido (outra língua)")
        return None
    if destino != VIDEOS_DIR:  # na raiz antiga (junction) nada de apagar nem rmdir
        # cada pasta só perde as anteriores se a versão nova dela saiu completa (outra língua: normal não sai)
        cens_nova = out_cens.with_suffix(".meta.json").exists()
        # a pasta normal só perde as anteriores se saiu normal nova (outra língua: a censurada substitui a normal; pt
        # só-censurada: a normal que existe FICA — é a única que o dono quer)
        normal_nova = out_mp4.with_suffix(".meta.json").exists() or (final == out_cens and bool(idioma))
        novas = ((dir_normal, normal_nova), (dir_cens, cens_nova))
        _limpar_versoes_anteriores([d for d, ok in novas if ok], output_suffix, (out_mp4, out_cens))
        for d in (dir_normal, dir_cens):
            try:
                d.rmdir()  # só se ficou vazia (outra língua não tem normal)
            except OSError:
                pass
    try:
        rel = final.relative_to(VIDEOS_DIR)
    except ValueError:
        rel = final
    log(f"  [OK] Vídeo final: {rel} ({final.stat().st_size / (1024 * 1024):.1f} MB)")
    return final


def run_batch(urls, args):
    """Processa vários capítulos em sequência (Ponto K), com retomada.

    Salva progresso em workspace/batch_progress.json. URLs já concluídas com
    sucesso são puladas em execuções seguintes (retoma após queda). Uma falha
    num capítulo NÃO interrompe o lote — registra e segue pro próximo.
    """
    import importlib.util
    fetcher_path = Path(__file__).resolve().parent / "hiper-fetcher.py"
    spec = importlib.util.spec_from_file_location("hiper_fetcher", fetcher_path)
    hiper_fetcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hiper_fetcher)

    progress_file = PROJECT_DIR / "workspace" / "batch_progress.json"
    try:
        progress = json.loads(progress_file.read_text()) if progress_file.exists() else {}
    except Exception:
        progress = {}

    total = len(urls)
    log(f"═══ LOTE: {total} capítulos ═══")
    done, failed, skipped = 0, 0, 0

    for idx, url in enumerate(urls, start=1):
        if progress.get(url, {}).get("status") == "done":
            log(f"[{idx}/{total}] ⏭  já concluído, pulando: {url}")
            skipped += 1
            continue

        slug = hiper_fetcher.slugify(url.split("/")[-1] or url.split("/")[-2] or "chapter")
        # Título por capítulo: base + sufixo do slug (ex: "... cap 3")
        cap_titulo = f"{args.titulo} — {slug}" if total > 1 else args.titulo
        log(f"[{idx}/{total}] ▶ {url}")

        try:
            panels = hiper_fetcher.fetch_chapter(url, slug, headed=args.headed)
            if not panels:
                raise RuntimeError("scrape retornou vazio")

            result = run_pipeline(
                panels, cap_titulo,
                max_panels=args.max_panels,
                skip_notify=args.skip_notify,
                dry_run=args.dry_run,
                animated=args.animated,
                start_panel=args.start_panel,
                skip_credits=args.skip_credits,
                fusao=args.fusao,
                narrator_gender=args.narrator_gender,
                subtitles=args.subtitles,
                branding=args.branding,
                karaoke=args.karaoke,
                censura=args.censura,
                force_llm=args.force_llm,
                force_tts=args.force_tts,
                hyperframes_karaoke=args.hyperframes_karaoke,
                output_suffix=args.output_suffix,
                acabamento=args.acabamento,
                skip_final=args.skip_final,
            )
            if result:
                progress[url] = {"status": "done", "file": str(result),
                                 "at": datetime.now(timezone.utc).isoformat()}
                done += 1
                log(f"[{idx}/{total}] [OK] pronto: {Path(result).name}")
            else:
                raise RuntimeError("pipeline retornou None")
        except Exception as e:
            progress[url] = {"status": "failed", "error": str(e),
                             "at": datetime.now(timezone.utc).isoformat()}
            failed += 1
            log(f"[{idx}/{total}] [X] falhou: {e}")

        # Salva progresso após CADA capítulo (retomável)
        try:
            progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
        except Exception:
            pass

    log(f"═══ LOTE FIM: {done} ok, {failed} falhas, {skipped} pulados ═══")
    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Pipeline de vídeo hipercool")
    parser.add_argument("--url", help="URL do capítulo (scrape + pipeline)")
    parser.add_argument("--slug", help="Slug de capítulo já no cache")
    parser.add_argument("--panels-dir", help="Diretório com painéis já cortados")
    parser.add_argument("--titulo", "-t", required=True, help="Título do manhwa/capítulo")
    parser.add_argument("--max-panels", type=int, default=MAX_PANELS_DEFAULT,
                        help=f"Máximo de painéis (default: {MAX_PANELS_DEFAULT})")
    parser.add_argument("--start-panel", type=int, default=0,
                        help="Offset de início (parte 2+ do capítulo; ex: 55)")
    parser.add_argument("--skip-credits", type=int, default=1,
                        help="Pula os N primeiros painéis (créditos/capa). 0 = mantém todos")
    parser.add_argument("--skip-notify", action="store_true",
                        help="Não enviar notificação Telegram")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria feito sem executar")
    parser.add_argument("--animated", action="store_true",
                        help="Usa modo animado (breathing/parallax) nos painéis")
    parser.add_argument("--fusao", action="store_true",
                        help="TESTE: funde visão+narração numa só chamada Gemini")
    parser.add_argument("--narrator-gender", choices=["M", "F"], default="F",
                        help="Gênero da narradora off (default F)")
    parser.add_argument("--subtitles", action="store_true",
                        help="Queima legendas estilo Shorts no vídeo")
    parser.add_argument("--karaoke", action="store_true",
                        help="Legendas progressivas (palavra ativa destacada). Requer --subtitles")
    parser.add_argument("--no-branding", dest="branding", action="store_false",
                        help="Desliga intro/outro (CTA inscreva-se)")
    parser.add_argument("--censura", action="store_true",
                        help="Gera também a versão censurada pro YouTube (mosaico só nas partes "
                             "explícitas dos painéis +18; legendas nítidas por cima)")
    parser.add_argument("--headed", action="store_true",
                        help="Browser visível (se usar --url)")
    # Ponto K: lote multi-capítulo
    parser.add_argument("--urls", nargs="+", metavar="URL",
                        help="Lote: várias URLs de capítulos processadas em sequência")
    parser.add_argument("--batch-file", metavar="ARQUIVO",
                        help="Lote: arquivo de texto com 1 URL por linha (# = comentário)")
    # Flags de rebuild/cache
    parser.add_argument("--force-llm", action="store_true",
                        help="Ignora narration_cache, força nova geração de narração via LLM")
    parser.add_argument("--force-tts", action="store_true",
                        help="Ignora tts_cache, força nova geração de áudio TTS")
    parser.add_argument("--hyperframes-karaoke", action="store_true",
                        help="Usa render_karaoke.py (Playwright) para legendas HyperFrames")
    parser.add_argument("--audio-only", action="store_true",
                        help="Só gera narração+TTS (enche os caches) e PARA antes do ffmpeg. Fase serial da fábrica de áudio.")
    parser.add_argument("--output-suffix", default="",
                        help="Sufixo no nome do vídeo final (ex: _NORMAL, _HYPERFRAMES)")
    parser.add_argument("--skip-final", type=int, default=0,
                        help="Descarta os N últimos painéis (propaganda do grupo de scan no fim do capítulo)")
    parser.add_argument("--idioma", choices=["hi", "id", "it", "ru", "th", "vi", "fr", "en"], default=None,
                        help="Versão em outra língua (bin/idiomas.py): traduz o roteiro do pt em cache, voz edge-tts")
    parser.add_argument("--no-acabamento", dest="acabamento", action="store_false", default=None,
                        help="Desliga o acabamento (fx_acabamento) e usa o fluxo antigo: intro/outro, "
                             "legenda PNG, trilha simples e upscale separado")

    args = parser.parse_args()

    # ── Modo LOTE (Ponto K) ────────────────────────────────────────────────
    batch_urls = []
    if args.urls:
        batch_urls = list(args.urls)
    elif args.batch_file:
        bf = Path(args.batch_file)
        if not bf.is_file():
            print(f"ERRO: batch-file '{bf}' não existe", file=sys.stderr)
            sys.exit(1)
        for line in bf.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                batch_urls.append(line)

    if batch_urls:
        run_batch(batch_urls, args)
        return

    # Determinar source dos painéis
    panels_dir = None

    if args.panels_dir:
        panels_dir = Path(args.panels_dir)
        if not panels_dir.is_dir():
            print(f"ERRO: {panels_dir} não existe", file=sys.stderr)
            sys.exit(1)

    elif args.slug:
        cache_path = CACHE_DIR / args.slug
        if not cache_path.is_dir():
            print(f"ERRO: slug '{args.slug}' não encontrado no cache", file=sys.stderr)
            sys.exit(1)
        panels_dir = cache_path

    elif args.url:
        # Importar fetcher (mesmo diretório bin/)
        import importlib.util
        fetcher_path = Path(__file__).resolve().parent / "hiper-fetcher.py"
        spec = importlib.util.spec_from_file_location("hiper_fetcher", fetcher_path)
        hiper_fetcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hiper_fetcher)

        slug = args.slug or hiper_fetcher.slugify(args.url.split("/")[-1] or "chapter")
        result = hiper_fetcher.fetch_chapter(args.url, slug, headed=args.headed)
        if not result:
            print("ERRO: Falha ao baixar capítulo", file=sys.stderr)
            sys.exit(1)
        panels_dir = result

    else:
        print("ERRO: forneça --url, --slug, ou --panels-dir", file=sys.stderr)
        sys.exit(1)

    result = run_pipeline(
        panels_dir, args.titulo,
        max_panels=args.max_panels,
        skip_notify=args.skip_notify,
        dry_run=args.dry_run,
        animated=args.animated,
        start_panel=args.start_panel,
        skip_credits=args.skip_credits,
        fusao=args.fusao,
        narrator_gender=args.narrator_gender,
        subtitles=args.subtitles,
        branding=args.branding,
        karaoke=args.karaoke,
        censura=args.censura,
        force_llm=args.force_llm,
        force_tts=args.force_tts,
        hyperframes_karaoke=args.hyperframes_karaoke,
        output_suffix=args.output_suffix,
        audio_only=args.audio_only,
        acabamento=args.acabamento,
        skip_final=args.skip_final,
        idioma=args.idioma,
    )

    if result:
        print(f"\n[OK] Vídeo pronto: {result}")
    elif not args.dry_run:
        print("\n[X] Pipeline falhou.", file=sys.stderr)
        sys.exit(1)


def _vez_na_fila():
    """Vez na fila de render ENTRE PROJETOS (D:\\video-fila, pedido do dono 17/10: "uma filinha pros projetos não
    se atrapalharem"; às 7h o PC tinha 1,1 GB de RAM livre com 4 renders juntos). Hipercool tem prioridade 1.
    Fila indisponível = segue sem esperar (o fila_render já trata isso)."""
    import contextlib
    try:
        sys.path.insert(0, r"D:\video-fila")
        import fila_render
        alvo = sys.argv[sys.argv.index("--panels-dir") + 1] if "--panels-dir" in sys.argv else "?"
        idioma = sys.argv[sys.argv.index("--idioma") + 1] if "--idioma" in sys.argv else "pt"
        return fila_render.vez("hipercool", f"{Path(alvo).name} {idioma}")
    except Exception:  # noqa: BLE001
        return contextlib.nullcontext()


if __name__ == "__main__":
    with _vez_na_fila():
        main()

