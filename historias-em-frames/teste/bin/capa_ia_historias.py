# -*- coding: utf-8 -*-
"""capa_ia_historias.py — capa da história (§2 de MELHORIAS_PARA_TODOS_OS_PROJETOS.md).

As histórias são Shorts verticais (720x1280): a capa é 9:16 e mostra o momento mais intrigante DA PRÓPRIA história
(título + tema), com o clima do gênero e a composição de uma pose do catálogo config/POSES_HISTORIAS.py.
Esquema copiado de D:\\hipercool-videos\\bin\\capa_ia.py:
- imagem pelo gateway OmniRoute (antigravity/gemini-3.1-flash-image), cache por prompt; desligado por hora (dono
  20/10, imagem_reserva.GATEWAY): vai direto pra reserva;
- checagem por VISÃO (Gemini): letra/logo desenhado, sangue/ferida, cara de menor, tela dividida -> reprova e tenta
  outra pose (até 3 imagens);
- frase grande (texto_capa do SEO) com contorno preto, linhas branco/amarelo, fonte LuckiestGuy.
Sem capa (gateway fora, tudo reprovado) devolve None: o vídeo sobe sem capa própria, nunca trava a postagem.

Quem chama: story_pipeline._write_postar_json (grava "thumb" no postar.json; a rede do manhwa-react sobe a capa).
Uso: python bin/capa_ia_historias.py --genero terror --tema "voz que sussurrava do ralo" \
         --titulo "O sussurro vindo do ralo" --texto "TEM ALGO NO RALO" --saida teste.jpg
"""
import argparse
import base64
import hashlib
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from POSES_HISTORIAS import POSES, POSES_CATEGORIA, REGRAS_HISTORIAS, ROUPAS_COMUNS  # noqa: E402
import visao_capa  # noqa: E402  (COMUM: corpo malformado + visão com reserva, igual ao hipercool)

CACHE = PROJECT_DIR / "workspace" / "cache" / "capa_ia_historias"
MODELO = "antigravity/gemini-3.1-flash-image"
FONTES = Path(r"D:\hipercool-materiais\assets\fonts")
QUADRO = {"9:16": (720, 1280), "16:9": (1280, 720)}
CLIMA = {
    "terror": "dark eerie horror mood, cold shadows, suspense",
    "drama": "emotional dramatic mood, contrast of warm and cold light",
    "superacao": "inspiring hopeful mood, golden light breaking through",
    "romance": "romantic cinematic mood, soft warm golden light",
    "comedia": "funny exaggerated expressive mood, bright saturated colors",
    "religioso": "serene spiritual mood, soft heavenly light",
}
_PERGUNTA = (
    'Quality check of a drawn YouTube thumbnail. Answer ONLY JSON: {"letras": true/false (readable letters, words, '
    'numbers, logos or emblems drawn anywhere; abstract patterns do not count), "sangue": true/false (blood, wounds, '
    'gore or a dead body), "adultos": true/false (every person looks 18 or older — young adults count as adults; '
    'false only if someone looks like a child or teenager), "dividida": '
    'true/false (looks split into two panels or has a visible seam or border), ' + visao_capa.DEFEITOS + '}')


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _gateway():
    """base_url/api_key do gateway: secrets/omniroute.json deste projeto (reserva: o do hipercool)."""
    for p, kb, kt in ((PROJECT_DIR / "secrets" / "omniroute.json", "base_url", "api_key"),
                      (Path(r"D:\hipercool-videos\secrets\claude_proxy.json"), "base_url", "auth_token")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
            return c[kb].rstrip("/"), c[kt]
        except (OSError, ValueError, KeyError):
            continue
    return None, None


def _gerar(prompt, formato):
    """Imagem (Path) pro prompt — do cache, do gateway (se imagem_reserva.GATEWAY) ou da reserva (imagem_reserva:
    Cloudflare/Pollinations). None se nada gerou."""
    import imagem_reserva
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{hashlib.md5(prompt.encode()).hexdigest()[:16]}.png"
    if out.exists() and out.stat().st_size > 5000:
        return out
    base, tok = _gateway() if imagem_reserva.GATEWAY else (None, None)
    b64 = None
    if imagem_reserva.GATEWAY and not base:
        log("  capa IA: sem credencial do gateway")
    elif base:
        corpo = json.dumps({"model": MODELO, "prompt": prompt, "n": 1, "response_format": "b64_json",
                            "size": "1024x1792" if formato == "9:16" else "1792x1024",
                            "aspect_ratio": formato}).encode()
        req = urllib.request.Request(base + "/v1/images/generations", data=corpo,
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b64 = ((json.loads(r.read()).get("data") or [{}])[0]).get("b64_json")
        except urllib.error.HTTPError as e:
            log(f"  capa IA: gateway HTTP {e.code} {e.read().decode('utf-8', 'replace')[:120]}")
        except Exception as e:  # noqa: BLE001
            log(f"  capa IA: gateway falhou ({type(e).__name__}: {str(e)[:100]})")
    if b64:
        out.write_bytes(base64.b64decode(b64))
        return out
    img, quem = imagem_reserva.gerar(prompt, formato)
    if not img:
        log(f"  capa IA: reserva também não gerou ({quem[:300]})")
        return None
    log(f"  capa IA: imagem pela reserva ({quem})")
    out.write_bytes(img)
    return out


def _checar(img):
    """Checagem por visão (Gemini; se ele falhar, Claude pelo gateway — visao_capa). None se os dois falharem (aí
    vale a imagem: as regras já vão no prompt)."""
    try:
        b = Path(img).read_bytes()
    except OSError:
        return None
    r = visao_capa.perguntar(b, _PERGUNTA, gateway=_gateway())
    if r is None:
        log("  capa IA: checagem por visão indisponível (Gemini e gateway)")
    return r


def _reprovada(c):
    """Letra/logo, sangue, cara de menor, tela dividida e (dono 20/10) corpo malformado."""
    return bool(c) and bool(c.get("letras") or c.get("sangue") or c.get("adultos") is False or c.get("dividida")
                            or visao_capa.defeitos(c, figurantes=False))


def _fonte(nome, tam):
    from PIL import ImageFont
    for n in (nome, "impact.ttf"):
        try:
            return ImageFont.truetype(str(FONTES / n), tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _quebrar(d, texto, f, larg):
    linhas, cur = [], ""
    for w in texto.split():
        tst = (cur + " " + w).strip()
        if cur and d.textlength(tst, font=f) > larg:
            linhas.append(cur)
            cur = w
        else:
            cur = tst
    return linhas + ([cur] if cur else [])


def _compor(img_path, texto, out_jpg, quadro):
    """Recorta pra preencher o quadro e escreve a frase grande (9:16: no alto; 16:9: à esquerda). JPEG < 2 MB."""
    from PIL import Image, ImageDraw
    W, H = quadro
    img = Image.open(img_path).convert("RGB")
    sc = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * sc) + 1, int(img.height * sc) + 1), Image.LANCZOS)
    ox, oy = (img.width - W) // 2, (img.height - H) // 2
    capa = img.crop((ox, oy, ox + W, oy + H))
    texto = re.sub(r"\s+", " ", texto or "").strip().upper()
    if texto:
        d = ImageDraw.Draw(capa)
        vertical = H > W
        area = int((0.88 if vertical else 0.42) * W)
        tam = 104 if vertical else 112
        while True:
            f = _fonte("LuckiestGuy-Regular.ttf", tam)
            linhas = _quebrar(d, texto, f, area)
            if len(linhas) <= 3 or tam <= 52:
                break
            tam -= 8
        lh = int(tam * 1.1)
        y = int(0.06 * H) if vertical else (H - len(linhas) * lh) // 2
        for i, ln in enumerate(linhas):
            x = (W - d.textlength(ln, font=f)) / 2 if vertical else 40
            d.text((x, y), ln, font=f, fill=(255, 214, 0) if i % 2 else (255, 255, 255),
                   stroke_width=9, stroke_fill=(0, 0, 0))
            y += lh
    Path(out_jpg).parent.mkdir(parents=True, exist_ok=True)
    for q in (90, 82, 72):
        capa.save(out_jpg, "JPEG", quality=q)
        if Path(out_jpg).stat().st_size < 1_900_000:  # o YouTube aceita até 2 MB
            break
    return Path(out_jpg)


# gênero sem pose no catálogo (drama, romance, comédia, religioso): só a cena da história, variando o enquadramento
COMPOSICOES_LIVRES = [
    "tight close-up of the main character's face showing the strongest emotion of the story",
    "two characters facing each other at the key moment, both faces visible and expressive",
    "cinematic medium shot of the main character at the key moment, the important object in the foreground",
]


STATS_CAPAS = PROJECT_DIR / "workspace" / "capas_poses.json"


def _stats_capas():
    try:
        return json.loads(STATS_CAPAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_stats(s):
    STATS_CAPAS.parent.mkdir(parents=True, exist_ok=True)
    STATS_CAPAS.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def _poses(genero):
    ps = [p for p, cats in POSES_CATEGORIA.items() if genero in cats and p in POSES]
    if not ps:
        return list(COMPOSICOES_LIVRES)
    # Thompson sampling: ordena pela probabilidade de ser a melhor pose
    s = _stats_capas()
    ps.sort(key=lambda p: random.betavariate(
        s.get(p, {}).get("vitorias", 0) + 1,
        s.get(p, {}).get("testes", 0) - s.get(p, {}).get("vitorias", 0) + 1), reverse=True)
    return ps


def registrar_teste(capa_json_path):
    """Chamado pelo postador quando as variantes entram num teste A/B do Studio."""
    try:
        d = json.loads(Path(capa_json_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    s = _stats_capas()
    for v in d.get("variantes", []):
        pose = v.get("pose")
        if pose:
            s.setdefault(pose, {"testes": 0, "vitorias": 0})["testes"] += 1
    _gravar_stats(s)


def registrar_resultado(pose, venceu):
    """Chamado pelo metricas_historias: a capa desta pose subiu e o vídeo rendeu acima (ou abaixo) da mediana do canal."""
    s = _stats_capas()
    d = s.setdefault(pose, {"testes": 0, "vitorias": 0})
    d["testes"] += 1
    d["vitorias"] += 1 if venceu else 0
    _gravar_stats(s)


def registrar_vencedora(capa_json_path, idx):
    """Chamado quando o Studio aponta a capa vencedora (idx na lista de variantes)."""
    try:
        vs = json.loads(Path(capa_json_path).read_text(encoding="utf-8")).get("variantes", [])
    except (OSError, ValueError):
        return
    if not 0 <= idx < len(vs):
        return
    s = _stats_capas()
    pose = vs[idx].get("pose")
    if pose:
        s.setdefault(pose, {"testes": 1, "vitorias": 0})["vitorias"] += 1
    _gravar_stats(s)


def gerar_capa(genero, saida, tema="", titulo="", texto="", formato="9:16"):
    """Gera até 3 capas com poses diferentes (teste A/B). Grava <saida>.capa.json com as variantes.
    Retorna a Path da capa principal (.jpg) ou None. As variantes ficam em <saida>_v1.jpg, _v2.jpg, _v3.jpg."""
    genero = (genero or "terror").lower()
    quadro = QUADRO.get(formato, QUADRO["9:16"])
    poses = _poses(genero)[:5]  # pool de até 5 para ter margem se alguma reprovar
    variantes = []
    principal = None
    for pose in poses:
        if len(variantes) >= 3:
            break
        comp = POSES.get(pose, (0, pose))[1]
        if pose not in POSES:
            pose = f"livre{COMPOSICOES_LIVRES.index(pose) + 1}"
        prompt = (f"{'Vertical 9:16' if formato == '9:16' else 'Horizontal 16:9'} illustration for the thumbnail of a "
                  f"short narrated story. Story (Portuguese, context only - never write it): \"{titulo}\" - {tema}. "
                  "Show the most intriguing moment of THIS story without revealing the ending. "
                  f"Mood: {CLIMA.get(genero, 'cinematic dramatic mood')}. Composition idea: {comp}. "
                  f"People wear {random.choice(ROUPAS_COMUNS)} and have clearly mature adult faces (late twenties "
                  f"to forties). {REGRAS_HISTORIAS} "
                  "Papers, notebooks, screens and signs appear blank or blurred, never with writing. "
                  "Figures and faces large in frame so it reads on a phone screen; leave the top area less busy.")
        chk = None
        for _ in range(2):  # dono 20/10: capa com defeito é refeita, não aceita
            img = _gerar(prompt, formato)
            if not img:
                break
            chk = _checar(img)
            if not _reprovada(chk):
                break
            log(f"  capa IA: pose {pose} reprovada na checagem ({chk})")
            Path(img).unlink(missing_ok=True)  # sai do cache: senão a mesma imagem ruim volta
            img = None
        if not img:
            log(f"  capa IA: sem imagem boa da pose {pose}")
            continue
        n = len(variantes) + 1
        out_n = Path(saida).with_name(Path(saida).stem + f"_v{n}.jpg")
        out_n = _compor(img, texto, str(out_n), quadro)
        variantes.append({"pose": pose, "arquivo": str(out_n), "checagem": chk, "prompt": prompt})
        if n == 1:
            # A primeira variante também é gravada como o arquivo principal
            import shutil
            shutil.copy2(str(out_n), str(saida))
            principal = Path(saida)
        log(f"  capa IA: variante {n} ({out_n.name}, pose {pose})")
    if not variantes:
        log("  capa IA: todas as tentativas reprovadas — sem capa")
        return None
    # Grava o JSON com todas as variantes (o Studio testa A/B entre elas)
    meta = {"genero": genero, "tema": tema, "titulo": titulo, "texto": texto, "formato": formato,
            "variantes": variantes}
    Path(saida).with_suffix(".capa.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"  capa IA: {len(variantes)} variante(s) gerada(s)")
    return principal


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Capa IA das histórias (9:16)")
    ap.add_argument("--genero", default="terror")
    ap.add_argument("--tema", default="")
    ap.add_argument("--titulo", default="")
    ap.add_argument("--texto", default="")
    ap.add_argument("--formato", default="9:16", choices=list(QUADRO))
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    sys.exit(0 if gerar_capa(a.genero, a.saida, a.tema, a.titulo, a.texto, a.formato) else 1)


if __name__ == "__main__":
    main()
