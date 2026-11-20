"""Marcas registradas PROFUNDAS do narrador (20/11, dona: "tem que ter um sistema de imitação dessas coisas que não é
voz, é o jeito deles de falar que só ele faz — até tinha mas não parece funcionar na profundidade; tem muito material
dele transcrito, deve ser usado pra absorver isso").

O marcas_registradas.py conta palavra-chave (regex) e pega exemplo ruim (frase solta onde "idiota" aparece). Aqui a IA
(Gemini 3.8, grátis) LÊ todas as falas reais transcritas em blocos e descreve cada truque dele: o que é, QUANDO ele usa,
como monta a frase, e 3 exemplos reais inteiros. Depois junta os blocos (só fica o que aparece em vários blocos).
Grava em linguagem_v2.json["marcas_registradas"] com "profunda": true (as "manual": true continuam), local + Drive.

    python marcas_profundas.py <voz> <pasta_com_segs.json> [<outra pasta> ...] [--sobe]
"""
import json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import claude_client  # noqa: E402

R = r"D:\tools\rclone.exe"
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
BLOCO = 220

LER = """Abaixo, falas REAIS (transcritas) do narrador brasileiro {voz}, de vídeos de recap de manhwa no YouTube.
Quero IMITAR o JEITO DE FALAR que só ele tem (não a voz): os truques de humor e de fala que ELE repete. Exemplos do
tipo de coisa: chamar personagem de burro/retardado/chuinga, chamar a mulher de burra, falar algo e logo dizer
"mentira", se atrapalhar e admitir, piada maliciosa com mulher bonita (RES-peito, "não vou mostrar"), imitar a voz
do personagem, apelidos que ele inventa, conectores dele ("então daí"), exageros, perguntas pro público.
Liste SÓ truques que aparecem 2+ vezes NESTE bloco. Para cada um:
- "truque": nome curto
- "quando": em que tipo de cena ele usa
- "como": a forma da frase (molde com <lacunas>)
- "exemplos": 2-3 frases REAIS dele, copiadas do bloco, inteiras e que mostram o truque claramente
- "vezes": quantas vezes aparece no bloco
Responda SÓ JSON: [{{"truque": "...", "quando": "...", "como": "...", "exemplos": ["..."], "vezes": n}}]

FALAS:
{falas}"""

JUNTAR = """Estes são truques de fala do narrador {voz}, achados por bloco do material dele (pode ter repetido com
nome diferente). Junte os iguais, some as vezes, descarte o que apareceu só uma vez no total e o que é genérico
(qualquer narrador faz). Fique com 6 a 12, do mais marcante para o menos. Para cada um escolha os 3 MELHORES exemplos
reais (frases inteiras, que mostram o truque claramente).
Responda SÓ JSON: [{{"o_que": "<truque + quando usa, 1 frase>", "como": "<molde>", "exemplos": ["..."], "vezes": n}}]

TRUQUES:
{truques}"""


def falas(pastas):
    out, vistos = [], set()
    for pasta in pastas:
        for sj in sorted(Path(pasta).rglob("segs.json")):
            for s in json.loads(sj.read_text(encoding="utf-8")):
                t = str(s.get("texto") or "").strip()
                if s.get("sim", 1) >= 0.5 and len(t.split()) >= 3 and t.lower() not in vistos:
                    vistos.add(t.lower())
                    out.append(t)
    return out


OUTROS = Path(r"D:\tmp\outros_narr")  # transcricao.json dos outros narradores (hermes-staging /opt/narradores/dados)
SEGS_VOZ = {"mike": [r"D:\tmp\estudo_voz\sv\sub_mike2", r"D:\tmp\estudo_voz\sv\sub_mike3", r"D:\tmp\estudo_voz\sv_mike"],
            "kkvirjao": [r"D:\tmp\estudo_voz\sv\sub_virjao1"]}

EXCLUSIVO = """Narrador {voz}. Abaixo, expressões que ELE usa muito e os OUTROS narradores de recap quase nunca usam
(contagem dele x média dos outros), com frases reais dele. E as expressões que os OUTROS usam muito e ELE quase
nunca usa. (A transcrição é do Whisper: gíria pode vir "corrigida" errado — deduza a gíria real pelo contexto.)
Diga o que é EXCLUSIVO do jeito dele (gírias regionais, apelidos, palavrões, expressões) e o que ele NÃO fala.
Responda SÓ JSON: {{"exclusivo": [{{"o_que": "<expressão/gíria + quando usa>", "exemplos": ["<frase real>"]}}],
"nao_fala": ["<expressão comum dos outros que ele não usa>"]}}

SÓ DELE:
{dele}

DOS OUTROS (ele quase não usa):
{outros}"""


def _ngramas(textos, n_max=3):
    from collections import Counter
    c = Counter()
    for t in textos:
        p = re.findall(r"[a-zà-ú]+", t.lower())
        for n in range(1, n_max + 1):
            for k in range(len(p) - n + 1):
                c[" ".join(p[k:k + n])] += 1
    tot = sum(1 for t in textos for _ in re.findall(r"\w+", t)) or 1
    return c, tot


def exclusivo(voz, ts):
    """Expressões dele x dos outros narradores (frequência por 10 mil palavras)."""
    meus, tot = _ngramas(ts)
    outros = []
    for f in sorted(OUTROS.glob("*.json")):
        if f.stem == voz:
            continue
        outros.append(_ngramas([s["texto"] for s in json.loads(f.read_text(encoding="utf-8"))]))
    for v, pastas in SEGS_VOZ.items():
        if v != voz and all(Path(p).exists() for p in pastas):
            outros.append(_ngramas(falas(pastas)))
    if not outros:
        return None

    def taxa(c, t, g):
        return c[g] * 10000 / t
    dele, deles = [], []
    for g, n in meus.items():
        if n < 4:
            continue
        mo = sum(taxa(c, t, g) for c, t in outros) / len(outros)
        md = taxa(meus, tot, g)
        if md >= 3 * (mo + 0.3):
            dele.append((md / (mo + 0.3), g, n, round(mo, 1)))
    vistos = set()
    for c, t in outros:
        for g, n in c.most_common(400):
            if g in vistos or len(g) < 4:
                continue
            vistos.add(g)
            mo = sum(taxa(cc, tt, g) for cc, tt in outros) / len(outros)
            if mo >= 4 and taxa(meus, tot, g) < mo / 6:
                deles.append((mo, g))
    dele.sort(reverse=True)
    deles.sort(reverse=True)
    linhas = []
    for _r, g, n, mo in dele[:70]:
        ex = [t for t in ts if re.search(rf"\b{re.escape(g)}\b", t.lower())][:2]
        linhas.append(f"- '{g}' (dele {n}x, outros {mo}/10mil): " + " | ".join(e[:120] for e in ex))
    return EXCLUSIVO.format(voz=voz, dele="\n".join(linhas), outros=", ".join(f"'{g}'" for _m, g in deles[:40]))


def _json(txt, abre="["):
    m = re.search(r"\[.*\]" if abre == "[" else r"\{.*\}", txt or "", re.S)
    return json.loads(m.group(0)) if m else []


def montar(voz, pastas, sobe=False):
    ts = falas(pastas)
    print(f"{voz}: {len(ts)} falas reais", flush=True)
    achados = []
    for b in range(0, len(ts), BLOCO):
        bloco = "\n".join(f"- {t}" for t in ts[b:b + BLOCO])
        try:
            r = claude_client.generate_text(LER.format(voz=voz, falas=bloco), max_tokens=4000, temperature=0.2,
                                            timeout=300)
            lst = _json(r)
            achados += lst
            print(f"  bloco {b // BLOCO + 1}/{(len(ts) + BLOCO - 1) // BLOCO}: {len(lst)} truques", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  bloco {b // BLOCO + 1}: falhou ({type(e).__name__}: {str(e)[:80]})", flush=True)
    if not achados:
        print(f"{voz}: nada achado — linguagem_v2 não mudou")
        return
    r = claude_client.generate_text(JUNTAR.format(voz=voz, truques=json.dumps(achados, ensure_ascii=False)),
                                    max_tokens=6000, temperature=0.2, timeout=400)
    marcas = [{**m, "profunda": True} for m in _json(r) if isinstance(m, dict) and m.get("o_que")]
    if not marcas:
        print(f"{voz}: junção vazia — linguagem_v2 não mudou")
        return
    arq = VOZES / voz / "linguagem_v2.json"
    g = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
    Path(str(arq) + ".bkp_marcas").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    manuais = [m for m in g.get("marcas_registradas") or [] if isinstance(m, dict) and m.get("manual")]
    # 20/11 dona ("o Virjão fala 'guria trancada no boga', os outros não falam isso; e tem coisa que os outros falam
    # que ele não fala"): o que é SÓ DELE vem primeiro; o que ele não fala vai pro "evitar"
    exc = {}
    try:
        p = exclusivo(voz, ts)
        if p:
            m = re.search(r"\{.*\}", claude_client.generate_text(p, max_tokens=4000, temperature=0.2, timeout=300)
                          or "", re.S)
            exc = json.loads(m.group(0)) if m else {}
    except Exception as e:  # noqa: BLE001
        print(f"  exclusivo falhou ({type(e).__name__}: {str(e)[:80]})")
    so_dele = [{"o_que": "SÓ DELE: " + x["o_que"], "exemplos": x.get("exemplos") or [], "profunda": True,
                "exclusivo": True} for x in exc.get("exclusivo") or [] if isinstance(x, dict) and x.get("o_que")]
    if exc.get("nao_fala"):
        g["nao_fala"] = [str(x) for x in exc["nao_fala"]][:15]
        print(f"  NÃO fala: {g['nao_fala']}")
    for x in so_dele:
        print(f" * {x['o_que']}  | ex: {(x['exemplos'] or [''])[0][:100]}")
    g["marcas_registradas"] = so_dele[:6] + manuais + marcas
    g["_marcas_registradas_fonte"] = f"marcas_profundas.py: IA leu {len(ts)} falas reais"
    arq.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{voz}: {len(marcas)} marcas profundas")
    for m in marcas:
        print(f" - {m['o_que']}  | ex: {(m.get('exemplos') or [''])[0][:110]}")
    if sobe:
        subprocess.run([R, "copyto", str(arq), f"manhwa-drive:colab_recap/vozes/{voz}/linguagem_v2.json"], check=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--sobe"]
    montar(args[0], args[1:], "--sobe" in sys.argv)
