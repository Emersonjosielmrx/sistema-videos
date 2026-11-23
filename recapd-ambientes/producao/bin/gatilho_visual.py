"""Gatilho de piada pela IMAGEM (dona 20/11: "os gatilhos de piadas gerais têm que ser pela imagem também,
principalmente os de duplo sentido sexual"; "mulher bonita com seios grandes na tela = 'com todo respeito',
obrigatório").

Para cada frase com momento conhecido no vídeo-fonte (tempos do roteiro), pega 1 quadro e o CLIP (zero-shot, funciona
em desenho de anime/manhwa) diz se a cena é SENSUAL (mulher bonita/decote/pose provocante), ENGRAÇADA (cara de
susto/vergonha/careta) ou neutra. Resultado em <pasta>/_gatilho_visual.json {i: "sensual"|"comico"|""}.
O anime_segments usa: frase "sensual" sem duplo sentido ganha o "com todo respeito" (o S é esticado na voz).
Sem GPU/CLIP = {} (nada muda). GATILHO_VISUAL=0 desliga.
"""
import json
import logging
import os
import subprocess
from pathlib import Path

ROTULOS = {
    "sensual": ["an anime drawing of a sexy woman with large breasts and cleavage",
                "a manhwa panel of a beautiful attractive woman in a revealing outfit, short top or bikini",
                "an anime girl in a seductive pose showing her body"],
    "comico": ["an anime character with a funny embarrassed face, blushing and sweating",
               "a chibi comedic anime reaction face", "an anime character shocked with a goofy expression"],
    # 20/11 (teste em 30 quadros reais): "dois homens conversando no estacionamento" saiu sensual 0,49 — o neutro
    # precisa cobrir HOMENS conversando/em pé e cenas sem mulher, senão o CLIP joga gente qualquer no sensual
    "neutro": ["an anime fight scene with action", "an anime landscape or building", "an anime man talking seriously",
               "two anime men talking to each other", "an anime boy in a t-shirt standing", "an anime man next to a car",
               "a dark dramatic anime scene", "an anime group of people walking", "a fully clothed anime schoolgirl"],
}
LIMIAR = {"sensual": 0.30, "comico": 0.55}  # 20/11: calibrado em 30 quadros reais (sensual certos 0,34-0,36; errados <= 0,19)


def _vec(x):
    """transformers novo devolve BaseModelOutputWithPooling em get_*_features; o antigo, o tensor."""
    import torch
    if isinstance(x, torch.Tensor):
        return x
    for k in ("text_embeds", "image_embeds", "pooler_output"):
        v = getattr(x, k, None)
        if v is not None:
            return v
    return x[0]


def _quadro(video, t, dst):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, t):.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=448:-2", str(dst)], capture_output=True)
    return r.returncode == 0 and Path(dst).exists()


def classificar(video, lines, tempos, pasta):
    """{i: 'sensual'|'comico'} pras frases com tempo. Cache em _gatilho_visual.json."""
    if os.environ.get("GATILHO_VISUAL", "1") == "0" or not tempos:
        return {}
    cache = Path(pasta) / "_gatilho_visual.json"
    try:
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("n") == len(lines):
            return {int(k): v for k, v in d["tags"].items()}
    except (OSError, ValueError, KeyError):
        pass
    try:
        import torch
        if not torch.cuda.is_available():
            return {}
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor
        nome = "openai/clip-vit-base-patch32"
        model = CLIPModel.from_pretrained(nome).to("cuda").eval()
        proc = CLIPProcessor.from_pretrained(nome)
        textos, dono = [], []
        for k, lst in ROTULOS.items():
            textos += lst
            dono += [k] * len(lst)
        tags, tmp = {}, Path(pasta) / "_gv_quadros"
        tmp.mkdir(exist_ok=True)
        for i, _l in enumerate(lines):
            t = tempos[i] if i < len(tempos) else None
            if isinstance(t, (list, tuple)):
                t = (float(t[0]) + float(t[1])) / 2 if len(t) >= 2 else float(t[0])
            if t is None:
                continue
            q = tmp / f"q{i}.jpg"
            if not _quadro(video, float(t), q):
                continue
            ent = proc(text=textos, images=Image.open(q).convert("RGB"), return_tensors="pt", padding=True).to("cuda")
            with torch.no_grad():
                p = model(**ent).logits_per_image.softmax(dim=-1)[0].tolist()  # caminho zero-shot oficial do CLIP
            soma = {}
            for k, v in zip(dono, p):
                soma[k] = soma.get(k, 0) + v
            # 20/11: sensual decide pelo limiar próprio (mesmo sem ser o maior: o neutro "puxa" cena de anime comum);
            # cômico só quando ganha de todos
            if soma.get("sensual", 0) >= LIMIAR["sensual"]:
                tags[i] = "sensual"
            elif max(soma, key=soma.get) == "comico" and soma["comico"] >= LIMIAR["comico"]:
                tags[i] = "comico"
        cache.write_text(json.dumps({"n": len(lines), "tags": tags}), encoding="utf-8")
        logging.info(f"[gatilho visual] {sum(1 for v in tags.values() if v == 'sensual')} cenas sensuais, "
                     f"{sum(1 for v in tags.values() if v == 'comico')} cômicas (de {len(lines)} frases)")
        return tags
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[gatilho visual] desligado neste vídeo ({type(e).__name__}: {str(e)[:120]})")
        return {}


_JA_TEM = None


_PIADAS = set()  # índices com a piada do respeito (a voz lê via RESPEITO_PIADA)


def aplicar(lines, tags):
    """23/11 dona: a piada do RES-peito na 1ª vez que uma mulher bonita aparece (cena sensual pela imagem + frase
    falando dela), no máximo RESPEITO_MAX (2) por vídeo, longe uma da outra. Devolve (lines, quantas mudaram)."""
    import re
    lines, n = list(lines), 0
    maxi = int(os.environ.get("RESPEITO_MAX", "2"))
    ela = re.compile(r"(?i)\b(ela|dela|mulher|moça|garota|menina|esposa|namorada|noiva|rainha|princesa|dama|"
                     r"senhorita|madame|secretária|professora|enfermeira|chefe|CEO|herdeira|filha|irmã|amiga|"
                     r"bela|linda|bonita|gata|mina)\b")
    ja_feitas = [i for i, l in enumerate(lines) if re.search(r"RES+[\s.\-…]*[Pp]eito", l or "")]
    n_tot = max(1, len(lines))
    feitas = list(ja_feitas)
    for i, tag in sorted(tags.items()):
        if len(feitas) >= maxi:
            break
        if tag != "sensual" or i >= len(lines) or not ela.search(lines[i] or ""):
            continue
        if re.search(r"(?i)respeit", lines[i]) or any(abs(i - j) < n_tot / 3 for j in feitas):
            continue
        frase = lines[i].rstrip()
        fim = frase[-1] if frase and frase[-1] in ".!?" else "."
        lines[i] = frase.rstrip(".!?…") + ", com todo respeito" + fim
        feitas.append(i)
        _PIADAS.add(i)
        n += 1
    os.environ["RESPEITO_PIADA"] = ",".join(str(x) for x in sorted(_PIADAS | set(ja_feitas)))
    return lines, n
