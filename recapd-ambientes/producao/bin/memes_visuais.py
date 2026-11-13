"""memes_visuais.py — memes VISUAIS no recap longo (dona 29/10: "não vi nenhum meme visual como os do hipercool, que
insere vídeos, memes e figurinhas na tela"). Copiado do D:\\hipercool-videos\\bin\\fx_memes.py:
  - figurinha: o meme estampado por cima do trecho, sem som, quando o narrador fala um gatilho de emoção
    ("eita", "como assim", "coitado"...) — fx_clips._com_figurinha;
  - interrupção: meme em TELA CHEIA com o som dele logo depois de uma fala de emoção forte (choque, deboche,
    vergonha, raiva), no máximo 1 por minuto — anime-pipeline._memes_resumo insere no concat.
Catálogo: config/memes_catalogo.json (o do historias-em-frames); arquivos em workspace/assets/memes_img."""
import json
import random
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "config" / "memes_catalogo.json"
MEMES_IMG = RAIZ / "workspace" / "assets" / "memes_img"

GATILHOS = {
    "choque": ["eita", "caramba", "caraca", "rapaz do céu", "meu deus", "pelo amor de deus", "que isso",
               "misericórdia", "não acredito", "impossível", "olha isso", "levou um susto", "toma um susto",
               "de repente", "sem acreditar", "chocado", "chocada"],
    "confusão": ["como assim", "ué", "hein", "peraí", "entendi nada", "não entende", "sem entender", "confuso"],
    "deboche": ["coitado", "coitada", "tadinho", "tadinha", "já era", "trouxa", "não aprende", "riu da cara",
                "humilhou", "humilhado", "humilhada"],
    "vergonha": ["sem graça", "que vergonha", "envergonhada", "envergonhado", "constrangedor", "corou"],
    "alegria": ["conseguiu", "venceu", "vitória", "comemora", "comemoram", "finalmente"],
    "tristeza": ["chorando", "chora", "triste", "sozinho", "sozinha", "se foi", "lágrimas"],
    "raiva": ["desgraçado", "maldito", "canalha", "cretino", "ousadia", "furioso", "furiosa", "irritado",
              "irritada", "com raiva"],
}
TAGS = {
    "choque": ["choque", "susto", "surpresa", "reação extrema", "pânico"],
    "confusão": ["confusão", "dúvida", "questionamento", "confuso"],
    "deboche": ["deboche", "sarcasmo", "ironia", "julgamento"],
    "vergonha": ["constrangimento", "awkward", "desconforto"],
    "alegria": ["alegria", "felicidade", "sucesso", "vitória"],
    "tristeza": ["tristeza", "choro", "decepção"],
    "raiva": ["raiva", "frustração", "desaprovação"],
}
INTERROMPE = {"choque", "deboche", "vergonha", "raiva"}
# O limite anterior de 3,5 s cortava falas que terminavam depois disso. Mantemos
# apenas uma proteção contra arquivos anômalos; a duração usada no render vem do áudio.
# Faixa apenas para rejeitar arquivos sem fala útil; não limita a duração final.
# 01/11 dona (nV2a: meme de MAIS DE 2 MINUTOS no meio do longo): teto de 12 s. O catálogo tinha a duração errada e o
# montar_clip usava a duração real do arquivo sem teto — agora meme real acima do teto é DESCARTADO (não entra cortado)
INTERROMPE_DUR = (1.0, 12.0)
MEME_TAIL_S = 0.15
_cat = None


def _local(arquivo):
    """O catálogo guarda D:\\hipercool-materiais\\assets\\memes_img\\...; aqui (PC ou Kaggle) é workspace/assets."""
    partes = Path(arquivo.replace("\\", "/")).parts
    if "memes_img" in partes:
        return MEMES_IMG.joinpath(*partes[partes.index("memes_img") + 1:])
    return Path(arquivo)


def catalogo():
    global _cat
    if _cat is None:
        try:
            raw = json.loads(CATALOGO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        _cat = []
        for m in raw.values():
            if m.get("ok"):
                local = _local(m["file"])
                from fx_detect import meme_proibido  # 31/10 dona: Roda Regina / trecho de música = fora
                if (local.exists() and local.suffix.lower() not in (".avif", ".webp")
                        and not meme_proibido(local) and not meme_proibido(m.get("title") or m.get("nome") or "")):
                    _cat.append({**m, "file": str(local)})
    return _cat


def emocao(texto):
    t = " " + re.sub(r"[^\wà-ú ]", " ", (texto or "").lower()) + " "
    for e, termos in GATILHOS.items():
        if any(f" {g} " in t for g in termos) and not (e == "choque" and " por que isso" in t):
            return e
    return None


def escolher(emo, usados, so_com_som=False, rnd=random):
    cand = [m for m in catalogo() if m["file"] not in usados
            and (not so_com_som or (m.get("has_audio") and Path(m["file"]).suffix.lower() == ".mp4"
                                    and INTERROMPE_DUR[0] <= float(m.get("duration") or 0) <= INTERROMPE_DUR[1]))]
    da_emocao = [m for m in cand if any(t.lower() in TAGS.get(emo, []) for t in m.get("tags", []))]
    pool = da_emocao or ([] if so_com_som else cand)
    if not pool:
        return None
    m = rnd.choice(pool)
    usados.add(m["file"])
    return m


def escolher_interrupcoes(textos, inicio=8, cada=12, rnd=random):
    """[(índice da frase, meme)] — depois de frase com emoção FORTE, no mínimo `cada` frases (~1 min) entre elas."""
    out, usados, ultimo = [], set(), -10 ** 6
    for k, texto in enumerate(textos):
        if k < inicio or k > len(textos) - 4 or k - ultimo < cada:
            continue
        emo = emocao(texto)
        if emo not in INTERROMPE:
            continue
        m = escolher(emo, usados, so_com_som=True, rnd=rnd)
        if m:
            out.append((k, m))
            ultimo = k
    return out


IMAGENS = (".jpg", ".jpeg", ".png", ".gif")
IMAGEM_S = 1.2


def escolher_imagens(textos, ocupados=(), inicio=8, cada=10, rnd=random):
    """Dona 31/10: a figurinha no canto não ajudava — meme de IMAGEM agora ocupa a tela toda, rápido (IMAGEM_S), depois
    de frase com qualquer emoção, no mínimo `cada` frases entre eles e fora das frases que já têm meme/série."""
    imgs = [m for m in catalogo() if Path(m["file"]).suffix.lower() in IMAGENS]
    out, usados, ultimo = [], set(), -10 ** 6
    ocupados = set(ocupados)
    for k, texto in enumerate(textos):
        if k < inicio or k > len(textos) - 4 or k - ultimo < cada or any(abs(k - o) < 3 for o in ocupados):
            continue
        emo = emocao(texto)
        if not emo:
            continue
        cand = [m for m in imgs if m["file"] not in usados]
        da_emo = [m for m in cand if any(t.lower() in TAGS.get(emo, []) for t in m.get("tags", []))]
        pool = da_emo or cand
        if not pool:
            continue
        m = rnd.choice(pool)
        usados.add(m["file"])
        out.append((k, m))
        ultimo = k
    return out


def montar_imagem(meme, out_path, w, h, sfx=None, fps=30):
    """Imagem em tela cheia por IMAGEM_S: fundo dela borrado + ela inteira entrando com um soco de zoom (1,25 -> 1)."""
    import subprocess
    d = IMAGEM_S
    entrada = ["-loop", "1", "-t", f"{d:.2f}", "-i", meme["file"]]
    if Path(meme["file"]).suffix.lower() == ".gif":
        entrada = ["-ignore_loop", "0", "-t", f"{d:.2f}", "-i", meme["file"]]
    audio = (["-i", str(sfx)] if sfx else ["-f", "lavfi", "-t", f"{d:.2f}", "-i", "anullsrc=r=44100:cl=stereo"])
    vf = (f"[0:v]fps={fps},format=yuv420p,split[a][b];"
          f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[fundo];"
          f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"scale='trunc(iw*(1+0.25*max(0,1-t/0.18))/2)*2':'trunc(ih*(1+0.25*max(0,1-t/0.18))/2)*2':eval=frame[meio];"
          f"[fundo][meio]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v];"
          f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=duration={d:.2f},"
          f"afade=t=out:st={d - 0.2:.2f}:d=0.2[au]")
    cmd = ["ffmpeg", "-y", "-v", "error", *entrada, *audio, "-filter_complex", vf, "-map", "[v]", "-map", "[au]",
           "-t", f"{d:.2f}", "-r", str(fps), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return Path(out_path).exists() and Path(out_path).stat().st_size > 1000


def montar_clip(meme, out_path, w, h, fps=30):
    """Meme em tela cheia, mantendo a fala inteira do áudio original."""
    import subprocess
    dur = 0.0
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             meme["file"]], capture_output=True, text=True, timeout=15)
        dur = float((probe.stdout or "").strip().splitlines()[0])
    except (ValueError, IndexError, OSError, subprocess.SubprocessError):
        dur = 0.0
    if dur <= 0:
        dur = float(meme.get("duration") or 2.0)
    if dur > INTERROMPE_DUR[1] + 0.5:  # duração real passa do teto (catálogo mentia): o meme não entra
        import logging
        logging.warning(f"[meme] {Path(meme['file']).name} tem {dur:.0f} s de verdade (teto {INTERROMPE_DUR[1]:.0f} s) — fora")
        return False
    # Pequena sobra evita cortar a última sílaba por arredondamento do AAC.
    dur += MEME_TAIL_S
    vf = (f"[0:v]fps={fps},split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"boxblur=20:2[fundo];[b]scale={w}:{h}:force_original_aspect_ratio=decrease[meio];"
          f"[fundo][meio]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", meme["file"],
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
           "-af", "loudnorm=I=-16:TP=-2", "-ar", "44100", "-ac", "2", "-t", f"{dur:.2f}", "-r", str(fps),
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
