"""Corte de camera: tira so a webcam de uma gravacao do OBS (webcam em cima, video do celular/desenho embaixo) e entrega
em 1920x1080, com o audio original.

Como acha a camera (sem numero fixo): pega ~12 quadros espalhados pelo video e mede, linha a linha, a diferenca de cor
entre uma linha e a de baixo (mediana entre as colunas, para legenda/texto nao enganar). A divisa da camera e uma borda
reta que atravessa a tela inteira e esta em TODOS os quadros (bordas da tela compartilhada vem e vao); entre as bordas
fortes e fixas, fica a mais perto de onde uma camera 16:9 terminaria (largura x 9/16). A linha da divisa costuma vir
misturada com o de baixo: fica de fora. Gravacoes do OBS de 06/10: divisa na linha 402 -> camera 714x402.
Depois corta a largura para 16:9 exato (centralizado) e amplia para 1920x1080.

Encode em pedacos de ~17 min (so video): se faltar memoria (pagefile da maquina), refaz so o pedaco que falhou. Junta os
pedacos sem reprocessar, poe o audio original copiado e confere se o numero de quadros bate com o original.

Uso: python manhwareact.py camera <video|pasta> [--area X:Y:L:A] [--so-detectar] [--saida PASTA] [--forcar]
"""
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

from mr.common import log, run

PEDACO_S = 1015          # ~17 min por pedaco de encode
AMOSTRAS = 12
SAIDA_PADRAO = "D:/hipercool-materiais/manhwa-react/camera"
VIDEO_EXT = {".mp4", ".mkv", ".mov", ".webm"}


def _ffprobe(cfg, path, *args):
    r = run([cfg["paths"]["ffprobe"], "-v", "error", *args, str(path)])
    return r.stdout.strip()


def info(cfg, path):
    d = json.loads(_ffprobe(cfg, path, "-show_entries",
                            "format=duration,start_time:stream=codec_type,width,height,r_frame_rate,start_time",
                            "-of", "json"))
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    n, den = (int(x) for x in v["r_frame_rate"].split("/"))
    # OBS/celular as vezes grava o video comecando alguns segundos depois do audio (ex.: video 4,0 s, audio 0,01 s):
    # os inicios entram no corte e no alinhamento do audio
    return {"w": int(v["width"]), "h": int(v["height"]), "fps": n / den, "dur": float(d["format"]["duration"]),
            "audio": a is not None, "v_ini": float(v.get("start_time") or 0),
            "a_ini": float((a or {}).get("start_time") or 0)}


def _quadro(cfg, path, t, w, h):
    """Um quadro em RGB (numpy h x w x 3) no instante t."""
    r = subprocess.run([cfg["paths"]["ffmpeg"], "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=120)
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    if buf.size != w * h * 3:
        return None
    return buf.reshape(h, w, 3).astype(np.int16)


def detectar(cfg, path, inf=None):
    """Acha a area da camera. Devolve dict com x, y, w, h (16:9), a linha da divisa e a confianca."""
    inf = inf or info(cfg, path)
    W, H, dur = inf["w"], inf["h"], inf["dur"]
    tempos = [dur * (0.03 + 0.94 * i / (AMOSTRAS - 1)) for i in range(AMOSTRAS)]
    perfis, quadros = [], []
    for t in tempos:
        q = _quadro(cfg, path, t, W, H)
        if q is None:
            continue
        quadros.append((t, q))
        dif = np.abs(np.diff(q, axis=0)).mean(axis=2)      # (H-1, W): mudanca da linha y para y+1
        perfis.append(np.median(dif, axis=1))              # mediana nas colunas: borda que atravessa a tela toda
    if not perfis:
        raise RuntimeError("nao consegui ler quadros do video")
    pilha = np.stack(perfis)
    # 20% mais fracos: a divisa da camera esta em TODOS os quadros; bordas da tela compartilhada (barra do navegador,
    # faixa "compartilhando") vem e vao quando o conteudo de baixo muda e ficam de fora.
    pontos = np.percentile(pilha, 20, axis=0)
    ini, fim = int(0.30 * W), min(H - 2, int(0.80 * W))   # camera 16:9 na largura toda termina perto de 0,5625 x W
    esperado = W * 9 / 16
    res = {"largura": W, "altura": H, "quadros_lidos": len(perfis)}
    if fim <= ini:
        res.update(achou=False, motivo="video baixo demais para ter camera + outra coisa embaixo")
    else:
        janela = pontos[ini:fim]
        maior = float(janela.max())
        # bordas fortes e fixas; entre elas, a mais perto de onde uma camera 16:9 terminaria
        candidatas = [ini + i for i, v in enumerate(janela) if v >= 0.6 * maior]
        y = min(candidatas, key=lambda c: abs(c - esperado))
        while y - 1 in candidatas:  # borda de 2-3 linhas seguidas: a camera para na primeira
            y -= 1
        forca = float(pontos[y])
        presenca = float((pilha[:, y] >= 0.5 * forca).mean()) if forca > 0 else 0.0
        res.update(divisa=y, forca=round(forca, 1), presenca=round(presenca, 2),
                   outras_bordas=[c for c in candidatas if abs(c - y) > 2][:5])
        res["achou"] = forca >= 6 and presenca >= 0.8
        if not res["achou"]:
            res["motivo"] = "nenhuma borda reta e fixa atravessando a tela (o video ja parece ser so a camera?)"
    altura_cam = res["divisa"] if res.get("achou") else H   # linhas 0..divisa-1; a da divisa vem misturada
    res.update(_area_16x9(W, altura_cam))
    res["_quadros"] = quadros
    return res


def _par(n):
    return int(n) - int(n) % 2


def _area_16x9(W, h_cam, y0=0):
    """Maior retangulo 16:9 dentro de (largura W, altura h_cam), centralizado."""
    h = _par(h_cam)
    w = _par(round(h * 16 / 9))
    if w > W:
        w = _par(W)
        h2 = _par(round(w * 9 / 16))
        y0 += (h - h2) // 2
        h = h2
    return {"x": (W - w) // 2, "y": y0, "w": w, "h": h}


def _previa_divisa(area, quadros, destino):
    """Um quadro do original com o retangulo do corte em vermelho (para conferir a deteccao)."""
    from PIL import Image, ImageDraw
    t, q = quadros[len(quadros) // 2]
    im = Image.fromarray(q.astype(np.uint8))
    d = ImageDraw.Draw(im)
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=(255, 0, 0), width=3)
    im.save(destino, quality=90)


def _encoder(cfg, src, vf, work):
    """h264_qsv (placa Intel, ~3x mais rapido) se funcionar neste video; senao libx264.
    Devolve (nome, final do filtro, args do codec)."""
    teste = work / "_teste_qsv.mp4"
    r = subprocess.run([cfg["paths"]["ffmpeg"], "-v", "error", "-y", "-ss", "1", "-t", "1", "-i", str(src), "-an",
                        "-vf", vf + ",format=nv12", "-c:v", "h264_qsv", "-global_quality", "21", str(teste)],
                       capture_output=True, timeout=120)
    teste.unlink(missing_ok=True)
    if r.returncode == 0:
        return "qsv", ",format=nv12", ["-c:v", "h264_qsv", "-preset", "slow", "-global_quality", "21", "-look_ahead", "1"]
    return "x264", "", ["-c:v", "libx264", "-preset", "faster", "-crf", "20", "-pix_fmt", "yuv420p"]


def _renomear(tmp, out, tentativas=30):
    """O Explorer (miniatura) ou o antivirus seguram o mp4 recem-criado por alguns segundos (WinError 32)."""
    for i in range(tentativas):
        try:
            tmp.replace(out)
            return
        except PermissionError:
            if i == tentativas - 1:
                raise
            time.sleep(2)


def _contar_quadros(cfg, path):
    return int(_ffprobe(cfg, path, "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0") or 0)


def cortar(cfg, video, saida_dir=None, area=None, so_detectar=False, forcar=False, alvo=(1920, 1080)):
    src = Path(video)
    saida_dir = Path(saida_dir or cfg["paths"].get("ready_camera", SAIDA_PADRAO))
    saida_dir.mkdir(parents=True, exist_ok=True)
    out = saida_dir / f"{src.stem}_SO_CAMERA_{alvo[1]}p.mp4"
    work = Path(cfg["paths"]["work"]) / "camera" / src.stem
    if out.exists() and not forcar and not so_detectar:
        log(f"camera: {out.name} ja existe (use --forcar para refazer)")
        return {"saida": str(out), "pulado": True}

    inf = info(cfg, src)
    log(f"camera: {src.name} {inf['w']}x{inf['h']} {inf['dur'] / 60:.1f} min")
    if area:
        x, y, w, h = (int(v) for v in area.split(":"))
        det = {"x": x, "y": y, "w": w, "h": h, "manual": True, "achou": True}
        det["_quadros"] = [(0, _quadro(cfg, src, inf["dur"] / 2, inf["w"], inf["h"]))]
    else:
        det = detectar(cfg, src, inf)
    previa = saida_dir / f"{src.stem}_SO_CAMERA_area.jpg"
    _previa_divisa(det, det.pop("_quadros"), previa)
    if det.get("achou"):
        log(f"camera: area {det['w']}x{det['h']} em x={det['x']} y={det['y']}"
            + ("" if det.get("manual") else f" (divisa na linha {det['divisa']}, forca {det['forca']}, presente em "
               f"{int(det['presenca'] * 100)}% dos quadros"
               + (f"; outras bordas fixas em {det['outras_bordas']}" if det["outras_bordas"] else "") + ")"))
    else:
        log(f"camera: NAO achei a divisa - {det.get('motivo')}")
    log(f"camera: previa da area (retangulo vermelho): {previa}")
    if so_detectar:
        return {"area": det, "previa": str(previa)}
    if not det.get("achou") and abs(inf["w"] / inf["h"] - 16 / 9) > 0.05:
        raise RuntimeError(f"nao achei onde a camera termina e o video nao e deitado 16:9. Veja a previa ({previa}) "
                           f"e rode de novo com --area X:Y:LARGURA:ALTURA")

    work.mkdir(parents=True, exist_ok=True)
    corte = (f"crop={det['w']}:{det['h']}:{det['x']}:{det['y']},"
             f"scale={alvo[0]}:{alvo[1]}:flags=lanczos,setsar=1")
    nome_enc, fim_vf, enc = _encoder(cfg, src, corte, work)
    fps, v_ini = inf["fps"], inf["v_ini"]
    q_src = _contar_quadros(cfg, src)
    por_pedaco = round(PEDACO_S * fps)
    n_ped = max(1, math.ceil(q_src / por_pedaco))
    pedacos = []
    for i in range(n_ped):
        seg = work / f"seg_{i:02d}.mp4"
        ok = work / f"seg_{i:02d}.ok"
        esperado = min(por_pedaco, q_src - i * por_pedaco)
        if not (ok.exists() and seg.exists()):
            # pedaco = quadros [i*N, (i+1)*N) no tempo do PROPRIO video (-copyts: tempos absolutos; meio quadro de folga
            # nas bordas para cada quadro cair em um pedaco so). O -ss so pula ate perto, o trim corta exato.
            t0 = v_ini + (i * por_pedaco - 0.5) / fps
            t1 = v_ini + ((i + 1) * por_pedaco - 0.5) / fps if i < n_ped - 1 else None
            pula = ["-ss", f"{max(0.0, t0 - 15):.3f}"] if i else []
            vf = (f"trim=start={t0:.6f}" + (f":end={t1:.6f}" if t1 else "") + ",setpts=PTS-STARTPTS,"
                  + corte + fim_vf)
            for tent in range(1, 4):
                log(f"camera: pedaco {i + 1}/{n_ped} ({nome_enc}) tentativa {tent}")
                r = subprocess.run([cfg["paths"]["ffmpeg"], "-v", "error", "-y", "-copyts", *pula, "-i", str(src),
                                    "-an", "-vf", vf, *enc, str(seg)], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
                if r.returncode == 0:
                    feitos = _contar_quadros(cfg, seg)
                    if feitos != esperado:
                        raise RuntimeError(f"pedaco {i + 1} saiu com {feitos} quadros, esperado {esperado}")
                    ok.write_text("ok")
                    break
                log(f"camera: pedaco {i + 1} falhou: {(r.stderr or '').strip()[-200:]}")
            else:
                raise RuntimeError(f"pedaco {i + 1} nao saiu em 3 tentativas (memoria?). Rode de novo: continua dele.")
        pedacos.append(seg)

    lista = work / "lista.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in pedacos), encoding="utf-8")
    junto = work / "video_junto.mp4"
    run([cfg["paths"]["ffmpeg"], "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
         str(junto)])

    # audio alinhado ao 1o quadro do video: o video novo comeca em 0 = instante v_ini do original
    tmp = out.with_suffix(".parcial.mp4")
    if not inf["audio"]:
        aud, alinhamento = [], "sem audio"
    elif abs(inf["a_ini"] - v_ini) <= 0.5 / fps:
        aud, alinhamento = ["-map", "1:a:0", "-c:a", "copy"], "audio copiado (ja comecava junto)"
    else:
        dif = inf["a_ini"] - v_ini
        af = (f"adelay={round(dif * 1000)}:all=1,asetpts=PTS-STARTPTS" if dif > 0
              else f"atrim=start={v_ini:.6f},asetpts=PTS-STARTPTS")
        aud = ["-map", "1:a:0", "-af", af, "-c:a", "aac", "-b:a", "192k"]
        alinhamento = (f"o video comecava {abs(dif):.2f} s {'antes' if dif > 0 else 'depois'} do audio no original: "
                       f"audio alinhado")
    # -copyts so quando o filtro de audio corta/atrasa em tempo absoluto; copiado, cada entrada ja comeca do 0
    absoluto = ["-copyts"] if "-af" in aud else []
    run([cfg["paths"]["ffmpeg"], "-v", "error", "-y", *absoluto, "-i", str(junto), "-i", str(src), "-map", "0:v:0",
         "-c:v", "copy", *aud, "-movflags", "+faststart", str(tmp)])
    log(f"camera: {alinhamento}")

    q_out = _contar_quadros(cfg, tmp)
    if q_out != q_src:
        raise RuntimeError(f"quadros nao batem: original {q_src}, saida {q_out} (saida parcial em {tmp})")
    if inf["audio"]:
        ini = info(cfg, tmp)
        if abs(ini["a_ini"] - ini["v_ini"]) > 0.05:
            raise RuntimeError(f"audio e video nao comecam juntos na saida ({ini['a_ini']} x {ini['v_ini']}): {tmp}")
    _renomear(tmp, out)
    shutil.rmtree(work, ignore_errors=True)
    mb = out.stat().st_size / 1e6
    log(f"camera: PRONTO {out} ({alvo[0]}x{alvo[1]}, {inf['dur'] / 60:.1f} min, {mb:.0f} MB, {q_out} quadros = original)")
    return {"saida": str(out), "area": det, "encoder": nome_enc, "quadros": q_out, "mb": round(mb)}


def cortar_tudo(cfg, alvo, **kw):
    p = Path(alvo)
    videos = (sorted(v for v in p.iterdir() if v.suffix.lower() in VIDEO_EXT and "_SO_CAMERA_" not in v.name)
              if p.is_dir() else [p])
    res = []
    for v in videos:
        try:
            res.append(cortar(cfg, v, **kw))
        except Exception as e:  # noqa: BLE001
            log(f"camera: ERRO em {v.name}: {e}")
            res.append({"video": str(v), "erro": str(e)})
    return res
