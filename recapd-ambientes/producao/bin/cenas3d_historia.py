"""23/11 dona: "o 3D recortado (sem fundo, como a mascote) está aprovado; falta usar pra coisas que façam sentido com a
história" — reação, meme, explicar algo da narração, complementar o que está sendo contado.

1) IA lê o roteiro do longo e escolhe os N momentos mais fortes (1 a cada ~CENA3D_CADA_S segundos), e pra cada um
   devolve uma RECEITA curta (não o storyboard): tipo da cena, quem aparece (gênero, papel, cor da roupa/cabelo do
   personagem da história), a ação/expressão de cada um, um ícone e um texto curto (onomatopeia/meme/dado).
2) O código monta o storyboard VÁLIDO do kit3d a partir de moldes testados (câmera, posições e tempos fixos), com
   recorte=True (fundo magenta = boneco recortado) e 1920x1080.
Tipos (moldes): tapa, briga, susto, comemora, dinheiro, romance, pensamento, choro, ri_da_cara, ameaca, explica,
   entra_poderoso, desmaio, fofoca.
Saída: <pasta>/cenas3d/<k>/storyboard.json + cenas3d.json [{frase_i, tipo, texto, storyboard}].
Uso: python cenas3d_historia.py <roteiro.txt> <pasta_saida> [n]   (CENAS3D=0 desliga no pipeline)."""
import json
import os
import re
import sys
from pathlib import Path

DUR = 4.5
ICONES = {"x", "v", "alerta", "interrogacao", "exclamacao", "coracao", "estrela", "lampada", "relogio", "dinheiro",
          "fogo", "proibido", "raio"}
EXPR = {"neutral", "happy", "laugh", "sad", "angry", "surprised", "worried", "thinking", "sleepy"}
CABELO = {"bald", "short", "fringe", "long", "ponytail", "bun", "curly", "sides"}


def _cor(c, padrao):
    return c if isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", c or "") else padrao


def _pessoa(p, pid, pos, giro, acoes):
    fem = str(p.get("genero", "m")).lower().startswith("f")
    papel = str(p.get("papel", "")).lower()
    preset = "velhinha" if fem and "idos" in papel else "velhinho" if "idos" in papel else \
        "menina" if fem and "crian" in papel else "crianca" if "crian" in papel else "mulher" if fem else "homem"
    ov = {"top": {"color": _cor(p.get("roupa"), "#e11d48" if fem else "#1f2937")},
          "hair": {"style": p.get("cabelo_estilo") if p.get("cabelo_estilo") in CABELO else ("long" if fem else "short"),
                   "color": _cor(p.get("cabelo"), "#3b2314")}}
    if p.get("calca"):
        ov["bottom"] = {"color": _cor(p.get("calca"), "#1e3a8a")}
    if p.get("oculos"):
        ov["face"] = {"glasses": True}
    if p.get("barba"):
        ov.setdefault("face", {})["beard"] = True
    return {"id": pid, "preset": preset, "pos": pos, "giro": giro, "overrides": ov, "acoes": acoes}


def _ex(p, padrao):
    e = str(p.get("expressao") or "").lower()
    return e if e in EXPR else padrao


def montar(rec):
    """receita da IA -> storyboard válido (moldes fixos)."""
    tipo = str(rec.get("tipo", "susto")).lower()
    ps = [p for p in (rec.get("personagens") or []) if isinstance(p, dict)][:2] or [{"genero": "m"}]
    a, b = ps[0], (ps[1] if len(ps) > 1 else None)
    um = lambda clip, ex, de=0.2, ate=DUR, **k: [{"clip": clip, "de": de, "ate": ate, "expressao": ex, **k}]  # noqa: E731
    pers, icone_pos = [], [0.5, 0.18]
    if b and tipo in ("tapa", "briga", "ameaca", "romance", "pensamento", "ri_da_cara", "fofoca", "explica"):
        X = 1.1
        acao_a = {"tapa": um("point", _ex(a, "angry"), 0.3, 1.3, params={"side": "R", "dir": "forward"}) +
                          um("idle", _ex(a, "angry"), 1.3),
                  "briga": um("push", _ex(a, "angry")),
                  "ameaca": um("point", _ex(a, "angry"), params={"side": "R", "dir": "forward"}),
                  "romance": um("wave", _ex(a, "happy")),
                  "pensamento": um("think", _ex(a, "thinking")),
                  "ri_da_cara": um("talk", "laugh", fala=False),
                  "fofoca": um("talk", _ex(a, "happy")),
                  "explica": um("point", _ex(a, "happy"), params={"side": "R", "dir": "forward"})}[tipo]
        acao_b = {"tapa": um("idle", "neutral", 0, 1.2) + um("surprised", _ex(b, "surprised"), 1.2),
                  "briga": um("surprised", _ex(b, "worried")),
                  "ameaca": um("shake_head", _ex(b, "worried")),
                  "romance": um("idle", _ex(b, "happy")),
                  "pensamento": um("idle", "happy", 0, 2) + um("surprised", _ex(b, "worried"), 2),
                  "ri_da_cara": um("idle", _ex(b, "sad")),
                  "fofoca": um("surprised", _ex(b, "surprised")),
                  "explica": um("think", _ex(b, "thinking"))}[tipo]
        pers = [_pessoa(a, "a", [-X, 0, 0], 60, acao_a), _pessoa(b, "b", [X, 0, 0], -60, acao_b)]
        cam = {"tipo": "fixa", "pos": [0, 1.45, 4.6], "olha": [0, 1.1, 0], "fov": 40}
        icone_pos = [0.62, 0.2] if tipo in ("tapa", "pensamento", "fofoca") else [0.5, 0.16]
    else:
        clip, ex = {"comemora": ("cheer", "laugh"), "dinheiro": ("cheer", "happy"), "susto": ("surprised", "surprised"),
                    "choro": ("idle", "sad"), "desmaio": ("surprised", "sleepy"), "entra_poderoso": ("walk", "angry"),
                    "pensamento": ("think", "thinking"), "explica": ("talk", "happy")}.get(tipo, ("surprised", "surprised"))
        p0 = _pessoa(a, "a", [0, 0, 0], 0, um(clip, _ex(a, ex)))
        if tipo == "entra_poderoso":
            p0["pos"] = [-1.6, 0, 0]
            p0["movimentos"] = [{"de": 0.1, "ate": 2.2, "para": [0, 0], "clip": "walk"}]
            p0["acoes"] = um("idle", _ex(a, "angry"), 2.2)
        if tipo == "explica":
            p0["acoes"] = um("talk", _ex(a, "happy"), fala=False)
        pers = [p0]
        cam = {"tipo": "fixa", "pos": [0, 1.3, 3.6], "olha": [0, 1.0, 0], "fov": 40}
    icone = rec.get("icone") if rec.get("icone") in ICONES else \
        {"tapa": "exclamacao", "dinheiro": "dinheiro", "romance": "coracao", "pensamento": "lampada",
         "susto": "exclamacao", "ameaca": "alerta", "choro": "interrogacao", "comemora": "estrela", "briga": "raio",
         "entra_poderoso": "fogo", "explica": "lampada", "fofoca": "interrogacao", "ri_da_cara": "x",
         "desmaio": "estrela"}.get(tipo, "exclamacao")
    els = [{"tipo": "icone", "icone": icone, "pos": icone_pos, "tamanho": 0.16, "de": 0.5, "ate": DUR}]
    if tipo in ("dinheiro", "comemora"):
        els.append({"tipo": "icone", "icone": icone, "pos": [0.28, 0.32], "tamanho": 0.12, "de": 0.9, "ate": DUR})
    if rec.get("etiqueta"):
        els.append({"tipo": "etiqueta", "texto": str(rec["etiqueta"])[:22], "pos": [0.5, 0.86], "ponto": "#ffd60a",
                    "de": 0.6, "ate": DUR})
    cena = {"inicio": 0, "fim": DUR, "transicao": "corte", "objetos": [], "personagens": pers, "camera": cam,
            "elementos": els}
    if rec.get("texto"):
        cena["textos"] = [{"texto": str(rec["texto"]).upper()[:24], "de": 0.4, "ate": DUR, "estilo": "destaque"}]
    if tipo in ("dinheiro", "comemora"):
        cena["fluxos"] = [{"material": "fagulha", "origem": [0, 3, 0], "taxa": 30, "tamanho": 0.08, "de": 0.4, "ate": DUR}]
    if tipo == "choro":
        cena["fluxos"] = [{"material": "agua", "origem": [0, 1.55, 0.15], "taxa": 12, "tamanho": 0.04, "de": 0.4, "ate": DUR}]
    if tipo == "entra_poderoso":
        cena["fluxos"] = [{"material": "fogo", "origem": [0, 0.1, 0], "taxa": 25, "tamanho": 0.12, "de": 2.2, "ate": DUR}]
    return {"versao": 1, "titulo": rec.get("texto") or tipo, "formato": {"largura": 1920, "altura": 1080, "fps": 30},
            "duracao": DUR, "recorte": True, "legendas": {"ativo": False},
            "ambiente": {"horario": "dia", "chao": "piso", "fundo": "interior"}, "cenas": [cena]}


PROMPT = """Você é o diretor de um canal de recap de manhwa narrado em PT-BR. Em cima do vídeo vão aparecer, pequenos e
recortados num canto (como figurinhas animadas), bonequinhos 3D low-poly que REFORÇAM o que o narrador está contando:
uma reação, um meme, uma explicação, a piada da cena. Escolha os {n} MOMENTOS em que isso mais combina (cenas fortes,
engraçadas, viradas, humilhação do vilão, dinheiro, romance, susto, poder revelado), espalhados pelo vídeo, no máximo 1
a cada {gap} frases. Para cada momento devolva:
- "linha": número da frase do roteiro;
- "tipo": um de tapa, briga, susto, comemora, dinheiro, romance, pensamento, choro, ri_da_cara, ameaca, explica,
  entra_poderoso, desmaio, fofoca;
- "personagens": 1 ou 2, cada um {{"nome", "genero": "m|f", "papel": "adulto|idoso|crianca", "roupa": "#hex da cor da
  roupa dele na história (chute coerente: vilão rico = terno escuro, CEO = preto, noiva = vermelho...)", "cabelo": "#hex",
  "cabelo_estilo": "short|long|ponytail|bun|curly|bald|fringe|sides", "expressao": "neutral|happy|laugh|sad|angry|
  surprised|worried|thinking|sleepy"}} — o 1º é quem FAZ a ação, o 2º quem recebe;
- "texto": 1 a 3 palavras na tela, engraçado/de meme (ex.: "PLAFT!", "10 MILHÕES", "ELA OUVIU", "TOMA!", "F", "CHORA");
- "icone" (opcional): x, v, alerta, interrogacao, exclamacao, coracao, estrela, lampada, relogio, dinheiro, fogo,
  proibido, raio;
- "etiqueta" (opcional, só quando explica algo): rótulo curto, ex.: "QI: 1 DÍGITO".
Responda SÓ um JSON: [{{...}}, ...]

ROTEIRO:
{roteiro}"""


def escolher(linhas, n=None):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import claude_client
    n = n or max(3, min(14, len(linhas) // 60))
    k = max(1, -(-sum(len(l) for l in linhas) // 60000))
    numerado = "\n".join(f"{i}: {linhas[i][:170]}" for i in range(0, len(linhas), k))
    resp, _m, _t = claude_client.generate_text_vivo(
        PROMPT.format(n=n, gap=max(15, len(linhas) // (n + 1)), roteiro=numerado), claude_client.CADEIA_TEXTO_LONGO,
        max_tokens=4000, temperature=0.6, timeout=180, rodadas=2)
    m = re.search(r"\[.*\]", resp or "", re.S)
    itens = json.loads(m.group(0)) if m else []
    return [x for x in itens if isinstance(x, dict) and isinstance(x.get("linha"), int) and 0 <= x["linha"] < len(linhas)]


def gerar(linhas, pasta, n=None):
    pasta = Path(pasta)
    (pasta / "cenas3d").mkdir(parents=True, exist_ok=True)
    out = []
    for k, rec in enumerate(sorted(escolher(linhas, n), key=lambda x: x["linha"])):
        sb = montar(rec)
        d = pasta / "cenas3d" / f"c{k:02d}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
        out.append({"k": k, "frase_i": rec["linha"], "frase": linhas[rec["linha"]], "tipo": rec.get("tipo"),
                    "texto": rec.get("texto"), "pasta": f"c{k:02d}"})
    (pasta / "cenas3d.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    linhas = [l.strip() for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
    r = gerar(linhas, sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    for x in r:
        print(x["frase_i"], x["tipo"], x["texto"], "|", x["frase"][:90])
