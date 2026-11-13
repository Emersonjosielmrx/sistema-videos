# 02/11 22h: 2º passo do banco de mulheres (roda no D:\veo\venv, que tem a visão): dá NOME e IDADE a cada personagem
# do indice.json cruzando a foto com o roteiro do nosso vídeo (como a ficha v4). Menor de idade (cânone) fica marcada
# "adulta": false e NUNCA vai como referência de capa.
#   python nomear.py <obra> [roteiro.txt]
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
from PIL import Image  # noqa: E402

import capa_ia_anime as c  # noqa: E402
import capa_longo_v2 as v  # noqa: E402

AQUI = Path(__file__).parent
PERGUNTA = (
    "These are face/body crops (side by side, numbered 1..N from left) that should show ONE female character from an anime/manhwa recap video. Story script (Portuguese, may be "
    "empty):\n<<<\n{roteiro}\n>>>\nAnswer ONLY JSON: {{\"nome\": \"<her name from the script, or a short description "
    "like 'ruiva de olhos verdes'>\", \"papel\": \"<her role in the story>\", \"visual\": \"<hair color/style, eye "
    "color, ears/horns/tail, signature accessory, in English>\", \"fotos_mulher\": [<1-based positions, left to "
    "right, of the crops that really show THIS woman; leave out men/boys and other people>], \"adulta\": <true only if she is clearly an adult "
    "woman (18+) in the story; false if a child, a teen/high-school student or unsure>, \"mulher\": <true if this is "
    "really a woman/girl, false if a man>}}")


def folha(arqs):
    ims = [Image.open(a).convert("RGB").resize((256, 256)) for a in arqs[:9]]
    f = Image.new("RGB", (256 * len(ims), 256))
    for i, im in enumerate(ims):
        f.paste(im, (256 * i, 0))
    b = io.BytesIO()
    f.save(b, "JPEG", quality=88)
    return b.getvalue()


def main(obra, roteiro=None):
    pasta = AQUI / obra
    ind = json.loads((pasta / "indice.json").read_text(encoding="utf-8"))
    rot = Path(roteiro).read_text(encoding="utf-8", errors="replace")[:30000] if roteiro else \
        v._roteiro(f"parceiro_{obra[:11]}.jpg")
    for m in ind["mulheres"]:
        rostos = [pasta / "mulheres" / m["personagem"] / a["arquivo"] for a in m["arquivos"]][:9]
        try:
            r = c.visao_capa.perguntar(folha(rostos), PERGUNTA.format(roteiro=rot or "(none)"),
                                       gateway=c._gateway(), max_tokens=600) or {}
        except Exception as e:  # noqa: BLE001
            print(m["personagem"], "falhou", e)
            continue
        r = json.loads(c._sem_mojibake(json.dumps(r, ensure_ascii=False)))
        # 03/11 teste 6g2b: o herói (menino de cabelo preto) caiu no mesmo grupo da mulher -> sai foto a foto
        boas = r.get("fotos_mulher")
        if isinstance(boas, list) and boas:
            fora = {rostos[i].name for i in range(len(rostos)) if i + 1 not in boas}
            for a in list(m["arquivos"]):
                if a["arquivo"] in fora:
                    (pasta / "mulheres" / m["personagem"] / a["arquivo"]).unlink(missing_ok=True)
                    m["arquivos"].remove(a)
        m.update(nome=r.get("nome", ""), papel=r.get("papel", ""), visual=r.get("visual", ""),
                 adulta=r.get("adulta") is True and not m.get("possivel_menor"), mulher=r.get("mulher") is not False)
        print(m["personagem"], m["nome"], "adulta" if m["adulta"] else "MENOR/INCERTA", "" if m["mulher"] else "(homem)")
    # 03/11 dona ("coletando fotos das mesmas mulheres, preciso de mulheres diferentes"): Mia saiu em p01..p05 e a
    # capa usava p01+p02 = a mesma mulher 2x. Mesmo nome = mesma mulher: fica a pasta que mais aparece, as outras
    # ganham "repetida" e a capa pula (capa_longo_v2.banco).
    vistos = {}
    for m in sorted(ind["mulheres"], key=lambda m: -m.get("aparicoes", 0)):
        k = _chave(m.get("nome"))
        m.pop("repetida", None)
        if k and k in vistos:
            m["repetida"] = vistos[k]
            vistos_m = next(x for x in ind["mulheres"] if x["personagem"] == vistos[k])
            vistos_m["aparicoes"] += m.get("aparicoes", 0)
        elif k:
            vistos[k] = m["personagem"]
    # principal = a adulta que mais aparece
    for m in ind["mulheres"]:
        m["principal"] = False
    ok = [m for m in ind["mulheres"] if m.get("adulta") and m.get("mulher") and not m.get("repetida")]
    if ok:
        max(ok, key=lambda m: m["aparicoes"])["principal"] = True
    (pasta / "indice.json").write_text(json.dumps(ind, ensure_ascii=False, indent=1), encoding="utf-8")
    print("diferentes:", ", ".join(m["nome"] for m in ind["mulheres"] if m.get("nome") and not m.get("repetida")))
    homens(pasta, rot)


def _chave(nome):
    """'Mi-kyung (ou Mikiung)' / 'Mi-kyung (Mikiung)' -> 'mikyung'; descrição genérica fica como está."""
    import re
    n = re.sub(r"\(.*?\)", "", (nome or "")).split("/")[0].strip().lower()
    return re.sub(r"[^a-z0-9à-ú]", "", n)


PERGUNTA_H = (
    "These are face crops (side by side, numbered 1..N from left) that should show ONE male character from an "
    "anime/manhwa recap video. Story script (Portuguese, may be empty):\n<<<\n{roteiro}\n>>>\nAnswer ONLY JSON: "
    "{{\"nome\": \"<his name from the script, or a short description>\", \"papel\": \"<protagonist / villain / "
    "ally ...>\", \"protagonista\": <true if he is the main character of the script>, \"adulto\": <false if he is a child/teen in the story or looks under 18, else true>, \"visual\": \"<hair color/style, "
    "eye color, scars, signature outfit/accessory, in English>\", \"fotos_dele\": [<1-based positions of the crops "
    "that really show HIM>]}}")


def homens(pasta, rot):
    """03/11: protagonista e homens principais (homens.json do banco_mulheres) ganham nome/papel/visual."""
    arq = pasta / "homens.json"
    if not arq.exists():
        return
    ind = json.loads(arq.read_text(encoding="utf-8"))
    for h in ind["homens"]:
        rostos = [pasta / "homens" / h["personagem"] / a["arquivo"] for a in h["arquivos"]][:9]
        try:
            r = c.visao_capa.perguntar(folha(rostos), PERGUNTA_H.format(roteiro=rot or "(none)"),
                                       gateway=c._gateway(), max_tokens=500) or {}
        except Exception as e:  # noqa: BLE001
            print(h["personagem"], "falhou", e)
            continue
        r = json.loads(c._sem_mojibake(json.dumps(r, ensure_ascii=False)))
        boas = r.get("fotos_dele")
        if isinstance(boas, list) and boas:
            fora = {rostos[i].name for i in range(len(rostos)) if i + 1 not in boas}
            for a in list(h["arquivos"]):
                if a["arquivo"] in fora:
                    (pasta / "homens" / h["personagem"] / a["arquivo"]).unlink(missing_ok=True)
                    h["arquivos"].remove(a)
        h.update(nome=r.get("nome", ""), papel=r.get("papel", ""), visual=r.get("visual", ""),
                 protagonista=r.get("protagonista") is True, adulto=r.get("adulto") is not False)
    prot = [h for h in ind["homens"] if h.get("protagonista") and h["arquivos"]]
    for h in ind["homens"]:
        h["principal"] = False
    alvo = max(prot or [h for h in ind["homens"] if h["arquivos"]] or [None],
               key=lambda h: h["aparicoes"] if h else 0)
    if alvo:
        alvo["principal"] = True
    arq.write_text(json.dumps(ind, ensure_ascii=False, indent=1), encoding="utf-8")
    print("homens:", ", ".join(f"{h['nome']}{' (protagonista)' if h.get('principal') else ''}" for h in ind["homens"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
