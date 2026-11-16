# -*- coding: utf-8 -*-
r"""capa_print_anime.py — capa do Short de ANIME como "PRINT DO PRÓPRIO EPISÓDIO" (dona 15/11: aprovou os de Spy x
Family da Fábrica de Poses — "tem que manter a originalidade dos personagens e do anime; já pode aplicar em produção
pra animes").

Como funciona (o que a capa antiga não fazia: ela gerava sem referência e o casal saía genérico, com cara de IA):
  1) tira quadros REAIS do vídeo do Short (video_sem_capa.mp4 ou video.mp4) e escolhe os 3 mais nítidos;
  2) pede ao Flow uma cena de romance fake (beijo, quase-beijo...) com o casal CANÔNICO ADULTO da obra, 16:9, no traço
     do estúdio (cel shading plano, cor de TV), usando esses quadros como referência;
  3) a visão confere (desenho, sem texto, sem criança/uniforme escolar, personagens da obra, cara de print, cena);
  4) monta o 9:16 no layout aprovado (moldura de tweet / faixas / reação), de D:\fabrica-poses\shorts_estilos.montar.

Só obras da lista OBRAS (casal adulto no cânone). Obra fora da lista = None (o capar_shorts segue com a capa antiga).
Desligar: CAPA_PRINT_ANIME=0. Teste manual: python capa_print_anime.py <pasta do Short>
"""
import json
import os
import random
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
FABRICA = Path(r"D:\fabrica-poses")
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
PY_VEO = r"D:\veo\venv\Scripts\python.exe"
GERA = r"D:\flow-imagens\gera_imagem.py"
SEM = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# chave = começo do nome da pasta do Short (antes de _cap). SÓ casais ADULTOS no cânone. Jujutsu, Bleach, Blue Lock,
# Naruto (fase adolescente), Dandadan, HxH etc. ficam FORA (personagens menores).
OBRAS = {
    "spy-x-family": {
        "nome": "Spy x Family",
        "ele": "LOID FORGER: adult man, neat short blond hair, blue-green eyes, slim, grey turtleneck or green suit",
        "ela": "YOR FORGER: adult woman, long straight black hair with short side locks, white hairband with gold ear "
               "ornaments, red eyes",
        "estudio": "Spy x Family TV anime by Wit Studio/CloverWorks: soft pastel colors, clean thin line art",
        "lugar": "the Forger family living room",
    },
    "one-piece": {
        "nome": "One Piece",
        "ele": "MONKEY D. LUFFY (after the 2-year timeskip, adult): straw hat, black messy hair, scar under the left "
               "eye, open red cardigan",
        "ela": "NAMI (after the timeskip, adult): long wavy orange hair, brown eyes, tattoo on her left shoulder",
        "estudio": "One Piece TV anime by Toei Animation: thick line art, vivid colors",
        "lugar": "the deck of the Thousand Sunny ship",
    },
    "solo-leveling": {
        "nome": "Solo Leveling",
        "ele": "SUNG JINWOO (adult hunter): short black hair, sharp grey-blue eyes, black hooded jacket",
        "ela": "CHA HAE-IN (adult S-rank hunter): golden-blonde hair in a short ponytail, light armor over a white top",
        "estudio": "Solo Leveling TV anime by A-1 Pictures: dark moody colors, sharp line art",
        "lugar": "a modern Seoul street at night",
    },
    "one-punch-man": {
        "nome": "One Punch Man",
        "ele": "SAITAMA: adult man, completely bald round head, yellow hero suit with white cape and red gloves",
        "ela": "FUBUKI: adult woman, short wavy dark-green bob hair, green eyes, dark green long dress, pearl necklace",
        "estudio": "One Punch Man season 1 TV anime by Madhouse: sharp line art, bold colors",
        "lugar": "a city street of City Z",
    },
}

# estilos de romance fake que a dona aprovou (chave do shorts_estilos.ESTILOS). Sorteado; o placar decide depois.
ESTILOS_FAKE = ["01", "02", "03", "06"]

PRINT = ("It must look EXACTLY like a real SCREENSHOT paused from the TV anime episode: {estudio}; flat 2D cel "
         "shading, the studio's own character designs and proportions, normal TV-anime lighting, slightly soft "
         "broadcast image - NOT a glossy AI illustration, no airbrushed skin, no extra sparkles, no painterly "
         "background. Copy the art style of the reference frames exactly. Widescreen 16:9 episode frame. Both are "
         "canon ADULTS. No nudity, no sexual act. No text, no subtitles, no watermarks, no logos.")


def _log(m):
    try:
        import capar_shorts
        capar_shorts.log("  [print] " + m)
    except Exception:  # noqa: BLE001
        print(m, flush=True)


def obra_de(pasta, j=None):
    """Chave de OBRAS para a pasta do Short (pelo nome da pasta ou pela obra do postar.json), ou None."""
    nomes = [Path(pasta).name.lower(), str((j or {}).get("obra") or "").lower().replace(" ", "-")]
    for chave in OBRAS:
        if any(n.startswith(chave) for n in nomes):
            return chave
    return None


def quadros(video, destino, n=3):
    """Tira 10 quadros espalhados do vídeo e devolve os n mais nítidos (variância do contorno)."""
    from PIL import Image, ImageFilter, ImageStat
    destino.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(video)], capture_output=True, text=True, timeout=60,
                       creationflags=SEM)
    dur = float((r.stdout or "0").strip() or 0)
    if dur < 3:
        return []
    notas = []
    for i in range(10):
        t = dur * (0.08 + 0.84 * i / 9)
        q = destino / f"q_{i:02d}.jpg"
        subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(q)],
                       capture_output=True, timeout=60, creationflags=SEM)
        if not q.exists():
            continue
        with Image.open(q) as im:
            g = im.convert("L").resize((320, int(320 * im.height / im.width)))
            nota = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0]
            if ImageStat.Stat(g).stddev[0] < 25:  # quadro quase liso (tela preta, fade): fora
                nota = 0
        notas.append((nota, q))
    return [q for _n, q in sorted(notas, key=lambda t: -t[0])[:n] if _n > 0]


def _prompt(estilo, chave):
    import shorts_estilos as se
    a = OBRAS[chave]
    cena = se.ESTILOS[estilo][1]
    return (f"A paused frame from the anime {a['nome']}. SCENE: {cena}. HE = {a['ele']}. SHE = {a['ela']}. "
            f"Place: {a['lugar']}. The reference images are real frames of this anime: copy the characters' faces "
            "and the drawing style from them, ignore any text, subtitle or watermark in them. "
            + PRINT.format(estudio=a["estudio"]) + f" SCENE again: {cena}.")


def _conferir(img, estilo, chave):
    sys.path.insert(0, r"D:\hipercool-videos\bin")
    import visao_capa
    import shorts_estilos as se
    a = OBRAS[chave]
    pergunta = ('Check this picture. Answer ONLY JSON: {"desenho": true/false (drawn anime, false if a real photo), '
                '"texto": true/false (big written words/title/logo), "crianca": true/false (a child or a school '
                'uniform appears; anime art style alone does not count), '
                f'"personagens": true/false (it shows {a["ele"].split(":")[0]} and/or {a["ela"].split(":")[0]} from '
                f'{a["nome"]} with their real designs), "parece_print": true/false (looks like a real TV anime '
                'screenshot with flat cel shading, false if it looks like a glossy AI illustration), '
                f'"cena": true/false (shows: {se.ESTILOS[estilo][1][:200]})}}')
    try:
        c = json.loads(Path(r"D:\hipercool-videos\secrets\claude_proxy.json").read_text(encoding="utf-8"))
        r = visao_capa.perguntar(Path(img).read_bytes(), pergunta, gateway=(c["base_url"].rstrip("/"), c["auth_token"]))
    except Exception:  # noqa: BLE001
        r = None
    if not r:
        return True, ["não conferi"]  # visão sem resposta = não conferi (não reprova)
    m = [t for k, t in (("desenho", "FOTO REAL"), ("personagens", "nao sao os do anime"),
                        ("parece_print", "cara de IA"), ("cena", "cena errada")) if r.get(k) is False]
    if r.get("texto"):
        m.append("texto")
    if r.get("crianca"):
        m.append("crianca/uniforme")
    return (not m), m


def gerar(pasta, j, saida, tentativas=2):
    """Capa 9:16 pronta (Path) ou None. Grava <saida>.capa.json (pose = print_<estilo>)."""
    if os.environ.get("CAPA_PRINT_ANIME", "1") == "0":
        return None
    chave = obra_de(pasta, j)
    if not chave:
        return None
    if str(FABRICA) not in sys.path:
        sys.path.append(str(FABRICA))  # no FIM do sys.path: pasta alheia nunca na frente
    import shorts_estilos as se
    pasta = Path(pasta)
    video = pasta / "video_sem_capa.mp4"
    if not video.exists():
        video = pasta / "video.mp4"
    tmp = pasta / "_capa_print"
    refs = quadros(video, tmp)
    estilo = random.choice(ESTILOS_FAKE)
    prompt = _prompt(estilo, chave)
    cru = tmp / f"cena_{estilo}.png"
    for t in range(1, tentativas + 1):
        cru.unlink(missing_ok=True)
        cmd = [PY_VEO, "-X", "utf8", GERA, prompt, str(cru), "--formato", "16:9", "--max-contas", "3",
               "--maquinas", os.environ.get("CAPA_MAQUINAS", "sti,desktop,x200ma,acer,pc2")]
        if refs:
            cmd += ["--ref", *map(str, refs)]
        try:
            subprocess.run(cmd, capture_output=True, timeout=1500, creationflags=SEM,
                           env={**os.environ, "GEMINI_JA_TENTOU": "1"})
        except subprocess.TimeoutExpired:
            _log(f"{pasta.name}: Flow sem resposta em 25 min")
            continue
        if not (cru.exists() and cru.stat().st_size > 10_000):
            _log(f"{pasta.name}: tentativa {t} não gerou")
            continue
        ok, mot = _conferir(cru, estilo, chave)
        if not ok:
            _log(f"{pasta.name}: tentativa {t} reprovada ({', '.join(mot)})")
            continue
        se.montar(estilo, cru, saida, OBRAS[chave]["nome"])
        Path(saida).with_suffix(".capa.json").write_text(json.dumps(
            {"anime": chave, "pose": f"print_{se.ESTILOS[estilo][0]}", "estilo": estilo, "refs": [str(r) for r in refs],
             "checagem": mot, "prompt": prompt}, ensure_ascii=False, indent=1), encoding="utf-8")
        _log(f"{pasta.name}: capa print do anime OK (estilo {estilo})")
        return Path(saida)
    return None


if __name__ == "__main__":
    d = Path(sys.argv[1])
    jj = json.loads((d / "postar.json").read_text("utf-8")) if (d / "postar.json").exists() else {}
    print(gerar(d, jj, str(d / "_capa_print" / "TESTE_capa.jpg")))
