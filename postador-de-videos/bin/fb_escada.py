"""Escada das Páginas do Facebook (dona 20/11/2026: "como seria o sistema de escada pro Facebook").

Mesma ideia da escada do YouTube (rampa_canais.py), adaptada ao Facebook:
  - cada Página começa no 'por_dia' do config/facebook_paginas.json (3) e sobe 1 degrau por vez até TETO_MAX (8);
  - sobe se: passaram DIAS_ENTRE_DEGRAUS desde a última mudança, ela ENCHEU o teto em >= DIAS_CHEIOS dos últimos 3
    dias, não teve bloqueio/restrição nesses dias e as views medidas (fb_medir.py) não estão caindo;
  - desce NA HORA (e segura 24 h sem postar) quando o Facebook bloqueia/restringe (descer(), chamado pelo postador);
  - Página "parada" (views da última medição = 0 em todos os reels com 3+ dias) não sobe.
Estado: config/fb_escada.json.  Log: logs/fb_escada.log.

    python fb_escada.py            # roda a subida do dia (tarefa FacebookEscada, 1x/dia)
    python fb_escada.py ver        # mostra o teto de cada Página
"""
import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parent
CFG = BIN.parent / "config" / "facebook_paginas.json"
ESTADO = BIN.parent / "config" / "fb_escada.json"
REG = BIN.parent / "logs" / "facebook_paginas.json"
VIEWS = BIN.parent / "logs" / "fb_views.jsonl"
LOG = BIN.parent / "logs" / "fb_escada.log"
TETO_MAX = 8
DIAS_ENTRE_DEGRAUS = 3
DIAS_CHEIOS = 2
SEGURAR_H = 24
PALAVRAS_BLOQUEIO = ("bloque", "restri", "limite", "temporariamente", "suspens", "violou", "spam", "checkpoint")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return padrao


def _gravar(d):
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, ESTADO)


def _log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {msg}\n")
    print(msg, flush=True)


def teto(chave, pag=None):
    """Quantos Reels a Página pode postar hoje (0 se está segurada por bloqueio). +1 no dia em que estagnou."""
    pag = pag or _ler(CFG, {}).get("paginas", {}).get(chave, {})
    e = _ler(ESTADO, {}).get(chave, {})
    if e.get("segurar_ate") and datetime.now().isoformat() < e["segurar_ate"]:
        return 0
    bonus = 1 if e.get("bonus_dia") == datetime.now().strftime("%Y-%m-%d") else 0
    return max(1, min(TETO_MAX + 1, min(TETO_MAX, pag.get("por_dia", 3) + e.get("degrau", 0)) + bonus))


# Igual ao YouTube (rampa_canais, dona 30/10): Reel decolando = segura a Página até esfriar (máx. VIRAL_MAX_H);
# Página que parou de ganhar view = +1 vaga no dia. Usa as 2 últimas medições do fb_medir (de 6 em 6 h).
VIRAL_X, VIRAL_MIN, VIRAL_MAX_H = 2.0, 300, 18


def _ganho(chave):
    """(ganho da última medição, ganho médio por medição antes dela) ou None."""
    m = [s for _, s, _n in _medicoes(chave)]
    if len(m) < 3:
        return None
    difs = [b - a for a, b in zip(m, m[1:])]
    return difs[-1], sum(difs[:-1]) / len(difs[:-1])


def _medicoes(chave):
    out = []
    if VIEWS.exists():
        for linha in VIEWS.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(linha)
            except Exception:
                continue
            if r.get("pagina") == chave:
                out.append((r["quando"], sum(x["views"] for x in r["reels"]), len(r["reels"])))
    return out


def segurar_viral(chave):
    """Texto se a Página tem Reel decolando agora (não posta outro); None senão."""
    g = _ganho(chave)
    d = _ler(ESTADO, {})
    e = d.setdefault(chave, {})
    desde = e.get("viral_desde")
    if not g or g[0] < max(VIRAL_MIN, VIRAL_X * g[1]):
        if desde:
            e.pop("viral_desde", None); _gravar(d)
        return None
    if desde and datetime.fromisoformat(desde) < datetime.now() - timedelta(hours=VIRAL_MAX_H):
        return None
    if not desde:
        e["viral_desde"] = datetime.now().isoformat(timespec="seconds"); _gravar(d)
        _log(f"[{chave}] Reel decolando (+{g[0]} x média {g[1]:.0f}): segura novos posts até esfriar")
    return f"Reel decolando (+{g[0]} views x média {g[1]:.0f})"


def marcar_estagnacao(chave):
    """Chamado depois de cada medição: ganho < 25% da média = +1 vaga hoje."""
    g = _ganho(chave)
    if g and g[1] >= 30 and g[0] < 0.25 * g[1]:
        d = _ler(ESTADO, {})
        e = d.setdefault(chave, {})
        hoje = datetime.now().strftime("%Y-%m-%d")
        if e.get("bonus_dia") != hoje:
            e["bonus_dia"] = hoje; _gravar(d)
            _log(f"[{chave}] estagnou (+{g[0]} x média {g[1]:.0f}): +1 Reel hoje")


def e_bloqueio(msg):
    m = (msg or "").casefold()
    return any(p in m for p in PALAVRAS_BLOQUEIO)


def descer(chave, motivo):
    d = _ler(ESTADO, {})
    e = d.setdefault(chave, {})
    e["degrau"] = e.get("degrau", 0) - 1
    e["mudou_em"] = datetime.now().isoformat(timespec="seconds")
    e["segurar_ate"] = (datetime.now() + timedelta(hours=SEGURAR_H)).isoformat(timespec="seconds")
    e.setdefault("historico", []).append({"quando": e["mudou_em"], "delta": -1, "motivo": motivo[:200]})
    _gravar(d)
    _log(f"[{chave}] DESCEU (degrau {e['degrau']}), segura {SEGURAR_H} h: {motivo[:150]}")


def _views_por_pagina():
    """{chave: [(data, soma_views, n_reels)]} das medições do fb_medir.py (1 por dia, a última do dia)."""
    out = {}
    if not VIEWS.exists():
        return out
    por_dia = {}
    for linha in VIEWS.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(linha)
        except Exception:
            continue
        por_dia[(r["pagina"], r["quando"][:10])] = (sum(x["views"] for x in r["reels"]), len(r["reels"]))
    for (chave, dia), (soma, n) in sorted(por_dia.items(), key=lambda t: t[0][1]):
        out.setdefault(chave, []).append((dia, soma, n))
    return out


def rodar():
    cfg = _ler(CFG, {})
    reg = _ler(REG, {})
    d = _ler(ESTADO, {})
    views = _views_por_pagina()
    hoje = datetime.now().date()
    for chave, pag in cfg.get("paginas", {}).items():
        if pag.get("pausada"):
            continue
        e = d.setdefault(chave, {"degrau": 0})
        atual = teto(chave, pag)
        mudou = e.get("mudou_em") or pag.get("_criada_iso") or "2000-01-01"
        if datetime.fromisoformat(mudou[:19]).date() > hoje - timedelta(days=DIAS_ENTRE_DEGRAUS):
            continue
        posts = reg.get("postados", {}).get(chave, [])
        cheios = sum(1 for i in range(1, 4)
                     if sum(1 for x in posts if x["quando"][:10] == str(hoje - timedelta(days=i))) >= atual)
        erros = [m for k, m in (reg.get("erros", {}).get(chave) or {}).items()
                 if k[:10] >= str(hoje - timedelta(days=3)) and e_bloqueio(m)]
        v = views.get(chave, [])
        caindo = len(v) >= 2 and v[-1][1] < v[-2][1]  # soma acumulada caiu = reels sumiram/removidos
        parada = bool(v) and v[-1][1] == 0 and v[-1][2] >= 3
        motivo = None
        if cheios < DIAS_CHEIOS:
            motivo = f"encheu o teto só em {cheios}/3 dias"
        elif erros:
            motivo = f"bloqueio recente: {erros[-1][:80]}"
        elif caindo:
            motivo = "views caindo"
        elif parada:
            motivo = "reels com 0 views"
        elif atual >= TETO_MAX:
            motivo = "já no teto máximo"
        if motivo:
            _log(f"[{chave}] fica em {atual}/dia ({motivo})")
            continue
        e["degrau"] = e.get("degrau", 0) + 1
        e["mudou_em"] = datetime.now().isoformat(timespec="seconds")
        e.setdefault("historico", []).append({"quando": e["mudou_em"], "delta": +1, "motivo": "encheu o teto, sem bloqueio"})
        _log(f"[{chave}] SUBIU para {min(TETO_MAX, pag.get('por_dia', 3) + e['degrau'])}/dia")
    _gravar(d)


def ver():
    cfg = _ler(CFG, {})
    for chave, pag in cfg.get("paginas", {}).items():
        e = _ler(ESTADO, {}).get(chave, {})
        print(f"{pag['nome']:28} teto hoje {teto(chave, pag)} (base {pag.get('por_dia', 3)}, degrau {e.get('degrau', 0)})"
              + (f" SEGURADA até {e['segurar_ate']}" if e.get("segurar_ate", "") > datetime.now().isoformat() else ""))


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ver() if (sys.argv[1:] or [""])[0] == "ver" else rodar()
