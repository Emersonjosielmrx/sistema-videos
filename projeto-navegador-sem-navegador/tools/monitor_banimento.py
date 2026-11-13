# -*- coding: utf-8 -*-
r"""tools/monitor_banimento.py — monitor de BANIMENTO por conta e por máquina + RAMPA automática dos tetos (D33).

Dona 29/10/2026 19:40: "pode subir mas adicione uma espécie de monitor pra ver se quanto você colocou a mais leva a
banimento e se não sobe mais ainda até chegarmos ao máximo possível, e principalmente de imagens que precisamos muito".

1) MONITOR — lê os logs que já existem (não abre Chrome, não faz pedido a nenhum site) e conta, por conta e máquina,
   os sinais de bloqueio das últimas 24 h / 7 d:
     instagram  feedback_required, checkpoint, challenge, 400 no upload, deslogado/NAO LOGADO/login caiu,
                conta restrita (erro 1357031, "user is inactive", /accounts/suspended)
     flow       UNUSUAL_ACTIVITY, age-restricted, RECAPTCHA_BLOQUEIO, recusa por política, Flow pediu login,
                SESSAO_EXPIRADA / "login caiu ou conta bloqueada no Flow", BLOQUEIO DETECTADO (cooldowns em massa)
     youtube/tiktok/fotos  o que o saude.py já mede (morto) + "suspensa"
   Fontes: postador logs\instagram_auto.log e maquina_remota.log; veo\beta\logs\cron_gerar_llm.log e foto_na_hora.jsonl;
   nsn logs\flow_gerar.jsonl; relatorios\saida\saude.json.
   Grava relatorios\saida\banimento.json (o painel lê) e logs\banimento.jsonl (1 linha por sinal novo e por degrau).
   Telegram (video-fila\avisos.py) só quando aparece sinal NOVO numa conta; forte/restrita sai na hora.

2) RAMPA — mexe em D:\postador-de-videos\config\tetos.json (só nas chaves "contas" e "global"):
     sem sinal na conta durante espera_h (e conta "viva" na saúde)  → sobe 1 degrau (nunca mais de 1 por rodada)
     sinal FORTE (feedback_required, checkpoint, challenge, 400, UNUSUAL, age-restricted, RECAPTCHA_BLOQUEIO)
                                                                   → volta 1 degrau e fica "no_limite" (não sobe mais sozinha)
     sinal de LOGIN (deslogado, SESSAO_EXPIRADA) ou recusa de política → "segurando" (nem sobe nem desce nesta janela)
     conta restrita/suspensa                                       → "fora" da rampa (teto volta à base)
   Ordem: imagens (espera 24 h, degraus maiores) → Reels (+1/dia) → Veo (global, por último). Cada conta continua
   postando pela mesma máquina de sempre (o monitor não mexe em ORDEM_NAVEGADOR nem em cookies).

    python tools\monitor_banimento.py            # rodada (tarefa NSN_Banimento, 1x por hora, pythonw)
    python tools\monitor_banimento.py --seco     # só mostra: não grava, não avisa, não mexe nos tetos
    python tools\monitor_banimento.py --mostrar  # imprime o último banimento.json
"""
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: E402,F401 — nenhum processo filho abre janela (tarefa agendada)
except ImportError:
    pass

POSTADOR = Path(r"D:\postador-de-videos")
VEO_LOGS = Path(r"D:\veo\beta\logs")
SAIDA = ROOT / "relatorios" / "saida" / "banimento.json"
LOG = ROOT / "logs" / "banimento.jsonl"
SAUDE = ROOT / "relatorios" / "saida" / "saude.json"
TETOS = POSTADOR / "config" / "tetos.json"
REUSO = POSTADOR / "config" / "reuso_plataformas.json"
GERACOES = Path(r"D:\flow-imagens\logs\geracoes.jsonl")
JANELA_H = 24
HISTORICO_D = 7
MAQUINAS = ("x200ma", "acer", "pc2", "desktop", "pc1")

# (regex, tipo, classe) — classe: restrita > forte > login > fraca
SINAIS = {
    "instagram": [
        (r"1357031|user is inactive|/accounts/suspended|conta restrita|suspens", "conta_restrita", "restrita"),
        (r"feedback_required", "feedback_required", "forte"),
        (r"checkpoint", "checkpoint", "forte"),
        (r"challenge", "challenge", "forte"),
        (r"(?:envio d[oa] (?:v[ií]deo|capa|foto) falhou|upload[^:]*falhou|recusad[oa]): 400\b|\b400 \{", "upload_400", "forte"),
        (r"NAO LOGADO|not[_-]logged[_-]in|deslogad|login do Instagram vencido|cookie vencido|n[aã]o reconheceu o login"
         r"|login caiu", "deslogado", "login"),
    ],
    "flow": [
        (r"UNUSUAL_ACTIVITY", "unusual_activity", "forte"),
        (r"age[-_ ]restricted", "age_restricted", "forte"),
        (r"RECAPTCHA_BLOQUEIO", "recaptcha_bloqueio", "forte"),
        (r"BLOQUEIO DETECTADO", "bloqueio_global", "forte"),
        (r"DireitosAutorais|recusou o pedido por pol[ií]tica|violate our policies|pode violar", "recusa_politica", "fraca"),
        (r"SESSAO_EXPIRADA|SessaoExpirada|Flow pediu login|login caiu ou conta bloqueada no Flow|cookies vencidos"
         r"|n[aã]o reconheceu o login", "sessao_expirada", "login"),
    ],
}
PESO = {"restrita": 3, "forte": 2, "login": 1, "fraca": 0}
# legenda fixa → conta (linhas de erro sem o nome da conta; o 1º caso: o MS Energy posta "Ms energy solar..." em paralelo)
LEGENDA_CONTA = (("caption: ms energy solar", "msenergysolar.pa"),)


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _log(reg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


def _cauda(p, bytes_max=1_500_000):
    try:
        with open(p, "rb") as f:
            f.seek(0, 2)
            tam = f.tell()
            f.seek(max(0, tam - bytes_max))
            txt = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    linhas = txt.splitlines()
    return linhas[1:] if tam > bytes_max else linhas


def _iso(dt):
    return dt.isoformat(timespec="seconds")


def _sinal(servico, conta, em, maquina, fonte, trecho, padroes=None):
    """Classifica o trecho; devolve o registro do sinal ou None (nenhum padrão bateu)."""
    for rx, tipo, classe in padroes or SINAIS[servico]:
        if re.search(rx, trecho, re.I):
            tr = " ".join(trecho.split())[:220]
            ident = hashlib.sha1(f"{fonte}|{em[:16]}|{conta}|{tipo}".encode("utf-8")).hexdigest()[:14]
            return {"id": ident, "em": em, "servico": servico, "conta": (conta or "?").lower(), "tipo": tipo,
                    "classe": classe, "maquina": maquina or "pc1", "fonte": fonte, "trecho": tr}
    return None


# ───────── fontes ─────────
def _contas_instagram():
    return set((_ler(REUSO, {}).get("instagram", {}).get("contas") or {}).keys())


def f_instagram_auto(desde):
    """instagram_auto.log: linhas "[HH:MM:SS] ..." SEM data — a data é inferida de trás pra frente a partir do mtime
    (hora menor que a da linha seguinte = virou o dia). Conta = último "[conta]" ou "  conta: "; máquina = último
    "HTTP no X"/"pelo Chrome do X" do mesmo item ("falhou no X — tento na próxima" = a próxima, no fim o PC1)."""
    arq = POSTADOR / "logs" / "instagram_auto.log"
    linhas = _cauda(arq)
    if not linhas:
        return []
    dia = datetime.fromtimestamp(arq.stat().st_mtime).date()
    datadas, prox = [], None
    for l in reversed(linhas):
        m = re.match(r"\[(\d\d):(\d\d):(\d\d)\]", l)
        if not m:
            continue
        t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
        if prox is not None and t > prox:
            dia -= timedelta(days=1)
        prox = t
        datadas.append((datetime.combine(dia, datetime.min.time()) + timedelta(seconds=t), l[11:]))
        if dia < desde.date():
            break
    datadas.reverse()
    conhecidas = _contas_instagram()
    # 29/10: rodadas diferentes (Instagram Auto e MSEnergy_PostarInsta) escrevem INTERCALADAS no mesmo log. Por isso
    # não vale "o último [conta]": cada "[conta] vídeo" entra numa fila de pendentes; linha com "conta: " é dela;
    # linha SEM nome (ERRO:/OK) é do item pendente mais antigo, que sai da fila. Máquina guardada por conta.
    out, pend, maq, proxima = [], [], {}, {}
    for em, l in datadas:
        if em < desde:
            continue
        m = re.match(r"\s*\[([^\]\s]+)\] ", l)
        if m and m[1] in conhecidas:
            if m[1] in pend:
                pend.remove(m[1])
            pend.append(m[1])
            maq[m[1]], proxima[m[1]] = None, False
            continue
        m = re.match(r"\s*([^\s:]+): ", l)
        conta = m[1] if m and m[1] in conhecidas else (pend[0] if pend else None)
        mc = next((c for pista, c in LEGENDA_CONTA if pista in l.lower()), None)
        if mc:
            conta = mc  # a rodada do MS Energy nem sempre escreve "[msenergysolar.pa]" antes do erro
        m = re.search(r"HTTP no (\w+)|pelo Chrome do (\w+)|falhou no (\w+)", l)
        if m and conta:
            maq[conta] = (m[1] or m[2] or m[3]).lower()
            proxima[conta] = bool(m[3])
        s = _sinal("instagram", conta, _iso(em), ("pc1" if proxima.get(conta) else maq.get(conta)),
                   "instagram_auto.log", l)
        if s:
            out.append(s)
        if conta in pend and re.match(r"\s*(OK |ERRO:|.*pulad)", l):
            pend.remove(conta)
    return out


def _data_mr(txt, agora):
    m = re.match(r"\[(\d\d)/(\d\d) (\d\d):(\d\d):(\d\d)\]", txt)
    if not m:
        return None
    ano = agora.year - (1 if int(m[2]) > agora.month else 0)
    try:
        return datetime(ano, int(m[2]), int(m[1]), int(m[3]), int(m[4]), int(m[5]))
    except ValueError:
        return None


def f_maquina_remota(desde):
    """maquina_remota.log: "[dd/mm HH:MM:SS] maq: Flow por HTTP ... (conta): ..." e "Reel por HTTP (conta) -> ...". """
    agora = datetime.now()
    out = []
    for l in _cauda(POSTADOR / "logs" / "maquina_remota.log"):
        em = _data_mr(l, agora)
        if not em or em < desde:
            continue
        m = re.match(r"\[[^\]]+\] (\w+): (.*)", l)
        if not m:
            continue
        maq, resto = m[1].lower(), m[2]
        mc = re.search(r"\(([^()\s]+)\)", resto)
        conta = (mc[1] if mc else "?").lower()
        servico = "flow" if "Flow" in resto else ("instagram" if "Reel" in resto or "ig_" in resto else None)
        if not servico:
            continue
        s = _sinal(servico, conta, _iso(em), maq, "maquina_remota.log", resto)
        if s:
            out.append(s)
    return out


def f_cron_veo(desde):
    """cron_gerar_llm.log (Veo no Flow): "[AAAA-MM-DD HH:MM:SS] [sessao] NOME fora do rodizio ... (login caiu ou conta
    bloqueada no Flow)", SESSAO_EXPIRADA, BLOQUEIO DETECTADO (global), UNUSUAL/recusas (conta = última [sessao] citada)."""
    out, conta = [], "?"
    for l in _cauda(VEO_LOGS / "cron_gerar_llm.log"):
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] (.*)", l)
        if not m:
            continue
        em = datetime.strptime(m[1], "%Y-%m-%d %H:%M:%S")
        if em < desde:
            continue
        resto = m[2]
        ms = re.match(r"\[sessao\] ([A-Za-z0-9_.]+)\b", resto)
        if ms and ms[1] not in ("fora", "em", "falhou"):
            conta = ms[1].lower()
        if "SESSAO_EXPIRADA" in resto and "fora do rodizio" not in resto:
            continue  # a linha seguinte ("fora do rodizio") diz a conta: sinal contado lá
        s = _sinal("flow", "*" if "BLOQUEIO DETECTADO" in resto else conta, _iso(em), "pc1", "cron_gerar_llm.log", resto)
        if s:
            out.append(s)
    return out


def f_foto_na_hora(desde):
    """foto_na_hora.jsonl: erro "nenhuma conta gerou a imagem: A: SessaoExpiradaError: ... | B: DireitosAutorais..."."""
    out = []
    for l in _cauda(VEO_LOGS / "foto_na_hora.jsonl", 600_000):
        if not l.startswith("{") or '"erro"' not in l:
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        em = str(r.get("em", ""))
        if not em or em < _iso(desde).replace("T", " "):
            continue
        for parte in str(r.get("erro", "")).split("imagem:")[-1].split(" | "):
            mp = re.match(r"\s*([A-Za-z0-9_.]+): (.*)", parte)
            if not mp:
                continue
            s = _sinal("flow", mp[1], em.replace(" ", "T")[:19], "?", "foto_na_hora.jsonl", mp[2])
            if s:
                out.append(s)
    return out


def f_flow_gerar(desde):
    """flow_gerar.jsonl (nsn, PC1): campo "recusa" preenchido = o Flow recusou o pedido por HTTP."""
    out = []
    for l in _cauda(ROOT / "logs" / "flow_gerar.jsonl", 600_000):
        if not l.startswith("{"):
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        em = str(r.get("quando", "")).replace(" ", "T")[:19]
        if not em or em < _iso(desde) or not r.get("recusa"):
            continue
        s = _sinal("flow", r.get("conta"), em, "pc1", "flow_gerar.jsonl", str(r["recusa"]))
        if s:
            out.append(s)
    return out


def f_saude(desde):
    """saude.json: conta morta (vivo=false) = sinal de login desde "desde"; obs com "suspens" = restrita.
    Conta "x@maquina" = o cookie daquela máquina."""
    est = _ler(SAUDE, {})
    out = []
    for servico, contas in est.items():
        if servico.startswith("_"):
            continue
        for conta, r in contas.items():
            if r.get("vivo") is not False:
                continue
            em = (r.get("desde") or r.get("em") or "")[:19]
            if not em or em < _iso(desde):
                continue
            nome, _, maq = conta.partition("@")
            obs = r.get("obs") or "morto"
            if re.search(r"SSLError|ConnectionError|ConnectTimeout|ReadTimeout|Max retries|timed out|Timeout", obs):
                continue  # 29/10: queda de rede/proxy não é sinal da conta (YouTube SSLError às 22:16 virou aviso falso)
            classe = "restrita" if re.search(r"suspens|restrit|inactive", obs, re.I) else "login"
            out.append({"id": hashlib.sha1(f"saude|{em}|{servico}|{conta}".encode()).hexdigest()[:14], "em": em,
                        "servico": servico if servico in ("instagram", "flow") else servico, "conta": nome.lower(),
                        "tipo": "conta_restrita" if classe == "restrita" else "saude_morto", "classe": classe,
                        "maquina": (maq or r.get("maquina") or "pc1").lower(), "fonte": "saude.json",
                        "trecho": obs[:220]})
    return out


FONTES = (f_instagram_auto, f_maquina_remota, f_cron_veo, f_foto_na_hora, f_flow_gerar, f_saude)


def coletar(dias=HISTORICO_D):
    desde = datetime.now() - timedelta(days=dias)
    vistos, out = set(), []
    for fn in FONTES:
        try:
            for s in fn(desde):
                if s["id"] in vistos:
                    continue
                vistos.add(s["id"])
                out.append(s)
        except Exception as e:  # noqa: BLE001 — uma fonte quebrada não para o monitor
            print(f"fonte {fn.__name__}: {type(e).__name__}: {str(e)[:120]}", flush=True)
    out.sort(key=lambda s: s["em"])
    return out


# ───────── saúde (conta "viva"?) ─────────
def _viva(servico, conta):
    """True/False pela última saúde (qualquer máquina viva = viva); None = a saúde não testa essa conta."""
    est = _ler(SAUDE, {})
    nome = conta.lower()
    cand = []
    for sv in ((servico,) if servico != "imagens" else ("flow",)):
        for k, r in (est.get(sv) or {}).items():
            if k.lower() == nome or k.lower().startswith(nome + "@"):
                cand.append(r.get("vivo"))
    if not cand:
        return None
    return any(v for v in cand) if any(v is not None for v in cand) else None


# ───────── rampa ─────────
def _contas_imagens(sinais):
    """Contas que geraram imagem nos últimos 7 dias (geracoes.jsonl) + as que deram sinal no Flow."""
    out = set()
    lim = (date.today() - timedelta(days=HISTORICO_D)).isoformat()
    for l in _cauda(GERACOES, 800_000):
        if not l.startswith("{"):
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if str(r.get("quando", ""))[:10] >= lim and r.get("conta"):
            out.add(str(r["conta"]).lower())
    out |= {s["conta"] for s in sinais if s["servico"] == "flow" and s["conta"] not in ("?", "*")}
    return out


def _janela(sinais, servico, conta, horas):
    lim = _iso(datetime.now() - timedelta(hours=horas))
    return [s for s in sinais if s["servico"] == servico and s["conta"] == conta and s["em"] >= lim]


def _pior(lista):
    return max((s["classe"] for s in lista), key=lambda c: PESO[c], default=None)


def _nova_linha(base, agora):
    return {"base": base, "nivel": 0, "teto": base, "estado": "subindo", "desde": agora, "ultimo_degrau": agora,
            "ultimo_sinal": None, "historico": []}


def _aplicar(linha, sv_cfg, classe, viva, agora, espera_h, chave="teto", sub=None):
    """Regra da rampa numa linha. Devolve texto do evento ou None. sub = config aninhada (veo.teto_dia...)."""
    cfg = sub or sv_cfg
    degrau, pmax = cfg.get("degrau", 1), cfg.get("patamar_max", linha["base"])
    estado = linha.get("estado", "subindo")
    ev = None
    if classe == "restrita":
        if estado != "fora":
            linha.update(nivel=0, estado="fora")
            ev = "conta restrita/suspensa: FORA da rampa (teto volta à base)"
    elif classe == "forte":
        if estado not in ("no_limite", "fora"):
            linha["nivel"] = max(0, linha["nivel"] - 1)
            linha["estado"] = "no_limite"
            ev = "sinal FORTE de bloqueio: volta 1 degrau e fica NO LIMITE (não sobe mais sozinha)"
    elif classe in ("login", "fraca"):
        if estado == "subindo":
            linha["estado"] = "segurando"
            ev = "sinal de login/recusa: segurando (não sobe nesta janela)"
    else:  # janela limpa
        if estado == "segurando":
            linha["estado"] = "subindo"
            ev = "janela limpa: volta a subir"
        if linha["estado"] == "subindo" and viva is not False:
            ult = linha.get("ultimo_degrau") or linha.get("desde") or agora
            if (datetime.fromisoformat(agora) - datetime.fromisoformat(ult)).total_seconds() >= espera_h * 3600:
                novo = min(pmax, linha["base"] + (linha["nivel"] + 1) * degrau)
                if novo > linha[chave]:
                    linha["nivel"] += 1
                    linha["ultimo_degrau"] = agora
                    ev = f"{espera_h} h sem sinal: sobe 1 degrau ({linha[chave]} → {novo})"
        elif linha["estado"] == "subindo" and viva is False:
            ev = None  # morta na saúde: espera voltar
    linha[chave] = min(pmax, linha["base"] + linha["nivel"] * degrau)
    if ev:
        linha.setdefault("historico", []).append({"em": agora, "o_que": ev, chave: linha[chave]})
        linha["historico"] = linha["historico"][-20:]
    return ev


def rampa(sinais, seco=False):
    """Atualiza tetos.json (contas/global). Devolve lista de eventos "servico conta: o que"."""
    try:
        lido_em = TETOS.stat().st_mtime_ns
    except OSError:
        lido_em = None
    t = _ler(TETOS, {})
    if not t or not (t.get("rampa") or {}).get("ligada", True):
        return []
    agora = _iso(datetime.now())
    svs = t.get("servicos") or {}
    contas = t.setdefault("contas", {})
    glob = t.setdefault("global", {})
    so_vivos = (t.get("rampa") or {}).get("so_vivos", True)
    eventos = []

    # 1) imagens (primeiro: o que a dona mais precisa)
    cfg = svs.get("imagens") or {}
    if cfg:
        alvo = contas.setdefault("imagens", {})
        for conta in sorted(_contas_imagens(sinais)):
            linha = alvo.setdefault(conta, _nova_linha(cfg.get("padrao", 90), agora))
            if linha.get("nivel", 0) == 0 and linha.get("base") != cfg.get("padrao", 90):
                linha["base"] = cfg.get("padrao", 90)  # a base do serviço mudou: a conta no degrau 0 acompanha
            jan = _janela(sinais, "flow", conta, cfg.get("espera_h", 24))
            classe = _pior(jan)
            if jan:
                linha["ultimo_sinal"] = {"em": jan[-1]["em"], "tipo": jan[-1]["tipo"], "maquina": jan[-1]["maquina"]}
            ev = _aplicar(linha, cfg, classe, _viva("imagens", conta) if so_vivos else None, agora, cfg.get("espera_h", 24))
            if ev:
                eventos.append(f"imagens {conta}: {ev}")
        # contas por pedido: global, sobe quando nenhuma conta do Flow deu sinal forte na janela
        sub = cfg.get("max_contas_por_pedido") or {}
        if sub:
            g = glob.setdefault("imagens", _nova_linha(sub.get("padrao", 2), agora))
            g.setdefault("max_contas_por_pedido", g["base"])
            fortes = {s["conta"] for s in sinais if s["servico"] == "flow" and s["classe"] in ("forte", "restrita")
                      and s["em"] >= _iso(datetime.now() - timedelta(hours=cfg.get("espera_h", 24)))}
            ev = _aplicar(g, cfg, "forte" if len(fortes) >= 2 else None, None, agora, cfg.get("espera_h", 24),
                          chave="<SEGREDO_REMOVIDO>", sub=sub)
            if ev:
                eventos.append(f"imagens (contas por pedido): {ev}")

    # 2) Instagram (Reels/dia por conta; base = max_dia do reuso_plataformas)
    cfg = svs.get("instagram") or {}
    reuso = _ler(REUSO, {}).get("instagram") or {}
    if cfg and reuso.get("contas"):
        alvo = contas.setdefault("instagram", {})
        for conta, r in reuso["contas"].items():
            base = r.get("max_dia") or reuso.get("max_por_conta_dia", 2)
            linha = alvo.setdefault(conta.lower(), _nova_linha(base, agora))
            if linha.get("base") != base and linha.get("nivel", 0) == 0:
                linha["base"] = base  # a dona mudou o max_dia no reuso: a base acompanha
            jan = _janela(sinais, "instagram", conta.lower(), cfg.get("espera_h", 36))
            classe = _pior(jan)
            if jan:
                linha["ultimo_sinal"] = {"em": jan[-1]["em"], "tipo": jan[-1]["tipo"], "maquina": jan[-1]["maquina"]}
            ev = _aplicar(linha, cfg, classe, _viva("instagram", conta) if so_vivos else None, agora, cfg.get("espera_h", 36))
            if ev:
                eventos.append(f"instagram {conta}: {ev}")

    # 3) Veo (global, por último): sinal forte em ≥ 2 contas do Flow ou bloqueio global = desce; login em ≥ 3 = segura
    cfg = svs.get("veo") or {}
    if cfg:
        g = glob.setdefault("veo", {**_nova_linha(cfg.get("teto_dia", {}).get("padrao", 40), agora),
                                    "reserva_min": cfg.get("reserva_min", {}).get("padrao", 100),
                                    "base_reserva": cfg.get("reserva_min", {}).get("padrao", 100)})
        g.setdefault("teto_dia", g["base"])
        lim = _iso(datetime.now() - timedelta(hours=cfg.get("espera_h", 72)))
        jan = [s for s in sinais if s["servico"] == "flow" and s["em"] >= lim]
        fortes = {s["conta"] for s in jan if s["classe"] in ("forte", "restrita")}
        logins = {s["conta"] for s in jan if s["classe"] == "login"}
        classe = "forte" if ("*" in fortes or len(fortes) >= 2) else ("login" if len(logins) >= 3 else None)
        if jan:
            g["ultimo_sinal"] = {"em": jan[-1]["em"], "tipo": jan[-1]["tipo"], "conta": jan[-1]["conta"]}
        nivel_antes = g["nivel"]
        ev = _aplicar(g, cfg, classe, None, agora, cfg.get("espera_h", 72), chave="<SEGREDO_REMOVIDO>", sub=cfg.get("teto_dia") or {})
        rc = cfg.get("reserva_min") or {}
        g["reserva_min"] = min(rc.get("patamar_max", 250), g.get("base_reserva", 100) + g["nivel"] * rc.get("degrau", 25))
        if ev:
            eventos.append(f"veo (global): {ev}; reserva mínima {g['reserva_min']}" if g["nivel"] != nivel_antes
                           else f"veo (global): {ev}")

    if not seco:
        try:
            mudou = TETOS.stat().st_mtime_ns != lido_em
        except OSError:
            mudou = True
        if mudou:  # 30/10: alguém (a dona, à mão) mexeu no tetos.json durante a rodada: não grava por cima;
            print("tetos.json mudou durante a rodada: não gravei (a próxima rodada refaz)", flush=True)
            return []  # a rampa da próxima hora recalcula a partir da versão nova
        _gravar(TETOS, t)
    return eventos


# ───────── saída ─────────
def _tabela(sinais, t):
    """Linhas do painel: serviço, conta, teto base→atual, estado, sinais 24 h / 7 d, último sinal, máquinas."""
    agora = datetime.now()
    lim24 = _iso(agora - timedelta(hours=JANELA_H))
    por = defaultdict(list)
    for s in sinais:
        por[(s["servico"], s["conta"])].append(s)
    linhas = []
    contas = t.get("contas") or {}
    pares = {("instagram", c) for c in (contas.get("instagram") or {})} | {("flow", c) for c in (contas.get("imagens") or {})}
    pares |= set(por)
    for servico, conta in sorted(pares):
        ss = por.get((servico, conta), [])
        s24 = [s for s in ss if s["em"] >= lim24]
        rampa_sv = "imagens" if servico == "flow" else servico
        ln = (contas.get(rampa_sv) or {}).get(conta) or {}
        ult = ss[-1] if ss else None
        linhas.append({"servico": servico, "conta": conta, "rampa": rampa_sv if ln else None,
                       "base": ln.get("base"), "teto": ln.get("teto"), "nivel": ln.get("nivel"),
                       "estado": ln.get("estado"), "ultimo_degrau": ln.get("ultimo_degrau"),
                       "sinais_24h": len(s24), "sinais_7d": len(ss), "pior_24h": _pior(s24),
                       "tipos_7d": dict(Counter(s["tipo"] for s in ss)),
                       "maquinas_7d": dict(Counter(s["maquina"] for s in ss)),
                       "ultimo": {"em": ult["em"], "tipo": ult["tipo"], "maquina": ult["maquina"], "trecho": ult["trecho"]} if ult else None,
                       "viva": _viva(rampa_sv, conta)})
    linhas.sort(key=lambda x: (-(PESO.get(x["pior_24h"]) if x["pior_24h"] else -1), -x["sinais_24h"], x["servico"], x["conta"]))
    return linhas


def _degraus(t):
    """Todos os degraus/eventos da rampa (data, serviço, conta, o que) — a dona vê "quanto a mais" por conta."""
    out = []
    for sv, contas in (t.get("contas") or {}).items():
        for c, ln in contas.items():
            for h in ln.get("historico") or []:
                out.append({"em": h["em"], "servico": sv, "conta": c, "o_que": h["o_que"], "teto": h.get("teto")})
    for sv, ln in (t.get("global") or {}).items():
        for h in ln.get("historico") or []:
            out.append({"em": h["em"], "servico": sv, "conta": "(global)", "o_que": h["o_que"],
                        "teto": h.get("teto_dia", h.get("max_contas_por_pedido", h.get("teto")))})
    return sorted(out, key=lambda x: x["em"])[-200:]


def _avisar(texto, importante, chave):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, origem="banimento", importante=importante, html_ok=False, chave=chave)
    except Exception as e:  # noqa: BLE001
        print(f"aviso não saiu ({type(e).__name__}: {str(e)[:100]})", flush=True)


def rodar(seco=False):
    ant = _ler(SAIDA, {})
    vistos = ant.get("vistos") or {}
    sinais = coletar()
    agora = _iso(datetime.now())
    novos = [s for s in sinais if s["id"] not in vistos]
    primeira = not vistos
    for s in novos:
        vistos[s["id"]] = s["em"]
        if not seco:
            _log({"evento": "sinal", **s})
    corte = _iso(datetime.now() - timedelta(days=HISTORICO_D + 1))
    vistos = {k: v for k, v in vistos.items() if v >= corte}

    eventos = rampa(sinais, seco=seco)
    t = _ler(TETOS, {})
    for ev in eventos:
        print("rampa:", ev, flush=True)
        if not seco:
            _log({"evento": "rampa", "em": agora, "o_que": ev})

    tabela = _tabela(sinais, t)
    lim24 = _iso(datetime.now() - timedelta(hours=JANELA_H))
    resumo = {sv: {"contas_com_sinal_24h": len({s["conta"] for s in sinais if s["servico"] == sv and s["em"] >= lim24}),
                   "sinais_24h": sum(1 for s in sinais if s["servico"] == sv and s["em"] >= lim24),
                   "sinais_7d": sum(1 for s in sinais if s["servico"] == sv),
                   "restritas": sorted({s["conta"] for s in sinais if s["servico"] == sv and s["classe"] == "restrita"})}
              for sv in sorted({s["servico"] for s in sinais} | {"instagram", "flow"})}
    saida = {"em": agora, "janela_h": JANELA_H, "resumo": resumo, "tabela": tabela, "degraus": _degraus(t),
             "tetos": {"rampa": t.get("rampa"), "servicos": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                                                             for k, v in (t.get("servicos") or {}).items()},
                       "global": t.get("global") or {}},
             "novos": [{k: s[k] for k in ("em", "servico", "conta", "tipo", "classe", "maquina", "trecho")} for s in novos][-50:],
             "sinais_7d": [{k: s[k] for k in ("em", "servico", "conta", "tipo", "classe", "maquina", "fonte", "trecho")} for s in sinais][-400:],
             "vistos": vistos}
    if not seco:
        _gravar(SAIDA, saida)

    for l in tabela:
        if l["sinais_7d"] or l["teto"] is not None:
            print(f"{l['servico']:<9} {l['conta']:<26} teto {str(l['base']) + '→' + str(l['teto']) if l['teto'] is not None else '—':<8} "
                  f"{(l['estado'] or '-'):<10} 24h {l['sinais_24h']:>2} 7d {l['sinais_7d']:>3} "
                  f"{(l['ultimo'] or {}).get('tipo', ''):<18} {(l['ultimo'] or {}).get('maquina', '')}", flush=True)
    print(f"{len(sinais)} sinais em {HISTORICO_D} d, {len(novos)} novos; {len(eventos)} evento(s) de rampa", flush=True)

    if seco:
        return saida
    # Telegram: sinal novo por conta (a 1ª rodada só resume: os sinais velhos a dona já viu nos logs)
    if novos and not primeira:
        por = defaultdict(list)
        for s in novos:
            por[(s["servico"], s["conta"])].append(s)
        partes = []
        for (sv, c), ss in sorted(por.items()):
            u = ss[-1]
            partes.append(f"{sv} {c} [{u['maquina']}]: {u['tipo']} ×{len(ss)} ({u['em'][11:16]}) {u['trecho'][:90]}")
        grave = any(s["classe"] in ("forte", "restrita") for s in novos)
        _avisar(("🚫 Monitor de banimento — sinal novo:\n" if grave else "⚠️ Monitor de banimento — sinal de login/recusa:\n")
                + "\n".join(partes[:12]) + (f"\n… e mais {len(partes) - 12}" if len(partes) > 12 else ""),
                importante=grave, chave="<SEGREDO_REMOVIDO>" + ";".join(f"{sv}{c}" for sv, c in sorted(por))[:80])
    elif novos and primeira:
        _avisar(f"🛡️ Monitor de banimento ligado: {len(sinais)} sinais nos últimos {HISTORICO_D} dias em "
                f"{len({(s['servico'], s['conta']) for s in sinais})} contas (restritas: "
                f"{', '.join(sorted({s['conta'] for s in sinais if s['classe'] == 'restrita'})) or 'nenhuma'}). "
                "Rampa de tetos ligada em degrau 0: imagens sobem depois de 24 h sem sinal, Reels 36 h, Veo 72 h.",
                importante=False, chave="<SEGREDO_REMOVIDO>")
    if eventos:
        _avisar("📶 Rampa de tetos:\n" + "\n".join(eventos[:15]), importante=any("FORTE" in e or "FORA" in e for e in eventos),
                chave="<SEGREDO_REMOVIDO>" + agora[:13])
    return saida


def mostrar():
    d = _ler(SAIDA, {})
    print(json.dumps(d.get("resumo"), ensure_ascii=False), "em", d.get("em"))
    for l in d.get("tabela") or []:
        print(f"{l['servico']:<9} {l['conta']:<26} teto {l.get('base')}→{l.get('teto')} {l.get('estado') or '-':<10} "
              f"24h {l['sinais_24h']} 7d {l['sinais_7d']} {(l.get('ultimo') or {}).get('tipo', '')}")
    for g in d.get("degraus") or []:
        print(f"  degrau {g['em'][:16]} {g['servico']} {g['conta']}: {g['o_que']}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--mostrar" in sys.argv:
        mostrar()
    else:
        rodar(seco="--seco" in sys.argv)
