"""Sistema de IMITAÇÃO do jeito de falar (dona 20/11: "tem que ter um sistema de imitação dessas coisas que não é voz,
é o jeito deles de falar que só ele faz" — KkVirjão chamando a mulher de burra, o homem de chuinga, o personagem de
retardado, falando uma coisa e depois "mentira").

Lê as falas REAIS transcritas do narrador (segs.json dos jobs de sub-vozes) e acha os truques que ELE repete, com
exemplo real de cada: xingar personagem, voltar atrás ("mentira"), se atrapalhar e admitir, conector próprio,
apelido do protagonista, desabafo, pergunta pro público, imitação de fala ("ele: ..."), exagero/comparação.
Grava em linguagem_v2.json["marcas_registradas"] (local + Drive). O anime_script põe 2-4 delas no roteiro, sempre
sobre os PERSONAGENS (nunca ofende quem assiste).

    python marcas_registradas.py <voz> <pasta_com_segs.json> [--sobe]
"""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path

R = r"D:\tools\rclone.exe"
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")

TRUQUES = [
    ("xinga o PERSONAGEM (nunca o público)",
     r"(?i)\b(burr[oa]|idiota|retardad[oa]|chuinga|otári[oa]|trouxa|lerd[oa]|besta|imbecil|jumento|anta|tapad[oa]|"
     r"lesad[oa]|panaca|mané|bocó|tongo)\b"),
    ("fala uma coisa e logo diz 'mentira' (volta atrás de zoeira)", r"(?i)\b(mentira|zoeira|brincadeira)\b"),
    ("se atrapalha e admite no meio da frase", r"(?i)(me atrapalh|me perdi|inverti|sei lá|esqueci o nome|como é o nome)"),
    ("desabafo / palavrão leve (máx. 1-2 por vídeo)", r"(?i)\b(porra|caralho|foda|puta que|merda|droga|ferrad)\w*"),
    ("pergunta direto pra quem assiste", r"(?i)(você(s)? (acha|acredita|imagina|viu)|cê(s)? (acha|viu)|sabe o que)"),
    ("imita a fala do personagem ('ele: ...', 'tipo assim')", r"(?i)(\b(ele|ela) (fala|diz|disse|responde)\b|tipo assim)"),
    ("exagero / comparação absurda", r"(?i)\b(que nem|parece (um|uma)|mais (\w+ )?que (um|uma)|pior que)\b"),
]


def falas(pasta):
    out = []
    for sj in Path(pasta).rglob("segs.json"):
        out += [s["texto"].strip() for s in json.loads(sj.read_text(encoding="utf-8")) if s.get("sim", 0) >= 0.5]
    return [t for t in out if len(t.split()) >= 4]


def conectores(ts, n=4):
    """Começos de frase que ele repete muito ('Então daí', 'E cara')."""
    c = Counter(" ".join(t.split()[:2]).strip(",.").lower() for t in ts)
    return [k for k, v in c.most_common(30) if v >= 6 and len(k) > 3][:n]


def montar(voz, pasta, sobe=False):
    ts = falas(pasta)
    marcas = []
    for o_que, p in TRUQUES:
        ex = [t for t in ts if re.search(p, t)]
        if len(ex) >= 3:  # só o que ele REPETE vira marca
            ex.sort(key=lambda t: abs(len(t) - 90))  # exemplo de tamanho legível
            marcas.append({"o_que": o_que, "exemplo": ex[0][:160], "vezes": len(ex)})
    con = conectores(ts)
    if con:
        marcas.append({"o_que": "começa frases assim: " + ", ".join(f"'{c}'" for c in con), "exemplo": "",
                       "vezes": 0})
    arq = VOZES / voz / "linguagem_v2.json"
    try:
        g = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        g = {}
    manuais = [m for m in g.get("marcas_registradas") or [] if isinstance(m, dict) and m.get("manual")]
    g["marcas_registradas"] = manuais + marcas
    g["_marcas_registradas_fonte"] = f"marcas_registradas.py: {len(ts)} falas reais de {pasta}"
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    print(voz, f"{len(ts)} falas ->", json.dumps(marcas, ensure_ascii=False, indent=1))
    if sobe:
        subprocess.run([R, "copyto", str(arq), f"manhwa-drive:colab_recap/vozes/{voz}/linguagem_v2.json"], check=True)


if __name__ == "__main__":
    montar(sys.argv[1], sys.argv[2], "--sobe" in sys.argv)
