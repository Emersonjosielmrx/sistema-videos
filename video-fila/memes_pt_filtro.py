# -*- coding: utf-8 -*-
"""Filtro dos memes pt: transcreve (Groq Whisper), corta o que vem ANTES da frase do meme (propaganda, vinheta,
apresentação) e o que sobra muito depois; meme falado em inglês vai para _ingles. Som sem fala não é mexido.
Original fica em memes_pt\\_originais.  Uso: python memes_pt_filtro.py [arquivo.mp4 ...]  (sem args = pasta toda)"""
import json, re, shutil, subprocess, sys, tempfile, unicodedata
from pathlib import Path

import types  # noqa: E402
sys.modules.setdefault("hp_common", types.SimpleNamespace(log=lambda *a, **k: print(*a, file=sys.stderr)))
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import groq_api  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
PASTA = Path(r"C:\Users\Haylla\Desktop\memes_pt")
ORIG = PASTA / "9_NAO USAR (ingles, duplicados, backups)" / "originais"
INGLES = PASTA / "9_NAO USAR (ingles, duplicados, backups)" / "ingles"
REV = PASTA / "3_VER - filtro em duvida (ouvir)"
FEITOS = ORIG / "filtro.json"
SEM_FALA = re.compile(r"som_de|efeito|sonoro|grilo|aplauso|tapa|batida|tururu|risada|_som_|sfx", re.I)
VAZIAS = {"meme", "som", "efeito", "sonoro", "faustao", "br", "de", "do", "da", "o", "a", "e", "que",
          # 24/11: rótulos da busca, não fala do meme (o 102 cortou por "galera"+"faustao"; o 103 exigia "xaropinho")
          "shorts", "brasileiro", "original", "xaropinho", "ratinho", "galvao", "classico", "audio", "curto"}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def frase_do_nome(p):
    m = re.match(r"\d+_(.+?)__", p.name)
    return [w for w in norm((m.group(1) if m else p.stem).replace("_", " ")).split() if w not in VAZIAS]


def cortar(src, dst, a, b):
    subprocess.run(stdin=subprocess.DEVNULL, timeout=120, args=[FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.2f}", "-i", str(src),
                    "-t", f"{b - a:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac",
                    "-b:a", "160k", "-af", "afade=t=in:d=0.05", str(dst)], check=True)


def dur(p):
    r = subprocess.run([FF.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of",
                        "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def mp3_pt(p):
    t = Path(tempfile.mkdtemp()) / "a.wav"
    subprocess.run(stdin=subprocess.DEVNULL, timeout=120, args=[FF, "-nostdin", "-loglevel", "error", "-y", "-i", str(p), "-map", "0:a:0", "-ac", "1", "-ar", "16000", str(t)], check=True)
    return t


def filtrar(p, feitos):
    if p.name in feitos:
        return feitos[p.name]
    chave = frase_do_nome(p)
    with tempfile.TemporaryDirectory() as td:
        mp3 = Path(td) / "a.wav"
        subprocess.run(stdin=subprocess.DEVNULL, timeout=120, args=[FF, "-nostdin", "-loglevel", "error", "-y", "-i", str(p), "-map", "0:a:0", "-ac", "1", "-ar", "16000", str(mp3)], check=True)
        j = groq_api.transcrever(str(mp3), idioma="auto", palavras=True)
    if not j:
        return "sem transcrição (Groq falhou) — não mexi"
    txt, lang = (j.get("text") or "").strip(), (j.get("language") or "").lower()
    pal = j.get("words") or []
    D = dur(p)
    if not pal or len(norm(txt).split()) < 1:
        return "sem fala — ok"
    if lang.startswith("en") and not SEM_FALA.search(p.name):
        # áudio curto engana o detector: confirma forçando pt — se em pt sai a frase do meme, é pt
        jp = groq_api.transcrever(str(mp3_pt(p)), idioma="pt", palavras=True) or {}
        tpt = norm(jp.get("text") or "").split()
        if any(c in tpt for c in chave if len(c) >= 3):
            j, txt, pal, lang = jp, jp.get("text", "").strip(), jp.get("words") or [], "pt"
    # 24/11: áudio curto (< 3 s) o detector erra (pt curto saiu "croata"/"inglês") — não manda pra _ingles
    if lang.startswith("en") and not SEM_FALA.search(p.name) and len(pal) >= 3 and D >= 3.0:
        INGLES.mkdir(exist_ok=True)
        shutil.move(str(p), INGLES / p.name)
        return f"INGLÊS → _ingles ({txt[:60]})"
    if SEM_FALA.search(p.name):
        return f"som (fala: {txt[:50]}) — ok"
    def bate(nw, c):
        return nw == c or (len(c) > 3 and len(nw) > 3 and (nw.startswith(c[:4]) or c.startswith(nw[:4])))
    fortes = [c for c in chave if len(c) >= 3] or chave
    ditas = set(norm(txt).split())
    achou = [c for c in fortes if any(bate(d, c) for d in ditas)]
    ini = None
    # 24/11: com 1 palavra só de 2+ da frase não corta (o 102 cortou cena errada por "galera") — manda pra revisão
    if len(fortes) >= 2 and len(achou) < 2:
        achou = []
    if achou and len(achou) * 2 >= len(fortes):
        for w in pal:
            nw = norm(w.get("word", "")).strip()
            if nw and any(bate(nw, c) for c in achou):
                ini = float(w["start"]); break
    if ini is None:
        REV.mkdir(exist_ok=True)
        if p.parent != REV:
            shutil.move(str(p), REV / p.name)
        return f"FRASE NÃO ACHADA → revisão ({txt[:70]})"
    # fim: última palavra da frase + folga
    fim = D
    ultimos = [float(w["end"]) for w in pal if any(norm(w.get("word", "")).strip().startswith(c[:4]) for c in chave if len(c) > 2)]
    if ultimos and D - max(ultimos) > 3.0:
        fim = min(D, max(ultimos) + 1.2)
    a = max(0.0, ini - 0.25)
    if a < 0.8 and fim >= D - 0.1:
        return f"limpo ({txt[:60]})"
    ORIG.mkdir(exist_ok=True)
    bk = ORIG / p.name
    if not bk.exists():
        shutil.copy2(p, bk)
    tmp = p.with_suffix(".tmp.mp4")
    cortar(bk, tmp, a, fim)
    tmp.replace(p)
    if p.parent == REV:  # consertado: volta para a pasta boa
        shutil.move(str(p), PASTA / p.name)
    return f"CORTADO {a:.1f}s→{fim:.1f}s de {D:.1f}s ({txt[:60]})"


def main(arqs):
    ORIG.mkdir(exist_ok=True)
    try:
        feitos = json.loads(FEITOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        feitos = {}
    lista = [Path(a) for a in arqs] or sorted(p for p in PASTA.rglob("*.mp4")
                                             if not any(x in p.parts for x in ("_originais", "_ingles")))
    for p in lista:
        if not p.exists():
            continue
        try:
            r = filtrar(p, feitos)
        except Exception as e:  # noqa: BLE001
            r = f"erro: {e}"
        feitos[p.name] = r
        FEITOS.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{p.name[:55]:55} {r}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
