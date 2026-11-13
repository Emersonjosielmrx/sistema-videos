"""anime_voz_clonada.py — Shorts de parceiro (todos os nichos desde 21/10) narrados com a voz clonada dos narradores
parceiros e dos personagens aprovados.

20/10/2026: VOZ_CLONADA_VERSAO=2 (perfil de ritmo/tom/volume/EQ do narrador real, medido pelo clone2.py), base
francisca/kokoro/misto. 21/10: o narrador é escolhido pelo ENCAIXE com o nicho do vídeo (config\\narradores_nichos.json,
nota 0-3), balanceado pelo uso (todos têm chance) e, com views suficientes, pelos dados (_historico.jsonl + métricas).
Registro (.txt) de cada vídeo em D:\\hipercool-materiais\\videos_voz_clonada\\<narrador>\\; o vídeo é o da fila (animes recap\\shorts).
Falhou 2x seguidas no mesmo (narrador, base) = pula essa base por 24 h.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
PY_VOZES = RAIZ / "python" / "venv_vozes" / "Scripts" / "python.exe"
PASTA = RAIZ / "videos_voz_clonada"
ESTADO = PASTA / "_rodizio.json"
NICHOS = {"anime", "manhwa"}
# Dono 21/10 ("só abriu um na tela"): com a divisão por gênero quase nenhum Short era anime/manhwa e 21 de 21 saíram com
# a voz edge. Agora todo Short de parceiro (qualquer nicho) sai com o narrador da vez. False = volta a só anime/manhwa.
TODOS_OS_NICHOS = True
BASES = ["francisca", "kokoro", "misto"]


FORA = {"lula", "bolsonaro"}  # dono 20/10: "Lula/Bolsonaro fora até ele confirmar de novo" (político = risco de strike)
FORA |= {"narrador_do_canal_fala_serio", "kratos_ascension", "capitao_nascimento", "asuka_langley_evangelion",
         "lula_molusco", "braum_lol", "seu_sirigueijo_peter_griffin", "omelhormanhwa", "omen_valorant", "kay_o_valorant",
         "sett_lol"}  # dona 29/10: ouviu e não vale a pena; pasta no Drive (.pth fica pra não treinar de novo)


def _personagens():
    """Vozes baixadas aprovadas pelo dono (20/10): models\\rvc\\vozes\\<voz>\\personagem.json."""
    return sorted(p.parent.name for p in VOZES.glob("*/personagem.json")
                  if (p.parent / f"{p.parent.name}.pth").exists() and p.parent.name not in FORA)


def _bases_da(voz):
    try:
        return json.loads((VOZES / voz / "personagem.json").read_text(encoding="utf-8"))["bases"]
    except (OSError, ValueError, KeyError):
        return BASES


def _ordem():
    """Parceiros e personagens intercalados (dono 20/10: o narrador varia a cada vídeo)."""
    texto = (RAIZ / "bin" / "voz_clonada.py").read_text(encoding="utf-8")
    bloco = texto[texto.find("PARCEIROS = ["):texto.find("BASES = [")]
    parceiros = [v for v in re.findall(r'\("(\w+)", "@', bloco) if (VOZES / v / f"{v}.pth").exists() and v not in FORA]
    personagens = _personagens()
    out = []
    for i in range(max(len(parceiros), len(personagens))):
        out += [x[i] for x in (parceiros, personagens) if i < len(x)]
    return out


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"indice": 0, "rodada": 1, "feitos": {}, "falhas": {}}


def _gravar(est):
    PASTA.mkdir(parents=True, exist_ok=True)
    # 22/10: tmp + os.replace — disco cheio no meio do write não zera o estado (aconteceu com o _rodizio em 20/10)
    tmp = Path(str(ESTADO) + ".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, ESTADO)


# Dono 21/10: "não seja só sorteando ou por vez, e sim qual voz encaixa melhor para cada tipo de vídeo, e claro tentando
# balancear as escolhas pra que todos tenham chance de serem usados; a partir dos dados vamos decidir os melhores".
# 12/11: o caminho era FIXO em D:\recapd-ambientes\producao\config — no PC2/PC3 o config fica em
# C:\recapd-e-animes\config (a junção D: de lá não tem config/): a tabela "não existia", toda voz virava nota 1 e saía
# a menos usada (Pica-Pau, Drezin, Mike, ei_nerd em canal de NEGÓCIOS/SAÚDE). Agora: o config/ ao lado deste bin/
# (vale nas 3 máquinas); o caminho antigo fica de reserva.
_CFG_LOCAL = Path(__file__).resolve().parent.parent / "config"


def _cfg_arq(nome):
    local = _CFG_LOCAL / nome
    return local if local.exists() else Path(r"D:\recapd-ambientes\producao\config") / nome


ENCAIXE = _cfg_arq("narradores_nichos.json")  # nota 0-3 voz x nicho (editável)
HISTORICO = PASTA / "_historico.jsonl"  # 1 linha por Short com voz clonada: narrador, nicho, canal, base, config, pasta
PARCEIRO_CFG = _cfg_arq("parceiro.json")
METRICAS = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")
FALHA_VALE_H = 24  # falha de uma voz para de valer depois disso (antes só zerava na virada da rodada)
ULTIMA_ESCOLHA = {}  # por que a última voz foi escolhida (o anime_auto põe no log)
ULTIMA_CORTADAS = []  # 12/11: vozes cortadas pelo ranking geral na última escolha


def nicho_do_video(tipo=None, canal=None):
    """Nicho do Short: o tipo da fonte (PARCEIRO_TIPO); "fatos" vira o nicho do canal de destino (curiosidades,
    historia_mitologia, animais...)."""
    tipo = (tipo or "").strip() or None
    if tipo == "fatos":
        try:
            c = json.loads(PARCEIRO_CFG.read_text(encoding="utf-8"))
            d = next((x for x in c.get("pt", []) if canal and canal in (x.get("canal"), x.get("nome"))), {})
            for n in (d.get("nichos") or [d.get("nicho")]):
                if n and n != "fatos":
                    return n
        except (OSError, ValueError):
            pass
        return "curiosidades"
    return tipo


def _historico():
    out = []
    try:
        linhas = HISTORICO.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for l in linhas:
        try:
            out.append(json.loads(l))
        except ValueError:
            continue
    return out


def _video_id(pasta):
    try:
        pj = json.loads((Path(pasta) / "postar.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    m = re.search(r"(?:youtu\.be/|shorts/|v=)([\w-]{11})", str(pj.get("posted_url") or ""))
    return m.group(1) if m else None


def completar_ids():
    """Grava no _historico.jsonl o video_id que ainda falta, ENQUANTO a pasta existe (fa0246, 22/10: o backup
    manda a pasta pro Drive 3 dias depois de postar e o elo voz→views se perdia). Reescrita atômica, 1x barata."""
    hist = _historico()
    mudou = False
    for h in hist:
        if not h.get("video_id") and h.get("pasta"):
            vid = _video_id(h["pasta"])
            if vid:
                h["video_id"] = vid
                mudou = True
    if mudou:
        tmp = Path(str(HISTORICO) + ".tmp")
        tmp.write_text("".join(json.dumps(h, ensure_ascii=False) + "\n" for h in hist), encoding="utf-8")
        os.replace(tmp, HISTORICO)
    return hist


def _views_48h():
    """{video_id: views} das medições públicas de 48 h (telegram_estado.medidas_48h) — sem navegador."""
    try:
        d = json.loads(Path(r"D:\postador-de-videos\config\telegram_estado.json").read_text(encoding="utf-8"))
        return {k: int(v.get("views", 0)) for k, v in (d.get("medidas_48h") or {}).items() if isinstance(v, dict)}
    except (OSError, ValueError):
        return {}


def _bonus_views(nicho, hist):
    """Os dados pesam: +1 pra quem tem >= 3 vídeos no nicho com views bem acima da mediana do nicho (>= 1,5x), -1 bem
    abaixo (<= 0,5x). Só com >= 6 vídeos medidos no nicho (antes disso é só o encaixe + balanceamento).
    22/10 (funil do dono): além do Studio (metricas_studio, ~6 leituras/dia), entram as medições PÚBLICAS de 48 h
    do telegram_estado — muito mais vídeos medidos, o aperto pros narradores virais acontece mais cedo."""
    import statistics
    try:
        met = json.loads(METRICAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        met = {}
    pub = _views_48h()
    por = {}
    for h in hist:
        if h.get("nicho") != nicho or not (h.get("pasta") or h.get("video_id")):
            continue
        vid = h.get("video_id") or _video_id(h.get("pasta") or "") or ""
        m = met.get(vid)
        views = m.get("views") if isinstance(m, dict) else None
        if views is None:
            views = pub.get(vid)
        if views is not None:
            por.setdefault(h["voz"], []).append(int(views))
    todos = [x for vs in por.values() for x in vs]
    if len(todos) < 6:
        return {}
    med = statistics.median(todos) or 1
    return {v: (1 if statistics.median(vs) / med >= 1.5 else -1 if statistics.median(vs) / med <= 0.5 else 0)
            for v, vs in por.items() if len(vs) >= 3}


def ranking_geral(hist=None):
    """02/11 (dona: "ranking de quem se sai melhor e pior em views"): o _bonus_views por nicho quase nunca pesava — o
    rodízio espalha ~20 vozes por nicho e nenhuma chegava a 3 vídeos no mesmo nicho. Aqui junta TODOS os nichos: cada
    vídeo vira views / mediana do nicho dele (nicho com >= 3 medidos), e a voz recebe a média de log2 dessa razão,
    puxada pra 0 com 3 vídeos "neutros" (pouco dado = nota perto de 0). Voz com >= 2 medidos: {voz: (nota -1,5..+1,5, n)}."""
    import math
    import statistics
    hist = _historico() if hist is None else hist
    try:
        met = json.loads(METRICAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        met = {}
    pub = _views_48h()
    por_nicho = {}
    for h in hist:
        vid = h.get("video_id")
        if not vid or not h.get("voz"):
            continue
        m = met.get(vid)
        views = m.get("views") if isinstance(m, dict) else None
        if views is None:
            views = pub.get(vid)
        if views is not None:
            por_nicho.setdefault(h.get("nicho") or "?", []).append((h["voz"], int(views)))
    razoes = {}
    for vs in por_nicho.values():
        if len(vs) < 3:
            continue
        med = statistics.median(v for _, v in vs) or 1
        for voz, v in vs:
            # cada vídeo vale no máximo 4x acima/abaixo da mediana (±2): 1 viral sozinho não leva a voz ao topo
            razoes.setdefault(voz, []).append(max(-2.0, min(2.0, math.log2(max(v, 1) / med))))
    return {voz: (round(max(-1.5, min(1.5, sum(rs) / (len(rs) + 3))), 3), len(rs))
            for voz, rs in razoes.items() if len(rs) >= 2}


def _bonus_placar(nicho):
    """23/10 (dona: "quem se sair bem aparece mais"): o placar de 48 h dos narradores (notificar_telegram registra
    "narradores" por mídia, vitória = views acima da mediana do CANAL) passa a pesar na escolha — antes só era gravado.
    Voz com >= 3 medidas: (taxa da voz - taxa do grupo) x 2, entre -1 e +1. Sem dados = {} (nada muda)."""
    try:
        import placar_titulos
        t = {}
        for g in {nicho, os.environ.get("PARCEIRO_TIPO")} - {None}:
            for v, (n, w) in placar_titulos.taxas("narradores", g).items():
                a = t.setdefault(v, [0, 0])
                a[0] += n
                a[1] += w
    except Exception:  # noqa: BLE001 — sem o placar (PC2) a escolha segue como antes
        return {}
    tot_n, tot_w = sum(n for n, _ in t.values()), sum(w for _, w in t.values())
    if tot_n < 6:
        return {}
    base = (tot_w + 1) / (tot_n + 2)
    return {v: max(-1.0, min(1.0, 2 * ((w + 1) / (n + 2) - base))) for v, (n, w) in t.items() if n >= 3}


def _falhou(est, k):
    """2 falhas seguidas no mesmo (narrador, base) pula essa combinação — por FALHA_VALE_H horas."""
    if est.get("falhas", {}).get(k, 0) < 2:
        return False
    quando = (est.get("falhas_em") or {}).get(k)
    return not quando or (datetime.now() - datetime.fromisoformat(quando)).total_seconds() < FALHA_VALE_H * 3600


def genero_da_voz(voz):
    """'f' / 'm' pelo tom medido da voz (personagem.json f0_tipo/f0; >= 165 Hz = voz feminina). Sem medida = None."""
    try:
        d = json.loads((VOZES / voz / "personagem.json").read_text(encoding="utf-8"))
        f0 = d.get("f0_tipo") or d.get("f0")
        return None if not f0 else ("f" if float(f0) >= 165 else "m")
    except (OSError, ValueError, TypeError):
        return None


def proxima(nicho=None, genero=None):
    """(narrador, base) do próximo Short com voz clonada, ou None. Entre os narradores que ENCAIXAM no nicho (nota >= 2
    em narradores_nichos.json; < 3 assim = nota >= 1) vai o de maior nota menos o uso: cada vídeo no nicho tira 0,6,
    então quem encaixa mais sai mais vezes e os outros também ganham vez. Base = a menos usada desse narrador."""
    from collections import Counter
    if not PY_VOZES.exists():
        return None
    ordem = _ordem()
    if not ordem:
        return None
    est = _ler()
    rodada = est.get("rodada", 1)
    try:
        tabela = json.loads(ENCAIXE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        tabela = {}
    hist = completar_ids()  # 22/10: preenche o video_id que falta ANTES de a pasta ir pro Drive (elo voz→views)
    usos_n = Counter(h["voz"] for h in hist if nicho and h.get("nicho") == nicho)
    usos = Counter(h["voz"] for h in hist)
    usos_b = Counter((h["voz"], h.get("base")) for h in hist)
    for k in est.get("feitos", {}):  # vídeos de antes do histórico (20-21/10) contam no uso geral e da base
        p = k.split(":")
        usos[p[0]] += 1
        if len(p) > 1:
            usos_b[(p[0], p[1])] += 1
    bonus = _bonus_views(nicho, hist) if nicho else {}
    for v, b in _bonus_placar(nicho).items():  # placar de 48 h por canal (23/10) soma ao das views
        bonus[v] = round(bonus.get(v, 0) + b, 3)
    rank = {v: n for v, (n, _) in ranking_geral(hist).items()}  # 02/11: ranking de views de todos os nichos
    for v, b in rank.items():
        bonus[v] = round(max(-2.0, min(2.0, bonus.get(v, 0) + b)), 3)  # teto: o encaixe (0-3) continua mandando
    cands = []
    for i, v in enumerate(ordem):
        if (tabela.get(v) or {}).get("fora"):  # dona: "não é bom dublador" — nunca narra
            continue
        if genero and genero_da_voz(v) != genero:  # 01/11 dona: dorama em 1ª pessoa de mulher = narradora mulher
            continue
        bases = [b for b in _bases_da(v) if not _falhou(est, f"{v}:{b}:r{rodada}")]
        if bases:
            n = tabela.get(v) or {}
            cands.append({"voz": v, "bases": bases, "i": i,
                          "fit": int(n.get(nicho, n.get("geral", 1)) if nicho else n.get("geral", 1))})
    if not cands:  # todo mundo com falha recente: zera e tenta de novo (era o que a virada da rodada fazia)
        est["falhas"], est["falhas_em"] = {}, {}
        _gravar(est)
        return ordem[0], _bases_da(ordem[0])[0]
    pool = [c for c in cands if c["fit"] >= 2]
    if len(pool) < 3:
        pool = [c for c in cands if c["fit"] >= 1] or cands
    # 12/11 dona ("os narradores que foram mal em todos: removidos ou com menos vídeos"): voz com ranking geral
    # <= VOZ_CORTE_NOTA (-0,5 = metade da mediana do nicho) em >= VOZ_CORTE_MIN (6) vídeos medidos sai do rodízio
    # sozinha — sem mexer na tabela (volta se o ranking subir). Nicho que ficaria com < 3 vozes mantém todas.
    # VOZ_CORTE_RANKING=0 desliga.
    if os.environ.get("VOZ_CORTE_RANKING", "1") != "0":
        rk_full = ranking_geral(hist)
        corte = float(os.environ.get("VOZ_CORTE_NOTA", "-0.5"))
        minimo = int(os.environ.get("VOZ_CORTE_MIN", "6"))
        bons = [c for c in pool if not (rk_full.get(c["voz"], (0, 0))[0] <= corte
                                        and rk_full.get(c["voz"], (0, 0))[1] >= minimo)]
        if len(bons) >= 3 and len(bons) < len(pool):
            ULTIMA_CORTADAS[:] = sorted({c["voz"] for c in pool} - {c["voz"] for c in bons})
            pool = bons

    def nota(c):
        # 02/11: quem vai bem no ranking perde menos por uso (aparece mais); quem vai mal perde mais (aparece menos).
        # Voz sem dados (< 2 medidos) fica no 0,6 normal = continua sendo testada.
        r = rank.get(c["voz"], 0)
        pena = 0.6 / (1 + r) if r > 0 else 0.6 * (1 - r)
        return c["fit"] + bonus.get(c["voz"], 0) - pena * usos_n[c["voz"]] - 0.05 * usos[c["voz"]]
    c = max(pool, key=lambda c: (round(nota(c), 3), -usos[c["voz"]], -c["i"]))
    base = min(c["bases"], key=lambda b: (usos_b[(c["voz"], b)], BASES.index(b) if b in BASES else 9))
    ULTIMA_ESCOLHA.clear()
    ULTIMA_ESCOLHA.update(nicho=nicho or "?", encaixe=c["fit"], usos_no_nicho=usos_n[c["voz"]], usos=usos[c["voz"]],
                          bonus_views=bonus.get(c["voz"], 0), ranking=rank.get(c["voz"]), candidatos=len(pool))
    return c["voz"], base


CONFIGS = {  # dono 20/10: produzir alternando e ele escolhe ouvindo (amostras_voz\semelhanca_20261020\CONFIGURACOES_1_E_2.md)
    "1": "Config 1 (produção): curva de locutor por frase — index_rate 0,30-0,85 (~0,38 nas normais), protect 0,22-0,41, "
         "volume_envelope 0,6-0,9",
    "2": "Config 2 (timbre forte, como as amostras aprovadas): index_rate 0,80, protect 0,33, volume_envelope 0,80 em "
         "todas as frases",
}
BASE_NOME = {"francisca": "edge Francisca", "kokoro": "Kokoro", "misto": "misto (Kokoro na abertura e nos impactos, "
             "edge Francisca no resto)"}


def config_da_vez():
    """Alterna 1, 2, 1, 2... entre os vídeos com voz clonada (vale o que já saiu, não a tentativa)."""
    return _ler().get("proxima_config", "1")


def registrar(voz, base, video=None, nome="", config="1", resumo=None, nicho=None, canal=None):
    """video = mp4 publicado (postar.json pronto): .txt na pasta do narrador com o que foi usado (base, configuração e
    cada frase) + 1 linha no _historico.jsonl (dados pra escolher os melhores). Dono 21/10: o vídeo não é mais copiado
    pra cá ("por que não abre só o vídeo feito em vez de copiar"): o registro aponta pro da fila. Sem video = falha."""
    est = _ler()
    rodada = est.get("rodada", 1)
    k = f"{voz}:{base}:r{rodada}"
    if video and Path(video).exists():
        txt = PASTA / voz / f"v2_r{rodada}_{base}_config{config}_{datetime.now():%d-%m_%H%M}_{nome or Path(video).parent.name}.txt"
        txt.parent.mkdir(parents=True, exist_ok=True)
        chave, n = k, 1  # a escolha por encaixe repete narrador+base: não sobrescreve o vídeo anterior no feitos
        while chave in est["feitos"]:
            n += 1
            chave = f"{k}.{n}"
        est["feitos"][chave] = {"video": str(video), "txt": str(txt), "postagem": str(Path(video).parent),
                                "config": config, "quando": f"{datetime.now():%d/%m %H:%M}", "nicho": nicho}
        est["proxima_config"] = "2" if config == "1" else "1"
        est.get("falhas", {}).pop(k, None)
        _descrever(txt, voz, base, config, video, resumo)
        try:
            with open(HISTORICO, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"quando": datetime.now().isoformat(timespec="seconds"), "voz": voz, "base": base,
                                     "config": config, "nicho": nicho, "canal": canal, "pasta": str(Path(video).parent),
                                     "video": str(video), "txt": str(txt), "escolha": dict(ULTIMA_ESCOLHA)},
                                    ensure_ascii=False) + "\n")
        except OSError:
            pass
    else:
        est.setdefault("falhas", {})[k] = est.get("falhas", {}).get(k, 0) + 1
        est.setdefault("falhas_em", {})[k] = datetime.now().isoformat(timespec="seconds")
    _gravar(est)


def _descrever(txt, voz, base, config, video, resumo):
    try:
        pj = json.loads((Path(video).parent / "postar.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pj = {}
    try:
        frases = json.loads(Path(resumo).read_text(encoding="utf-8")) if resumo else []
    except (OSError, ValueError):
        frases = []
    linhas = [f"Narrador (voz clonada): {voz}", f"Voz base: {BASE_NOME.get(base, base)}", CONFIGS.get(config, config),
              f"Canal: {pj.get('canal_postado') or pj.get('canal') or '?'}  |  título: {pj.get('titulo') or '?'}",
              f"Vídeo: {video}", ""]
    for f in frases:
        linhas.append(f"frase {f.get('i')}: {f.get('base')} {f.get('rate')} | clima {f.get('clima', 'normal')} | "
                      f"tom {f.get('tom_extra', 0):+d} | index {f.get('index_rate')} | protect {f.get('protect')} | "
                      f"vol {f.get('volume_envelope')} | {f.get('texto', '')[:90]}")
    txt.write_text("\n".join(linhas) + "\n", encoding="utf-8")
