# 02/11 20h50 dona: capas A/B/C dos longos de ANIME (fontes do Dragon - Animes Recap). Regras diferentes do manhwa:
# "nos animes as personagens são muito mais marcantes, então não pode perder a fidelidade dos personagens nunca; se
# tiver mulher na capa também não pode deixar de usar ela, e as mulheres que forem colocadas têm que ser pelo menos
# parecidas com as do anime mesmo".
#   python anime_capas.py <url> [<url> ...]   -> <titulo (vid)>\A.jpg B.jpg C.jpg (+ original.jpg)
# Mesmo filtro dos longos (checagem + vestidas + tela dividida); reprovada vai pra <obra>\reprovadas.
import json
import shutil
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
sys.path.insert(0, r"D:\hipercool-materiais\capas_longos_refeitas")
import capa_ia_anime as c  # noqa: E402
import capa_longo_v2 as v  # noqa: E402
import refazer  # noqa: E402

AQUI = Path(__file__).parent
TENTATIVAS = 3

FIEL = ("ANIME FIDELITY RULE (most important after the bikini rule): this is an ANIME, its characters are iconic and "
        "fans recognize them instantly. Draw in the SAME anime art style as the FIRST reference (same line art, eye "
        "shape, shading and color palette - it must look like an official screenshot/key visual of that anime, not a "
        "generic manhwa). The MAN is the SAME character as in the FIRST reference: copy his face, hair color and "
        "hairstyle, eyes, glasses, build and age EXACTLY. EVERY woman who appears in the FIRST reference MUST appear "
        "and be the MAIN WOMAN: copy her face, hair color and hairstyle, eye color and hair accessories EXACTLY, only "
        "her clothes become the costume-bikini (her body grown-up and curvy). Any other woman added must look like she "
        "belongs to the SAME anime: same art style, same kind of face and eyes, a heroine design that fits this "
        "anime's cast.")


def _titulo(vid):
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://youtu.be/{vid}&format=json",
                                    timeout=20) as r:
            return json.load(r).get("title", "")
    except Exception:  # noqa: BLE001
        return ""


# 02/11 21h40 dona (q5Sv A aprovada, mas com uma bruxa que não existe na obra — "só a do engenheiro era bruxa; você
# tem que analisar coisas da história pra poder fazer as capas"). Sem roteiro nosso, a ficha inventava as mulheres
# pelos exemplos do FICHA (witch, goddess...). Aqui: descrição do vídeo + a visão identifica o anime e o elenco
# feminino real; vira o "roteiro" que a ficha v4 lê (capa_longo_v2.ROTEIROS).
HISTORIAS = AQUI / "_historias"
HISTORIA = (
    "This is the thumbnail of a Portuguese anime recap video. Title: {titulo}\nVideo description:\n<<<\n{desc}\n>>>\n"
    "Identify WHICH ANIME this is (official name) and describe its REAL main female characters, as fans know them. "
    "Answer ONLY JSON: {{\"anime\": \"<official name or 'unknown'>\", \"resumo\": \"<the story in 3 sentences>\", "
    "\"heroi\": \"<the male protagonist: name, hair, eyes, glasses, look>\", \"mulheres\": [{{\"nome\": \"<name>\", "
    "\"visual\": \"<hair color/style, eye color, ears/horns/tail, signature accessory>\", \"papel\": \"<her real role "
    "in the story (priestess, classmate, wife, demon...)>\", \"idade\": \"<her canon age or school year>\", "
    "\"adulta\": <true ONLY if she is canonically 18 or older (an adult, not a high-school or younger student); "
    "false otherwise or if unsure>}}, ...the 2-4 main women, the one in the thumbnail first]}}. Only what is really "
    "in this anime; never invent roles (no witch unless she is a witch).")


def _historia(vid, titulo, ref):
    f = HISTORIAS / vid / "roteiro.txt"
    if f.exists():
        return f.read_text(encoding="utf-8")
    desc = ""
    try:
        req = urllib.request.Request(f"https://www.youtube.com/watch?v={vid}", headers={"User-Agent": "Mozilla/5.0",
                                                                                     "Accept-Language": "pt-BR"})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
        m = refazer.re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', html)
        desc = json.loads(f'"{m.group(1)}"')[:4000] if m else ""
    except Exception:  # noqa: BLE001
        pass
    try:
        h = c.visao_capa.perguntar(Path(ref).read_bytes(), HISTORIA.format(titulo=titulo, desc=desc or "(none)"),
                                   gateway=c._gateway(), max_tokens=1500) or {}
    except Exception as e:  # noqa: BLE001
        refazer.log(f"[anime] {vid}: história falhou ({e})")
        return ""
    if not h.get("mulheres"):
        return ""
    h = json.loads(c._sem_mojibake(json.dumps(h, ensure_ascii=False)))  # "devassidÃ£o" da visão
    # Personagem menor de idade no cânone (colegial, irmã pequena) NUNCA entra em capa sensual, nem "desenhada adulta".
    adultas = [m for m in h["mulheres"] if m.get("adulta") is True]
    menores = [m for m in h["mulheres"] if m.get("adulta") is not True]
    txt = (f"ANIME: {h.get('anime')}\nHISTÓRIA: {h.get('resumo')}\nPROTAGONISTA: {h.get('heroi')}\n"
           + ("PERSONAGENS FEMININAS ADULTAS REAIS DA OBRA (use SÓ estas, com o papel real delas):\n"
              + "\n".join(f"- {m.get('nome')}: {m.get('visual')} | papel: {m.get('papel')}" for m in adultas)
              if adultas else "NENHUMA personagem feminina adulta na obra.\n")
           + ("\nNUNCA DESENHAR (menores de idade): "
              + "; ".join(f"{m.get('nome')} ({m.get('idade')})" for m in menores) if menores else "")
           + f"\nDESCRIÇÃO DO VÍDEO: {desc}")
    (f.parent / "menores.json").parent.mkdir(parents=True, exist_ok=True)
    (f.parent / "menores.json").write_text(json.dumps({"todas": [f"{m.get('nome')}: {m.get('visual')} | "
                                                                 f"{m.get('papel')}" for m in h["mulheres"]],
                                                       "heroi": h.get("heroi"),
                                                       "capa_adulta": h["mulheres"][0].get("adulta") is True,
                                                       "adultas": [m.get("nome") for m in adultas],
                                                       "menores": [f"{m.get('nome')} ({m.get('idade')})"
                                                                   for m in menores]}, ensure_ascii=False),
                                           encoding="utf-8")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(txt, encoding="utf-8")
    refazer.log(f"[anime] {vid}: história -> {h.get('anime')} / {[m.get('nome') for m in h['mulheres']]}")
    return txt


# 02/11 22h30 dona (asv0): "está sem mulher, as mulheres devem ser as da obra". Lá todas são colegiais (15-17 anos):
# entram como no anime, com a roupa delas, em cena de ação/comédia — nunca biquíni, nunca pose sensual.
CENA_MENOR = {
    "A": "the SAME situation as the FIRST reference, made funny and dramatic: the hero's shocked face and the girls "
         "reacting (angry blush, pointing at him), everyone fully dressed",
    "B": "a comedic everyday scene from the story: the hero in trouble, the girls teasing or scolding him",
    "C": "an EPIC BATTLE: the hero BIG and central with his weapon, the girls fighting at his side with their powers, "
         "enemies blasted away, speed lines and sparks",
}


def montar_com_menores(historia, ficha, letra):
    return (f"A 16:9 anime recap YouTube thumbnail: {CENA_MENOR[letra]}. Draw in the SAME anime art style as the "
            f"FIRST reference. The hero is the SAME character as in the FIRST reference ({ficha.get('heroi', '')}). "
            "The girls are the REAL female characters of this anime, exactly as fans know them, wearing their own "
            "canonical outfits from the anime (school uniform or battle uniform), fully covered, normal teenage "
            "proportions: NO bikini, NO swimsuit, NO underwear, NO cleavage, NO sensual pose, NO fanservice, no "
            f"blush-at-the-camera poses. Characters (from the story analysis):\n{historia}\nNo text, no speech "
            "bubbles. Bright vivid colors.")


def _anime(txt):
    return txt.replace("manhwa recap", "anime recap").replace("manhwa", "anime")


def prompt(ficha, letra, url):
    base = v.montar_b(ficha, url) if letra == "B" else v.montar(ficha, letra, url)
    return f"{v.ROUPA} {FIEL} {_anime(base)} Again: {FIEL}"


def gerar(url):
    vid = url.rstrip("/").split("/")[-1].split("?")[0][-11:]
    titulo = _titulo(vid)
    p = {"vid": vid, "titulo": titulo}
    nome = refazer.re.sub(r"[^\w ]+", "", titulo).strip()[:40].strip()
    d = AQUI / f"{nome} ({vid})"
    (d / "_tmp").mkdir(parents=True, exist_ok=True)
    ref = c._capa_do_parceiro(f"https://youtu.be/{vid}")
    if not ref:
        refazer.log(f"[anime] {vid}: sem capa original")
        return
    if not (d / "original.jpg").exists():
        shutil.copy2(ref, d / "original.jpg")
    if HISTORIAS not in v.ROTEIROS:
        v.ROTEIROS.append(HISTORIAS)
    _historia(vid, titulo, ref)
    ficha = c._ficha_v2(ref, titulo, "16:9")
    if not ficha:
        refazer.log(f"[anime] {d.name}: sem ficha")
        return
    try:
        idades = json.loads((HISTORIAS / vid / "menores.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        idades = {}
    # mulher da capa menor de idade, ou nenhuma adulta na obra -> capa só do herói (regra do X90), nada sensual
    so_heroi = v.sem_mulheres(ficha) or not idades.get("capa_adulta") or not idades.get("adultas")
    # elenco feminino só de menores (colegiais): elas entram VESTIDAS, sem nada sensual (sem_mulheres = herói bebê)
    menores = so_heroi and not v.sem_mulheres(ficha) and bool(idades.get("menores"))
    historia = ("\n".join(f"- {x}" for x in idades.get("todas", [])[:3])
                + f"\nThe hero: {idades.get('heroi', '')}") if menores else ""
    if so_heroi:
        refazer.log(f"[anime] {d.name}: {'com as meninas vestidas' if menores else 'só herói'} "
                    f"(menores: {idades.get('menores')})")
    # 02/11 21h20: a visão chamou de "dividida" a q5Sv (ele em primeiro plano + ela atrás do batente da porta: uma cena
    # só) e as 2 A saíram reprovadas por "A inteira". Anime é quadro do episódio: tela dividida só se a obra pedir.
    dividida = False
    for letra in "ABC":
        if (d / f"{letra}.jpg").exists():
            continue
        for t in range(TENTATIVAS):
            if menores:
                txt = montar_com_menores(historia, ficha, letra) + (" Different composition." * t)
                extras = []
            elif so_heroi:
                txt = _anime(v.montar_so_heroi(ficha, letra)) + (" Different composition." * t)
                extras = []
            else:
                txt = prompt(ficha, letra, f"{url}#{t}" if t else url)
                extras = [str(x) for x in v.refs_extras(url, letra)]
                b = v.banco(vid)  # 03/11: rostos das mulheres tirados do próprio vídeo
                txt += v.texto_banco(b, len(extras) + 2)
                extras += [str(f) for f, _ in b]
            img = c._gerar_com_ref(txt, ref, "16:9", extras)
            if not img:
                refazer.log(f"[anime] {d.name} {letra}: Flow sem imagem")
                continue
            chk = c._checar(str(img))
            if chk and menores:  # as meninas são colegiais: vestidas é o certo; pele exposta reprova
                chk = dict(chk, adultos=True, vestidas=False)
            elif chk and so_heroi:  # sem mulher é o certo; mulher na imagem reprova
                chk = dict(chk, adultos=False if chk.get("ela") else chk.get("adultos"), vestidas=False)
            if chk and dividida and letra == "A":
                chk = dict(chk, dividida=False, a_nao_dividida=not chk.get("dividida"))
            if (chk or {}).get("a_nao_dividida") or (c._reprovada(chk) if so_heroi else c._reprovada_v2(chk, str(img))):
                refazer.log(f"[anime] {d.name} {letra}: reprovada no filtro {chk}")
                (d / "reprovadas").mkdir(exist_ok=True)
                shutil.copy2(img, d / "reprovadas" / f"{letra}_{t}.png")
                continue
            (d / "_tmp" / f"{letra}.txt").write_text(txt, encoding="utf-8")
            shutil.copy2(img, d / "_tmp" / f"{letra}.png")
            c._compor(str(img), refazer.palavra(p["titulo"]), str(d / f"{letra}.jpg"), c.QUADRO["16:9"], rostos=chk)
            refazer.log(f"[anime] {d.name} {letra}: ok")
            break


if __name__ == "__main__":
    for u in sys.argv[1:]:
        try:
            gerar(u)
        except Exception as e:  # noqa: BLE001
            refazer.log(f"[anime] {u}: erro {type(e).__name__}: {e}")
