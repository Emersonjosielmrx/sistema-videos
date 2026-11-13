"""Memoria dos videos ja feitos - para nao processar (nem postar) a mesma coisa duas vezes.

Cada gravacao processada fica em work/memoria_videos.json com:
- nome da gravacao, duracao, tamanho e impressao do arquivo (sha1 de 2 MB do comeco + 2 MB do fim);
- impressao visual do video reagido: dHash (64 bits) do centro do conteudo, 1 quadro a cada 1,5 s;
- status, canal, saidas e assunto.
Duas checagens:
1. Antes de processar (batch): mesmo arquivo (impressao), ou mesmo nome de gravacao com a mesma duracao = JA FEITO, pula.
   Pega o mesmo video baixado de novo do Drive (data do arquivo muda, conteudo nao).
2. Depois do layout (process): mesmo VIDEO REAGIDO gravado de novo (muitos quadros iguais aos de outra gravacao) = REPETIDO,
   nao renderiza (salvo --forcar-repetido). Pega o caso "espada de mola" reagida duas vezes, mesmo sem fala em comum.
"""
import hashlib
import json
import subprocess
import time
from pathlib import Path
import numpy as np
from .common import log, load_json, save_json


def _arq(cfg):
    return Path(cfg["paths"]["work"]) / "memoria_videos.json"


def carregar(cfg):
    p = _arq(cfg)
    return load_json(p) if p.exists() else {}


def salvar(cfg, mem):
    save_json(mem, _arq(cfg))


def impressao_arquivo(path, bloco=2 * 1024 * 1024):
    p = Path(path)
    h = hashlib.sha1(str(p.stat().st_size).encode())
    with open(p, "rb") as f:
        h.update(f.read(bloco))
        if p.stat().st_size > 2 * bloco:
            f.seek(-bloco, 2)
            h.update(f.read(bloco))
    return h.hexdigest()[:20]


def hashes_quadros(cfg, video, caixa, passo=0.5):
    """dHash do quadrado central da caixa (x0, y0, x1, y1), 1 quadro a cada `passo` s, numa passada do ffmpeg."""
    x0, y0, x1, y1 = [int(v) for v in caixa]
    lado = min(x1 - x0, y1 - y0) // 2 * 2
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    vf = f"fps=1/{passo},crop={lado}:{lado}:{cx - lado // 2}:{cy - lado // 2},scale=9:8:flags=area,format=gray"
    r = subprocess.run([cfg["paths"]["ffmpeg"], "-hide_banner", "-loglevel", "error", "-threads", "2", "-i", str(video), "-an",
                        "-vf", vf, "-f", "rawvideo", "-"], capture_output=True, timeout=900)
    dados = np.frombuffer(r.stdout, np.uint8)
    out = []
    for i in range(len(dados) // 72):
        q = dados[i * 72:(i + 1) * 72].reshape(8, 9).astype(np.int16)
        if q.std() > 6:  # tela preta/lisa nao identifica nada
            out.append(int("".join("1" if v else "0" for v in (q[:, 1:] > q[:, :-1]).flatten()), 2))
    return out


def _parecido(a, b, dist=10):
    """Fracao dos quadros de `a` que tem um quadro quase igual em `b`."""
    if not a or not b:
        return 0.0
    B = np.array(b, dtype=np.uint64)
    hit = 0
    for x in a:
        xo = np.bitwise_xor(B, np.uint64(x))
        bits = np.unpackbits(xo.view(np.uint8)).reshape(len(B), 64).sum(axis=1)
        if bits.min() <= dist:
            hit += 1
    return hit / len(a)


def ja_feito(cfg, video, mem=None):
    """Entrada da memoria se esta gravacao ja foi processada (mesmo arquivo, ou mesmo nome + mesma duracao)."""
    from .pipeline import slugify
    from . import probe as P
    mem = mem if mem is not None else carregar(cfg)
    slug = slugify(Path(video).stem)
    try:
        imp = impressao_arquivo(video)
    except OSError:
        imp = None
    for e in mem.values():
        if imp and e.get("impressao") == imp:
            return e
    e = mem.get(slug)
    if e and e.get("duracao"):
        dur = P.probe(cfg, video)["duration"]
        if abs(dur - e["duracao"]) < 0.6:
            return e
    return None


def repetido(cfg, slug, hashes, limiar=None, mem=None):
    """(entrada, fracao) da gravacao anterior com o mesmo video reagido, ou None."""
    limiar = limiar if limiar is not None else float(cfg.get("memoria", {}).get("limiar_repetido", 0.35))
    mem = mem if mem is not None else carregar(cfg)
    melhor = None
    for s, e in mem.items():
        # so gravacao x gravacao: impressao tirada do Short final (recortado, com legenda) nao bate com a gravacao
        if s == slug or not e.get("hashes") or e.get("hashes_origem") == "saida" or e.get("status") not in ("done", "repetido_forcado"):
            continue
        r = max(_parecido(hashes, e["hashes"]), _parecido(e["hashes"], hashes))
        if melhor is None or r > melhor[1]:
            melhor = (e, r)
    if melhor and melhor[1] >= limiar:
        return melhor
    return None


def registrar(cfg, slug, video, duracao, status, canal=None, saidas=None, assunto=None, hashes=None):
    mem = carregar(cfg)
    e = mem.get(slug, {})
    try:
        imp = impressao_arquivo(video)
    except OSError:
        imp = e.get("impressao")
    e.update({"slug": slug, "arquivo": Path(video).name, "duracao": round(float(duracao), 2), "impressao": imp,
              "status": status, "canal": canal, "saidas": saidas or e.get("saidas", []), "assunto": assunto or e.get("assunto"),
              "quando": time.strftime("%Y-%m-%d %H:%M")})
    if hashes is not None:
        e["hashes"], e["hashes_origem"] = hashes, "gravacao"
    mem[slug] = e
    salvar(cfg, mem)
    return e


def _trigramas(words):
    from .base import _norm
    ws = [x for x in (_norm(w["w"]) for w in words) if x]
    return {tuple(ws[i:i + 3]) for i in range(len(ws) - 2)}


def repetido_texto(cfg, slug, words, limiar=0.3, mem=None):
    """Mesmo video reagido pela FALA: fracao de trigramas em comum com outra gravacao ja feita (vale quando o
    video reagido tem narracao/dialogo). (entrada, fracao) ou None."""
    mem = mem if mem is not None else carregar(cfg)
    a = _trigramas(words)
    if len(a) < 20:
        return None
    melhor = None
    for s, e in mem.items():
        tp = Path(cfg["paths"]["work"]) / s / "transcript.json"
        if s == slug or e.get("status") not in ("done", "repetido_forcado") or not tp.exists():
            continue
        b = _trigramas(load_json(tp)["words"])
        if len(b) < 20:
            continue
        r = len(a & b) / min(len(a), len(b))
        if melhor is None or r > melhor[1]:
            melhor = (e, r)
    if melhor and melhor[1] >= limiar:
        return melhor
    return None


def preencher_com_o_que_ja_existe(cfg):
    """Registra na memoria tudo o que ja foi processado (work/<slug>/summary.json). Se a gravacao original sumiu,
    a impressao visual sai do Short final (centro da area do conteudo)."""
    mem = carregar(cfg)
    work = Path(cfg["paths"]["work"])
    prontos = [Path(cfg["paths"][k]) for k in ("ready", "ready_cortes") if cfg["paths"].get(k)]
    n = 0
    for sp in sorted(work.glob("*/summary.json")):
        slug = sp.parent.name
        if slug in mem and mem[slug].get("hashes"):
            continue
        s = load_json(sp)
        probe = load_json(sp.parent / "probe.json") if (sp.parent / "probe.json").exists() else {}
        video = s.get("video") or probe.get("path", "")
        ed = s.get("editorial") or {}
        hashes = None
        if Path(video).exists() and (sp.parent / "layout.json").exists():
            hashes = hashes_quadros(cfg, video, load_json(sp.parent / "layout.json")["content"])
        else:
            saidas = sorted(p for pasta in prontos for p in pasta.glob(f"*/{slug}*.mp4"))
            plan = load_json(sp.parent / "plan.json") if (sp.parent / "plan.json").exists() else None
            if saidas and plan:
                y0 = int(plan["content"]["out_y"]) + 60
                hashes = []
                for mp4 in saidas:  # corpo do Short sem a faixa de legenda/CTA de baixo
                    hashes += hashes_quadros(cfg, mp4, [0, y0, 1080, 1920 - 200])
        e = mem.get(slug, {})
        e.update({"slug": slug, "arquivo": Path(video).name if video else slug, "duracao": round(float(s.get("duration") or probe.get("duration") or 0), 2),
                  "status": s.get("status") or ("done" if s.get("outputs") else "?"), "canal": s.get("channel"),
                  "saidas": [Path(o["file"]).name for o in s.get("outputs", [])], "assunto": ed.get("topic") or ed.get("work"),
                  "quando": e.get("quando") or time.strftime("%Y-%m-%d %H:%M")})
        if Path(video).exists():
            e["impressao"] = impressao_arquivo(video)
        if hashes:
            e["hashes"] = hashes
            e["hashes_origem"] = "gravacao" if Path(video).exists() else "saida"
        mem[slug] = e
        n += 1
        log(f"memoria: {slug} ({e['status']}, {e['canal']}, {len(e.get('hashes') or [])} quadros)")
    salvar(cfg, mem)
    log(f"memoria: {n} gravacao(oes) registrada(s); total {len(mem)}")
    return mem
