"""Registro dos créditos do Fish Audio por conta — para escolher a conta CERTA sem abrir todas (dona 18/11: "deixando
registrado pra não precisar ficar abrindo e vendo todas a cada vez").

creditos.json:  {email: {"restantes": int, "lido_em": "AAAA-MM-DDTHH:MM", "renova_dia": 18, "logado": bool,
                          "erro": str|None, "gasto_desde_leitura": int}}
- Cada geração desconta len(texto) (1 crédito por caractere, medido 18/11) -> o número fica certo sem abrir o site.
- Leitura real (página de cobrança) só quando: nunca leu, passou do dia da renovação, ou a estimativa ficou baixa.
    python creditos.py                 # mostra o registro
    python creditos.py ler <email>     # saldo real dessa conta: HTTP com a sessão guardada (sessoes_fish), sem
                                       # Chrome; só sem sessão guardada abre a página de cobrança
"""
import json, os, re, sys, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
AQUI = Path(__file__).resolve().parent
ARQ = AQUI / "creditos.json"
MINIMO = 300  # abaixo disso a conta não é escolhida (um Short tem ~450 caracteres)


def carregar():
    try:
        return json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvar(d):
    tmp = ARQ.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ARQ)


def _renovou(reg):
    """Passou do dia da renovação desde a última leitura? (cota grátis renova todo mês no mesmo dia)"""
    try:
        lido = datetime.fromisoformat(reg["lido_em"])
    except (KeyError, ValueError):
        return True
    hoje = datetime.now()
    dia = int(reg.get("renova_dia") or 18)
    if (hoje.year, hoje.month) == (lido.year, lido.month):
        return lido.day < dia <= hoje.day
    return True if hoje.day >= dia or (hoje - lido).days > 31 else lido.day < dia


def estimado(reg):
    if not reg or reg.get("restantes") is None:
        return None
    if _renovou(reg):
        return None  # renovou: precisa ler de novo
    return int(reg["restantes"]) - int(reg.get("gasto_desde_leitura") or 0)


def gastar(email, n):
    d = carregar()
    r = d.setdefault(email, {})
    r["gasto_desde_leitura"] = int(r.get("gasto_desde_leitura") or 0) + int(n)
    salvar(d)


def marcar(email, **campos):
    d = carregar()
    d.setdefault(email, {}).update(campos)
    salvar(d)


def ler_na_pagina(pg):
    """Na página de cobrança: devolve (restantes, total, renova_dia) ou None se deslogado."""
    pg.goto("https://fish.audio/pt/app/billing/", wait_until="domcontentloaded", timeout=60000)
    time.sleep(8)
    t = pg.inner_text("body")
    if "My Team" not in t or "restantes" not in t:
        return None
    m = re.search(r"([\d.]+)\s*restantes de\s*([\d.]+)", t)
    dia = re.search(r"Renovam em (\d+)", t)
    if not m:
        return None
    return int(m.group(1).replace(".", "")), int(m.group(2).replace(".", "")), int(dia.group(1)) if dia else 18


def gravar_leitura(email, lido):
    if lido is None:
        marcar(email, logado=False, erro="deslogado", lido_em=datetime.now().isoformat(timespec="minutes"))
        return
    rest, total, dia = lido
    marcar(email, restantes=rest, total=total, renova_dia=dia, logado=True, erro=None, gasto_desde_leitura=0,
           lido_em=datetime.now().isoformat(timespec="minutes"))


def ler(email):
    """Saldo REAL da conta. 1º por HTTP com a sessão guardada (sessoes_fish: sem Chrome, pela saída dela);
    só se não houver sessão guardada (ou ela morreu) abre o Chrome e lê a página de cobrança."""
    try:
        import sessoes_fish
        r = sessoes_fish.saldo(email)
        if r is not None:
            return r[0], r[1], int(carregar().get(email, {}).get("renova_dia") or 18)
    except Exception:  # noqa: BLE001 — sessão morta / sem sessão: cai no Chrome
        pass
    return ler_pelo_chrome(email)


def ler_pelo_chrome(email):
    """Último recurso: abre a conta pela saída dela, lê a página de cobrança e grava."""
    import cofre
    import fish_audio as fa
    _, ip_n = fa.checar_conta(email)
    pp = fa._subir_ponte(ip_n)
    porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{pp}",))
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = b.contexts[0].pages[0] if b.contexts[0].pages else b.contexts[0].new_page()
            lido = ler_na_pagina(pg)
            gravar_leitura(email, lido)
            return lido
    finally:
        try:
            cofre.fechar(proc, nome=email)
        except Exception:  # noqa: BLE001
            pass


def escolher(precisa, excluir=()):
    """Conta logada com crédito estimado >= precisa (e >= MINIMO), a de MAIS crédito primeiro.
    Devolve (email, estimado) — estimado None = precisa ler antes (renovou/nunca leu). None = nenhuma serve."""
    d = carregar()
    boas, ler_antes = [], []
    # 25/11: 1 conta = 1 máquina (sessoes_remotas\donos.json). Conta de outra máquina CONTINUA no rodízio do PC1: o
    # fish_http usa a fábrica DAQUELA máquina (Chrome lá) e o mesmo IP fixo — nunca abre o Chrome dela aqui.
    # FISH_SO_MINHAS=1 tira do rodízio as contas de outras máquinas (para quando a máquina dona produzir sozinha).
    try:
        donos = json.loads((Path(__file__).resolve().parent / "sessoes_remotas" / "donos.json").read_text("utf-8"))
    except (OSError, ValueError):
        donos = {}
    eu = os.environ.get("FISH_MAQUINA", "pc1")
    so_minhas = os.environ.get("FISH_SO_MINHAS") == "1"
    for email, r in d.items():
        if email in excluir or not r.get("logado"):
            continue
        if so_minhas and (donos.get(email) or {}).get("maquina", eu) != eu:
            continue
        e = estimado(r)
        if e is None:
            ler_antes.append(email)
        elif e >= max(precisa, MINIMO):
            boas.append((e, email))
    if boas:
        boas.sort(reverse=True)
        return boas[0][1], boas[0][0]
    if ler_antes:
        return ler_antes[0], None
    return None


def mostrar():
    d = carregar()
    tot = 0
    for email, r in sorted(d.items(), key=lambda kv: -(estimado(kv[1]) or 0)):
        e = estimado(r)
        tot += e or 0
        print(f"{email:40s} {'logada' if r.get('logado') else 'SEM LOGIN':9s} restantes~{e if e is not None else '?':>6} "
              f"(lido {r.get('lido_em', '-')}, renova dia {r.get('renova_dia', '?')}) {r.get('erro') or ''}")
    print(f"total estimado: {tot} créditos ≈ {tot // 450} Shorts de 30 s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["ler"]:
        print(ler(sys.argv[2].lower()))
    else:
        mostrar()
