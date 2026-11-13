# Gera a proposta comercial MS Energy em PDF.
# Uso: python -I gerar_proposta.py [solis|micro|parque]   (imagens recortadas em _img\, PDF gravado nesta pasta)
import base64, os, sys, datetime
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "_img")

# ---------------- versoes da proposta ----------------
# ger_media: geracao media fixada (kWh/mes); sem ela, a geracao sai da potencia (kWp).
# so_maxima: nao mostra media em lugar nenhum, so "ate X kWh/mes" (o mes mais forte).
VERSOES = {
    "solis": dict(
        n=12, ger_media=1000, consumo=1000, valor=22900.00, num="P26-1031",
        saida="Proposta MS Energy - 1.000 kWh - 12x625W Solis 7k.pdf",
        cliente="", cliente_doc="", cliente_end="", ligacao="Bifásico", grupo="Grupo B – Convencional", minimo=50,
        inversores=[(1, "INVERSOR SOLAR SOLIS 7 kW MONOFÁSICO", "2 MPPT · monitoramento Wi-Fi pelo celular", "SOLIS")],
        inv_curto="Solis 7 kW", inv_card="Inversor com monitoramento pelo celular",
        inv_garantia="Inversor Solis: 10 anos (conforme fabricante)",
        estrutura=("ESTRUTURA TELHADO CERÂMICO P/ 4 PAINÉIS", "Alumínio e inox, à prova de corrosão"), cabo_m=50,
        porque=["Menos painéis para a mesma energia: menos peso e menos furos no telhado.",
                "Tecnologia N-type: perde menos rendimento no calor do Pará e envelhece mais devagar (cerca de 0,4% ao ano).",
                "Inversor Solis de 7 kW com folga para a potência dos painéis e acompanhamento da geração pelo aplicativo."]),
    "iedson": dict(
        n=12, ger_media=1000, consumo=941, valor=22900.00, num="P26-1104", tarifa=1.28,
        saida="Proposta MS Energy - Iedson dos Santos Dantas - 941 kWh - 12x625W Solis 7k.pdf",
        cliente="IEDSON DOS SANTOS DANTAS", cliente_doc="CPF: ____________________",
        cliente_end="R. E 26, Qd 13 – Fonte Boa · CEP 68740-001 · Castanhal – PA · UC 2.864.836.013-02",
        ligacao="Trifásico", grupo="Grupo B1 – Residencial", minimo=100,
        inversores=[(1, "INVERSOR SOLAR SOLIS 7 kW", "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "SOLIS")],
        inv_curto="Solis 7 kW", inv_card="Inversor com monitoramento pelo celular",
        inv_garantia="Inversor Solis: 10 anos (conforme fabricante)",
        estrutura=("ESTRUTURA TELHADO CERÂMICO P/ 4 PAINÉIS", "Alumínio e inox, à prova de corrosão"), cabo_m=50,
        porque=["Gera cerca de 1.000 kWh por mês para um consumo de 941 kWh: cobre a conta com folga e ainda guarda crédito.",
                "Menos painéis para a mesma energia: menos peso e menos furos no telhado.",
                "Tecnologia N-type: perde menos rendimento no calor do Pará e envelhece mais devagar (cerca de 0,4% ao ano).",
                "Inversor Solis de 7 kW com folga para a potência dos painéis e acompanhamento da geração pelo aplicativo."]),
    "micro": dict(
        n=4, ger_media=399, consumo=399, valor=9900.00, num="P26-1031M",
        saida="Proposta MS Energy - 399 kWh - 4x625W Microinversor Deye 2,25k.pdf",
        cliente="", cliente_doc="", cliente_end="", ligacao="Bifásico", grupo="Grupo B – Convencional", minimo=50,
        inversores=[(1, "MICROINVERSOR DEYE 2,25 kW (SUN-M2250G4)", "4 entradas, uma por painel · monitoramento Wi-Fi pelo celular", "DEYE")],
        inv_curto="Micro Deye 2,25 kW", inv_card="Microinversor: cada painel trabalha sozinho",
        inv_garantia="Microinversor Deye: conforme garantia do fabricante",
        estrutura=("ESTRUTURA TELHADO CERÂMICO P/ 4 PAINÉIS", "Alumínio e inox, à prova de corrosão"), cabo_m=20,
        porque=["Microinversor: cada painel trabalha sozinho, então sombra ou sujeira em um não derruba a geração dos outros.",
                "Mais segurança: sem alta tensão em corrente contínua passando pela casa.",
                "Acompanhamento da geração pelo aplicativo e fácil de aumentar depois com mais painéis.",
                "Tecnologia N-type: perde menos rendimento no calor do Pará e envelhece mais devagar (cerca de 0,4% ao ano)."]),
    "parque": dict(
        n=216, consumo=20000, valor=495000.00, num="P26-1031C", so_maxima=True,
        saida="Proposta MS Energy - Condominio Parque Paraiso - ate 20.000 kWh - 216x625W Solis.pdf",
        cliente="CONDOMÍNIO RESIDENCIAL PARQUE PARAÍSO", cliente_doc="CNPJ: ____________________",
        cliente_end="Rod. Transcastanhal, 3994 – Academia do Condomínio · CEP 68740-001 · Castanhal – PA",
        ligacao="Trifásico", grupo="Grupo B3 – Comercial / Serviços", minimo=100,
        inversores=[(2, "INVERSOR SOLAR SOLIS 60 kW TRIFÁSICO", "Uso comercial · vários MPPT · monitoramento remoto 24 h", "SOLIS")],
        inv_curto="2 × Solis 60 kW", inv_card="Inversores trifásicos de uso comercial",
        inv_garantia="Inversores Solis: 10 anos (conforme fabricante)",
        estrutura=("ESTRUTURA DE SOLO (MESA) P/ 4 PAINÉIS", "Alumínio e aço galvanizado · fundação em estacas de concreto inclusa", "inst3.jpg"),
        cabo_m=600, solo=True,
        extras=[("STRING BOX / PROTEÇÕES CC E CA", "Disjuntores, DPS e chaves seccionadoras dimensionados no projeto", "CJ", 1)],
        porque=["Usina de solo de 135 kWp: não usa telhado, fica na inclinação e na direção ideais e é fácil de limpar e manter.",
                "Feita para a conta das áreas comuns do condomínio: portaria, iluminação, bombas, academia.",
                "Painéis N-type de 625 W: menos painéis por kWp, menos área ocupada e menos perda no calor do Pará.",
                "Dois inversores Solis de 60 kW: se um precisar de manutenção, o outro continua gerando.",
                "Monitoramento remoto: a síndica ou o síndico acompanha a geração de cada dia pelo celular."]),
}
for _chave, _n, _ger, _valor in [("iedson1600", 20, 1600, 34900.00), ("iedson1800", 22, 1800, 38900.00)]:
    VERSOES[_chave] = dict(
        VERSOES["iedson"], n=_n, ger_media=_ger, consumo=_ger, valor=_valor, num=f"P26-1104-{_ger}",
        saida=f"Proposta MS Energy - Iedson dos Santos Dantas - {_ger // 1000}.{_ger % 1000:03d} kWh - {_n}x625W Solis 10k.pdf",
        inversores=[(1, "INVERSOR SOLAR SOLIS 10 kW", "Ligação trifásica 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "SOLIS")],
        inv_curto="Solis 10 kW",
        porque=[f"Gera cerca de {_ger // 1000}.{_ger % 1000:03d} kWh por mês: cobre a conta de hoje e deixa folga para aumentar o consumo "
                "(ar-condicionado, chuveiro, carro elétrico).",
                f"{_n} painéis de 625 W ({str(_n * 0.625).rstrip('0').replace('.', ',')} kWp) num inversor Solis de 10 kW: "
                "aproveita melhor as horas de sol fraco.",
                "Tecnologia N-type: perde menos rendimento no calor do Pará e envelhece mais devagar (cerca de 0,4% ao ano).",
                "Acompanhamento da geração pelo aplicativo do inversor."])
CHAVE = sys.argv[1] if len(sys.argv) > 1 else "solis"
V = VERSOES[CHAVE]
SAIDA = os.path.join(AQUI, V["saida"])
SO_MAX = V.get("so_maxima", False)

# ---------------- dados da proposta ----------------
N_PAINEIS, W_PAINEL = V["n"], 625
KWP = N_PAINEIS * W_PAINEL / 1000
CONSUMO = V["consumo"]
MINIMO = V["minimo"]
TARIFA = V.get("tarifa", 1.10)              # R$/kWh com impostos
VALOR = V["valor"]
INFLA = 0.04                                # reajuste anual da tarifa
DEGRAD1, DEGRAD = 0.01, 0.004               # N-type: 1% no 1o ano, 0,4%/ano depois
POUP = 0.0617                               # poupanca ao ano
DESCONTO = 0.10                             # taxa do VPL
HOJE = datetime.date.today()
NUM = V["num"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
# perfil mensal de sol da regiao; 7,5 kWp -> 1.000 kWh/mes na media (mesma base das propostas anteriores)
PERFIL = [491, 491, 497, 515, 537, 567, 580, 603, 606, 587, 571, 525]
media = V.get("ger_media") or KWP * 1000 / 7.5
GER = [round(p * media * 12 / sum(PERFIL)) for p in PERFIL]
GER_MAX = max(GER)


def brl(v, casas=2):
    s = f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s


def simula_ano(fator_ger, tarifa):
    """Compensacao mes a mes: sobra vira credito, falta usa credito; paga no minimo o custo de disponibilidade."""
    cred, linhas, conta_com = 0, [], 0.0
    for m, g in zip(MESES, GER):
        g = g * fator_ger
        saldo = g - CONSUMO
        if saldo >= 0:
            cred += saldo
            falta = 0
        else:
            usa = min(cred, -saldo)
            cred -= usa
            falta = -saldo - usa
        fat = max(MINIMO, falta) * tarifa
        conta_com += fat
        linhas.append((m, CONSUMO, g, max(saldo, 0), cred, CONSUMO * tarifa, fat))
    return linhas, CONSUMO * 12 * tarifa - conta_com


ano1, ECON_ANO1 = simula_ano(1.0, TARIFA)
fluxo, anos = [-VALOR], []
acum, poup, fator = -VALOR, VALOR, 1.0
for a in range(1, 26):
    if a > 1:
        fator *= (1 - DEGRAD) if a > 2 else (1 - DEGRAD1)
    tar = TARIFA * (1 + INFLA) ** (a - 1)
    _, econ = simula_ano(fator, tar)
    acum += econ
    poup *= 1 + POUP
    fluxo.append(econ)
    anos.append((a, tar, sum(GER) * fator, econ, acum, poup - VALOR))


def vpl(taxa):
    return sum(f / (1 + taxa) ** i for i, f in enumerate(fluxo))


lo, hi = 0.0, 5.0
for _ in range(200):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if vpl(mid) > 0 else (lo, mid)
TIR, VPL = mid, vpl(DESCONTO)
s, pb = -VALOR, None
for a, _t, _g, econ, _ac, _p in anos:
    if s + econ >= 0:
        pb = (a - 1) * 12 + int(-s / econ * 12 + 0.999)
        break
    s += econ
PB_TXT = f"{pb // 12} ano{'s' if pb // 12 != 1 else ''}" + (f" e {pb % 12} {'mês' if pb % 12 == 1 else 'meses'}" if pb % 12 else "")
TOTAL_25 = anos[-1][4]
MWH_25 = sum(x[2] for x in anos) / 1000
CO2 = MWH_25 * 0.29                         # t de CO2 por MWh (mesmo fator da proposta anterior)
ARVORES = round(CO2 * 7.13)
# painel 625 W ~ 2,38 x 1,13 m; no solo as fileiras precisam de corredor para nao fazer sombra uma na outra
AREA = round(N_PAINEIS * 2.38 * 1.13 * (1.8 if V.get("solo") else 1.25 if N_PAINEIS > 40 else 1))

_cache = {}


def b64(nome):
    if nome not in _cache:
        with open(os.path.join(IMG, nome), "rb") as f:
            _cache[nome] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    return _cache[nome]


# ---------------- cores e icones ----------------
AZUL, AZUL2, AMARELO, TINTA, TINTA2, GRADE, FUNDO = "#123b57", "#1d5a80", "#f2a900", "#1f2933", "#52606d", "#e4e7eb", "#f4f7f9"


def ico(nome, cor=AMARELO, t=26):
    p = {
        "sol": '<circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1" stroke-width="2" stroke-linecap="round" fill="none" stroke="currentColor"/>',
        "painel": '<path d="M3 5h18l-2 12H5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M4 11h16M9 5l-1 12M15 5l1 12" stroke="currentColor" stroke-width="1.6" fill="none"/><path d="M12 17v4M8 21h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
        "raio": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
        "inversor": '<rect x="5" y="2.5" width="14" height="19" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><rect x="8" y="6" width="8" height="5" rx="1"/><circle cx="12" cy="16" r="2"/>',
        "dinheiro": '<rect x="2" y="6" width="20" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="2"/>',
        "area": '<path d="M3 3h18v18H3z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 9h18M9 3v18" stroke="currentColor" stroke-width="1.5"/>',
        "relogio": '<circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 6.5V12l3.5 2.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>',
        "grafico": '<path d="M3 20h18" stroke="currentColor" stroke-width="2"/><path d="M6 16l4-5 3 3 5-7" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "folha": '<path d="M5 19c0-9 6-14 15-15-1 9-6 15-15 15z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M5 19 13 11" stroke="currentColor" stroke-width="2"/>',
        "arvore": '<path d="M12 2 5 12h4l-3 5h12l-3-5h4z"/><rect x="11" y="17" width="2" height="5"/>',
        "nuvem": '<path d="M7 18a4.5 4.5 0 0 1-.6-9A6 6 0 0 1 18 9.5 4.3 4.3 0 0 1 17.5 18z" fill="none" stroke="currentColor" stroke-width="2"/>',
        "escudo": '<path d="M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="m8.5 12 2.5 2.5 4.5-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>',
        "check": '<circle cx="12" cy="12" r="10"/><path d="m7.5 12.5 3 3 6-6.5" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    }[nome]
    return f'<svg viewBox="0 0 24 24" width="{t}" height="{t}" fill="currentColor" style="color:{cor}">{p}</svg>'


def nice_step(span, alvo=5):
    bruto = span / alvo
    mag = 10 ** len(str(int(bruto))) / 10
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * mag:
            return m * mag
    return 10 * mag


def fmt_eixo(v):
    if abs(v) >= 1_000_000:
        return f"{brl(v/1e6, 1)} mi"
    if abs(v) >= 10000:
        return f"{brl(v/1000, 0)} mil"
    return brl(v, 0)


# ---------------- graficos SVG ----------------
def grafico_geracao():
    W, H, ml, mb, mt = 680, 250, 54, 28, 14
    serie_c = [] if SO_MAX else [CONSUMO] * 12
    topo = max(GER + serie_c) * 1.12
    passo = nice_step(topo)
    vmax = passo * (int(topo / passo) + 1)
    pw, ph = W - ml - 10, H - mb - mt
    g = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="Segoe UI,Arial" font-size="11">',
         '<defs><linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a76a8"/>'
         f'<stop offset="1" stop-color="{AZUL}"/></linearGradient></defs>']
    v = 0
    while v <= vmax:
        y = mt + ph - v / vmax * ph
        g.append(f'<line x1="{ml}" x2="{W-10}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRADE}"/>'
                 f'<text x="{ml-7}" y="{y+4:.1f}" text-anchor="end" fill="{TINTA2}">{fmt_eixo(v)}</text>')
        v += passo
    slot = pw / 12
    series = [(serie_c, AMARELO, "Consumo"), (GER, "url(#gA)", "Geração")] if serie_c else [(GER, "url(#gA)", "Geração")]
    bw = slot * (0.32 if serie_c else 0.56)
    for i, m in enumerate(MESES):
        x0 = ml + i * slot + slot / 2 - (bw + 1) * len(series) / 2
        for j, (s_, cor, nome) in enumerate(series):
            h = s_[i] / vmax * ph
            x = x0 + j * (bw + 2)
            g.append(f'<rect x="{x:.1f}" y="{mt+ph-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{cor}">'
                     f'<title>{m} – {nome}: {brl(s_[i],0)} kWh</title></rect>')
            if nome == "Geração" and (SO_MAX or len(series) == 1) and s_[i] == GER_MAX:
                g.append(f'<text x="{x+bw/2:.1f}" y="{mt+ph-h-5:.1f}" text-anchor="middle" font-weight="700" fill="{TINTA}">'
                         f'{brl(s_[i],0)}</text>')
        g.append(f'<text x="{ml+i*slot+slot/2:.1f}" y="{H-9}" text-anchor="middle" fill="{TINTA2}">{m}</text>')
    g.append(f'<line x1="{ml}" x2="{W-10}" y1="{mt+ph}" y2="{mt+ph}" stroke="{TINTA2}"/></svg>')
    return "".join(g)


def grafico_fluxo():
    W, H, ml, mb, mt = 680, 250, 64, 28, 14
    vals = [-VALOR] + [x[4] for x in anos]
    pou = [0] + [x[5] for x in anos]
    passo = nice_step(max(vals) + VALOR, 6)
    vmin = -passo * (int(VALOR / passo) + 1)
    vmax = passo * (int(max(vals) / passo) + 1)
    pw, ph = W - ml - 10, H - mb - mt
    Y = lambda v: mt + ph - (v - vmin) / (vmax - vmin) * ph
    g = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="Segoe UI,Arial" font-size="11">']
    v = vmin
    while v <= vmax + 1:
        g.append(f'<line x1="{ml}" x2="{W-10}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{GRADE}"/>'
                 f'<text x="{ml-7}" y="{Y(v)+4:.1f}" text-anchor="end" fill="{TINTA2}">{fmt_eixo(v)}</text>')
        v += passo
    slot = pw / 26
    bw = slot * 0.36
    for i, (a, b) in enumerate(zip(vals, pou)):
        cx = ml + i * slot + slot / 2
        for j, (vv, cor, nome) in enumerate([(a, "#b42318" if a < 0 else AZUL2, "Energia solar"), (b, AMARELO, "Poupança")]):
            x = cx - bw - 1 + j * (bw + 2)
            y0, y1 = sorted([Y(0), Y(vv)])
            g.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1-y0,1):.1f}" rx="2" fill="{cor}">'
                     f'<title>Ano {i} – {nome}: R$ {brl(vv)}</title></rect>')
        if i % 5 == 0:
            g.append(f'<text x="{cx:.1f}" y="{H-9}" text-anchor="middle" fill="{TINTA2}">{i}</text>')
    g.append(f'<line x1="{ml}" x2="{W-10}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="{TINTA2}"/>'
             f'<text x="{W-10}" y="{Y(vals[-1])-6:.1f}" text-anchor="end" font-weight="700" fill="{TINTA}">{reais_curto(vals[-1])}</text></svg>')
    return "".join(g)


# ---------------- pedacos de HTML ----------------
SEDE = "Sede Mãe do Rio · CNPJ 41.472.680/0001-23 · Rua Bararu, 250, Novo Horizonte, Mãe do Rio – PA, 68675-000"
TEL = "(91) 98469-8653"


def card(icone, valor, rotulo):
    return f'<div class="card">{ico(icone)}<div><div class="v">{valor}</div><div class="l">{rotulo}</div></div></div>'


def titulo(t, sub=""):
    return f'<h1>{t}</h1>' + (f'<p class="sub">{sub}</p>' if sub else "")


PAGINAS = []


def pagina(corpo, classe=""):
    PAGINAS.append((corpo, classe))


def reais_curto(v):
    if abs(v) >= 1_000_000:
        return f"R$ {brl(v/1e6, 1)} milhões"
    return f"R$ {brl(v/1000, 0)} mil"


KWP_TXT = brl(KWP, 0 if KWP >= 100 else 2 if round(KWP * 100) % 10 else 1)
GER_TXT = f"até {brl(round(GER_MAX/1000),0)} mil kWh/mês" if SO_MAX and GER_MAX >= 10000 else \
    (f"até {brl(GER_MAX,0)} kWh/mês" if SO_MAX else f"{brl(media,0)} kWh/mês")
GER_ROT = "Geração no mês de mais sol" if SO_MAX else "Geração média estimada por mês"
ECON_TXT, ECON_ROT = (f"R$ {brl(ECON_ANO1/1000,0)} mil", "Economia estimada no 1º ano") if SO_MAX or ECON_ANO1 > 60000 \
    else (f"R$ {brl(ECON_ANO1/12,0)}", "Economia média por mês no 1º ano")

# --- 1. capa
cli_capa = (f'<div class="cli"><span>Preparada para</span><b>{V["cliente"]}</b><small>{V["cliente_end"]}</small></div>'
            if V["cliente"] else '<div class="cli"><span>Preparada para</span><b>______________________________________</b></div>')
pagina(f"""
  <div class="capa-foto" style="background-image:url('{b64('capa_foto.jpg')}')">
    <div class="capa-veu"></div>
    <img class="capa-logo" src="{b64('logo.jpg')}">
    <div class="capa-tit"><small>PROPOSTA COMERCIAL</small>Usina solar<br>fotovoltaica</div>
  </div>
  <div class="capa-info">
    {cli_capa}
    <div class="tags">
      <span class="tag">{ico('raio','#fff',14)} {KWP_TXT} kWp</span>
      <span class="tag">{ico('painel','#fff',14)} {N_PAINEIS} painéis de {W_PAINEL} W</span>
      <span class="tag">{ico('inversor','#fff',14)} {V['inv_curto']}</span>
      <span class="tag am">{ico('sol',TINTA,14)} {GER_TXT}</span>
    </div>
    <div class="capa-rod"><div><b>Proposta {NUM}</b> · {HOJE:%d/%m/%Y} · válida por 10 dias</div>
    <div><b>MS ENERGY</b> · Tel/WhatsApp {TEL}</div></div>
    <div class="sede">{SEDE}</div>
  </div>""", "capa")

# --- 2. empresa
pagina(f"""
  {titulo('Quem somos', 'MS ENERGY · soluções fotovoltaicas no Pará')}
  <div class="intro"><p>Há quase 10 anos levamos energia solar para casas, comércios, indústrias e propriedades rurais
  do Pará. Cuidamos de tudo: visita técnica, projeto, homologação na Equatorial, instalação e acompanhamento depois da
  entrega. A economia aparece já nas primeiras contas e o sistema dura mais de 25 anos.</p></div>
  <div class="tri">
    <div class="pilar">{ico('sol')}<h3>Visão</h3><p>Ser referência em energia solar no estado do Pará.</p></div>
    <div class="pilar">{ico('escudo')}<h3>Missão</h3><p>Esclarecer todas as dúvidas do cliente, do primeiro contato até depois da entrega.</p></div>
    <div class="pilar">{ico('folha')}<h3>Valores</h3><p>Comprometimento, ética e transparência em cada serviço.</p></div>
  </div>
  <h2>Nossos parceiros</h2><p class="sub">Trabalhamos com marcas de primeira linha.</p>
  <div class="parc"><img src="{b64('parceiros.jpg')}"></div>
  <h2>Algumas instalações</h2>
  <div class="fotos">{''.join(f'<figure><img src="{b64(f"inst{i}.jpg")}"><figcaption>{c}</figcaption></figure>' for i, c in enumerate(["Capitão Poço", "Santa Maria do Pará", "Capitão Poço", "Capitão Poço", "Capitão Poço", "Capitão Poço"]))}</div>
  <div class="contato"><img src="{b64('logo.jpg')}"><div><b>MS ENERGY</b> · CNPJ 37.422.735/0001-13<br>
  Av. Moura Carvalho, 1886, Anexo B, Goiabarana · Capitão Poço – PA, 68650-000<br>
  Tel/WhatsApp: {TEL} · energysolution03@hotmail.com</div></div>
""")

# --- 3. sistema
cli_box = ""
if V["cliente"]:
    cli_box = (f'<div class="clibox"><div><span>Cliente</span><b>{V["cliente"]}</b><small>{V["cliente_end"]}</small></div>'
               f'<div><span>Unidade consumidora</span><b>{V["grupo"]}</b><small>Ligação {V["ligacao"].lower()}</small></div></div>')
cons_col = "" if SO_MAX else f"<th>Consumo (kWh/mês)</th>"
cons_val = "" if SO_MAX else f"<td>{brl(CONSUMO,0)}</td>"
pagina(f"""
  {titulo('Seu sistema solar', 'O que está sendo proposto, em resumo')}
  {cli_box}
  <div class="cards">
    {card('raio', f"{KWP_TXT} kWp", 'Potência instalada')}
    {card('painel', f"{N_PAINEIS} × {W_PAINEL} W", 'Painéis N-type de última geração')}
    {card('inversor', V['inv_curto'], V['inv_card'])}
    {card('sol', GER_TXT.replace(' kWh/mês',' kWh'), GER_ROT)}
    {card('dinheiro', ECON_TXT, ECON_ROT)}
    {card('area', f"≈ {brl(AREA,0)} m²", 'Área de terreno necessária' if V.get('solo') else 'Área necessária para os painéis')}
  </div>
  <h2>Conta de energia considerada</h2>
  <table><tr><th>Unidade</th><th>Ligação</th>{cons_col}<th>Consumo mínimo (kWh)</th><th>Preço do kWh (R$)</th></tr>
  <tr><td>{V['grupo']}</td><td>{V['ligacao']}</td>{cons_val}<td>{MINIMO}</td><td>{brl(TARIFA)} *</td></tr></table>
  <p class="mut">* Valor médio do kWh com impostos. A unidade consumidora fica com 100% do crédito gerado.</p>
  <h2>Por que esta solução?</h2>
  <div class="lista">{''.join(f'<div>{ico("check",AZUL2,18)}<span>{t}</span></div>' for t in V['porque'])}</div>
""")

# --- 4. geracao
if SO_MAX:
    linhas_mes = "".join(f"<tr><td>{m}</td><td>{brl(g,0)}</td><td>R$ {brl(g*TARIFA)}</td></tr>" for m, _c, g, *_r in ano1)
    linhas_mes += (f'<tr class="tot"><td>Ano</td><td>{brl(sum(GER),0)}</td><td>R$ {brl(sum(GER)*TARIFA)}</td></tr>')
    tabela_mes = f"<table><tr><th>Mês</th><th>Geração estimada (kWh)</th><th>Energia gerada em R$ (tarifa de R$ {brl(TARIFA)})</th></tr>{linhas_mes}</table>"
    nota_ger = (f"A geração chega a <b>{brl(GER_MAX,0)} kWh</b> no mês de mais sol e varia ao longo do ano com o clima. "
                "Toda a energia gerada abate a conta do condomínio; o que sobrar vira crédito por até 60 meses.")
    leg = f'<div class="leg"><span><i style="background:{AZUL2}"></i>Geração estimada</span></div>'
else:
    linhas_mes = "".join(
        f"<tr><td>{m}</td><td>{brl(c,0)}</td><td>{brl(g,0)}</td><td>{brl(cr,0)}</td><td>{brl(ac,0)}</td>"
        f"<td>R$ {brl(fs)}</td><td>R$ {brl(fc)}</td></tr>" for m, c, g, cr, ac, fs, fc in ano1)
    linhas_mes += (f'<tr class="tot"><td>Ano</td><td>{brl(CONSUMO*12,0)}</td><td>{brl(sum(GER),0)}</td><td></td>'
                   f'<td>{brl(ano1[-1][4],0)}</td><td>R$ {brl(sum(l[5] for l in ano1))}</td><td>R$ {brl(sum(l[6] for l in ano1))}</td></tr>')
    tabela_mes = ("<table><tr><th>Mês</th><th>Consumo (kWh)</th><th>Geração (kWh)</th><th>Crédito do mês</th>"
                  f"<th>Crédito acumulado</th><th>Fatura sem sistema</th><th>Fatura com sistema</th></tr>{linhas_mes}</table>")
    nota_ger = ("Nos meses de menos sol a conta usa os créditos guardados; sem crédito, paga só a diferença. "
                f"A fatura com sistema inclui o custo mínimo de disponibilidade ({MINIMO} kWh).")
    leg = f'<div class="leg"><span><i style="background:{AMARELO}"></i>Consumo</span><span><i style="background:{AZUL2}"></i>Geração</span></div>'
pagina(f"""
  {titulo('Geração de energia', 'Estimativa mês a mês no 1º ano')}
  <div class="painelg">{grafico_geracao()}{leg}</div>
  {tabela_mes}
  <p class="mut">{nota_ger} Valores estimados; a geração varia com o clima, sombras e a inclinação do local. Não considera a
  cobrança do Fio B prevista na Lei 14.300/2022 nem possíveis cobranças de ICMS sobre a TUSD.</p>
""")

# --- 5. produtos
PAINEL_SVG = ('<svg viewBox="0 0 80 80" width="64" height="64"><rect x="16" y="4" width="48" height="72" rx="2" fill="#1d3557" stroke="#9aa5b1" stroke-width="2"/>'
              + "".join(f'<line x1="16" x2="64" y1="{4+i*12}" y2="{4+i*12}" stroke="#4a6fa5"/>' for i in range(1, 6))
              + '<line x1="32" x2="32" y1="4" y2="76" stroke="#4a6fa5"/><line x1="48" x2="48" y1="4" y2="76" stroke="#4a6fa5"/>'
              + f'<rect x="22" y="33" width="36" height="14" rx="2" fill="#f2a900"/><text x="40" y="43.5" font-size="9" font-weight="700" text-anchor="middle" font-family="Arial" fill="#1f2933">{W_PAINEL}W</text></svg>')


def inv_svg(marca):
    return ('<svg viewBox="0 0 80 80" width="64" height="64"><rect x="14" y="8" width="52" height="64" rx="6" fill="#f4f6f8" stroke="#9aa5b1"/>'
            '<rect x="24" y="20" width="32" height="16" rx="2" fill="#123b57"/><circle cx="40" cy="52" r="7" fill="#f2a900"/>'
            f'<text x="40" y="31" fill="#fff" font-size="9" text-anchor="middle" font-family="Arial">{marca}</text></svg>')


def protecao_svg():
    return ('<svg viewBox="0 0 80 80" width="64" height="64"><rect x="12" y="10" width="56" height="60" rx="4" fill="#f4f6f8" stroke="#9aa5b1"/>'
            + "".join(f'<rect x="{20+i*14}" y="24" width="10" height="26" rx="2" fill="#123b57"/><rect x="{22+i*14}" y="30" width="6" height="8" fill="#f2a900"/>' for i in range(3))
            + '</svg>')


produtos = [(PAINEL_SVG, f"PAINEL SOLAR {W_PAINEL} W MONOCRISTALINO N-TYPE (TOPCon)",
             "Garantia de 30 anos de desempenho · alta eficiência em calor", "PC", N_PAINEIS)]
produtos += [(inv_svg(m), n, d, "PC", q) for q, n, d, m in V["inversores"]]
img_estr = V["estrutura"][2] if len(V["estrutura"]) > 2 else "prod_estrutura.jpg"
produtos += [(f'<img src="{b64(img_estr)}">', V["estrutura"][0], V["estrutura"][1], "KIT", -(-N_PAINEIS // 4))]
produtos += [(protecao_svg(), n, d, u, q) for n, d, u, q in V.get("extras", [])]
produtos += [
    (f'<img src="{b64("prod_cabo_preto.jpg")}">', "CABO SOLAR NEXANS 0,6/1 kV PRETO", "Proteção UV para uso externo", "M", V["cabo_m"]),
    (f'<img src="{b64("prod_cabo_verm.jpg")}">', "CABO SOLAR NEXANS 0,6/1 kV VERMELHO", "Proteção UV para uso externo", "M", V["cabo_m"]),
    (f'<img src="{b64("prod_projeto.jpg")}">', "PROJETO DE ENGENHARIA", "Projeto elétrico, ART e homologação na Equatorial", "SV", 1),
    (f'<img src="{b64("prod_instalacao.jpg")}">', "INSTALAÇÃO", "Equipe própria com NR-10 e NR-35", "SV", 1),
]
linhas_prod = "".join(f'<tr><td class="pimg">{im}</td><td class="pn"><b>{n}</b><br><span class="mut">{d}</span></td>'
                      f'<td>{u}</td><td class="q">{brl(q,0)}</td></tr>' for im, n, d, u, q in produtos)
pagina(f"""
  {titulo('Os produtos', 'Tudo o que está incluso nesta proposta')}
  <table class="prod"><tr><th></th><th style="text-align:left">Produto</th><th>Unid.</th><th>Qtde</th></tr>{linhas_prod}</table>
  <div class="preco"><div><span>Investimento total</span><b>R$ {brl(VALOR)}</b><small>Material, projeto, homologação e instalação inclusos</small></div></div>
""")

# --- 6. retorno
linhas_ret = "".join(
    f'<tr><td class="{"inv" if ac < 0 else "luc"}">{"Investimento" if ac < 0 else "Lucro"}</td><td>{a}</td>'
    f"<td>{brl(t)}</td><td>{brl(g,0)}</td><td>{brl(e)}</td><td>{brl(ac)}</td><td>{brl(p)}</td></tr>"
    for a, t, g, e, ac, p in anos)
pagina(f"""
  {titulo('Retorno do investimento', 'Quanto o sistema devolve ao longo de 25 anos')}
  <div class="cards c3">
    {card('relogio', PB_TXT, 'Payback: tempo para o sistema se pagar')}
    {card('grafico', f"{brl(TIR*100,1)}% a.a.", 'TIR: rentabilidade ao ano')}
    {card('dinheiro', reais_curto(TOTAL_25), 'Resultado acumulado em 25 anos')}
  </div>
  <table class="ret"><tr><th>Status</th><th>Ano</th><th>Tarifa (R$/kWh)</th><th>Geração (kWh/ano)</th><th>Economia no ano (R$)</th><th>Acumulado (R$)</th><th>Se ficasse na poupança (R$)</th></tr>
  {linhas_ret}</table>
  <p class="mut">Reajuste da tarifa: {brl(INFLA*100,0)}% ao ano · Painéis: perda de 1% no 1º ano e 0,4% ao ano depois, conforme fabricante ·
  Poupança: {brl(POUP*100,2)}% ao ano sobre os mesmos R$ {brl(VALOR)} · VPL (taxa de {brl(DESCONTO*100,0)}% a.a.): R$ {brl(VPL)}.</p>
""")

# --- 7. fluxo + ambiental
pagina(f"""
  {titulo('Energia solar x poupança', 'Resultado acumulado ano a ano com o mesmo dinheiro')}
  <div class="painelg">{grafico_fluxo()}
  <div class="leg"><span><i style="background:#b42318"></i>Investimento</span><span><i style="background:{AZUL2}"></i>Energia solar</span><span><i style="background:{AMARELO}"></i>Poupança</span></div></div>
  <div class="destaque">Em 25 anos a energia solar rende <b>{reais_curto(TOTAL_25)}</b>; o mesmo dinheiro na poupança renderia
  <b>{reais_curto(anos[-1][5])}</b>. São <b>{brl(TOTAL_25/max(anos[-1][5],1),0)} vezes</b> mais.</div>
  <h2>Retorno ambiental em 25 anos</h2>
  <div class="cards c3 verde">
    {card('nuvem', f"{brl(CO2,0)} t", 'de CO₂ que deixam de ser emitidas')}
    {card('arvore', brl(ARVORES,0), 'árvores seriam necessárias para retirar esse CO₂')}
    {card('folha', f"{brl(MWH_25,0)} MWh", 'de energia limpa gerada no período')}
  </div>
""")

# --- 8. etapas + condicoes + assinatura
etapas = [("Visita técnica", "Medição do local e confirmação do projeto"), ("Projeto e ART", "Engenharia elétrica e documentação"),
          ("Homologação", "Pedido de acesso na Equatorial"), ("Instalação", "Montagem por equipe própria"),
          ("Ligação", "Vistoria, troca do medidor e geração")]
linha_et = "".join(f'<div class="et"><div class="num">{i+1}</div><b>{t}</b><span>{d}</span></div>' for i, (t, d) in enumerate(etapas))
nao_cob = ["Obras civis (parede, reboco etc.)", "Adequação do padrão de entrada de energia", "Taxa mínima da concessionária"]
if V.get("solo"):
    nao_cob[0] = "Limpeza, terraplenagem e cerca do terreno"
if KWP > 75:
    nao_cob.append("Adequações exigidas pela Equatorial para minigeração (acima de 75 kW), se houver")
assin_cli = V["cliente"] or "CLIENTE"
pagina(f"""
  {titulo('Como funciona', 'Do contrato à energia gerada')}
  <div class="etapas">{linha_et}</div>
  <div class="duas">
    <div class="box"><h3>{ico('relogio',AZUL2,18)} Prazo de entrega</h3>Até 60 dias após a assinatura, incluindo a homologação na concessionária.</div>
    <div class="box"><h3>{ico('dinheiro',AZUL2,18)} Formas de pagamento</h3>À vista · financiamento em até 84× · cartão em até 18×
    <img src="{b64('bancos.jpg')}" class="bancos"></div>
    <div class="box"><h3>{ico('escudo',AZUL2,18)} Garantias</h3><ul><li>Painéis: 30 anos de desempenho (fabricante)</li>
    <li>{V['inv_garantia']}</li><li>Instalação: 1 ano</li></ul></div>
    <div class="box"><h3>{ico('area',AZUL2,18)} Não incluso</h3><ul>{''.join(f'<li>{t}</li>' for t in nao_cob)}</ul></div>
  </div>
  <p class="aceite">Estando de acordo com os produtos, valores e termos desta proposta, MS ENERGY e o(a) cliente firmam a proposta.</p>
  <div class="ass"><div>FREDSON ANDERSON TEIXEIRA MOTA<br><small>MS ENERGY · CNPJ 37.422.735/0001-13</small></div>
  <div>{assin_cli}<br><small>{V['cliente_doc'] or 'CPF/CNPJ: ____________________'}</small></div></div>
  <p class="mut" style="margin-top:6mm">Local e data: ______________________, ____/____/______</p>
""")

TOTAL_PAG = len(PAGINAS)
corpo = ""
for i, (c, classe) in enumerate(PAGINAS, 1):
    rod = "" if classe == "capa" else (
        f'<div class="topo"><img src="{b64("logo.jpg")}"><span>Proposta {NUM}</span></div>'
        f'<div class="rod">MS ENERGY · Tel/WhatsApp {TEL} · página {i} de {TOTAL_PAG}<div class="sede">{SEDE}</div></div>')
    corpo += f'<section class="pg {classe}">{rod}{c}</section>'

CSS = f"""
@page {{ size: A4; margin: 0 }}
* {{ box-sizing: border-box }}
body {{ margin:0; font-family:'Segoe UI',Calibri,Arial,sans-serif; color:{TINTA}; font-size:10pt; background:#fff }}
.pg {{ width:210mm; height:297mm; position:relative; padding:26mm 16mm 20mm; page-break-after:always; overflow:hidden }}
.pg:last-child {{ page-break-after:auto }}
.topo {{ position:absolute; top:0; left:0; right:0; height:16mm; padding:0 16mm; display:flex; align-items:center;
  justify-content:space-between; border-bottom:3px solid {AMARELO}; background:linear-gradient(90deg,#fff 60%,#fdf6e3) }}
.topo img {{ height:10mm }} .topo span {{ font-size:8.5pt; color:{TINTA2}; letter-spacing:.06em; text-transform:uppercase }}
h1 {{ font-size:23pt; font-weight:700; margin:0 0 1mm; color:{AZUL}; letter-spacing:-.01em }}
h1:after {{ content:''; display:block; width:16mm; height:3px; background:{AMARELO}; border-radius:2px; margin-top:2mm }}
h2 {{ font-size:13pt; font-weight:700; margin:6mm 0 2.5mm; color:{AZUL} }}
h3 {{ margin:0 0 1.5mm; font-size:10.5pt; color:{AZUL}; display:flex; align-items:center; gap:2mm }}
.sub {{ color:{TINTA2}; margin:1mm 0 5mm }}
.mut {{ color:{TINTA2}; font-size:8.3pt; line-height:1.45 }}
.rod {{ position:absolute; bottom:7mm; left:16mm; right:16mm; border-top:1px solid {GRADE}; padding-top:2mm; font-size:7.8pt; color:{TINTA2}; text-align:center }}
.sede {{ font-size:6.3pt; color:#a8b2bd; margin-top:.8mm }}
table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:9pt; border-radius:6px; overflow:hidden; border:1px solid {GRADE} }}
th {{ background:{AZUL}; color:#fff; font-weight:600; padding:2mm; text-align:center; font-size:8.6pt }}
td {{ padding:1.5mm 2mm; border-bottom:1px solid {GRADE}; text-align:center }}
tr:nth-child(odd) td {{ background:#fafbfc }}
tr:last-child td {{ border-bottom:0 }}
tr.tot td {{ font-weight:700; background:#fdf3d6 !important }}
.cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3.5mm; margin:3mm 0 }}
.card {{ background:{FUNDO}; border-radius:8px; padding:4mm; display:flex; gap:3mm; align-items:flex-start; border:1px solid #e9eef2 }}
.card svg {{ flex:none; margin-top:1mm }}
.card .v {{ font-size:15pt; font-weight:700; color:{AZUL}; line-height:1.15 }}
.card .l {{ font-size:8.4pt; color:{TINTA2}; margin-top:.8mm }}
.verde .card {{ background:#eef7f0; border-color:#dcefe0 }} .verde .card .v {{ color:#1a7f37 }} .verde svg {{ color:#1a7f37 !important }}
.leg {{ font-size:8.5pt; color:{TINTA2}; display:flex; gap:6mm; justify-content:center; margin-top:1mm }}
.leg i {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:4px; vertical-align:-1px }}
.painelg {{ border:1px solid {GRADE}; border-radius:8px; padding:3mm 3mm 2mm; margin-bottom:4mm }}
/* capa */
.capa {{ padding:0 }}
.capa-foto {{ height:178mm; background-size:cover; background-position:center 40%; position:relative }}
.capa-veu {{ position:absolute; inset:0; background:linear-gradient(180deg,rgba(18,59,87,.88) 0%,rgba(18,59,87,.55) 38%,rgba(18,59,87,0) 62%) }}
.capa-logo {{ position:absolute; top:12mm; right:14mm; height:20mm; background:#fff; border-radius:8px; padding:2mm 3mm }}
.capa-tit {{ position:absolute; top:22mm; left:16mm; color:#fff; font-size:38pt; font-weight:700; line-height:1.02; letter-spacing:-.02em }}
.capa-tit small {{ display:block; font-size:11pt; letter-spacing:.25em; font-weight:600; color:{AMARELO}; margin-bottom:4mm }}
.capa-info {{ position:relative; margin-top:-14mm; background:#fff; border-radius:14px 14px 0 0; padding:9mm 16mm 0; height:133mm }}
.cli span {{ display:block; font-size:8.5pt; letter-spacing:.15em; text-transform:uppercase; color:{TINTA2} }}
.cli b {{ display:block; font-size:17pt; color:{AZUL}; margin:1mm 0 }} .cli small {{ color:{TINTA2}; font-size:9pt }}
.tags {{ display:flex; flex-wrap:wrap; gap:2.5mm; margin:7mm 0 }}
.tag {{ display:inline-flex; align-items:center; gap:2mm; background:{AZUL}; color:#fff; border-radius:30px; padding:2.2mm 4.5mm; font-weight:600; font-size:10pt }}
.tag.am {{ background:{AMARELO}; color:{TINTA} }}
.capa-rod {{ position:absolute; left:16mm; right:16mm; bottom:16mm; display:flex; justify-content:space-between; font-size:9.5pt;
  border-top:1px solid {GRADE}; padding-top:3mm; color:{TINTA2} }}
.capa .sede {{ position:absolute; bottom:8mm; left:16mm; right:16mm; text-align:center }}
/* empresa */
.intro p {{ font-size:10.5pt; line-height:1.55; margin:0 }}
.tri {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3.5mm; margin-top:5mm }}
.pilar {{ background:{FUNDO}; border-radius:8px; padding:4mm; border-top:3px solid {AMARELO} }} .pilar h3 {{ margin-top:2mm }} .pilar p {{ margin:0; font-size:9pt; color:{TINTA2} }}
.parc img {{ width:125mm }}
.fotos {{ display:grid; grid-template-columns:repeat(3,1fr); gap:2.5mm }}
figure {{ margin:0; position:relative }} figure img {{ width:100%; height:36mm; object-fit:cover; border-radius:6px; display:block }}
figcaption {{ position:absolute; left:2mm; bottom:2mm; background:rgba(18,59,87,.85); color:#fff; font-size:7.5pt; padding:.6mm 2mm; border-radius:3px }}
.contato {{ display:flex; gap:5mm; align-items:center; margin-top:5mm; background:{FUNDO}; border-radius:8px; padding:3mm 5mm; font-size:9pt; line-height:1.5 }}
.contato img {{ height:16mm }}
/* sistema */
.clibox {{ display:grid; grid-template-columns:1.6fr 1fr; gap:3.5mm; margin-bottom:2mm }}
.clibox div {{ border:1px solid {GRADE}; border-left:4px solid {AZUL2}; border-radius:6px; padding:3mm 4mm }}
.clibox span {{ display:block; font-size:7.8pt; text-transform:uppercase; letter-spacing:.1em; color:{TINTA2} }}
.clibox b {{ display:block; font-size:11pt; color:{AZUL}; margin:.6mm 0 }} .clibox small {{ font-size:8.5pt; color:{TINTA2} }}
.lista div {{ display:flex; gap:3mm; align-items:flex-start; padding:2mm 0; border-bottom:1px dashed {GRADE}; font-size:9.6pt }}
.lista svg {{ flex:none }}
/* produtos */
.prod td {{ padding:2mm }} .pimg {{ width:26mm }} .pimg img {{ max-width:22mm; max-height:17mm; border-radius:4px }}
td.pn {{ text-align:left }} td.q {{ font-size:13pt; font-weight:700; color:{AZUL} }}
.preco {{ margin-top:6mm; display:flex; justify-content:flex-end }}
.preco div {{ background:linear-gradient(135deg,{AZUL},{AZUL2}); color:#fff; border-radius:10px; padding:5mm 9mm; text-align:right; border-bottom:4px solid {AMARELO} }}
.preco span {{ font-size:9pt; letter-spacing:.12em; text-transform:uppercase; opacity:.85 }}
.preco b {{ font-size:26pt; display:block; margin:1mm 0 }} .preco small {{ font-size:8.5pt; opacity:.85 }}
/* retorno */
.c3 {{ grid-template-columns:repeat(3,1fr) }}
td.inv {{ color:#b42318; font-weight:600 }} td.luc {{ color:#1a7f37; font-weight:600 }}
.ret td {{ padding:.75mm 1.5mm; font-size:8.2pt }}
.destaque {{ background:#fdf3d6; border-left:4px solid {AMARELO}; border-radius:6px; padding:4mm 5mm; font-size:10.5pt; margin:2mm 0 }}
/* etapas */
.etapas {{ display:grid; grid-template-columns:repeat(5,1fr); gap:2mm; margin:4mm 0 6mm; position:relative }}
.etapas:before {{ content:''; position:absolute; top:5.5mm; left:10%; right:10%; height:2px; background:{AMARELO} }}
.et {{ text-align:center; position:relative; font-size:8.3pt; color:{TINTA2} }}
.et .num {{ width:11mm; height:11mm; border-radius:50%; background:{AZUL}; color:#fff; font-weight:700; font-size:12pt;
  display:flex; align-items:center; justify-content:center; margin:0 auto 2mm; border:3px solid #fff; box-shadow:0 0 0 2px {AMARELO} }}
.et b {{ display:block; color:{AZUL}; font-size:9.3pt; margin-bottom:.5mm }}
.duas {{ display:grid; grid-template-columns:1fr 1fr; gap:3.5mm }}
.box {{ background:{FUNDO}; border-radius:8px; padding:3.5mm 4.5mm; font-size:9pt }}
.box ul {{ margin:0; padding-left:4.5mm }} .bancos {{ width:100%; margin-top:2.5mm }}
.aceite {{ margin-top:6mm; font-size:9.5pt }}
.ass {{ display:flex; gap:12mm; margin-top:16mm }} .ass div {{ flex:1; border-top:1.5px solid {TINTA}; padding-top:2mm; text-align:center; font-size:9pt; font-weight:600 }}
.ass small {{ font-weight:400; color:{TINTA2} }}
"""

html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{corpo}</body></html>'
with open(os.path.join(AQUI, f"proposta_{CHAVE}.html"), "w", encoding="utf-8") as f:
    f.write(html)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.set_content(html, wait_until="load")
    pg.pdf(path=SAIDA, format="A4", print_background=True, prefer_css_page_size=True)
    b.close()
print(SAIDA)
print(f"{TOTAL_PAG} pag | {KWP} kWp | ger max {GER_MAX} | payback {PB_TXT} | TIR {TIR*100:.1f}% | 25 anos {TOTAL_25:.0f} | econ ano1 {ECON_ANO1:.0f}")
