#!/usr/bin/env python3
"""montar-fila-materiais.py — A "COLA": varre D:\\hipercool-materiais\\ e gera as
filas de postagem (fila_*.json) que o postador diario (postar_hoje.py -> postar-fila.py)
ja sabe consumir. NAO posta nada: so descobre videos prontos, resolve metadados e roteia
por canal/tema, escrevendo as filas em D:\\hipercool-producao\\_LEIA_POSTAR_VIDEOS\\.

Regras (fechadas com a dona):
  - Video final por capitulo: .mp4 com sufixo de versao (_CENSURADA/_ELEMENTAL/_ELEVEN/
    _REVISADO/_1080p) tem prioridade; senao censored\\v1.mp4. _PRONTOS\\ do projeto,
    se existir, prioriza. Ignora _iteracoes_antigas/hyperframes/edge/gemini/normal (rascunhos).
  - Metadados: usa doc do projeto (metadata.json completo OU .meta.json com tags) se existir;
    senao gera com postagem_meta (manga) ou gemini_llm (vo3).
  - Roteamento: recap(manga)->canais manga; animes->inovare recap manga; vo3->Gemini classifica
    pelo nome; historias-em-frames->pendente.
  - Pos-postagem: cada item leva 'postados_dir' -> postar-fila.py move o mp4 pra la depois do OK.

Uso:
    python bin/montar-fila-materiais.py --preview           # so mostra, nao escreve fila
    python bin/montar-fila-materiais.py                      # escreve as filas
    python bin/montar-fila-materiais.py --cat recap          # so uma categoria
    python bin/montar-fila-materiais.py --cat vo3 --preview
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
import postagem_meta as PM  # noqa: E402

BRT = timezone(timedelta(hours=-3))

MATERIAIS = Path(r"D:\hipercool-materiais")
VIDEOS_DIR = MATERIAIS / "videos"
ANIMES_DIR = MATERIAIS / "animes recap"
POSTADOS_BASE = MATERIAIS / "_postados"
FILAS_DIR = PROJECT / "_LEIA_POSTAR_VIDEOS"
VO3_DIR = Path(r"D:\downloads\agendar")
CANAIS_JSON = Path(r"D:\credenciais-canais\youtube_canais.json")

# sufixos que marcam a versao FINAL de um cap (prioridade > v1.mp4)
SUFIXOS_FINAIS = ["_CENSURADA", "_ELEMENTAL", "_ELEVEN", "_REVISADO", "_OFICIAL", "_1080p"]
# subpastas que sao rascunho/intermediario — nunca sao o final
SUBPASTAS_RASCUNHO = {"_iteracoes_antigas", "hyperframes", "edge", "gemini", "normal"}

QUOTA_DIA = 6
SLOTS_BRT = ["10:30", "12:00", "13:30", "15:00", "16:30", "18:00", "19:30", "21:00"]

# --- Roteamento por categoria ---
CANAIS_MANGA = ["inovare recap manga", "nova conta de manga br"]
CANAIS_ANIME = ["inovare recap manga"]  # cota livre hoje (proj separado)
# obras de manga/manhwa em videos/
OBRAS_MANGA = ["the-meek-cat", "regressed-warriors", "the-man-who-devours", "taming-noona"]

# vo3 (clones/cenas IA) — canais fixos de nicho "IA/tech"
CANAIS_VO3 = [
    "fabio com ia",
    "seebotstia (inovare com ia",
    "inovarecap(inovare ia",
    "raiz fabricadeautomacoes0(ia pro",
    "raiz 6 emersongencshin(ia brasileira",
    "emersongenc( cerebro digital",
]
# historias-em-frames (terror/superacao/religioso/motivacional) — canais fixos
CANAIS_HISTORIAS = [
    "emersonjosiel1995( motivação",
    "raiz 5 aulasrevolution (aula com ia",
    "raiz3 emersonjosielmrx1995(curiosidade",
    "mundosolar1995 (video cassetadas",
    "doctor192(fofos",
    "gameoftrones(game",
]
HISTORIAS_DIR = Path(r"D:\historias-em-frames")


def _brt_to_utc_iso(dia_str, hhmm):
    h, m = map(int, hhmm.split(":"))
    y, mo, d = map(int, dia_str.split("-"))
    dt = datetime(y, mo, d, h, m, tzinfo=BRT)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _pick_slots(n, pool):
    if n <= 0:
        return []
    if n == 1:
        return [pool[len(pool) // 2]]
    if n >= len(pool):
        return (pool + pool * ((n // len(pool)) + 1))[:n]
    idx = [round(i * (len(pool) - 1) / (n - 1)) for i in range(n)]
    return [pool[i] for i in idx]


def _obra_nome(slug):
    """the-meek-cat -> The Meek Cat"""
    return " ".join(w.capitalize() for w in slug.replace("_", "-").split("-"))


def _cap_num(cap_folder):
    m = re.search(r"(\d+)", cap_folder)
    return int(m.group(1)) if m else 0


def _mb(p):
    try:
        return p.stat().st_size / (1024 * 1024)
    except OSError:
        return 0.0


# --------------------- DESCOBERTA DO VIDEO FINAL ---------------------
def achar_final_do_cap(cap_dir: Path):
    """Retorna o Path do mp4 FINAL de um cap, ou None. Aplica a regra de sufixos."""
    candidatos = []
    # 1. mp4 com sufixo final direto em censored/ ou na raiz do cap
    for base in [cap_dir / "censored", cap_dir]:
        if not base.is_dir():
            continue
        for mp4 in base.glob("*.mp4"):
            candidatos.append(mp4)
    if not candidatos:
        return None
    # prioriza os que tem sufixo final (maior, mais recente entre eles)
    com_sufixo = [c for c in candidatos
                  if any(s.lower() in c.stem.lower() for s in SUFIXOS_FINAIS)]
    pool = com_sufixo if com_sufixo else candidatos
    # entre o pool, prefere censored/ e o maior arquivo
    pool.sort(key=lambda c: (("censored" in str(c.parent).lower()), _mb(c)), reverse=True)
    return pool[0]


def achar_prontos(projeto_dir: Path):
    """Se projeto tem _PRONTOS/, retorna dict {capNN: mp4} priorizando sufixos."""
    pdir = projeto_dir / "_PRONTOS"
    if not pdir.is_dir():
        return {}
    out = {}
    for mp4 in pdir.glob("*.mp4"):
        m = re.search(r"cap0*(\d+)", mp4.stem, re.IGNORECASE)
        if not m:
            continue
        cap = int(m.group(1))
        tem_sufixo = any(s.lower() in mp4.stem.lower() for s in SUFIXOS_FINAIS)
        if cap not in out or tem_sufixo:
            out[cap] = mp4
    return out


# --------------------- METADADOS ---------------------
# avisos acumulados (docs faltando / errados / gerados por IA) — mostrados no fim
AVISOS = []
CAMPOS_OBRIG = ["arquivo", "categoria", "tipo", "titulo", "descricao", "tags"]


def _avisar(msg):
    AVISOS.append(msg)


def ler_postar_json(pasta: Path):
    """Le postar.json (padrao novo) da pasta. Retorna (doc, problemas[list]) ou (None, [])."""
    pj = pasta / "postar.json"
    if not pj.exists():
        return None, []
    try:
        d = json.loads(pj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return None, [f"postar.json ilegivel em {pasta}: {e}"]
    if d.get("pronto") is False:
        return "SKIP", []
    faltando = [c for c in CAMPOS_OBRIG if not d.get(c)]
    return d, faltando


def gerar_meta_ia(pasta, mp4, categoria, contexto=""):
    """Gera titulo/desc/tags via Gemini quando nao ha doc. Escreve postar.json p/ revisao.
    Retorna (titulo, descricao, tags, canal_sugerido|None)."""
    nome = mp4.stem
    prompt = (
        f"Gere metadados de YouTube pra um video da categoria '{categoria}'.\n"
        f"Arquivo: {nome}\n{contexto}\n\n"
        f"Responda SO um JSON: {{\"titulo\": \"<viral PT-BR ate 90 chars>\", "
        f"\"descricao\": \"<3-4 linhas + hashtags>\", \"tags\": [\"6-12 tags\"]}}"
    )
    titulo, desc, tags = nome.replace("_", " ")[:90], "", []
    try:
        import gemini_llm
        resp = gemini_llm.generate_text(prompt)
        js = re.search(r"\{.*\}", resp, re.DOTALL)
        d = json.loads(js.group(0))
        titulo = (d.get("titulo") or titulo)[:100]
        desc = d.get("descricao", "")
        tags = d.get("tags", [])
        origem = "gemini-gerado"
    except Exception as e:  # noqa
        origem = f"fallback({type(e).__name__})"
        desc = f"{titulo}\n\n#shorts"
        tags = ["shorts"]
    # escreve postar.json pra dona revisar
    try:
        doc = {"arquivo": mp4.name, "categoria": categoria, "tipo": "completo",
               "titulo": titulo, "descricao": desc, "tags": tags,
               "pronto": True, "_gerado_por": origem,
               "_REVISAR": "gerado por IA (sem doc do projeto) — confira e corrija"}
        (pasta / "postar.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    _avisar(f"[{categoria}] SEM postar.json em {pasta.name} — GEREI via {origem}. "
            f"Escrevi postar.json pra revisao. Titulo: {titulo[:50]}")
    return titulo, desc, tags, None


def _achar_meta_doc(cap_dir: Path):
    """Procura metadata.json completo ou .meta.json com tags nao-vazias."""
    # metadata.json completo (formato videos laterais)
    for mj in cap_dir.rglob("metadata.json"):
        try:
            d = json.loads(mj.read_text(encoding="utf-8"))
            if d.get("titulo") and d.get("descricao") and d.get("tags"):
                return d
        except (json.JSONDecodeError, OSError):
            pass
    # .meta.json (formato videos/) — so serve se tags nao-vazias
    for mj in cap_dir.rglob("*.meta.json"):
        try:
            d = json.loads(mj.read_text(encoding="utf-8"))
            if d.get("titulo") and d.get("tags"):
                return d
        except (json.JSONDecodeError, OSError):
            pass
    return None


def meta_do_cap(obra, cap, cap_dir, tipo="completo", parte=None, total=None):
    """Retorna (titulo, descricao, tags[list], origem_meta). Ordem de prioridade:
    postar.json (padrao novo) > metadata.json/.meta.json antigo > template manga."""
    # 1. metadata.json/.meta.json legado (formato ja existente no projeto)
    doc = _achar_meta_doc(cap_dir)
    if doc:
        tg = doc.get("tags") or PM.tags(obra, cap)
        if isinstance(tg, str):
            tg = [t.strip() for t in tg.split(",") if t.strip()]
        return (doc["titulo"], doc.get("descricao", ""), tg, "doc-projeto")
    # 2. template manga (obras conhecidas têm template bom, não precisa IA)
    if tipo == "short" and parte and total:
        return (PM.titulo_short(obra, cap, parte, total),
                PM.descricao_short(obra, cap, parte, total),
                PM.tags(obra, cap), "template")
    return (PM.titulo_completo(obra, cap),
            PM.descricao_completo(obra, cap),
            PM.tags(obra, cap), "template")


# --------------------- COLETA POR CATEGORIA ---------------------
def coletar_recap():
    """Manga/manhwa em videos/<obra>/capXX -> itens de fila."""
    itens = []
    for obra_slug in OBRAS_MANGA:
        proj = VIDEOS_DIR / obra_slug
        if not proj.is_dir():
            continue
        obra = _obra_nome(obra_slug)
        prontos = achar_prontos(proj)
        caps_vistos = set()
        # _PRONTOS primeiro
        for cap, mp4 in sorted(prontos.items()):
            caps_vistos.add(cap)
            tit, des, tg, org = meta_do_cap(obra, cap, proj, "completo")
            itens.append(_item(f"{obra_slug}_cap{cap}_completo", mp4, "completo",
                               cap, None, tit, des, tg, "recap", org))
        # caps soltos
        for cap_dir in sorted(proj.glob("cap*")):
            if not cap_dir.is_dir():
                continue
            cap = _cap_num(cap_dir.name)
            if cap in caps_vistos:
                continue
            it = item_de_pasta(cap_dir, "recap", obra=obra, cap=cap,
                               id_base=f"{obra_slug}_cap{cap}")
            if it:
                itens.append(it)
    return itens


def item_de_pasta(pasta, categoria, obra=None, cap=0, id_base=None):
    """Constroi 1 item priorizando postar.json; senao acha o final + gera meta.
    Retorna item ou None se nao ha video."""
    id_base = id_base or f"{categoria}_{pasta.name}"
    doc, faltando = ler_postar_json(pasta)
    if doc == "SKIP":
        return None
    if doc and not faltando:
        # postar.json completo — fonte de verdade
        mp4 = pasta / doc["arquivo"]
        if not mp4.exists():
            _avisar(f"[{categoria}] postar.json de {pasta.name} aponta '{doc['arquivo']}' "
                    f"que NAO existe — pulei.")
            return None
        tg = doc["tags"]
        if isinstance(tg, str):
            tg = [t.strip() for t in tg.split(",") if t.strip()]
        canal = doc.get("canais", [None])[0] if doc.get("canais") else None
        return _item(id_base, mp4, doc.get("tipo", "completo"), cap,
                     doc.get("parte"), doc["titulo"], doc["descricao"], tg,
                     categoria, "postar.json", canal_forcado=canal)
    if doc and faltando:
        _avisar(f"[{categoria}] postar.json de {pasta.name} INCOMPLETO "
                f"(falta: {', '.join(faltando)}) — completei com IA/template.")
    # sem doc valido: acha o final
    final = achar_final_do_cap(pasta)
    if not final:
        return None
    # obra conhecida de manga -> template; senao -> Gemini
    if obra and categoria == "recap":
        tit, des, tg, org = meta_do_cap(obra, cap, pasta, "completo")
    else:
        tit, des, tg, _ = gerar_meta_ia(pasta, final, categoria)
        org = "gemini-gerado"
    return _item(id_base, final, "completo", cap, None, tit, des, tg, categoria, org)


def coletar_animes():
    """animes recap/videos laterais/<slug>/video.mp4 (+ postar.json ou metadata.json)."""
    itens = []
    laterais = ANIMES_DIR / "videos laterais"
    if not laterais.is_dir():
        return itens
    for slug_dir in sorted(laterais.iterdir()):
        if not slug_dir.is_dir():
            continue
        # 1. postar.json (padrao novo)
        doc, faltando = ler_postar_json(slug_dir)
        if doc == "SKIP":
            continue
        if doc and not faltando:
            it = item_de_pasta(slug_dir, "animes", id_base=f"anime_{slug_dir.name}")
            if it:
                itens.append(it)
            continue
        # 2. video final da pasta
        mp4 = slug_dir / "video.mp4"
        if not mp4.exists():
            mp4s = list(slug_dir.glob("*.mp4"))
            if not mp4s:
                continue
            mp4 = max(mp4s, key=_mb)
        # 3. metadata.json legado
        legado = _achar_meta_doc(slug_dir)
        if legado:
            tg = legado.get("tags") or []
            if isinstance(tg, str):
                tg = [t.strip() for t in tg.split(",") if t.strip()]
            tit, des, org = legado["titulo"], legado.get("descricao", ""), "doc-projeto"
        else:
            # 4. sem doc -> Gemini gera + avisa + escreve postar.json
            tit, des, tg, _ = gerar_meta_ia(slug_dir, mp4, "animes")
            org = "gemini-gerado"
        itens.append(_item(f"anime_{slug_dir.name}", mp4, "completo",
                           0, None, tit, des, tg, "animes", org))
    return itens


def coletar_vo3(canais_desc=None):
    """VO3 em D:\\downloads\\agendar -> Gemini escolhe entre CANAIS_VO3 (nicho IA) + gera meta."""
    itens = []
    if not VO3_DIR.is_dir():
        return itens
    # Gemini so pode escolher entre os canais fixos de vo3
    canais = CANAIS_VO3
    # filtra: VO3 sao os que NAO sao final_anime_* (esses sao recap ja movidos)
    videos = [p for p in sorted(VO3_DIR.glob("*.mp4"))
              if "final_anime" not in p.stem and "recap_" not in p.stem
              and "teste_limpeza" not in p.stem]
    for mp4 in videos:
        canal, tit, des, tg, org = classificar_vo3(mp4, canais)
        itens.append(_item(f"vo3_{mp4.stem[:40]}", mp4, "short",
                           0, None, tit, des, tg, "vo3", org, canal_forcado=canal))
    return itens


def coletar_historias():
    """historias-em-frames -> Gemini escolhe entre CANAIS_HISTORIAS por genero/tema.
    Cuidado: este projeto coloca varias versoes (_FINAL/_ULTIMO/_shorts) na MESMA pasta."""
    itens = []
    saida = HISTORIAS_DIR / "workspace"
    # procura mp4s finais (prioriza _FINAL/_ULTIMO, ignora _TESTE/_shorts intermediarios)
    bases = [saida, HISTORIAS_DIR / "output", HISTORIAS_DIR / "videos"]
    vistos = set()
    for base in bases:
        if not base.is_dir():
            continue
        for pasta in sorted([p for p in base.rglob("*") if p.is_dir()]) + [base]:
            # 1. postar.json tem prioridade
            doc, faltando = ler_postar_json(pasta)
            if doc == "SKIP":
                continue
            if doc and not faltando:
                it = item_de_pasta(pasta, "historias", id_base=f"hist_{pasta.name}")
                if it and it["arquivo"] not in vistos:
                    vistos.add(it["arquivo"])
                    itens.append(it)
                continue
        # 2. sem doc: acha finais soltos (_FINAL/_ULTIMO), gera via Gemini
        for mp4 in base.rglob("*_FINAL*.mp4"):
            if str(mp4) in vistos or "_TESTE" in mp4.stem or "shorts" in mp4.stem.lower():
                continue
            vistos.add(str(mp4))
            canal, tit, des, tg, org = classificar_historia(mp4, CANAIS_HISTORIAS)
            itens.append(_item(f"hist_{mp4.stem[:40]}", mp4, "completo",
                               0, None, tit, des, tg, "historias", org, canal_forcado=canal))
    return itens


def classificar_historia(mp4, canais):
    """Gemini escolhe canal de historias pelo tema/genero do nome + gera meta."""
    return classificar_vo3(mp4, canais)  # mesma logica: nome -> canal + meta


def classificar_vo3(mp4: Path, canais_desc):
    """Usa Gemini pra escolher canal + gerar titulo/desc/tags pelo nome do arquivo."""
    nome = mp4.stem
    # roteiro .md opcional
    roteiro = ""
    for cand in [mp4.with_suffix(".md"), mp4.parent / f"{nome}.md"]:
        if cand.exists():
            roteiro = cand.read_text(encoding="utf-8", errors="replace")[:1500]
            break
    canais_txt = "\n".join(f"- {c}" for c in canais_desc)
    prompt = (
        f"Voce roteia videos curtos (VO3/IA) pro canal certo do YouTube pelo TEMA.\n"
        f"Nome do arquivo: {nome}\n"
        f"{('Roteiro: ' + roteiro) if roteiro else ''}\n\n"
        f"Canais disponiveis:\n{canais_txt}\n\n"
        f"Responda SO um JSON: {{\"canal\": \"<nome exato de um canal da lista>\", "
        f"\"titulo\": \"<titulo viral PT-BR ate 90 chars com #shorts>\", "
        f"\"descricao\": \"<2-3 linhas + hashtags>\", "
        f"\"tags\": [\"5-10 tags\"]}}"
    )
    try:
        import gemini_llm
        resp = gemini_llm.generate_text(prompt)
        js = re.search(r"\{.*\}", resp, re.DOTALL)
        d = json.loads(js.group(0))
        canal = d["canal"]
        if canal not in canais_desc:
            canal = canais_desc[0]
        return (canal, d.get("titulo", nome)[:100], d.get("descricao", ""),
                d.get("tags", ["shorts", "viral"]), "gemini")
    except Exception as e:  # noqa
        # fallback: canal default + titulo do nome
        tit = nome.replace("_", " ").replace("1080p", "").strip()[:80] + " #shorts"
        return (canais_desc[0], tit, "#shorts #viral #ia",
                ["shorts", "viral", "ia"], f"fallback({type(e).__name__})")


def _item(id_, arquivo, tipo, cap, parte, titulo, descricao, tags, categoria,
          origem_meta, canal_forcado=None):
    return {
        "id": id_, "arquivo": str(arquivo), "tipo": tipo, "cap": cap, "parte": parte,
        "titulo": titulo, "descricao": descricao, "tags": tags,
        "_categoria": categoria, "_origem_meta": origem_meta,
        "_mb": round(_mb(Path(arquivo)), 1), "_canal_forcado": canal_forcado,
    }


# --------------------- DISTRIBUICAO + AGENDAMENTO ---------------------
def _slots_validos(dia0):
    """Descarta slots ja vencidos se dia0 for hoje (evita publish_at no passado)."""
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    if dia0 != hoje:
        return list(SLOTS_BRT)
    agora = datetime.now(BRT)
    validos = [s for s in SLOTS_BRT
               if datetime.strptime(f"{dia0} {s}", "%Y-%m-%d %H:%M").replace(tzinfo=BRT)
               > agora + timedelta(minutes=20)]
    if not validos:  # tudo passou: usa de hora em hora a partir de agora+30min
        base = (agora + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)
        validos = [(base + timedelta(hours=i)).strftime("%H:%M") for i in range(8)]
    return validos


def distribuir(itens, canais, dia0):
    """Distribui itens entre canais (balanceado) e agenda dia/hora respeitando quota."""
    canal_itens = {ch: [] for ch in canais}
    for it in itens:
        if it.get("_canal_forcado"):
            ch = it["_canal_forcado"]
            canal_itens.setdefault(ch, []).append(it)
        else:
            alvo = min(canais, key=lambda c: len(canal_itens[c]))
            canal_itens[alvo].append(it)

    fila_itens = []
    for ch, its in canal_itens.items():
        por_dia = {}
        for idx, it in enumerate(its):
            offset = idx // QUOTA_DIA
            dia = (datetime.strptime(dia0, "%Y-%m-%d") + timedelta(days=offset)).strftime("%Y-%m-%d")
            it["upload_dia"] = dia
            por_dia.setdefault(dia, []).append(it)
        for dia, grupo in por_dia.items():
            slots = _slots_validos(dia)
            for it, hhmm in zip(grupo, _pick_slots(len(grupo), slots)):
                it["canal"] = ch
                it["publish_at"] = _brt_to_utc_iso(dia, hhmm)
                it["publish_brt"] = f"{dia} {hhmm}"
                it["status"] = "pendente"
                fila_itens.append(it)
    fila_itens.sort(key=lambda it: (it["upload_dia"], it["publish_at"]))
    return fila_itens


def montar(categoria, itens, canais, saida_nome):
    dia0 = datetime.now(BRT).strftime("%Y-%m-%d")
    fila_itens = distribuir(itens, canais, dia0)
    postados_dir = str(POSTADOS_BASE / categoria)
    for it in fila_itens:
        it["postados_dir"] = postados_dir
    return {
        "obra": f"materiais/{categoria}",
        "categoria": categoria,
        "gerado_em": datetime.now(BRT).isoformat(),
        "quota_por_canal_dia": QUOTA_DIA,
        "canais": canais,
        "postados_dir": postados_dir,
        "total_itens": len(fila_itens),
        "itens": fila_itens,
    }


# --------------------- PREVIEW ---------------------
def preview(fila):
    cat = fila["categoria"]
    print(f"\n{'=' * 70}")
    print(f"CATEGORIA: {cat}  |  {fila['total_itens']} videos  |  canais: {', '.join(fila['canais'])}")
    print(f"postados_dir: {fila['postados_dir']}")
    print("=" * 70)
    if not fila["itens"]:
        print("  (nenhum video encontrado)")
        return
    dias = sorted({it["upload_dia"] for it in fila["itens"]})
    for dia in dias:
        do_dia = [it for it in fila["itens"] if it["upload_dia"] == dia]
        print(f"\n-- DIA {dia} ({len(do_dia)} uploads) --")
        for it in do_dia:
            hhmm = it["publish_brt"].split()[1]
            arq = Path(it["arquivo"]).name
            print(f"  {hhmm} [{it['canal']}]")
            print(f"       {it['titulo'][:66]}")
            print(f"       arq: {arq[:50]} ({it['_mb']}MB) meta:{it['_origem_meta']}")


def main():
    ap = argparse.ArgumentParser(description="Cola: materiais -> filas de postagem")
    ap.add_argument("--preview", action="store_true", help="so mostra, nao escreve fila")
    ap.add_argument("--cat", choices=["recap", "animes", "vo3", "historias", "todos"], default="todos")
    args = ap.parse_args()

    cats = ["recap", "animes", "vo3", "historias"] if args.cat == "todos" else [args.cat]
    filas = {}
    for cat in cats:
        if cat == "recap":
            itens = coletar_recap()
            filas[cat] = montar("recap", itens, CANAIS_MANGA, "fila_materiais_recap.json")
        elif cat == "animes":
            itens = coletar_animes()
            filas[cat] = montar("animes", itens, CANAIS_ANIME, "fila_materiais_animes.json")
        elif cat == "vo3":
            itens = coletar_vo3()
            # vo3 usa canal forcado por item (Gemini escolhe entre CANAIS_VO3)
            filas[cat] = montar("vo3", itens, CANAIS_VO3, "fila_materiais_vo3.json")
        elif cat == "historias":
            itens = coletar_historias()
            filas[cat] = montar("historias", itens, CANAIS_HISTORIAS, "fila_materiais_historias.json")

    for cat, fila in filas.items():
        preview(fila)

    if AVISOS:
        print(f"\n{'!' * 70}")
        print(f"AVISOS ({len(AVISOS)}) — docs faltando/errados/gerados por IA (REVISAR):")
        print("!" * 70)
        for a in AVISOS:
            print(f"  ⚠️  {a}")

    if args.preview:
        print(f"\n>>> PREVIEW apenas. Nenhuma fila escrita. Rode sem --preview pra gerar.")
        return

    FILAS_DIR.mkdir(parents=True, exist_ok=True)
    for cat, fila in filas.items():
        saida = FILAS_DIR / f"fila_materiais_{cat}.json"
        saida.write_text(json.dumps(fila, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] fila escrita: {saida}  ({fila['total_itens']} itens)")


if __name__ == "__main__":
    main()
