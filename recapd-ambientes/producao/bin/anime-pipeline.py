"""anime-pipeline.py — orquestrador do recap de anime descaracterizado.

Só amarra as peças (cada uma num módulo pequeno):
  anime_tts.py      → narração
  anime_probe.py    → duração de mídia
  anime_segments.py → corte+descaracterização dos clipes
  anime_captions.py → legenda queimada (PNG overlay)
  fx_clips.py       → concat final (reuso do motor hipercool)

IMPORTANTE — orientação por PROCESSO:
  O motor (fx_assets) decide W/H no IMPORT, lendo ANIME_ORIENT. Por isso cada
  formato roda num subprocesso próprio: o dispatcher (main) só dispara; o
  trabalho pesado roda em run_one(), que importa o motor já na orientação certa.

Uso:
  python anime-pipeline.py --video-source anime.mp4 --script roteiro.txt
  python anime-pipeline.py ... --formato deitado   # só 16:9
  python anime-pipeline.py ... --formato short     # só 9:16
"""
import sys
import os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
import logging
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                    ])
_stream_handler = logging.root.handlers[0]
try:
    _stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Formato → (orientação do motor, nome do arquivo final)
_FORMATS = {
    "deitado": ("landscape", "final_anime_deitado.mp4"),
    "short":   ("vertical",  "final_anime_short.mp4"),
}


def parse_txt_script(script_path):
    """Lê o roteiro .txt (1 frase por linha) e devolve a lista de frases não-vazias.
    Cada frase vira um clipe: é narrada (TTS) e mapeada sobre uma fatia do vídeo."""
    with open(script_path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def run_one(video_path, script_path, orient, out_name, max_panels):
    """Gera UM formato. Roda num processo onde ANIME_ORIENT já está setado
    ANTES de importar o motor, então W/H nascem na orientação certa."""
    # imports pesados aqui dentro (pós-ANIME_ORIENT), não no topo do módulo.
    from anime_segments import build_segments
    from anime_captions import burn_captions
    from fx_clips import concat_with_xfade

    workspace = Path(video_path).parent
    lines = parse_txt_script(script_path)
    if max_panels > 0:
        lines = lines[:max_panels]
    if not lines:
        logging.error("Script vazio")
        return False

    # Áudio TTS COMPARTILHADO entre as orientações (gera 1x, reusa).
    audio_dir = workspace / "audio_cache"
    clip_dir = workspace / f"clipes_{orient}"

    if orient == "vertical":
        # 22/10 (dono: "os pequenos cortes entre as palavras deixam mais dinâmico — bom pros CURTOS, não pros
        # longos"): no Short o respiro entre falas cai de 0,5 s pra 0,2 s (teto 0,6 s) = ritmo de jump cut.
        # Só default: CLIP_GAP_S/CLIP_GAP_MAX setados por fora continuam mandando. O deitado segue 0,5/1,2.
        # 22/10 (tarde): com os MICROCORTES da fala (anime_segments._fala_do_short) cada fala já sai com 0,035 s de
        # folga em cada ponta = 0,07 s entre as falas (o que o dono aprovou); respiro fixo por cima desfaria o corte.
        # O gap ainda cresce pra caber SFX (dinâmico, teto CLIP_GAP_MAX).
        os.environ.setdefault("CLIP_GAP_S", "0")
        os.environ.setdefault("CLIP_GAP_MAX", "0.6")
    tempos = None  # segundo do original de cada frase (roteiro curto com tempo, 21/10)
    try:
        arq_t = Path(script_path).with_name("roteiro_tempos.json")
        if arq_t.exists():
            t = json.loads(arq_t.read_text(encoding="utf-8"))
            tempos = t if isinstance(t, list) and len(t) >= len(lines) else None
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[{orient}] tempos do roteiro ilegíveis ({e}) — frases espalhadas pelo original")
    if orient == "landscape":
        lines, tempos = _cta_longo(lines, tempos, Path(video_path).parent.name)
        lines, tempos = _resumo_longo(lines, tempos, workspace, video_path)  # depois do CTA: o "depois da frase 4" segue na história
        lines, tempos = _ganchos_longo(lines, tempos, workspace)
        lines, tempos = _falas_personagem(lines, tempos, workspace)
        _marcar_falas_mascote(lines)
    clips, entries, sfx_durs, word_times = build_segments(video_path, lines, clip_dir,
                                    audio_dir=audio_dir, orient=orient, tempos=tempos)
    if not clips:
        logging.error(f"[{orient}] nenhum clipe gerado")
        return False

    logging.info(f"[{orient}] concatenando {len(clips)} clipes...")
    concat_out = str(workspace / f"_semlegenda_{orient}.mp4")
    # 28/10: memes abrindo uma brecha no resumo de abertura — entram só no concat; as posições deles saem dos offsets
    # (legenda/capítulos/mascote seguem alinhados às frases)
    _ENTRIES_TEXTO[:] = [e[0] for e in entries] if len(entries) == len(clips) else []
    para_concat, sfx_concat, memes_idx = (_memes_resumo(clips, sfx_durs, workspace) if orient == "landscape"
                                          else (clips, sfx_durs, set()))
    concat_with_xfade(para_concat, concat_out, clip_sfx_dur=sfx_concat,
                      clip_texts=["" if k in memes_idx else "fala" for k in range(len(para_concat))] if memes_idx else None)

    # Offsets ABSOLUTOS de início de cada clipe no vídeo concatenado. O xfade
    # comprime o tempo de forma NÃO-linear (só nas fronteiras fala→fala), então
    # somar durações "desanda" a legenda ~30s ao longo de 1h. Estes offsets vêm
    # medidos por ffprobe dentro do concat e sincronizam a legenda com o vídeo.
    import fx_clips
    offsets = list(getattr(fx_clips, "_CLIP_ABS_STARTS", []) or [])
    if memes_idx and len(offsets) == len(para_concat):
        offsets = [o for k, o in enumerate(offsets) if k not in memes_idx]
    if len(offsets) != len(clips):
        logging.warning(f"[{orient}] offsets ({len(offsets)}) != clips ({len(clips)}) "
                        "— legenda cai na estimativa por duração")
        offsets = None
    if orient == "landscape" and Path(concat_out).exists() and Path(concat_out).stat().st_size > 10 ** 6:
        # 31/10: SNhb31 morreu com "No space left on device" na música (Kaggle ~20 GB) e o 4wuf chegou na legenda com
        # 1,4 GB livres — em 1080p o final fica ~2x maior. Depois do concat os trechos não servem mais: apaga já.
        import shutil
        livre = shutil.disk_usage(str(workspace)).free / 1e9
        shutil.rmtree(clip_dir, ignore_errors=True)
        for lixo in Path(workspace).glob("_meme_resumo_*.mp4"):
            lixo.unlink(missing_ok=True)
        logging.info(f"[{orient}] disco depois do concat: {livre:.1f} -> "
                     f"{shutil.disk_usage(str(workspace)).free / 1e9:.1f} GB livres (trechos apagados)")

    # -- Integração de Música Dinâmica --
    # Independência TOTAL: usa SÓ as trilhas do próprio projeto
    # (workspace/assets/trilhas, que é junction pro hub compartilhado
    # hipercool-materiais — a única pasta externa permitida). Sem fallback pra
    # outras pastas hipercool: apagar qualquer uma delas não quebra o recap.
    _trilhas_dir = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "trilhas"
    if _trilhas_dir.exists() and (_trilhas_dir / "moods.json").exists():
        import effects_engine
        
        # Mapeamos o texto para o formato que add_dynamic_music gosta 
        # (lista de descrições para inferir o mood). 
        # No formato antigo era recap["locucoes"].
        # chave "text": é a que o add_dynamic_music lê ("texto" deixava todo bloco vazio → clima nunca detectado; 16/10)
        mock_locucoes = [{"text": e[0]} for e in entries]
        
        logging.info(f"[{orient}] queimando música dinâmica...")
        concat_music = str(workspace / f"_semlegenda_music_{orient}.mp4")
        # 29/10 dona (longo): "às vezes a voz fica baixa e a trilha sobe, não dá pra ouvir — baixar a trilha um pouco
        # mais de forma geral" — 0,18 → 0,10 só no deitado (o Short dos Cortes segue como estava)
        effects_engine.add_dynamic_music(Path(concat_out), mock_locucoes, Path(concat_music),
                                         _trilhas_dir, music_volume=0.10 if orient == "landscape" else 0.18,
                                         no_copyright=True)  # dona 01/11: Naruto/JJBA/Pokémon (copyright_risk) fora
                                         
        if Path(concat_music).exists():
            Path(concat_out).unlink()
            Path(concat_music).rename(concat_out)

    final_out = str(workspace / out_name)
    # Gancho na tela nos 1os ~3 s + barra de progresso (padrão do hipercool, 16/10): o recap abre com a frase
    # que prende escrita no topo. Sem gancho (LLM fora) a barra entra do mesmo jeito.
    gancho = ""
    if os.environ.get("ANIME_GANCHO", "1") == "1":
        import anime_gancho
        gancho = anime_gancho.gerar_gancho([e[0] for e in entries])
        logging.info(f"[{orient}] gancho: {gancho or '(sem)'}")
    # Capítulos do longo ANTES da legenda: servem à descrição (capitulos.json) e à tarja, que entra na mesma passada.
    caps = None
    # 12/11 dona ("compilado da série: parte 1+2, depois 1+2+3, cortando os resumos e deixando só o primeiro"): grava
    # onde termina o resumo de abertura (1º segundo da história) pra compilar_serie.py cortar sem reencodar.
    try:
        n_res_ = int(os.environ.get("ANIME_RESUMO_N") or 0)
        if orient == "landscape" and offsets and 0 < n_res_ < len(offsets):
            (Path(workspace) / "resumo_fim.json").write_text(json.dumps({"resumo_fim_s": float(offsets[n_res_]),
                                                                       "frases": n_res_}), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if orient == "landscape" and offsets and len(entries) >= 40:
        try:
            caps = _capitulos(entries, offsets, workspace)
        except Exception as e:  # noqa: BLE001 — capítulo é acabamento; nunca derruba o vídeo
            logging.warning(f"[longo] capítulos não saíram ({type(e).__name__}: {e})")
    # Fonte COM legenda queimada (ANIME_HARDSUB_RECT, só quando a detecção achou): tarja branca com o capítulo por cima
    # da legenda deles, como nos Cortes (dona 25/10), e a nossa legenda logo acima dela. Sem capítulo = só o borrão.
    tarja = None
    rect = os.environ.get("ANIME_HARDSUB_RECT", "").strip()
    if orient == "landscape" and rect and caps:
        try:
            import anime_tarja_capitulo
            placa = anime_tarja_capitulo.placa(rect)
            tarja = anime_tarja_capitulo.extras(caps, placa)
            centro = anime_tarja_capitulo.centro_legenda(placa)
            if centro and "SUB_Y_CENTER" not in os.environ:
                os.environ["SUB_Y_CENTER"] = str(centro)
            logging.info(f"[longo] tarja de capítulo na faixa {placa}; nossa legenda em {centro or 'lugar de sempre'}")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] tarja não montada ({type(e).__name__}: {e}) — fica só o borrão")
    if orient == "landscape" and offsets and caps:
        _mascote_longo(concat_out, entries, offsets, caps, workspace)
    logging.info(f"[{orient}] queimando legendas...")
    # 23/10: formato com várias vozes = cor/nome de quem fala (None no Short solo = legenda igual à de sempre)
    import anime_segments
    falantes = anime_segments.ULTIMOS_FALANTES
    if falantes is not None and len(falantes) != len(entries):
        falantes = None
    # 04/11 (dona, item 3): no longo deitado o master -14 LUFS vai na junção das fatias da legenda (mesma reescrita do
    # arquivo) em vez de uma passada à parte; sem fatias/medida falhou = master separado como antes (abaixo)
    import fx_subtitles as _fxs
    _fxs.ULTIMO_MASTER = None
    if orient == "landscape":
        os.environ["ANIME_MASTER_NA_JUNCAO"] = "1"
    ok_leg = burn_captions(concat_out, entries, final_out, orient=orient,
                           word_times=word_times, offsets=offsets, gancho=gancho, falantes=falantes, tarja=tarja)
    os.environ.pop("ANIME_MASTER_NA_JUNCAO", None)
    if not ok_leg and orient == "vertical":
        # 30/10: 5 Shorts saíram sem legenda/gancho/barra (falta de RAM na queima); com delogo a legenda deles já foi
        # apagada = vídeo sem nenhum texto. Espera RAM e tenta 1x; se falhar de novo, o Short não sai.
        logging.warning(f"[{orient}] legenda falhou — espero RAM e tento de novo")
        try:
            fx_clips._wait_for_ram(min_mb=1500, max_wait_s=900)
        except Exception:  # noqa: BLE001
            pass
        ok_leg = burn_captions(concat_out, entries, final_out, orient=orient,
                               word_times=word_times, offsets=offsets, gancho=gancho, falantes=falantes, tarja=tarja)
        if not ok_leg:
            logging.error(f"[{orient}] legenda falhou de novo — Short sem legenda não sai")
            return False
    if not ok_leg:
        logging.warning(f"[{orient}] legenda falhou — usando sem legenda")
        import shutil
        shutil.copy2(concat_out, final_out)

    cortes_feitos = False
    if orient == "landscape" and ok_leg and offsets and len(entries) >= 40 and Path(concat_out).exists() \
            and os.environ.get("ANIME_CORTES_VERTICAL", "1") != "0":
        # 02/11 (dona: "a legenda MIX e os cartões nos cortes dos longos também"): o corte saía do vídeo JÁ legendado
        # (16:9 encolhido no meio do 9:16 = legenda e cartões miúdos). Agora sai do vídeo SEM legenda, em pé, e cada
        # corte ganha a legenda MIX/cartões/efeitos do formato em pé (melhores_cortes.legendar). Antes de apagar o
        # vídeo sem legenda (logo abaixo).
        try:
            import melhores_cortes
            cta = {int(x) for x in os.environ.get("ANIME_MASCOTE_FALAS", "").split(",") if x.strip().isdigit()}
            melhores_cortes.gerar(concat_out, [e[0] for e in entries], offsets, workspace,
                                  pular=int(os.environ.get("ANIME_RESUMO_N", "0") or 0), proibidas=cta,
                                  word_times=word_times)
            cortes_feitos = True
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[cortes] vertical com legenda própria falhou ({type(e).__name__}: {e}) — vai o antigo")
    if orient == "landscape" and Path(final_out).exists():
        # 30/10 (Fable): no Pastor (1030 trechos) o master e os 5 cortes deram "Conversion failed" ao FECHAR o arquivo —
        # disco do Kaggle cheio (trechos + vídeo sem legenda + final + cópia nova). Com a legenda queimada, os trechos
        # e o vídeo sem legenda não servem mais: apaga antes do master/cortes. O áudio da fala (audio_cache) fica.
        import shutil
        livre_antes = shutil.disk_usage(str(workspace)).free / 1e9
        shutil.rmtree(clip_dir, ignore_errors=True)
        for lixo in [Path(concat_out), *Path(workspace).glob("_meme_resumo_*.mp4"), *Path(workspace).glob("_reacao_*.wav")]:
            try:
                lixo.unlink()
            except OSError:
                pass
        logging.info(f"[{orient}] disco: {livre_antes:.1f} GB livres -> {shutil.disk_usage(str(workspace)).free / 1e9:.1f} GB "
                     "(trechos e vídeo sem legenda apagados antes do master)")

    # Master -14 LUFS / -1 dBTP (padrão do hipercool, 16/10): o mix sai ~-25 LUFS e o YouTube só abaixa, nunca
    # sobe. Duas passadas, vídeo copiado. Falhou = fica o mix sem master (não perde o vídeo).
    m_junc = getattr(_fxs, "ULTIMO_MASTER", None) if ok_leg and orient == "landscape" else None
    if m_junc:  # master já feito na junção das fatias: sem a passada separada
        nivel = float(m_junc.get("input_i"))
        if nivel < -23:
            logging.warning(f"[{orient}] mix baixo ({nivel} LUFS): conferir se a narração saiu")
        logging.info(f"[{orient}] master: {m_junc.get('input_i')} LUFS -> -14 (na junção da legenda)")
    try:
        if m_junc:
            raise _MasterFeito
        import master_loudness as ML
        m = ML.measure_pass(final_out, -14.0, -1.0)
        # 20/10: 238 Shorts bons entraram aqui entre -17,5 e -20,8 LUFS; os 9 de narração muda, de -23,7 a -30,4
        # (só trilha). Vertical abaixo de -23 não sai; nos outros formatos ainda não há medida, só avisa.
        nivel = float(m.get("input_i"))
        if nivel < -23:
            if orient == "vertical":
                logging.error(f"[{orient}] NARRAÇÃO MUDA: mix em {nivel} LUFS (normal -17 a -21) — vídeo não sai")
                return False
            logging.warning(f"[{orient}] mix baixo ({nivel} LUFS): conferir se a narração saiu")
        mastered = str(workspace / f"_master_{orient}.mp4")
        ML.apply_pass(final_out, mastered, -14.0, -1.0, m)
        if Path(mastered).exists() and Path(mastered).stat().st_size > 10000:
            Path(mastered).replace(final_out)
            logging.info(f"[{orient}] master: {m.get('input_i')} LUFS -> -14")
    except _MasterFeito:
        pass
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[{orient}] master falhou ({type(e).__name__}: {e}) — segue sem master")

    _garantir_1080(final_out, workspace)
    if orient == "vertical":
        _teto_short(final_out, workspace)
    elif offsets and len(entries) >= 40 and not cortes_feitos:
        # 28/10 dona: os melhores trechos do longo viram Shorts pros canais de cortes (fora o resumo e os CTAs dela)
        import melhores_cortes
        cta = {int(x) for x in os.environ.get("ANIME_MASCOTE_FALAS", "").split(",") if x.strip().isdigit()}
        melhores_cortes.gerar(final_out, [e[0] for e in entries], offsets, workspace,
                              pular=int(os.environ.get("ANIME_RESUMO_N", "0") or 0), proibidas=cta)
    if orient == "landscape":
        _tempo_diferente_do_original(final_out, video_path, workspace)

    logging.info(f"[{orient}] PRONTO: {final_out}")
    return True


# 02/11 dona: "nenhum anime ou manhwa pode ter exatamente o mesmo tempo do original — nem que seja um minuto a mais ou a
# menos, mas nunca o mesmo (o 2jtdp4vB1WQ saiu assim); esses o YouTube não veicula bem". Final a menos de DIF_MIN_S do
# original = muda a velocidade (imagem + voz, tom mantido) o MÍNIMO pra abrir DIF_MIN_S, até VEL_MAX (5%). Roda depois
# dos cortes (que usam os tempos originais) e reescala os capítulos da descrição junto.
DIF_MIN_S = 90.0
VEL_MAX = 0.05


def _tempo_diferente_do_original(final_out, video_path, workspace):
    def _dur(a):
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     str(a)], capture_output=True, text=True, timeout=60).stdout.strip())
    try:
        src, fin = _dur(video_path), _dur(final_out)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[tempo] não deu pra medir original/final ({type(e).__name__}) — sem conferência")
        return
    if abs(fin - src) >= DIF_MIN_S:
        logging.info(f"[tempo] final {fin / 60:.1f} min x original {src / 60:.1f} min — diferença ok")
        return
    # f > 1 acelera (fica src - DIF), f < 1 desacelera (fica src + DIF): vale a menor mudança
    f = min((fin / (src - DIF_MIN_S), fin / (src + DIF_MIN_S)), key=lambda x: abs(x - 1))
    if abs(f - 1) > VEL_MAX:
        logging.warning(f"[tempo] final {fin:.0f}s quase igual ao original {src:.0f}s, mas precisaria {f:.3f}x — deixado")
        return
    tmp = Path(workspace) / "_tempo_dif.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(final_out),
                        "-filter_complex", f"[0:v]setpts=PTS/{f:.5f}[v];[0:a]atempo={f:.5f}[a]",
                        "-map", "[v]", "-map", "[a]", "-r", "30" if os.environ.get("ANIME_60FPS") == "0" else "60",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-g", "60",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                        str(tmp)], capture_output=True, text=True, timeout=7200)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 10000:
        logging.warning(f"[tempo] ajuste falhou ({(r.stderr or '')[-200:]}) — segue com {fin:.0f}s")
        return
    tmp.replace(final_out)
    cap = Path(workspace) / "capitulos.json"
    try:
        if cap.exists():
            c = json.loads(cap.read_text(encoding="utf-8"))
            cap.write_text(json.dumps([[round(s / f), t] for s, t in c], ensure_ascii=False), encoding="utf-8")
    except (OSError, ValueError, TypeError):
        pass
    logging.info(f"[tempo] final {fin:.0f}s era quase o original ({src:.0f}s): velocidade {f:.3f}x -> "
                 f"{fin / f:.0f}s (diferença {abs(fin / f - src):.0f}s)")


def _dims(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0:s=x", str(arq)], capture_output=True, text=True, timeout=60)
    w, h = (int(x) for x in r.stdout.strip().split("x")[:2])
    return w, h


class _MasterFeito(Exception):
    """04/11: master -14 LUFS já aplicado na junção das fatias da legenda (pula a passada separada)."""


def _garantir_1080(final_out, workspace):
    """31/10 regra da dona: nenhum vídeo sai com menos de 1080p. A legenda já sobe (fx_subtitles); esta guarda confere
    o arquivo REAL e sobe o que escapou (legenda pelo PNG, legenda que falhou). Falhou o upscale = levanta (não sai)."""
    w, h = _dims(final_out)
    if min(w, h) >= 1080:
        logging.info(f"[1080] final {w}x{h} ok")
        return
    alvo = "1920:1080" if w >= h else "1080:1920"
    tmp = str(Path(workspace) / "_up1080.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(final_out), "-vf", f"scale={alvo}:flags=spline,unsharp=5:5:0.6",
                    "-c:v", "libx264", "-preset", os.environ.get("ANIME_PRESET_LEGENDA") or "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    w2, h2 = _dims(tmp)
    if min(w2, h2) < 1080:
        raise RuntimeError(f"upscale não chegou a 1080p ({w2}x{h2})")
    Path(tmp).replace(final_out)
    logging.info(f"[1080] final {w}x{h} -> {w2}x{h2} (upscale)")


# 23/10: o Short do YouTube vai até 180 s; acima disso vira vídeo comum (fora do feed de Shorts). Em 20-22/10 saíram
# 2 de 303 assim (220 s e 185 s). Passou de TETO_SHORT_S = acelera imagem+voz na medida exata pra fechar em ALVO_SHORT_S;
# só até TETO_ACELERA (mais rápido que isso a voz fica estranha: aí só avisa e deixa como está).
TETO_SHORT_S = 178.0
ALVO_SHORT_S = 176.0
TETO_ACELERA = 1.25


def _teto_short(final_out, workspace):
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(final_out)], capture_output=True, text=True, timeout=30).stdout.strip())
    except Exception:  # noqa: BLE001
        return
    if dur <= TETO_SHORT_S:
        return
    f = dur / ALVO_SHORT_S
    if f > TETO_ACELERA:
        logging.warning(f"[vertical] Short com {dur:.0f} s (> 180): precisaria acelerar {f:.2f}x — deixado como está")
        return
    tmp = Path(workspace) / "_teto180_vertical.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(final_out),
                        "-filter_complex", f"[0:v]setpts=PTS/{f:.4f}[v];[0:a]atempo={f:.4f}[a]",
                        "-map", "[v]", "-map", "[a]", "-r", "30" if os.environ.get("ANIME_60FPS") == "0" else "60",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-g", "60",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                        str(tmp)], capture_output=True, text=True, timeout=900)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 10000:
        tmp.replace(final_out)
        logging.info(f"[vertical] Short tinha {dur:.0f} s: acelerado {f:.2f}x pra caber em 180 s")
    else:
        logging.warning(f"[vertical] acelerar pra 180 s falhou ({(r.stderr or '')[-200:]}) — segue com {dur:.0f} s")


def _capitulos(entries, offsets, workspace):
    """capitulos.json [[segundo, título], ...] do longo pra descrição do YouTube (dona 25/10: trazer pro longo o que os
    outros projetos têm — capítulos prendem quem pula e ajudam a busca) e pra tarja de capítulo (anime_tarja_capitulo,
    quando a fonte tem legenda). Um a cada config/longo.json "capitulos"."a_cada_s" (4 até "max"), o 1º em 0:00, todos
    com 10 s ou mais; títulos curtos pela IA (1 chamada). Sem IA = sem capítulos (título genérico não ajuda).
    Devolve a lista (ou None)."""
    total = offsets[-1] + entries[-1][1]
    try:
        cfg = _cfg_longo()
        cfg = cfg.get("capitulos") or {}
    except (OSError, ValueError):
        cfg = {}
    n = max(4, min(int(cfg.get("max", 24)), round(total / float(cfg.get("a_cada_s", 300)))))
    if total < 600:
        return None
    marcos = [0]
    for k in range(1, n):
        alvo = total * k / n
        i = next((j for j, t in enumerate(offsets) if t >= alvo), None)
        if i is not None and offsets[i] - offsets[marcos[-1]] >= 60:
            marcos.append(i)
    trechos = []
    for a, b in zip(marcos, marcos[1:] + [len(entries)]):
        trechos.append(" ".join(e[0] for e in entries[a:b][:8]))
    import claude_client
    if not claude_client.is_available():
        return None
    import re
    # o título também vai pra tela (tarja): nunca nome de obra/personagem (regra do dono pros textos na tela)
    prompt = (f"Abaixo estão as {len(trechos)} partes de um recap em vídeo, em ordem. Dê um título de capítulo pra CADA "
              "parte: 2 a 6 palavras em PT-BR, chamativo, como título de capítulo de série (promessa ou virada do que "
              "acontece naquela parte), sem número, sem nome de personagem nem da obra. Responda SÓ um JSON com uma "
              f"lista de exatamente {len(trechos)} textos, na mesma ordem, ex.: [\"título 1\", \"título 2\"].\n\n"
              + "\n".join(f"Parte {k + 1}: {t[:600]}" for k, t in enumerate(trechos)))
    titulos = []
    for _tentativa in (1, 2):
        resp = claude_client.generate_text(prompt, max_tokens=900, temperature=0.4, timeout=120) or ""
        m = re.search(r"\[.*\]", resp, re.S)
        try:
            titulos = [re.sub(r"^\s*parte\s*\d+\s*[:\-–]\s*", "", str(t), flags=re.I).strip() for t in json.loads(m.group(0))] if m else []
        except ValueError:
            titulos = []
        if len(titulos) == len(marcos) and all(titulos):
            break
    if len(titulos) != len(marcos) or not all(titulos):
        logging.warning(f"[longo] capítulos: a IA devolveu {len(titulos)} títulos pra {len(marcos)} partes — sem capítulos")
        return None
    caps = [[round(offsets[i] if i else 0.0, 1), titulos[k][:60]] for k, i in enumerate(marcos)]
    # L-F3 (LONGOS_MELHORIAS.md) 30/10 (Fable; engenharia reversa: Porão G1 + PADROES_COMUNS item 9): o capítulo perto dos 20-25 min vira o pedido
    # de comentário "Comente PARTE 2" (puxa comentário no ponto em que a retenção do longo costuma cair).
    # config/longo.json capitulos.parte2 (false desliga; o melhorador pode testar A/B).
    if cfg.get("parte2", True) and len(caps) >= 4:
        alvo = min(range(1, len(caps)), key=lambda k: abs(caps[k][0] - 22 * 60))
        if 15 * 60 <= caps[alvo][0] <= 35 * 60:
            caps[alvo][1] = 'Comente "PARTE 2" pra continuar'
    (Path(workspace) / "capitulos.json").write_text(json.dumps(caps, ensure_ascii=False), encoding="utf-8")
    logging.info(f"[longo] {len(caps)} capítulos: " + " | ".join(f"{int(s) // 60}:{int(s) % 60:02d} {t}" for s, t in caps))
    return caps


def _cfg_longo():
    """config/longo.json + a VARIANTE do teste A/B do melhorador (28/10): ANIME_LONGO_OVERRIDE = JSON {"resumo.ligado":
    false, ...} que o kaggle_trabalhador põe a partir do pedido.json (o cliente alterna A/B pelo experimento.json da
    linha LONGOS). Levanta OSError/ValueError como antes (quem chama já trata)."""
    cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "longo.json").read_text(encoding="utf-8"))
    try:
        ovr = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        ovr = {}
    for chave, valor in (ovr.items() if isinstance(ovr, dict) else []):
        alvo, partes = cfg, str(chave).split(".")
        for p in partes[:-1]:
            alvo = alvo.setdefault(p, {})
        alvo[partes[-1]] = valor
    return cfg


def _mascote_longo(concat_out, entries, offsets, caps, workspace):
    """26/10 (prompt LONGOS, base item 2): garota-mascote no canto inferior esquerdo do longo — 2 s depois do começo de
    cada capítulo (menos o 1º) e na frase do CTA do meio. config/longo.json "mascote". Falhou = vídeo sem mascote."""
    try:
        cfg = _cfg_longo()
        m = cfg.get("mascote") or {}
        if not m.get("ligado"):
            return
        c = cfg.get("cta") or {}
        meio = set(c.get("meio") or [])
        # 28/10: as frases que ELA fala (todos os CTAs, anime_segments._falas_mascote) — fica na tela a fala inteira
        dela = set(c.get("inicio") or []) | meio | set(c.get("fim") or []) if m.get("fala") else meio
        cta = [(offsets[i] + 0.1, e[0]) for i, e in enumerate(entries) if e[0] in dela and i < len(offsets)]
        fala = {round(offsets[i] + 0.1, 3): float(e[1]) for i, e in enumerate(entries)
                if m.get("fala") and e[0] in dela and i < len(offsets)}
        if not cta and meio and len(offsets) >= 60:  # revezamento reescreve a frase do CTA: ela fica no meio
            cta = [(offsets[len(offsets) // 2] + 0.3, "olha")]
        maximo = int(m.get("max", 8))
        momentos = sorted(cta + [(float(s) + 2.0, t) for s, t in caps[1:]][:max(0, maximo - len(cta))])
        import mascote_overlay
        ev = mascote_overlay.eventos_deitado(momentos, maximo + len(cta))
        textos = {round(t, 3): tx for t, tx in momentos}
        for k, e in enumerate(ev):
            e["dur"] = max(e["dur"], fala.get(round(e["t"], 3), 0.0))
            if m.get("viva", True) and round(e["t"], 3) in fala:  # 28/10: ela falando = a gravação viva do Veo
                # 01/11 dona (sempre a mesma roupa no começo): rodízio deslocado por vídeo
                import hashlib
                e["vivo"] = mascote_overlay.gravacao_viva(
                    textos.get(round(e["t"], 3), ""),
                    k + int(hashlib.md5(str(offsets[:5]).encode()).hexdigest(), 16) % 997)
        # 31/10 dona: a amiga aqui aparecia MUDA (o som dela não entrava) e no centro, em cima da Maria. Por cima da
        # narração não há tempo pra ela falar sem tampar o narrador — ela conversa com a Maria nas PAUSAS
        # (anime_segments -> mascote_overlay.montar_pausa: lado oposto, mesmo tamanho, fala depois da Maria).
        # 29/10 dona: só a mascote nova (gravações vivas dela andando) — as animações MOV antigas nos capítulos saem
        ev = [e for e in ev if e.get("vivo")]
        # 30/10 dona: "cenas engraçadas sem falar nada — passeando, apontando calada no canto, pendurada estilo Homem-
        # Aranha, de avião com a faixa 'deixe seu like'... sem parar o vídeo": a cada ~mascote.cenas_a_cada_s (420 s)
        # uma cena muda por cima do vídeo andando (só a imagem; o som é o do vídeo). Fora do 1º e do último minuto e
        # a 20 s de qualquer outra aparição dela.
        cada = float(m.get("cenas_a_cada_s", 420))
        fim = offsets[-1] if offsets else 0.0
        if cada > 0 and fim > 180:
            ocupado = [(e["t"] - 20, e["t"] + e["dur"] + 20) for e in ev]
            t, k = 60.0 + cada / 2, 0
            while t < fim - 60:
                cena = mascote_overlay.cena_viva(k)
                if not cena:
                    break
                dur = min(8.0, mascote_overlay._probe_dur(cena) or 8.0)
                if not any(a < t + dur and t < b for a, b in ocupado):
                    ev.append({"t": t, "dur": dur, "pose": "cena " + Path(cena).name.split("_")[1], "file": None,
                               "vivo": cena})
                    k += 1
                t += cada
        if not ev:
            logging.info("[longo] mascote: nenhum momento com gravação viva fora das pausas — sem sobreposição")
            return
        # 02/11: só gravações vivas = os eventos vão pra passada da legenda (fx_subtitles lê _mascote_eventos.json e
        # põe no mesmo filtro): 1 regravação do vídeo inteiro a menos. ANIME_MASCOTE_NA_LEGENDA=0 volta ao antigo
        if os.environ.get("ANIME_MASCOTE_NA_LEGENDA", "1") != "0" and all(e.get("vivo") for e in ev):
            (Path(workspace) / "_mascote_eventos.json").write_text(json.dumps(ev, ensure_ascii=False),
                                                                   encoding="utf-8")
            logging.info(f"[longo] mascote em {len(ev)} momentos (entra na passada da legenda): " + ", ".join(
                f"{int(e['t']) // 60}:{int(e['t']) % 60:02d} {e['pose']}" for e in ev))
            return
        saida = Path(workspace) / "_com_mascote.mp4"
        if mascote_overlay.overlay_mascote_deitado(concat_out, saida, ev):
            Path(saida).replace(concat_out)
            logging.info(f"[longo] mascote em {len(ev)} momentos: " + ", ".join(f"{int(e['t']) // 60}:{int(e['t']) % 60:02d} "
                                                                             f"{e['pose']}" for e in ev))
        else:
            logging.warning("[longo] mascote não entrou (overlay falhou) — segue sem")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[longo] mascote indisponível ({type(e).__name__}: {e}) — segue sem")


MEME_RESUMO_MAX_S = 6.0


def _memes_resumo(clips, sfx_durs, workspace):
    """Dona 28/10: "o resumo do começo pode e deve ter memes, estampando em cima ou o vídeo abrindo uma brecha".
    Põe config/longo.json resumo.memes (2) clipes de meme (assets/memes_img/memes, ~2 s com som, verticais -> 16:9
    com fundo borrado) DEPOIS de frases do resumo (a 2ª e a 4ª). Devolve (clipes pro concat, sfx_durs, índices dos
    memes). Sem resumo/memes/falha = tudo como estava."""
    try:
        cfg = _cfg_longo().get("resumo") or {}
        n_res = int(os.environ.get("ANIME_RESUMO_N") or 0)
        qtd = int(cfg.get("memes", 0))
    except (OSError, ValueError):
        cfg, n_res, qtd = {}, 0, 0
    pasta = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "memes_img" / "memes"
    pool = sorted(pasta.glob("*.mp4")) if pasta.exists() else []
    # 01/11 dona (nV2a: meme de 2 min 14 s no resumo): a pasta tem memes de até 134 s e aqui entrava qualquer um,
    # inteiro (amix duration=first). Só os de até MEME_RESUMO_MAX_S de verdade (duração medida) e não proibidos.
    from anime_probe import video_duration
    try:
        from fx_detect import meme_proibido
    except ImportError:
        meme_proibido = lambda _p: False  # noqa: E731
    pool = [p for p in pool if not meme_proibido(p) and 0 < (video_duration(str(p)) or 0) <= MEME_RESUMO_MAX_S] \
        if pool and int((_cfg_longo().get("resumo") or {}).get("memes", 0) or 0) > 0 else pool
    import hashlib
    import random
    rnd = random.Random(int(hashlib.md5(str(workspace).encode()).hexdigest(), 16))
    # 11/11 dona (Medieval 9: "memes horríveis no começo, não está dando prioridade aos memes novos; o primeiro com
    # piiiii que deixa surdo"): os 20 memes NOVOS em português (memes_para_escolher_5l8a, separados 01/11 e nunca
    # usados) vão no resumo NO LUGAR do sorteio entre os 86 velhos de nome aleatório. MEMES_NOVOS_RESUMO=0 volta.
    if os.environ.get("MEMES_NOVOS_RESUMO", "1") != "0":
        novos_dir = next((d for d in (pasta.parent / "memes_novos",
                                      Path(r"D:\hipercool-materiais\memes_para_escolher_5l8a")) if d.exists()), None)
        if novos_dir:
            nv = [p for p in sorted(novos_dir.glob("*.mp4")) if not meme_proibido(p)
                  and 0 < (video_duration(str(p)) or 0) <= MEME_RESUMO_MAX_S]
            if nv:
                pool = nv
    depois = [k for k in (1, 3, 2, 4) if k < n_res - 1][:qtd] \
        if (cfg.get("ligado") and qtd > 0 and n_res >= 4 and pool and len(clips) > n_res) else []
    from fx_assets import W, H
    novos, sfx2, idx = list(clips), list(sfx_durs), set()
    series = _memes_series(clips, workspace, rnd, n_res)
    # 29/10 dona: memes VISUAIS (como o hipercool) — depois de fala de emoção forte, o meme em tela cheia com o som
    # dele (memes_visuais.escolher_interrupcoes, ~1 por minuto); não no mesmo ponto de uma fala de série
    inter = []
    # 12/11 dona (longo em outra língua): memes_visuais.so_imagem = sem os memes com SOM/fala (português); ficam só os
    # de imagem em tela cheia (escolher_imagens, abaixo)
    if _cfg_longo().get("memes_visuais", {}).get("ligado", True) and len(_ENTRIES_TEXTO) == len(clips) \
            and not _cfg_longo().get("memes_visuais", {}).get("so_imagem"):
        try:
            import memes_visuais
            com_serie = {k for k, _w in series}
            inter = [(k, m) for k, m in memes_visuais.escolher_interrupcoes(_ENTRIES_TEXTO, inicio=n_res + 2, rnd=rnd)
                     if k not in com_serie]
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] memes visuais indisponíveis ({type(e).__name__}: {e})")
    prontos = []  # (frase, clipe) — séries e memes visuais entram juntos, do fim pro começo (posição não desloca)
    reacoes = []
    for j, (k, m) in enumerate(inter):
        # 29/10 noite (Fable): 1 em cada 2 interrupções vira a MASCOTE reagindo (gravação dela andando, com a voz dela),
        # se houver reação que combine e ainda não usada; senão o meme como antes. Até 3 por vídeo.
        # 31/10 dona: figurinha de meme no canto = ruim (desligada); a mascote reage mais no lugar (reacoes_max)
        if j % 2 == 1 and len(reacoes) < int((_cfg_longo().get("mascote") or {}).get("reacoes_max", 3)) \
                and (_cfg_longo().get("mascote") or {}).get("reacoes", True):
            try:
                import mascote_overlay
                emo = memes_visuais.emocao(_ENTRIES_TEXTO[k])
                ja = {r[1] for r in reacoes}
                # 02/11 dona: (1) conversa Maria x amiga (a amiga RESPONDE, outra fala) quando tem gravada
                dup = mascote_overlay.dupla_viva(emo, ja)
                if dup:
                    wa, wb = dup
                    wav = Path(workspace) / f"_reacao_{k}.wav"
                    out = Path(workspace) / f"_meme_resumo_r{k}.mp4"
                    a = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wa, "-vn", "-ac", "2", "-ar", "44100",
                                        "-c:a", "pcm_s16le", str(wav)], capture_output=True)
                    if a.returncode == 0 and mascote_overlay.montar_pausa(str(clips[k]), 0.0, wa, str(wav), str(out),
                                                                         W, H, k, "esquerda", amiga=wb):
                        prontos.append((k, str(out)))
                        reacoes.append((k, wa))
                        continue
                rea = mascote_overlay.reacao_viva(emo, ja)
                # (2) reação CURTA = no canto, por cima da própria frase, sem parar o vídeo
                if rea and mascote_overlay._probe_dur(rea[0]) <= 3.2 and len(reacoes) % 2 == 0:
                    out = Path(workspace) / f"_canto_{k}.mp4"
                    if mascote_overlay.reacao_no_canto(str(clips[k]), rea[0], str(out), W, H, len(reacoes) // 2):
                        clips[k] = str(out)  # troca o clipe (mesma duração): não entra nada novo no concat
                        novos[k] = str(out)
                        reacoes.append((k, rea[0]))
                        continue
                if rea:
                    webm, _fala, lado = rea
                    wav = Path(workspace) / f"_reacao_{k}.wav"
                    out = Path(workspace) / f"_meme_resumo_r{k}.mp4"
                    a = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", webm, "-vn", "-ac", "2", "-ar", "44100",
                                        "-c:a", "pcm_s16le", str(wav)], capture_output=True)
                    if a.returncode == 0 and mascote_overlay.montar_pausa(str(clips[k]), 0.0, webm, str(wav), str(out),
                                                                         W, H, k, lado):
                        prontos.append((k, str(out)))
                        reacoes.append((k, webm))
                        continue
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[longo] reação da mascote na frase {k} falhou ({type(e).__name__}) — vai o meme")
        out = Path(workspace) / f"_meme_resumo_i{k}.mp4"
        if memes_visuais.montar_clip(m, out, W, H):
            prontos.append((k, str(out)))
    # 31/10 dona: meme de IMAGEM ocupa a tela toda, rápido (1,2 s com whoosh), no lugar da figurinha do canto
    mv_cfg = _cfg_longo().get("memes_visuais") or {}
    if mv_cfg.get("ligado", True) and int(mv_cfg.get("imagem_cada", 15)) > 0 and len(_ENTRIES_TEXTO) == len(clips):
        try:
            import fx_detect
            import memes_visuais
            ocup = {k for k, _w in series} | {k for k, _m in inter}
            imgs = memes_visuais.escolher_imagens(_ENTRIES_TEXTO, ocup, inicio=n_res + 2,
                                                  cada=int(mv_cfg.get("imagem_cada", 15)), rnd=rnd)
            feitos = 0
            for k, m in imgs:
                out = Path(workspace) / f"_meme_resumo_g{k}.mp4"
                if memes_visuais.montar_imagem(m, out, W, H, fx_detect.pick_sfx("transition")):
                    prontos.append((k, str(out)))
                    feitos += 1
            logging.info(f"[longo] {feitos} meme(s) de imagem em tela cheia (1,2 s)")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] memes de imagem indisponíveis ({type(e).__name__}: {e})")
    if reacoes:
        logging.info(f"[longo] mascote reagindo em {len(reacoes)} momento(s): "
                     + ", ".join(f"frase {k}: {Path(w).stem}" for k, w in reacoes))
    if inter:
        logging.info(f"[longo] {len(inter)} meme(s) visual(is) em tela cheia: "
                     + ", ".join(f"frase {k}: {Path(m['file']).name}" for k, m in inter))
    for k, wav in sorted(series, reverse=True):  # fala real de série: congela o fim da frase k e o meme toca
        out = Path(workspace) / f"_meme_resumo_s{k}.mp4"
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", str(clips[k]), "-i", str(wav),
                            "-filter_complex", f"[0:v]scale={W}:{H},loop=loop=-1:size=1:start=0,fps=30,"
                            "zoompan=z='min(1+0.0015*on,1.08)':d=1:s=%dx%d:fps=30,format=yuv420p[v]" % (W, H),
                            "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-shortest", str(out)],
                           check=True, capture_output=True, timeout=120)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] meme de série depois da frase {k} falhou ({type(e).__name__}) — segue sem")
            continue
        prontos.append((k, str(out)))
    for k, out in sorted(prontos, key=lambda x: -x[0]):
        novos.insert(k + 1, out)
        sfx2.insert(k + 1, 0.0)
    for k in sorted(depois, reverse=True):
        src = rnd.choice(pool)
        out = Path(workspace) / f"_meme_resumo_{k}.mp4"
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-f", "lavfi", "-t", "4",
                            "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
                            f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                            f"gblur=sigma=25[bg];[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,fps=30,format=yuv420p[v];"
                            "[0:a][1:a]amix=inputs=2:duration=first[au]",
                            "-map", "[v]", "-map", "[au]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-shortest",
                            "-t", f"{MEME_RESUMO_MAX_S + 0.5:.1f}", str(out)],  # trava final: nunca passa do teto
                           check=True, capture_output=True, timeout=120)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] meme do resumo falhou ({type(e).__name__}) — segue sem")
            continue
        novos.insert(k + 1, str(out))
        sfx2.insert(k + 1, 0.0)
    # índices finais dos memes na lista do concat
    idx = {i for i, c in enumerate(novos) if Path(str(c)).name.startswith("_meme_resumo_")}
    if idx:
        logging.info(f"[longo] {len(idx)} meme(s) abrindo brecha no resumo (posições {sorted(idx)})")
    return novos, sfx2, idx


_ENTRIES_TEXTO = []  # texto narrado de cada clipe (run_one preenche antes do concat)


_GENERICOS = {"?", "", "ele", "ela", "garoto", "garota", "menino", "menina", "homem", "mulher", "rapaz", "moça",
              "jovem", "protagonista", "heroi", "heroina", "personagem", "narrador"}


def _nome_personagem(nome, fem):
    """Dona 31/10 (voz do personagem mudava no vídeo): a IA chamava a mesma pessoa de 'Garota', 'a garota', 'Lia'.
    Sem acento/artigo/maiúscula; apelido genérico vira 1 só personagem por gênero (o protagonista dele)."""
    import re
    import unicodedata
    n = unicodedata.normalize("NFKD", str(nome or "")).encode("ascii", "ignore").decode().lower().strip()
    n = re.sub(r"^(o|a|os|as|the)\s+", "", re.sub(r"[^a-z0-9 ]", " ", n)).strip()
    n = re.sub(r"\s+", " ", n)
    if n in _GENERICOS or n.split(" ")[0] in _GENERICOS:
        return "_protagonista_f" if fem else "_protagonista_m"
    return n.split(" ")[0]  # "Kai Shin" e "Kai" = o mesmo


def _falas_personagem(lines, tempos, workspace):
    """Dona 28/10 ("adicionar falas de personagens como o Mike faz: hora ele narra, hora faz a voz do personagem; nesse
    caso podemos usar outra voz de verdade"): a IA escolhe frases em que alguém FALA (diz/grita/responde...), ~1 a cada
    config/longo.json personagens.a_cada_s, e escreve a fala curta em 1ª pessoa; ela entra logo DEPOIS da frase, com a
    mesma imagem e a voz clonada de um personagem (vozes_m / vozes_f, por gênero; fixa por personagem no vídeo).
    ANIME_PERSONAGEM_FALAS = JSON {índice: voz} pro anime_segments. personagens.json na pasta. Falhou = sem falas."""
    try:
        cfg = _cfg_longo().get("personagens") or {}
    except (OSError, ValueError):
        return lines, tempos
    if not cfg.get("ligado") or len(lines) < 60 or not tempos:
        return lines, tempos
    n_res = int(os.environ.get("ANIME_RESUMO_N") or 0)
    arq = Path(workspace) / "personagens.json"
    itens = None
    try:
        itens = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
    except (OSError, ValueError):
        itens = None
    if itens is None:
        import re
        import claude_client
        qtd = max(3, int(len(lines) * 5.0 / float(cfg.get("a_cada_s", 90))))
        k = max(1, -(-sum(len(l) for l in lines) // 60000))
        numerado = "\n".join(f"{i}: {lines[i][:160]}" for i in range(n_res, len(lines), k))
        prompt = (
            "Roteiro de um recap narrado em PT-BR, uma frase por linha com o número. Como um narrador que às vezes faz "
            f"a VOZ do personagem, escolha até {qtd} frases em que um personagem FALA algo marcante (ameaça, piada, "
            "grito, resposta afiada), espalhadas pelo vídeo, e escreva a FALA dele em 1ª pessoa, curta (3 a 18 "
            "palavras; 12/11 dona: falas dos personagens o máximo possível, então prefira cenas de DIÁLOGO, "
            "discussões, ameaças e reações — vale mais de um personagem na mesma cena, um respondendo o outro), do "
            "jeito que ele diria, sem palavrão, sem repetir a frase do narrador palavra por palavra. "
            "Diga o gênero de quem fala (m/f), o nome do personagem e o papel dele. O NOME tem que ser SEMPRE o mesmo "
            "pro mesmo personagem (o nome próprio dele; se o roteiro não diz o nome, um apelido fixo como "
            "'protagonista' ou 'a guerreira' e use exatamente o mesmo em todas as falas dele). papel = "
            "protagonista | aliado | vilao | monstro | crianca (monstro = criatura gigante/demônio/fera, não humano; "
            "crianca = criança, menina pequena fofa, filhote, mascote fofo).\n"
            "Responda SÓ um JSON: [{\"linha\": 123, \"fala\": \"...\", \"genero\": \"m\", \"personagem\": \"Kai\", "
            "\"papel\": \"protagonista\"}]\n\nROTEIRO:\n" + numerado)
        _tent_falas = []
        try:
            # 29/10 (Fable, LONGOS_07): cadeia de modelos vivos; falhou tudo = registra "faltou falas" e avisa
            resp, _mod, _tent_falas = claude_client.generate_text_vivo(prompt, claude_client.CADEIA_TEXTO_LONGO,
                                                                       # 11/11: com a_cada_s 25 pede ~200 falas
                                                                       # (~45 tokens cada): 3000 cortava o JSON
                                                                       max_tokens=max(3000, qtd * 60), temperature=0.7,
                                                                       timeout=180,
                                                                       rodadas=3)
            m = re.search(r"\[.*\]", resp, re.S)
            itens = [x for x in (json.loads(m.group(0)) if m else []) if isinstance(x, dict) and x.get("fala")]
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] falas de personagem: IA falhou ({type(e).__name__}) — sem falas")
            itens = []
        if not itens:
            claude_client.registrar_faltou(arq.parent, "falas de personagem", "a IA não devolveu falas", _tent_falas)
        try:
            arq.write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    import random
    vm, vf = list(cfg.get("vozes_m") or []), list(cfg.get("vozes_f") or [])
    vmonstro = list(cfg.get("vozes_monstro") or [])
    # 11/11 dona: "vozes de inimigos ou monstros" só nesses papéis; "meninas fofas e crianças nas falas dos personagens"
    vvilao, vcrianca = list(cfg.get("vozes_vilao") or []), list(cfg.get("vozes_crianca") or [])
    if not itens or not (vm or vf):
        return lines, tempos
    rnd = random.Random(str(workspace))  # sorteio fixo por vídeo: refazer o mesmo vídeo dá as mesmas vozes
    for p in (vm, vf, vmonstro, vvilao, vcrianca):
        rnd.shuffle(p)  # antes saía sempre a 1ª da lista (Vegeta/Jett): sorteio dá vez a todas e permite medir
    voz_de, falas, ultimo = {}, {}, -10 ** 6
    # 12/11 dona ("falas dos personagens o máximo possível"): o piso de 5 frases (~25 s) segurava o a_cada_s 15;
    # agora PERSONAGEM_DIST_MIN (3) frases — permite diálogo curto. PERSONAGEM_DIST_MIN=5 volta.
    dist = max(int(os.environ.get("PERSONAGEM_DIST_MIN", "3")), int(float(cfg.get("a_cada_s", 90)) / 5.0 * 0.5))
    for it in sorted(itens, key=lambda x: int(x.get("linha") or 0)):
        i = int(it.get("linha") or 0)
        if i < n_res or i >= len(lines) or i - ultimo < dist:
            continue
        fem = str(it.get("genero", "m")).lower().startswith("f")
        papel = str(it.get("papel") or "").lower()
        monstro = papel.startswith("monstr") and not fem and vmonstro
        nome = _nome_personagem(it.get("personagem"), fem)
        if papel.startswith("crian") and vcrianca:
            pool = vcrianca
        elif monstro:
            pool = vmonstro
        elif papel.startswith("vil") and not fem and vvilao:
            pool = vvilao
        else:
            pool = vf if fem and vf else (vm or vf)
        if nome not in voz_de:  # mesma voz pro mesmo personagem no vídeo inteiro
            usadas = [v for v in voz_de.values() if v in pool]
            livres = [v for v in pool if v not in usadas] or pool
            voz_de[nome] = livres[0]
        falas[i] = (str(it["fala"]).strip()[:120], voz_de[nome])
        ultimo = i
    if voz_de:
        logging.info(f"[longo] voz de cada personagem: {voz_de}")
    novas, novos_t, marcadas = [], [], {}
    for i, l in enumerate(lines):
        novas.append(l)
        novos_t.append(tempos[i])
        if i in falas:
            marcadas[len(novas)] = falas[i][1]
            novas.append(falas[i][0])
            novos_t.append(tempos[i])
    if marcadas:
        os.environ["ANIME_PERSONAGEM_FALAS"] = json.dumps(marcadas)
        logging.info(f"[longo] {len(marcadas)} falas de personagem: " + ", ".join(
            f"{k}:{v}" for k, v in list(marcadas.items())[:12]))
    return novas, novos_t


def _memes_series(clips, workspace, rnd, n_res):
    """Dona 28/10: arsenal de falas REAIS curtas de séries (Chaves, Julius, Greg...) no momento certo. Catálogo do
    hipercool-materiais\\bin\\arsenal_memes.py (gatilhos por palavra da narração). [(índice do clipe, wav)].
    config/longo.json "memes_series": a_cada_s (1 no máximo a cada ~N s de vídeo), nunca o mesmo 2x, fora do resumo."""
    try:
        cfg = _cfg_longo().get("memes_series") or {}
        cat_arq = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "memes_series" / "memes_series.json"
        cat = json.loads(cat_arq.read_text(encoding="utf-8")) if cat_arq.exists() else {}
    except (OSError, ValueError):
        return []
    if not cfg.get("ligado") or not cat or len(_ENTRIES_TEXTO) != len(clips):
        return []
    from fx_detect import meme_proibido  # 31/10 dona: Roda Regina / trecho de música = fora
    dist = max(10, int(float(cfg.get("a_cada_s", 120)) / 5.0))  # ~5 s por frase
    usados, ultimo, saida = set(), -10 ** 6, []
    for k, texto in enumerate(_ENTRIES_TEXTO):
        if k < n_res + 3 or k - ultimo < dist:
            continue
        t = (texto or "").lower()
        opcoes = [n for n, m in cat.items() if n not in usados and any(g in t for g in m.get("gatilhos", []))
                  and (cat_arq.parent / m["arquivo"]).exists() and not meme_proibido(n)
                  and not meme_proibido(m["arquivo"])]
        if opcoes:
            n = rnd.choice(opcoes)
            usados.add(n)
            ultimo = k
            saida.append((k, cat_arq.parent / cat[n]["arquivo"]))
    if saida:
        logging.info(f"[longo] {len(saida)} fala(s) de série: " + ", ".join(
            f"frase {k}: {Path(w).stem}" for k, w in saida))
    return saida


def _marcar_falas_mascote(lines):
    """Dona 28/10 ("dar voz à mascote"): os CTAs do longo (config/longo.json "cta") passam a ser falados pela mascote
    — ANIME_MASCOTE_FALAS (índices) + ANIME_MASCOTE_VOZ pro anime_segments._falas_mascote; o _mascote_longo a mantém
    na tela a fala inteira. config/longo.json "mascote"."fala" (+ "voz"/"tom"). Variável já setada por fora manda."""
    try:
        cfg = _cfg_longo()
    except (OSError, ValueError):
        return
    m, c = cfg.get("mascote") or {}, cfg.get("cta") or {}
    if not (m.get("ligado") and m.get("fala")):
        return
    dela = set(c.get("inicio") or []) | set(c.get("meio") or []) | set(c.get("fim") or [])
    idx = [str(i) for i, l in enumerate(lines) if l in dela]
    if idx:
        os.environ.setdefault("ANIME_MASCOTE_FALAS", ",".join(idx))
        os.environ.setdefault("ANIME_MASCOTE_VOZ", m.get("voz") or "pt-BR-FranciscaNeural")
        os.environ.setdefault("ANIME_MASCOTE_TOM", m.get("tom") or "+6%,+22Hz")
        os.environ.setdefault("ANIME_MASCOTE_CLONE", m.get("voz_clone") or "")  # 28/10: edge puro nunca
        logging.info(f"[longo] mascote fala as frases {', '.join(idx)} ({os.environ['ANIME_MASCOTE_VOZ']})")


def _resumo_longo(lines, tempos, workspace, video_path):
    """Dona 28/10 ("falta ambientação e explicação inicial; um resumo como fazem alguns canais: hoje vamos ver o nosso
    prota, expulso da guilda, traído pela namorada... depois ganhou poderes e virou um cara foda, com as imagens desses
    momentos, e o gancho pra começar"): 5–8 frases no começo do longo, cada uma com a IMAGEM do momento que ela cita
    (o tempo da frase do roteiro que a IA aponta) + 1 virada que volta pro início. Custo: ~40 s a mais de vídeo, nenhum
    efeito novo. Sem roteiro_tempos.json o tempo vem da proporção do texto. config/longo.json "resumo"; resumo.json na
    pasta (a 2ª passada não chama a IA de novo). Falhou = longo sem resumo."""
    try:
        cfg = _cfg_longo()
        rcfg = cfg.get("resumo") or {}
    except (OSError, ValueError):
        return lines, tempos
    lingua = (os.environ.get("ANIME_LANG_NOME") or "").lower()
    if not rcfg.get("ligado") or len(lines) < 60 or (lingua and not lingua.startswith("portugu")):
        return lines, tempos
    if not tempos:  # roteiro da legenda do YouTube vem sem tempo: segundo de cada frase pela proporção do texto
        try:
            from anime_probe import video_duration
            dur = float(video_duration(video_path) or 0)
        except Exception:  # noqa: BLE001
            dur = 0.0
        if dur <= 0:
            return lines, tempos
        total, acum, tempos = sum(len(l) for l in lines) or 1, 0, []
        for l in lines:
            tempos.append(round(dur * acum / total, 2))
            acum += len(l)
    arq = Path(workspace) / "resumo_v2.json"  # L-05: v2 = abre no choque (o resumo.json antigo não vale mais)
    itens = None
    try:
        itens = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
    except (OSError, ValueError):
        itens = None
    if not itens:
        import re
        import claude_client
        # roteiro inteiro numerado (encurtado se passar de ~60 mil caracteres: 1 a cada k frases, número real mantido)
        k = max(1, -(-sum(len(l) for l in lines) // 60000))
        numerado = "\n".join(f"{i}: {lines[i][:160]}" for i in range(0, len(lines), k))
        prompt = (
            "Você escreve a ABERTURA de um vídeo longo de recap (manhwa/anime) narrado em PT-BR. Abaixo está o roteiro "
            "inteiro, uma frase por linha, com o número de cada frase. Escreva um RESUMO de abertura como os grandes "
            "canais de recap fazem. "
            # L-05 (LONGOS_MELHORIAS, 01/11): os que estouram (bXe7 2,1 mi, hJaA, 5FDt, yKfg) ABREM NO CHOQUE — a 1ª
            # frase é o pior/maior momento (traição, morte, desastre) e só depois "pra entender, vamos voltar"
            "A 1ª FRASE é o CHOQUE: o momento mais forte da história contado como se estivesse acontecendo agora (a "
            "traição, a morte, a humilhação pública, o desastre — ex.: \"A noiva dele ri enquanto o empurra do "
            "penhasco.\"), SEM explicar nada antes. Só na 2ª frase apresente o protagonista pelo nome (ex.: \"Esse é o "
            "X, e até ontem ele era...\"), depois conte em poucas frases rápidas a queda dele e as viradas mais fortes "
            "(o poder que ganha, as vitórias mais marcantes), SEM contar o final, e feche com uma frase-gancho que "
            "volta pro início (ex.: \"Mas pra entender como ele chegou aqui, a gente precisa voltar pro começo.\"). "
            "A frase do choque também aponta pro número da frase do roteiro que mostra aquele momento.\n"
            f"Regras: {int(rcfg.get('min', 5))} a {int(rcfg.get('max', 8))} frases no total; cada frase com até 22 "
            "palavras, ritmo de trailer, linguagem falada do Brasil, sem palavrão, sem citar o nome da obra. Cada "
            "frase conta um ACONTECIMENTO CONCRETO da história (quem fez o quê: \"o próprio amigo enfia uma faca nas "
            "costas dele\", \"ele derruba o general com um golpe só\"); proibido frase genérica como \"traições colocam "
            "todos em risco\" ou \"ele enfrenta grandes perigos\". Para cada frase (menos a última) diga o número da "
            "frase do roteiro que MOSTRA aquele momento (a imagem dela vai aparecer enquanto a frase é narrada): "
            "números em ordem crescente, no máximo 1 no primeiro décimo do roteiro e pelo menos metade na segunda "
            f"metade (o resumo mostra o melhor do vídeo inteiro, não o começo), e NENHUM depois da frase "
            f"{int(len(lines) * 0.85)} (lá está o desfecho, que não pode ser contado).\n"
            "Responda SÓ um JSON: [{\"frase\": \"...\", \"linha\": 123}, ..., {\"frase\": \"virada final\", "
            "\"linha\": 0}]\n\nROTEIRO:\n" + numerado)
        _tent_resumo = []
        for _tentativa in (1, 2):
            try:
                # texto longo (roteiro inteiro) = Gemini 3.8 direto, como o jeito do narrador (DECISOES 27/10); o
                # padrão do claude_client ainda é o Gemini 3 (no 1º teste copiou frases e esqueceu o protagonista).
                # 29/10 (Fable, LONGOS_07): cadeia de modelos vivos em vez de 1 modelo que trava 12 min e some calado
                resp, _mod, _t = claude_client.generate_text_vivo(prompt, claude_client.CADEIA_TEXTO_LONGO,
                                                                 max_tokens=1500, temperature=0.6, timeout=120,
                                                                 rodadas=3)
                _tent_resumo += _t
                if _mod and _mod != claude_client.CADEIA_TEXTO_LONGO[0]:
                    logging.warning(f"[longo] resumo: veio da reserva {_mod}")
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[longo] resumo: IA falhou ({type(e).__name__}: {e})")
                resp = ""
            m = re.search(r"\[.*\]", resp, re.S)
            try:
                bruto = json.loads(m.group(0)) if m else []
                itens = [{"frase": str(x["frase"]).strip(), "linha": int(x.get("linha") or 0)} for x in bruto
                         if isinstance(x, dict) and str(x.get("frase") or "").strip()]
            except (ValueError, TypeError, KeyError):
                itens = []
            # 1º teste 28/10 (RA4H): 3 de 5 imagens no 1º minuto — resumo que só mostra o começo não vende o vídeo
            momentos = [x["linha"] for x in itens[:-1]]
            espalhado = momentos and sum(m >= len(lines) // 2 for m in momentos) * 2 >= len(momentos) \
                and sum(m < len(lines) // 10 for m in momentos) <= 1
            if int(rcfg.get("min", 5)) <= len(itens) <= int(rcfg.get("max", 8)) + 2 and (espalhado or _tentativa == 2):
                break
            itens = None
        if not itens:
            logging.warning("[longo] resumo: a IA não devolveu um resumo válido — longo sem resumo")
            claude_client.registrar_faltou(arq.parent, "resumo", "a IA não devolveu um resumo válido", _tent_resumo)
            return lines, tempos
        try:
            arq.write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    n = len(lines)
    # trava de spoiler (teste 28/10: com "SEM contar o final" no prompt a IA ainda usou a frase 521 de 556, o desfecho):
    # momento nos últimos 12% do roteiro sai do resumo; a virada final fica
    corte = int(n * 0.88)
    itens = [x for x in itens[:-1] if int(x.get("linha") or 0) < corte] + itens[-1:]
    novas, novos_t = [], []
    for j, it in enumerate(itens):
        ultima = j == len(itens) - 1
        # imagem: o momento citado (2 s depois do começo da frase); a virada final já mostra o início da história
        i = 0 if ultima else min(max(int(it["linha"]), 0), n - 1)
        novas.append(it["frase"])
        novos_t.append(float(tempos[i]) + (0.0 if ultima else 2.0))
    os.environ["ANIME_RESUMO_N"] = str(len(novas))  # anime_segments._inicios: o resumo pode "voltar no tempo"
    logging.info(f"[longo] resumo de abertura: {len(novas)} frases -> " + " | ".join(
        f"{t // 60:.0f}:{t % 60:02.0f}" for t in novos_t))
    return novas + list(lines), novos_t + list(tempos)


def _ganchos_longo(lines, tempos, workspace):
    """L-F2 (LONGOS_MELHORIAS.md) 30/10 (Fable; engenharia reversa: Porão 482k + PADROES_COMUNS item 7 — "a cada 15-20 min o narrador interrompe com
    um gancho do que vem": mini-gancho do narrador a cada config/longo.json ganchos.a_cada_s (900 s ≈ 180 frases). UMA
    chamada à IA (cadeia de modelos vivos) escreve todos: cada um provoca o que acontece nas ~60 frases seguintes, sem
    contar o desfecho. Falhou = longo sem ganchos. ganchos.json na pasta."""
    try:
        g = _cfg_longo().get("ganchos") or {}
    except (OSError, ValueError):
        return lines, tempos
    lingua = (os.environ.get("ANIME_LANG_NOME") or "").lower()
    if not g.get("ligado") or len(lines) < 300 or (lingua and not lingua.startswith("portugu")):
        return lines, tempos
    passo = max(60, int(float(g.get("a_cada_s", 900)) / 5.0))
    n_res = int(os.environ.get("ANIME_RESUMO_N") or 0)
    marcas = list(range(n_res + passo, len(lines) - 80, passo))
    if not marcas:
        return lines, tempos
    arq = Path(workspace) / "ganchos.json"
    try:
        itens = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
    except (OSError, ValueError):
        itens = None
    if not itens:
        import re
        import claude_client
        blocos = "\n\n".join(f"GANCHO {k + 1} (antes da frase {m}). O que vem a seguir:\n"
                             + " ".join(l[:140] for l in lines[m:m + 60]) for k, m in enumerate(marcas))
        prompt = ("Você é o narrador de um recap longo de manhwa em PT-BR. Em cada ponto abaixo, escreva UMA frase curta "
                  "(até 20 palavras) que o narrador diz pra segurar o público, provocando o que vem a seguir sem contar "
                  "como termina, no estilo \"Fica aí, porque daqui a pouco ele vai...\" ou \"E se você acha que isso foi "
                  "pesado, espera só o que vem agora\". Linguagem falada do Brasil, sem palavrão, sem nome da obra, cada "
                  f"frase diferente. Responda SÓ um JSON com uma lista de {len(marcas)} textos, na ordem.\n\n" + blocos)
        tent = []
        try:
            resp, _m, tent = claude_client.generate_text_vivo(prompt, claude_client.CADEIA_TEXTO_LONGO, max_tokens=1500,
                                                              temperature=0.7, timeout=120, rodadas=2)
            m = re.search(r"\[.*\]", resp or "", re.S)
            itens = [str(x).strip() for x in (json.loads(m.group(0)) if m else []) if str(x).strip()]
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[longo] ganchos: IA falhou ({type(e).__name__}) — sem ganchos")
            itens = []
        if len(itens) != len(marcas):
            claude_client.registrar_faltou(arq.parent, "ganchos a cada 15 min", f"a IA devolveu {len(itens)} de {len(marcas)}", tent)
            return lines, tempos
        try:
            arq.write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    from viralizador import anti_ban
    lines, tempos = list(lines), (list(tempos) if tempos else None)
    for m, texto in sorted(zip(marcas, itens), reverse=True):  # do fim pro começo: o índice não desloca
        lines.insert(m, anti_ban(texto)[:200])
        if tempos:
            tempos.insert(m, tempos[m - 1])
    logging.info(f"[longo] {len(itens)} mini-ganchos (a cada ~{passo} frases): " + " | ".join(i[:50] for i in itens[:4]))
    return lines, tempos


def _cta_longo(lines, tempos, semente):
    """Dona 25/10 (o longo atrás dos Cortes): 1 pedido de inscrição depois da abertura e 1 no fim (config/longo.json
    "cta"). Só em português e só em roteiro de verdade (20+ frases). O CTA herda o tempo da frase anterior (a imagem
    segue a cena em vez de pular)."""
    try:
        cfg = _cfg_longo()
        cta = cfg.get("cta") or {}
    except (OSError, ValueError):
        return lines, tempos
    lingua = (os.environ.get("ANIME_LANG_NOME") or "").lower()
    if not cta.get("ligado") or len(lines) < 20 or (lingua and not lingua.startswith("portugu")):
        return lines, tempos
    import hashlib
    n = int(hashlib.md5(str(semente).encode("utf-8")).hexdigest(), 16)
    lines, tempos = list(lines), (list(tempos) if tempos else None)
    k = min(int(cta.get("depois_da_frase", 4)), len(lines) - 1)
    if cta.get("inicio"):
        lines.insert(k, cta["inicio"][n % len(cta["inicio"])])
        if tempos:
            tempos.insert(k, tempos[k - 1])
    if cta.get("meio") and len(lines) >= 60:  # 26/10 (prompt LONGOS, base item 2): CTA também no meio do vídeo
        m = len(lines) // 2
        lines.insert(m, cta["meio"][n % len(cta["meio"])])
        if tempos:
            tempos.insert(m, tempos[m - 1])
    if cta.get("fim"):
        lines.append(cta["fim"][n % len(cta["fim"])])
        if tempos:
            tempos.append(tempos[-1])
    logging.info(f"[longo] CTA: depois da frase {k}{', no meio' if cta.get('meio') else ''} e no fim")
    return lines, tempos


def _perfil_longo(video_source, titulo):
    """{variável: valor} do config/longo.json pro formato deitado (dona 25/10: o longo ganha os efeitos dos Cortes).
    Tipo da fonte: pedido.json ao lado do vídeo (Kaggle/Colab/VPS) > palavras do título > tipo_padrao."""
    try:
        cfg = _cfg_longo()
    except (OSError, ValueError) as e:
        logging.warning(f"[longo] config/longo.json ilegível ({e}) — longo sem o perfil")
        return {}, "?"
    tipo = None
    try:
        ped = json.loads((Path(video_source).parent / "pedido.json").read_text(encoding="utf-8"))
        tipo = ped.get("tipo")
    except (OSError, ValueError):
        pass
    if not tipo:
        t = (titulo or "").lower()
        tipo = next((tp for tp, pal in (cfg.get("palavras") or {}).items() if any(p in t for p in pal)), None)
    tipo = tipo or cfg.get("tipo_padrao", "anime")
    env = {k: str(v) for k, v in (cfg.get("efeitos") or {}).items() if not k.startswith("_")}
    env.update({k: str(v) for k, v in ((cfg.get("por_tipo") or {}).get(tipo) or {}).items() if not k.startswith("_")})
    return env, tipo


def main():
    parser = argparse.ArgumentParser(description="Recap de anime descaracterizado (narração TTS)")
    parser.add_argument("--video-source", required=True, help="Arquivo de video original mp4")
    parser.add_argument("--script", required=True, help="Arquivo txt com as frases (roteiro)")
    parser.add_argument("--titulo", default="Anime Recap", help="Título")
    parser.add_argument("--skip-notify", action="store_true", help="Pula a notificação")
    parser.add_argument("--max-panels", type=int, default=1000, help="Limite de frases (teste)")
    parser.add_argument("--formato", choices=["deitado", "short", "ambos"], default="ambos",
                        help="deitado (16:9 principal), short (9:16) ou ambos")
    parser.add_argument("--short-source-kind", choices=["native", "reframe"], default="reframe",
                        help="Se o short usa fonte vertical nativa ou vai emoldurar vídeo horizontal")
    parser.add_argument("--cover-hardsub", action="store_true",
                        help="Força o borrão fixo no rodapé (sem detecção) — só quando se SABE que a fonte tem "
                             "legenda queimada e a detecção não acha")
    # interno: quando setado, este processo gera SÓ um formato (não redispatcha).
    parser.add_argument("--_orient", choices=["landscape", "vertical"], help=argparse.SUPPRESS)
    parser.add_argument("--_out-name", help=argparse.SUPPRESS)
    args = parser.parse_args()

    # 04/11 dona (projeto João Lucas Virjão): pedido com longo_override {"voz_original": true} MANTÉM a narração do
    # original (narrador parceiro autorizado) — sem roteiro/TTS; só legenda MIX, efeitos, memes e trilha (voz_original.py)
    try:
        _ovr_vo = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        _ovr_vo = {}
    if isinstance(_ovr_vo, dict) and _ovr_vo.get("voz_original") and not args._orient:
        logging.info("[voz_original] pedido com a narração ORIGINAL — voz_original.py")
        sys.exit(subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).with_name("voz_original.py")),
                                 args.video_source, args.titulo]).returncode)

    # Modo worker: um formato só, orientação já fixada pela env no import.
    if args._orient:
        # fila de render entre projetos (D:\video-fila, dono 17/10): um render pesado por vez no PC
        import contextlib
        try:
            sys.path.insert(0, r"D:\video-fila")
            import fila_render
            projeto = "parceiro" if os.environ.get("ANIME_FX_MOV") == "1" else "anime"
            vez = fila_render.vez(projeto, f"{Path(args.video_source).parent.name} {args._orient}")
        except Exception:  # noqa: BLE001
            vez = contextlib.nullcontext()
        with vez:
            ok = run_one(args.video_source, args.script, args._orient,
                         args._out_name, args.max_panels)
        sys.exit(0 if ok else 1)

    # 25/10: o alimentador do longo manda só o original quando o YouTube não dá legenda — a transcrição do vídeo inteiro
    # e o roteiro com tempo são feitos aqui, no trabalhador (anime_preparo_longo.py), não no PC1 sobrecarregado.
    if not Path(args.script).exists():
        logging.info(f"[preparo] sem roteiro ({args.script}) — transcrevendo e roteirizando aqui")
        r = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).with_name("anime_preparo_longo.py")),
                            str(Path(args.video_source).parent), args.titulo])
        if r.returncode != 0 or not Path(args.script).exists():
            logging.error("[preparo] roteiro não ficou pronto — vídeo não sai")
            sys.exit(1)
        # LONGOS_MELHORIAS 10/11 (b): o trabalhador pegou este pedido sem saber o tamanho do roteiro (chute de 7 h).
        # Agora que o roteiro existe, confere de novo: não cabe no resto da sessão = sai JÁ (código 75) e o trabalhador
        # guarda o roteiro e solta o pedido, em vez de renderizar até o Kaggle cortar.
        import cabe_na_sessao
        _cabe_ok, _cabe_txt = cabe_na_sessao.conferir(args.script)
        logging.info(f"[preparo] {_cabe_txt}")
        if not _cabe_ok:
            logging.error("[preparo] o longo não cabe no que resta da sessão — devolvo pra fila com o roteiro pronto")
            sys.exit(cabe_na_sessao.CODIGO_NAO_CABE)

    # Legenda QUEIMADA da fonte (dona 25/10: "se não tem legenda não tinha por que ter borrado a tela"): detecta UMA vez
    # por source (anime_legenda_fonte: ~100 quadros do vídeo inteiro) e os formatos herdam via env. Tem legenda = borra
    # SÓ a faixa dela (ANIME_HARDSUB_RECT, e no longo a tarja de capítulo cobre por cima). Sem legenda, ou detecção que
    # falhou = vídeo LIMPO (antes caía no borrão fixo do rodapé). --cover-hardsub força a faixa fixa (sem detecção);
    # ANIME_HARDSUB_DETECT=0 desliga a detecção.
    hardsub_rect_env = None
    hardsub_cover_env = "1" if args.cover_hardsub else None
    if not args.cover_hardsub and os.environ.get("ANIME_HARDSUB_DETECT", "1").strip() != "0":
        try:
            import anime_legenda_fonte
            det = anime_legenda_fonte.detectar(args.video_source)
            if det.get("tem") and det.get("faixa"):
                y0, y1 = det["faixa"]
                y0, y1 = max(0.0, y0 - 0.012), min(1.0, y1 + 0.012)  # contorno/sombra das letras
                hardsub_rect_env = f"{y0:.4f},{y1 - y0:.4f}"
                logging.info(f"[legenda-fonte] legenda queimada na faixa {y0:.3f}-{y1:.3f} — borra só ela")
            else:
                logging.info(f"[legenda-fonte] fonte sem legenda queimada ({det.get('motivo')}) — sem borrão")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[legenda-fonte] detecção falhou ({type(e).__name__}: {e}) — sem borrão")

    # Modo dispatcher: dispara um subprocesso por formato pedido.
    formatos = ["deitado", "short"] if args.formato == "ambos" else [args.formato]
    falhou = False
    for fmt in formatos:
        orient, out_name = _FORMATS[fmt]
        logging.info(f"===== Disparando formato: {fmt} ({orient}) =====")
        env = dict(os.environ, ANIME_ORIENT=orient, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        if fmt == "short":
            env["ANIME_SHORT_SOURCE"] = args.short_source_kind
        else:  # deitado: perfil do longo (o que vem de fora manda mais)
            perfil, tipo = _perfil_longo(args.video_source, args.titulo)
            novos = {k: v for k, v in perfil.items() if k not in os.environ}
            env.update(novos)
            logging.info(f"[longo] fonte tipo {tipo}; perfil: {novos or '(nada novo)'}")
        if hardsub_rect_env:
            env["ANIME_HARDSUB_RECT"] = hardsub_rect_env
        elif hardsub_cover_env:
            env["ANIME_HARDSUB_COVER"] = "1"
        cmd = [sys.executable, os.path.abspath(__file__),
               "--video-source", args.video_source,
               "--script", args.script,
               "--max-panels", str(args.max_panels),
               "--_orient", orient, "--_out-name", out_name]
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            logging.error(f"[{fmt}] subprocesso falhou (rc={r.returncode})")
            falhou = True

    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()
