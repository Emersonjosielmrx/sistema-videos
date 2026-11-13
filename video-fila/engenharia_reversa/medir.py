"""Mede o VÍDEO de cada amostra (29/10), sem IA: duração, cortes (ffmpeg scdet), cortes nos 2 primeiros segundos,
1º corte, volume do começo x resto, silêncio no começo, e do .info.json data/likes/comentários/views atuais.
Grava 1 linha por vídeo em medidas.jsonl (já medido = pula). Também pode medir um vídeo NOSSO: medir.py <mp4>.
Os vídeos baixados são dado de fora: só passam pelo ffmpeg/ffprobe, nunca são executados nem importados."""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
AMOSTRAS = Path(r"D:\hipercool-materiais\engenharia_reversa\amostras")
MEDIDAS = AQUI / "medidas.jsonl"


def _ff(args, timeout=300):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def duracao(mp4):
    r = _ff(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate",
             "-of", "json", str(mp4)])
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("width")), {})
    return float(d.get("format", {}).get("duration") or 0), v.get("width"), v.get("height")


def cortes(mp4, limiar=10, ate=None):
    lim = ["-t", str(ate)] if ate else []
    r = _ff(["ffmpeg", "-hide_banner", "-nostats", *lim, "-i", str(mp4), "-an", "-vf",
             f"scale=160:-2,scdet=threshold={limiar}", "-f", "null", "-"], timeout=600)
    return [float(t) for t in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", r.stderr)]


def volume(mp4, ini, fim):
    r = _ff(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(ini), "-to", str(fim), "-i", str(mp4), "-vn",
             "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume:\s*(-?[\d.]+)", r.stderr)
    return float(m.group(1)) if m else None


def silencio_inicial(mp4):
    r = _ff(["ffmpeg", "-hide_banner", "-nostats", "-t", "5", "-i", str(mp4), "-vn",
             "-af", "silencedetect=noise=-35dB:d=0.2", "-f", "null", "-"])
    ini = re.findall(r"silence_start:\s*(-?[\d.]+)", r.stderr)
    fim = re.findall(r"silence_end:\s*([\d.]+)", r.stderr)
    if ini and float(ini[0]) <= 0.05:
        return float(fim[0]) if fim else 5.0
    return 0.0


def medir(mp4, janela=None):
    """`janela` (s): mede só o começo do vídeo. 30/10: as fontes do Cortes têm 40 min a 3,5 h em AV1 e este PC decodifica
    AV1 a ~0,4× o tempo real (libaom, sem dav1d) — 13 de 36 deram TimeoutExpired e cada uma gastava 10 min da passada.
    O que importa da fonte (gancho, 1º corte, silêncio, volume do começo) está no início; cortes_s/maior_plano_s/vol_resto
    passam a valer para a janela (campo janela_s na linha)."""
    dur, w, h = duracao(mp4)
    fim = min(dur, janela) if janela and dur > janela else dur
    cs = cortes(mp4, ate=janela if fim < dur else None)
    out = {"dur": round(dur, 2), "w": w, "h": h, "n_cortes": len(cs),
           "cortes_s": round(len(cs) / fim, 3) if fim else None,
           "cortes_2s": sum(t <= 2 for t in cs), "primeiro_corte": round(cs[0], 2) if cs else None,
           "maior_plano_s": round(max([b - a for a, b in zip([0] + cs, cs + [fim])] or [fim]), 2),
           "vol_2s": volume(mp4, 0, 2), "vol_resto": volume(mp4, 2, fim) if fim > 3 else None,
           "silencio_ini_s": silencio_inicial(mp4)}
    if fim < dur:
        out["janela_s"] = round(fim, 2)
    if out["vol_2s"] is not None and out["vol_resto"] is not None:
        out["vol_dif"] = round(out["vol_2s"] - out["vol_resto"], 1)
    return out


def info(pasta):
    try:
        d = json.loads((pasta / "video.info.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    up = d.get("upload_date")
    idade = (date.today() - date(int(up[:4]), int(up[4:6]), int(up[6:]))).days if up else None
    v = d.get("view_count") or 0
    return {"upload": up, "idade_dias": idade, "views_agora": v, "likes": d.get("like_count"),
            "comentarios": d.get("comment_count"), "inscritos_canal": d.get("channel_follower_count"),
            "likes_por_mil": round(1000 * (d.get("like_count") or 0) / v, 1) if v else None,
            "titulo": d.get("title"), "descricao_len": len(d.get("description") or ""),
            "tags_n": len(d.get("tags") or [])}


def main():
    if len(sys.argv) > 1:  # vídeo avulso (nosso)
        print(json.dumps(medir(Path(sys.argv[1])), ensure_ascii=False, indent=1))
        return
    feitos = set()
    if MEDIDAS.exists():
        for ln in MEDIDAS.read_text(encoding="utf-8").splitlines():
            try:
                feitos.add(json.loads(ln)["pasta"])
            except (ValueError, KeyError):
                pass
    n = 0
    for mp4 in sorted(AMOSTRAS.glob("*/*/video.mp4")):
        pasta = mp4.parent
        if str(pasta) in feitos:
            continue
        try:
            lista = json.loads((pasta / "lista.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        linha = {"pasta": str(pasta), "parceiro": lista.get("parceiro_nome"), "grupo": lista.get("grupo"),
                 "id": lista.get("id"), "views_lista": lista.get("views"), **info(pasta)}
        try:
            linha.update(medir(mp4))
        except Exception as e:  # noqa: BLE001
            linha["erro"] = f"{type(e).__name__}: {e}"
        with open(MEDIDAS, "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        (pasta / "video.info.json").unlink(missing_ok=True)  # ~600 KB cada; o que interessa já está na linha
        n += 1
        print(f"medido {linha['parceiro']} {linha['grupo']} dur {linha.get('dur')} cortes/s {linha.get('cortes_s')} "
              f"2s {linha.get('cortes_2s')} idade {linha.get('idade_dias')}")
    print(f"{n} medidos agora")


if __name__ == "__main__":
    main()
