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


def _molde_v2(tipo, rec, ps, um):
    """24/11: moldes próprios de manhwa. Devolve storyboard pronto ou None."""
    if tipo not in ("raiva", "level_up", "despertar", "humilhacao", "riu_ate_ver", "plateia_chocada", "ex_arrependida"):
        return None
    a = ps[0]
    b = ps[1] if len(ps) > 1 else {"genero": "m"}
    pers, els, fl, ef, cam = [], [], [], [], {"tipo": "fixa", "pos": [0, 1.3, 4.6], "olha": [0, 1.1, 0], "fov": 40}
    txt = rec.get("texto")
    if tipo == "raiva":
        pers = [_pessoa(a, "a", [0, 0, 0], 0, um("shake_head", "angry", 0.2, 1.4) + um("surprised", "angry", 1.4))]
        fl = [{"material": "fumaca", "origem": [0, 1.9, 0], "taxa": 18, "tamanho": 0.12, "de": 0.4, "ate": DUR}]
        ef = [{"tipo": "tremor", "de": 1.4, "ate": 1.9}]
        els = [{"tipo": "icone", "icone": "fogo", "pos": [0.64, 0.17], "tamanho": 0.16, "de": 0.4, "ate": DUR}]
    elif tipo == "level_up":
        pers = [_pessoa(a, "a", [0, 0, 0], 0, um("surprised", "surprised", 0.2, 1.6) + um("cheer", "laugh", 1.6))]
        fl = [{"material": "luz", "origem": [0, 0.1, 0], "taxa": 35, "tamanho": 0.08, "de": 1.4, "ate": DUR}]
        et = rec.get("etiqueta") or "NÍVEL UP!"
        els = [{"tipo": "etiqueta", "texto": str(et)[:22], "pos": [0.5, 0.2], "ponto": "#38bdf8", "de": 0.5, "ate": DUR},
               {"tipo": "icone", "icone": "estrela", "pos": [0.66, 0.3], "tamanho": 0.13, "de": 1.5, "ate": DUR}]
        txt = txt or "LEVEL UP"
    elif tipo == "despertar":
        p0 = _pessoa(a, "a", [0, 0, 0], 0, um("idle", "angry"))
        p0["anim"] = {"escala": [[0, 1.0], [1.2, 1.08], [2.4, 1.0], [3.6, 1.08]]}
        pers = [p0]
        fl = [{"material": "fagulha", "origem": [0, 1.0, 0], "taxa": 30, "tamanho": 0.09, "de": 0.6, "ate": DUR},
              {"material": "luz", "origem": [0, 0.1, 0], "taxa": 25, "tamanho": 0.09, "de": 0.3, "ate": DUR}]
        ef = [{"tipo": "tremor", "de": 0.6, "ate": 1.2}]
        els = [{"tipo": "icone", "icone": "raio", "pos": [0.65, 0.18], "tamanho": 0.15, "de": 0.6, "ate": DUR}]
        txt = txt or "DESPERTOU"
    elif tipo in ("humilhacao", "plateia_chocada"):
        centro = _pessoa(a, "a", [-0.4, 0, 0.6], 0, um("idle", "sad" if tipo == "humilhacao" else "surprised"))
        figs = [{"genero": "m", "roupa": "#64748b"}, {"genero": "f", "roupa": "#a855f7"}, {"genero": "m", "papel": "idoso",
                "roupa": "#78716c"}]
        clip, ex = ("talk", "laugh") if tipo == "humilhacao" else ("surprised", "surprised")
        for k, (x, z) in enumerate(((-1.9, -0.6), (0.95, -1.5), (1.9, -0.6))):
            pf = _pessoa(figs[k], f"f{k}", [x, 0, z], 0, um(clip, ex, 0.2 + 0.15 * k))
            if tipo == "humilhacao" and k == 1:
                pf["acoes"] = um("point", "laugh", 0.3, params={"side": "R", "dir": "forward"})
            pers.append(pf)
        pers.insert(0, centro)
        cam = {"tipo": "fixa", "pos": [0, 1.7, 7.0], "olha": [0, 1.0, -0.5], "fov": 44}
        els = [{"tipo": "icone", "icone": "x" if tipo == "humilhacao" else "exclamacao", "pos": [0.78, 0.3],
                "tamanho": 0.14, "de": 0.5, "ate": DUR}]
        if tipo == "plateia_chocada":
            ef = [{"tipo": "pretoebranco", "de": 0.3, "ate": 0.9}]
    elif tipo == "riu_ate_ver":  # o vilão ri... até ver
        vil = _pessoa(b if len(ps) > 1 else a, "v", [0.6, 0, 0], -60, um("talk", "laugh", 0.1, 2.1, fala=False) +
                      um("surprised", "surprised", 2.1))
        pro = _pessoa(a, "p", [-0.9, 0, 0], 60, um("idle", "neutral"))
        pers = [pro, vil]
        ef = [{"tipo": "pretoebranco", "de": 2.1, "ate": 2.6}, {"tipo": "zoom", "de": 2.1, "ate": 2.8}]
        els = [{"tipo": "icone", "icone": "exclamacao", "pos": [0.64, 0.18], "tamanho": 0.15, "de": 2.1, "ate": DUR}]
    elif tipo == "ex_arrependida":
        ela = _pessoa(a if str(a.get("genero", "")).startswith("f") else b, "e", [-0.6, 0, 0.3], 0, um("idle", "sad"))
        ele = _pessoa(b if str(a.get("genero", "")).startswith("f") else a, "h", [0.6, 0, 0], 180, um("idle", "neutral"))
        ele["movimentos"] = [{"de": 0.6, "ate": 3.6, "para": [2.6, -1.0], "clip": "walk"}]
        pers = [ela, ele]
        fl = [{"material": "agua", "origem": [-0.6, 1.55, 0.45], "taxa": 10, "tamanho": 0.04, "de": 0.5, "ate": DUR}]
        els = [{"tipo": "icone", "icone": "coracao", "pos": [0.36, 0.2], "tamanho": 0.13, "de": 0.5, "ate": 2.0},
               {"tipo": "icone", "icone": "x", "pos": [0.36, 0.2], "tamanho": 0.15, "de": 2.0, "ate": DUR}]
        txt = txt or "AGORA É TARDE"
    cena = {"inicio": 0, "fim": DUR, "transicao": "corte", "objetos": [], "personagens": pers, "camera": cam,
            "elementos": els}
    if fl:
        cena["fluxos"] = fl
    if ef:
        cena["efeitos"] = ef
    if txt:
        cena["textos"] = [{"texto": str(txt).upper()[:24], "de": 0.4, "ate": DUR, "estilo": "meme"}]
    return {"versao": 1, "titulo": txt or tipo, "formato": {"largura": 1920, "altura": 1080, "fps": 30},
            "duracao": DUR, "recorte": True, "legendas": {"ativo": False},
            "ambiente": {"horario": "dia", "chao": "piso", "fundo": "interior"}, "cenas": [cena]}


TIPOS = {"tapa", "briga", "susto", "comemora", "dinheiro", "romance", "pensamento", "choro", "ri_da_cara", "ameaca",
         "explica", "entra_poderoso", "desmaio", "fofoca", "raiva", "level_up", "despertar", "humilhacao",
         "riu_ate_ver", "plateia_chocada", "ex_arrependida"}


def _validar(itens, n_linhas, n_max):
    """24/11: tipo conhecido, no máx. 2 do mesmo tipo, distância mínima entre cenas, elenco fixo por nome."""
    out, por_tipo, elenco = [], {}, {}
    gap = max(15, n_linhas // (n_max * 2 + 1))
    for x in sorted(itens, key=lambda y: y.get("linha", 0)):
        t = str(x.get("tipo", "")).lower()
        if t not in TIPOS or por_tipo.get(t, 0) >= 2:
            continue
        if out and x["linha"] - out[-1]["linha"] < gap:
            continue
        for p in x.get("personagens") or []:
            if not isinstance(p, dict):
                continue
            nome = str(p.get("nome") or "").strip().lower()
            if nome and nome in elenco:  # mesma pessoa = mesmo visual no vídeo todo
                for k in ("roupa", "cabelo", "cabelo_estilo", "genero", "papel", "oculos", "barba", "calca"):
                    if k in elenco[nome]:
                        p[k] = elenco[nome][k]
            elif nome:
                elenco[nome] = {k: p[k] for k in ("roupa", "cabelo", "cabelo_estilo", "genero", "papel", "oculos",
                                                  "barba", "calca") if k in p}
        x["tipo"] = t
        por_tipo[t] = por_tipo.get(t, 0) + 1
        out.append(x)
        if len(out) >= n_max:
            break
    return out


def montar(rec):
    """receita da IA -> storyboard válido (moldes fixos)."""
    tipo = str(rec.get("tipo", "susto")).lower()
    ps = [p for p in (rec.get("personagens") or []) if isinstance(p, dict)][:4] or [{"genero": "m"}]
    a, b = ps[0], (ps[1] if len(ps) > 1 else None)
    um = lambda clip, ex, de=0.2, ate=DUR, **k: [{"clip": clip, "de": de, "ate": ate, "expressao": ex, **k}]  # noqa: E731
    pers, icone_pos = [], [0.5, 0.18]
    extra = _molde_v2(tipo, rec, ps, um)
    if extra:
        return extra
    if b and tipo in ("tapa", "briga", "ameaca", "romance", "pensamento", "ri_da_cara", "fofoca", "explica"):
        X = 0.55 if tipo in ("tapa", "briga", "romance") else 1.1  # 24/11: tapa/briga/beijo com contato
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
        pers = [_pessoa(a, "a", [-X, 0, 0], 70, acao_a), _pessoa(b, "b", [X, 0, 0], -70, acao_b)]
        if tipo in ("tapa", "briga"):  # quem apanha é empurrado pra trás depois do golpe
            pers[1]["movimentos"] = [{"de": 1.25, "ate": 1.7, "para": [X + 0.35, 0], "clip": "walk", "velocidade": 2.5}]
        cam = {"tipo": "fixa", "pos": [0, 1.45, 4.6], "olha": [0, 1.1, 0], "fov": 40}
        icone_pos = [0.74, 0.34]
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
        cam = {"tipo": "fixa", "pos": [0, 1.25, 4.4], "olha": [0, 1.15, 0], "fov": 40}
        icone_pos = [0.66, 0.34]  # 24/11: ao lado da cabeça, abaixo do texto de meme
    icone = rec.get("icone") if rec.get("icone") in ICONES else \
        {"tapa": "exclamacao", "dinheiro": "dinheiro", "romance": "coracao", "pensamento": "lampada",
         "susto": "exclamacao", "ameaca": "alerta", "choro": "interrogacao", "comemora": "estrela", "briga": "raio",
         "entra_poderoso": "fogo", "explica": "lampada", "fofoca": "interrogacao", "ri_da_cara": "x",
         "desmaio": "estrela"}.get(tipo, "exclamacao")
    els = [{"tipo": "icone", "icone": icone, "pos": icone_pos, "tamanho": 0.16, "de": 0.5, "ate": DUR}]
    if tipo in ("dinheiro", "comemora"):
        els.append({"tipo": "icone", "icone": icone, "pos": [0.36, 0.3], "tamanho": 0.12, "de": 0.9, "ate": DUR})
    if rec.get("etiqueta"):
        els.append({"tipo": "etiqueta", "texto": str(rec["etiqueta"])[:22], "pos": [0.5, 0.88], "ponto": "#ffd60a", "tamanho": 1.8,
                    "de": 0.6, "ate": DUR})
    cena = {"inicio": 0, "fim": DUR, "transicao": "corte", "objetos": [], "personagens": pers, "camera": cam,
            "elementos": els}
    if rec.get("texto"):
        cena["textos"] = [{"texto": str(rec["texto"]).upper()[:24], "de": 0.4, "ate": DUR, "estilo": "meme"}]
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
  entra_poderoso, desmaio, fofoca, raiva (alguém surtando/quebrando coisa), level_up (janela de sistema, subiu de nível,
  ganhou habilidade), despertar (aura, poder revelado), humilhacao (todo mundo rindo de alguém), riu_ate_ver (o vilão
  debocha e depois leva o choque), plateia_chocada (a sala inteira trava), ex_arrependida (ela se arrepende e ele vai
  embora). VARIE: no máximo 2 do mesmo tipo; prefira os que viram MEME/REAÇÃO, não só repetir o que a imagem mostra;
- "personagens": 1 ou 2, cada um {{"nome", "genero": "m|f", "papel": "adulto|idoso|crianca", "roupa": "#hex da cor da
  roupa dele na história (chute coerente: vilão rico = terno escuro, CEO = preto, noiva = vermelho...)", "cabelo": "#hex",
  "cabelo_estilo": "short|long|ponytail|bun|curly|bald|fringe|sides", "expressao": "neutral|happy|laugh|sad|angry|
  surprised|worried|thinking|sleepy"}} — o 1º é quem FAZ a ação, o 2º quem recebe;
- "texto": 1 a 3 palavras na tela, engraçado/de meme (ex.: "PLAFT!", "10 MILHÕES", "ELA OUVIU", "TOMA!", "F", "CHORA");
  números SÓ se estiverem na frase, exatamente iguais (não troque milhões por bilhões);
- use SEMPRE o mesmo "nome" pra mesma pessoa (o visual dela fica fixo no vídeo todo);
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
        PROMPT.format(n=n + 4, gap=max(15, len(linhas) // (n + 1)), roteiro=numerado), claude_client.CADEIA_TEXTO_LONGO,
        max_tokens=4000, temperature=0.6, timeout=180, rodadas=2)
    m = re.search(r"\[.*\]", resp or "", re.S)
    try:
        itens = json.loads(m.group(0)) if m else []
    except ValueError:
        itens = []
    itens = [x for x in itens if isinstance(x, dict) and isinstance(x.get("linha"), int) and 0 <= x["linha"] < len(linhas)]
    return _validar(itens, len(linhas), n)


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
