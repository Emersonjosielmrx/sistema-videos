# -*- coding: utf-8 -*-
"""Reel com VIDEO REAL da MS Energy (dono 22/10/2026 "faça": vídeos reais do Google Fotos nos Reels). Sem Veo.

Por que: no perfil, os Reels antigos com vídeo real tiveram ~25x mais views que os de IA (mediana 170 x 7,
docs\\ANALISE_CAMPANHA.md frente 4).

  1. roteiro_ms.gerar("video_real") — mesma pauta/regras/revisor dos outros formatos (fala + convite falado)
  2. 2 trechos de assets\\videos_reais\\clipes.json (aprovados a olho: sem rosto, sem tela de app, sem IA): o 1º casa
     com a pauta, o 2º é o usado há mais tempo; emenda de 0,4 s; recorte 9:16
  3. narradora pt-BR (edge-tts Thalita, a voz padrão dos outros projetos) com o tempo de cada palavra (a legenda sai
     sincronizada sem Whisper; se o edge cair, voz pelo edge_tts_engine COMUM + Whisper)
  4. trilha de licença livre baixinha; o áudio original sai (pode ter conversa de cliente/equipe)
  5. montagem_ms.montar (frase no topo + legenda + cartão) e a mesma trava final; reprovado vai para videos\\_revisar

    python video_real_ms.py [--lote 1]
"""
import argparse
import asyncio
import datetime
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

DIR_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIR_PROJETO / "bin"))
sys.path.insert(0, r"D:\veo\beta")

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
CLIPES_JSON = DIR_PROJETO / "assets" / "videos_reais" / "clipes.json"
VIDEOS_DIR = DIR_PROJETO / "assets" / "fotos_instagram" / "google_fotos" / "videos"
DIR_VIDEOS = DIR_PROJETO / "videos" / "shorts_veo"
DIR_REVISAR = DIR_PROJETO / "videos" / "_revisar"
DIR_TMP = DIR_PROJETO / "cache" / "tmp_real"
# licença livre: Mixkit (uso comercial liberado) e YouTube Audio Library
TRILHAS = [r"D:\hipercool-materiais\assets\trilhas\calm_chill.mp3",              # Serene View (Mixkit)
           r"D:\hipercool-materiais\assets\trilhas\Beyond - Patrick Patrikios.mp3"]
VOZ, VOZ_RATE = "pt-BR-ThalitaMultilingualNeural", "+5%"
TRECHO_S = 5.0
EMENDA_S = 0.4
ATRASO_VOZ_S = 0.4
VOLUME_TRILHA = 0.16


def _carregar_clipes():
    lista = json.loads(CLIPES_JSON.read_text("utf-8"))["clipes"]
    return [c for c in lista if (VIDEOS_DIR / c["arquivo"]).exists()]


def escolher_clipes(pauta_id):
    """[clipe da pauta, outro] — entre os candidatos, o usado há mais tempo (histórico dos roteiros)."""
    import roteiro_ms
    usados = {}
    for i, h in enumerate(roteiro_ms._hist()):
        for cid in h.get("clipes") or []:
            usados[cid] = i
    clipes = _carregar_clipes()
    if len(clipes) < 2:
        return None
    frio = lambda cs: sorted(cs, key=lambda c: (usados.get(c["id"], -1), random.random()))  # noqa: E731
    da_pauta = [c for c in clipes if pauta_id in c.get("pautas", [])]
    a = frio(da_pauta or clipes)[0]
    # 25/10: fala de até ~25 s -> até 5 trechos (o montar_base usa só os que precisar); a pauta primeiro, depois os
    # usados há mais tempo, sem repetir o mesmo vídeo de origem em seguida
    resto = [c for c in frio([c for c in clipes if c["id"] != a["id"]])]
    escolhidos = [a]
    for c in resto:
        if len(escolhidos) >= 5:
            break
        if c.get("origem", c["arquivo"]) != escolhidos[-1].get("origem", escolhidos[-1]["arquivo"]):  # mesmo vídeo de origem
            escolhidos.append(c)
    return escolhidos


async def _edge(texto, mp3):
    import edge_tts
    palavras = []
    with open(mp3, "wb") as f:
        async for ch in edge_tts.Communicate(texto, VOZ, rate=VOZ_RATE, boundary="WordBoundary").stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                ini = ch["offset"] / 1e7
                palavras.append((ch["text"], round(ini, 2), round(ini + ch["duration"] / 1e7, 2)))
    return palavras


def narrar(texto, mp3, log=print):
    """(arquivo, palavras [(palavra, inicio, fim)])."""
    try:
        palavras = asyncio.run(_edge(texto, str(mp3)))
        if palavras and Path(mp3).stat().st_size > 5000:
            return mp3, palavras
        log("  [VOZ] edge-tts sem tempos das palavras — vou pelo motor comum")
    except Exception as e:  # noqa: BLE001
        log(f"  [VOZ] edge-tts direto falhou ({type(e).__name__}: {str(e)[:80]}) — vou pelo motor comum (proxy)")
    sys.path.insert(0, r"D:\hipercool-materiais\comum")
    import edge_tts_engine
    import qa_ms
    wav = Path(mp3).with_suffix(".wav")
    edge_tts_engine.speak(texto, voice=VOZ, out_wav=str(wav))
    return wav, qa_ms.transcrever(wav)


def _dur(p):
    """Duração de vídeo OU só áudio (qa_ms.probe exige faixa de vídeo)."""
    r = subprocess.run([FF.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, timeout=30)
    return float(r.stdout.strip())


def montar_base(clipes, voz, saida, log=print):
    """Trechos emendados em 1080x1920 + narradora + trilha. Duração: cobre a fala com folga (o cartão vem depois)."""
    from montagem_ms import CORTE_FIM_S, H, W
    precisa = ATRASO_VOZ_S + _dur(voz) + 0.9 + CORTE_FIM_S + EMENDA_S
    disp = [c["fim"] - c["inicio"] for c in clipes]
    lens = [min(TRECHO_S, d) for d in disp]
    # 25/10: com até 5 trechos, usa só os necessários pra cobrir a fala (mínimo 2)
    while len(clipes) > 2 and sum(lens[:-1]) - EMENDA_S * (len(lens) - 2) >= precisa:
        clipes, disp, lens = clipes[:-1], disp[:-1], lens[:-1]
    while sum(lens) - EMENDA_S * (len(lens) - 1) < precisa and any(l < d for l, d in zip(lens, disp)):
        lens = [min(l + 0.5, d) for l, d in zip(lens, disp)]
    total = sum(lens) - EMENDA_S * (len(lens) - 1)
    trilha = random.choice([t for t in TRILHAS if Path(t).exists()])
    ent, fc = [], []
    for i, (c, l) in enumerate(zip(clipes, lens)):
        ent += ["-ss", f"{c['inicio']:.2f}", "-t", f"{l:.2f}", "-i", str(VIDEOS_DIR / c["arquivo"])]
        fc.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1,"
                  f"format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
    atual, t = "v0", lens[0]
    for i in range(1, len(clipes)):
        fc.append(f"[{atual}][v{i}]xfade=transition=fade:duration={EMENDA_S}:offset={t - EMENDA_S:.2f}[x{i}]")
        atual, t = f"x{i}", t + lens[i] - EMENDA_S
    n = len(clipes)
    ent += ["-i", str(voz), "-stream_loop", "-1", "-i", trilha]
    atraso = int(ATRASO_VOZ_S * 1000)
    fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={atraso}|{atraso}[vz]")
    fc.append(f"[{n + 1}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.2f},asetpts=PTS-STARTPTS,"
              f"volume={VOLUME_TRILHA},afade=t=in:d=0.6,afade=t=out:st={max(total - 1.2, 0):.2f}:d=1.2[mu]")
    fc.append(f"[vz][mu]amix=inputs=2:duration=longest:normalize=0,atrim=0:{total:.2f}[a]")
    cmd = [FF, "-y", "-v", "error"] + ent + ["-filter_complex", ";".join(fc), "-map", f"[{atual}]", "-map", "[a]",
                                            "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                                            "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", str(saida)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not Path(saida).exists():
        log(f"  [BASE] ffmpeg falhou: {r.stderr[-500:]}")
        return None
    log(f"  [BASE] {' + '.join(c['id'] for c in clipes)} ({total:.1f}s) | trilha {Path(trilha).stem}")
    return {"duracao": round(total, 2), "trilha": Path(trilha).name, "trechos": [
        {"id": c["id"], "arquivo": c["arquivo"], "inicio": c["inicio"], "dur": l} for c, l in zip(clipes, lens)]}


def gerar_short_real(output_dir=None, log=print):
    """Devolve o caminho do Reel aprovado ou None (nada vai para a fila)."""
    import montagem_ms
    import qa_ms
    import roteiro_ms
    from gerar_short_veo import _limpar_tmp, _nivelar_audio, _tem_audio
    output_dir = Path(output_dir) if output_dir else DIR_VIDEOS
    for p in (output_dir, DIR_TMP, DIR_REVISAR):
        p.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log(f"{'=' * 50}\n  MS Energy — Reel com VÍDEO REAL (sem Veo)\n{'=' * 50}")

    roteiro = roteiro_ms.gerar("video_real", log=log)
    clipes = escolher_clipes(roteiro["pauta"])
    if not clipes:
        log("  [STOP] menos de 2 clipes reais disponíveis (assets\\videos_reais\\clipes.json)")
        return None
    roteiro["clipes"] = [c["id"] for c in clipes]
    voz, palavras = narrar(roteiro["fala_final"], DIR_TMP / f"voz_{ts}.mp3", log)
    palavras = [(w, s + ATRASO_VOZ_S, e + ATRASO_VOZ_S) for w, s, e in palavras]
    base = DIR_TMP / f"base_{ts}.mp4"
    info_base = montar_base(clipes, voz, base, log)
    if not info_base:
        return None
    roteiro["clipes"] = [t["id"] for t in info_base["trechos"]]  # só os usados (até 5 escolhidos)

    stem = f"ms_energy_solar_{ts}"
    out = output_dir / f"{stem}.mp4"
    foto = roteiro_ms.escolher_foto()
    fundo = roteiro_ms.quadro_916(foto[0], float((foto[1].get("visao") or {}).get("foco_x") or 0.5)) if foto else None
    ok, info = montagem_ms.montar(base, roteiro, palavras, out, foto_fundo=fundo, log=log)
    if not ok:  # pico de memoria do PC (23/10 00:12 derrubou o ffmpeg de outro short): mais 1x depois de 90 s
        import time
        log("  [MONTAGEM] falhou — espero 90 s e tento de novo (pico de memória?)")
        time.sleep(90)
        ok, info = montagem_ms.montar(base, roteiro, palavras, out, foto_fundo=fundo, log=log)
    if not ok:
        log("  [STOP] montagem falhou — nada vai para a fila")
        return None
    _nivelar_audio(out, log)
    final = qa_ms.checar_final(out, log=log)
    side = {
        "titulo": roteiro["titulo"], "descricao": roteiro["legenda_insta"], "legenda_insta": roteiro["legenda_insta"],
        "legenda_tiktok": roteiro["legenda_tiktok"], "hashtags": roteiro["hashtags"], "tags": roteiro["hashtags"],
        "pipeline": "ms_v2", "tipo": "ms_v2", "tipo_video": "video_real", "pauta": roteiro["pauta"],
        "fala": roteiro["fala_final"], "gancho_tela": roteiro["gancho_tela"], "roteiro_fonte": roteiro["fonte"],
        "clipes": info_base["trechos"], "trilha": info_base["trilha"], "voz": VOZ, "legendas": info["legendas"],
        "qa_final": final, "duracao_s": _dur(out), "tem_audio_nativo": _tem_audio(out),
        "gerado_em": datetime.datetime.now().isoformat(),
    }
    if not final["ok"]:
        destino = DIR_REVISAR / out.name
        shutil.move(str(out), str(destino))
        side["revisar_motivos"] = final["motivos"]
        destino.with_suffix(".json").write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
        log(f"  [STOP] reprovado na trava final ({'; '.join(final['motivos'])}) → {destino}")
        return None
    out.with_suffix(".json").write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
    roteiro_ms.registrar(roteiro, stem)
    shutil.rmtree(DIR_TMP, ignore_errors=True)
    _limpar_tmp()
    log(f"\n  Reel aprovado: {out} ({side['duracao_s']:.1f}s)")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", type=int, default=1)
    ap.add_argument("--output", default=str(DIR_VIDEOS))
    a = ap.parse_args()
    for _ in range(a.lote):
        gerar_short_real(a.output)
