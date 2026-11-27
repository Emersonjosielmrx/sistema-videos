# /opt/orcamentos-ms/servidor/motor.py
"""Motor da proposta MS Energy: dimensionamento, preço, retorno financeiro e HTML (A4) da proposta.

Porte em forma de função do gerador original D:\\ms-energy\\propostas\\gerar_proposta.py (mesmas contas e
mesmo layout). Entrada: um dicionário `d` (o orçamento que o vendedor preencheu) e `cfg` (configuração da
empresa: preços, catálogo, financeiras). Saída: html completo da proposta + resumo numérico.
"""
import base64
import datetime
import html as _h
import math
import os

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
# perfil mensal de sol da região (mesma base das propostas feitas à mão: 7,5 kWp -> 1.000 kWh/mês)
PERFIL = [491, 491, 497, 515, 537, 567, 580, 603, 606, 587, 571, 525]
AZUL, AZUL2, AMARELO, TINTA, TINTA2, GRADE, FUNDO = "#123b57", "#1d5a80", "#f2a900", "#1f2933", "#52606d", "#e4e7eb", "#f4f7f9"
_cache = {}

# ----------------------------------------------------------------------------- configuração padrão
CONFIG_PADRAO = {
    "empresa": {
        "nome": "MS ENERGY",
        "cnpj": "37.422.735/0001-13",
        "endereco": "Av. Moura Carvalho, 1886, Anexo B, Goiabarana · Capitão Poço – PA, 68650-000",
        "sede": "Sede Mãe do Rio · CNPJ 41.472.680/0001-23 · Rua Bararu, 250, Novo Horizonte, Mãe do Rio – PA, 68675-000",
        "telefone": "(91) 98469-8653",
        "email": "energysolution03@hotmail.com",
        "responsavel": "FREDSON ANDERSON TEIXEIRA MOTA",
        "validade_dias": 10,
        "prazo_entrega": "Até 60 dias após a assinatura, incluindo a homologação na concessionária.",
        "garantia_instalacao": "1 ano",
    },
    "calculo": {
        "kwh_por_kwp_mes": 133.3333,  # 7,5 kWp -> 1.000 kWh/mês
        "tarifa": 1.10,              # R$/kWh com impostos
        "reajuste_tarifa": 0.04,
        "poupanca": 0.0617,
        "taxa_vpl": 0.10,
        "degrad1": 0.01,
        "degrad": 0.004,
        "co2_t_por_mwh": 0.29,
        "minimo_mono": 30, "minimo_bi": 50, "minimo_tri": 100,
    },
    "preco": {
        # preço do solar = fixo + por kWp (calibrado nas propostas: 3,75 kWp = 13.900; 7,5 kWp = 22.900)
        "fixo": 4900.0,
        "por_kwp": 2400.0,
        "adicional_hibrido": 3000.0,
        "adicional_micro": 0.0,
        "adicional_solo_por_kwp": 600.0,
        "arredondar": 100,
        "desconto_max_vendedor_pct": 5.0,
    },
    "paineis": [
        {"id": "p625", "nome": "PAINEL SOLAR 625 W MONOCRISTALINO N-TYPE (TOPCon)", "w": 625,
         "desc": "Garantia de 30 anos de desempenho · alta eficiência em calor"},
        {"id": "p610", "nome": "PAINEL SOLAR 610 W MONOCRISTALINO N-TYPE (TOPCon)", "w": 610,
         "desc": "Garantia de 30 anos de desempenho · alta eficiência em calor"},
        {"id": "p585", "nome": "PAINEL SOLAR 585 W MONOCRISTALINO N-TYPE", "w": 585,
         "desc": "Garantia de 30 anos de desempenho"},
        {"id": "p700", "nome": "PAINEL SOLAR 700 W BIFACIAL N-TYPE (HJT)", "w": 700,
         "desc": "Bifacial: gera também pela parte de trás · garantia de 30 anos"},
    ],
    "inversores": [
        {"id": "solis3", "nome": "INVERSOR SOLAR SOLIS 3 kW MONOFÁSICO", "curto": "Solis 3 kW", "marca": "SOLIS", "kw": 3, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis4", "nome": "INVERSOR SOLAR SOLIS 4 kW", "curto": "Solis 4 kW", "marca": "SOLIS", "kw": 4, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis5", "nome": "INVERSOR SOLAR SOLIS 5 kW", "curto": "Solis 5 kW", "marca": "SOLIS", "kw": 5, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis6", "nome": "INVERSOR SOLAR SOLIS 6 kW", "curto": "Solis 6 kW", "marca": "SOLIS", "kw": 6, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis7", "nome": "INVERSOR SOLAR SOLIS 7 kW", "curto": "Solis 7 kW", "marca": "SOLIS", "kw": 7, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis8", "nome": "INVERSOR SOLAR SOLIS 8 kW", "curto": "Solis 8 kW", "marca": "SOLIS", "kw": 8, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis10", "nome": "INVERSOR SOLAR SOLIS 10 kW", "curto": "Solis 10 kW", "marca": "SOLIS", "kw": 10, "tipo": "ongrid",
         "desc": "Ligação 220 V · 2 MPPT · monitoramento Wi-Fi pelo celular", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis15", "nome": "INVERSOR SOLAR SOLIS 15 kW TRIFÁSICO", "curto": "Solis 15 kW", "marca": "SOLIS", "kw": 15, "tipo": "ongrid",
         "desc": "Ligação trifásica · 2 MPPT · monitoramento Wi-Fi", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis20", "nome": "INVERSOR SOLAR SOLIS 20 kW TRIFÁSICO", "curto": "Solis 20 kW", "marca": "SOLIS", "kw": 20, "tipo": "ongrid",
         "desc": "Ligação trifásica · 2 MPPT · monitoramento Wi-Fi", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis30", "nome": "INVERSOR SOLAR SOLIS 30 kW TRIFÁSICO", "curto": "Solis 30 kW", "marca": "SOLIS", "kw": 30, "tipo": "ongrid",
         "desc": "Uso comercial · vários MPPT · monitoramento remoto", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "solis60", "nome": "INVERSOR SOLAR SOLIS 60 kW TRIFÁSICO", "curto": "Solis 60 kW", "marca": "SOLIS", "kw": 60, "tipo": "ongrid",
         "desc": "Uso comercial · vários MPPT · monitoramento remoto 24 h", "garantia": "Inversor Solis: 10 anos (conforme fabricante)"},
        {"id": "deyemicro", "nome": "MICROINVERSOR DEYE 2,25 kW (SUN-M2250G4)", "curto": "Micro Deye 2,25 kW", "marca": "DEYE", "kw": 2.25, "tipo": "micro",
         "desc": "4 entradas, uma por painel · monitoramento Wi-Fi pelo celular", "garantia": "Microinversor Deye: conforme garantia do fabricante"},
        {"id": "deyeh5", "nome": "INVERSOR HÍBRIDO DEYE 5 kW (SUN-5K-SG)", "curto": "Híbrido Deye 5 kW", "marca": "DEYE", "kw": 5, "tipo": "hibrido",
         "desc": "Funciona ligado à rede e com bateria · backup automático na falta de energia · Wi-Fi", "garantia": "Inversor híbrido Deye: conforme garantia do fabricante"},
        {"id": "deyeh8", "nome": "INVERSOR HÍBRIDO DEYE 8 kW (SUN-8K-SG)", "curto": "Híbrido Deye 8 kW", "marca": "DEYE", "kw": 8, "tipo": "hibrido",
         "desc": "Funciona ligado à rede e com bateria · backup automático na falta de energia · Wi-Fi", "garantia": "Inversor híbrido Deye: conforme garantia do fabricante"},
        {"id": "deyeh12", "nome": "INVERSOR HÍBRIDO DEYE 12 kW TRIFÁSICO", "curto": "Híbrido Deye 12 kW", "marca": "DEYE", "kw": 12, "tipo": "hibrido",
         "desc": "Rede + bateria · backup automático · trifásico · Wi-Fi", "garantia": "Inversor híbrido Deye: conforme garantia do fabricante"},
    ],
    "estruturas": [
        {"id": "ceramico", "nome": "ESTRUTURA TELHADO CERÂMICO P/ 4 PAINÉIS", "desc": "Alumínio e inox, à prova de corrosão", "img": "prod_estrutura.jpg"},
        {"id": "fibrocimento", "nome": "ESTRUTURA TELHADO FIBROCIMENTO P/ 4 PAINÉIS", "desc": "Alumínio e inox, fixação em madeira ou metal", "img": "prod_estrutura.jpg"},
        {"id": "metalico", "nome": "ESTRUTURA TELHADO METÁLICO P/ 4 PAINÉIS", "desc": "Perfil de alumínio sobre telha metálica · vedação inclusa", "img": "prod_estrutura.jpg"},
        {"id": "laje", "nome": "ESTRUTURA PARA LAJE P/ 4 PAINÉIS", "desc": "Triângulos de alumínio com a inclinação ideal", "img": "prod_estrutura.jpg"},
        {"id": "solo", "nome": "ESTRUTURA DE SOLO (MESA) P/ 4 PAINÉIS", "desc": "Alumínio e aço galvanizado · fundação em estacas de concreto inclusa", "img": "inst3.jpg"},
    ],
    # itens opcionais que o vendedor pode somar (preço = quanto entra no valor da proposta)
    "extras": [
        {"id": "ar9", "nome": "AR-CONDICIONADO SPLIT INVERTER 9.000 BTUs", "desc": "Instalação inclusa · tecnologia inverter, gasta menos energia", "unid": "PC", "icone": "ar", "preco": 3500.0},
        {"id": "ar12", "nome": "AR-CONDICIONADO SPLIT INVERTER 12.000 BTUs", "desc": "Instalação inclusa · tecnologia inverter, gasta menos energia", "unid": "PC", "icone": "ar", "preco": 4000.0},
        {"id": "ar18", "nome": "AR-CONDICIONADO SPLIT INVERTER 18.000 BTUs", "desc": "Instalação inclusa · tecnologia inverter, gasta menos energia", "unid": "PC", "icone": "ar", "preco": 5200.0},
        {"id": "ar24", "nome": "AR-CONDICIONADO SPLIT INVERTER 24.000 BTUs", "desc": "Instalação inclusa · tecnologia inverter, gasta menos energia", "unid": "PC", "icone": "ar", "preco": 6500.0},
        {"id": "poste", "nome": "POSTE DE ALUMÍNIO PARA PADRÃO DE ENTRADA", "desc": "Leve, não enferruja · instalação inclusa", "unid": "PC", "icone": "poste", "preco": 1800.0},
        {"id": "padrao", "nome": "ADEQUAÇÃO DO PADRÃO DE ENTRADA", "desc": "Caixa de medição, disjuntor e aterramento conforme a Equatorial", "unid": "SV", "icone": "protecao", "preco": 1500.0},
        {"id": "stringbox", "nome": "STRING BOX / PROTEÇÕES CC E CA", "desc": "Disjuntores, DPS e chaves seccionadoras dimensionados no projeto", "unid": "CJ", "icone": "protecao", "preco": 900.0},
        {"id": "carregador", "nome": "CARREGADOR VEICULAR 7 kW (WALLBOX)", "desc": "Carrega o carro elétrico em casa · instalação inclusa", "unid": "PC", "icone": "carro", "preco": 5900.0},
        {"id": "limpeza", "nome": "PLANO DE LIMPEZA E MANUTENÇÃO (1 ANO)", "desc": "2 limpezas dos painéis e revisão elétrica no ano", "unid": "SV", "icone": "limpeza", "preco": 600.0},
        {"id": "monitor", "nome": "MONITORAMENTO PREMIUM (1 ANO)", "desc": "Acompanhamento da geração pela equipe e aviso de falhas", "unid": "SV", "icone": "monitor", "preco": 480.0},
    ],
    # baterias (para sistema híbrido); entram como OPÇÃO de preço na proposta
    "baterias": [
        {"id": "mb48314", "rotulo": "Com bateria MB48314", "nome": "BATERIA DE LÍTIO MB48314 (48 V)", "desc": "Lítio LiFePO4 · guarda a energia do sol para a noite e para quedas de energia", "preco": 24900.0},
        {"id": "basica5", "rotulo": "Com bateria básica 5 kWh", "nome": "BATERIA DE LÍTIO 48 V 100 Ah (5 kWh) – BÁSICA",
         "desc": "Lítio LiFePO4 · a menor que o inversor aceita · mantém geladeira, lâmpadas, TV e internet por cerca de 8 a 10 horas na falta de luz (não segura ar-condicionado)",
         "preco": 8900.0},
        {"id": "lit10", "rotulo": "Com bateria 10 kWh", "nome": "BATERIA DE LÍTIO 48 V 200 Ah (10 kWh)", "desc": "Lítio LiFePO4 · segura a casa quase toda por uma noite (sem ar-condicionado ligado o tempo todo)", "preco": 16900.0},
    ],
    "financeiras": [
        {"id": "solfacil", "nome": "Solfácil – Financiamento Solar", "prazo": 120, "taxa": 0.0215, "carencia": 6, "obs": "Pelo portal do integrador · sem conta em banco", "ativo": True},
        {"id": "bv", "nome": "BV – Meu Financiamento Solar", "prazo": 96, "taxa": 0.0219, "carencia": 4, "obs": "Pelo portal do integrador · sem conta em banco", "ativo": True},
        {"id": "santander", "nome": "Santander – CDC Socioambiental", "prazo": 96, "taxa": 0.0229, "carencia": 4, "obs": "Pelo portal do parceiro · sem conta em banco", "ativo": True},
        {"id": "basa", "nome": "Banco da Amazônia – FNO Energia Verde PF", "prazo": 120, "taxa": 0.0115, "carencia": 6, "obs": "Recurso FNO da Região Norte · exige conta no BASA", "ativo": False},
        {"id": "sicredi", "nome": "Sicredi – Crédito Energia Solar", "prazo": 120, "taxa": 0.0175, "carencia": 6, "obs": "Exige ser associado(a) da cooperativa", "ativo": False},
        {"id": "bb", "nome": "Banco do Brasil – BB Crédito Energia Renovável", "prazo": 96, "taxa": 0.0199, "carencia": 6, "obs": "Exige conta no BB", "ativo": False},
    ],
    "pagamento": {
        "avista": {"ativo": True, "desconto_pct": 5.0},
        "direto": {"ativo": True, "pct1": 50, "n1": 21, "boleto_n": 3, "cartao_n": 12},
        "cartao": {"ativo": False, "n": 18, "juros_am": 0.0199},
        "entrada": {"ativo": False, "pct": 30},
        "financiamento": {"ativo": True, "prazos_tabela": [24, 36, 48, 60, 72, 84, 96, 120], "margem_pct": 10.0},
    },
}


# ----------------------------------------------------------------------------- utilidades
def brl(v, casas=2):
    s = f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s


def esc(t):
    return _h.escape(str(t or ""))


def b64(nome):
    if nome not in _cache:
        caminho = os.path.join(IMG, nome)
        if not os.path.exists(caminho):
            caminho = os.path.join(IMG, "prod_estrutura.jpg")
        with open(caminho, "rb") as f:
            _cache[nome] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    return _cache[nome]


def pmt(pv, i, n):
    return pv * i / (1 - (1 + i) ** -n) if i else pv / n


def achar(lista, _id, padrao=None):
    for x in lista:
        if x.get("id") == _id:
            return x
    return padrao


def mesclar(base, novo):
    """Mescla dicionários em profundidade (config salva por cima do padrão)."""
    out = dict(base)
    for k, v in (novo or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = mesclar(out[k], v)
        else:
            out[k] = v
    return out


def kwp_txt(kwp):
    if kwp >= 100 or kwp == int(kwp):
        return brl(kwp, 0)
    if round(kwp * 1000) % 10:
        return brl(kwp, 3)
    if round(kwp * 100) % 10:
        return brl(kwp, 2)
    return brl(kwp, 1)


def validar_cpf_cnpj(doc):
    n = "".join(c for c in str(doc or "") if c.isdigit())
    if len(n) == 11:
        if n == n[0] * 11:
            return False
        for t in (9, 10):
            s = sum(int(n[i]) * (t + 1 - i) for i in range(t))
            if (s * 10 % 11) % 10 != int(n[t]):
                return False
        return True
    if len(n) == 14:
        if n == n[0] * 14:
            return False
        for t, pesos in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]), (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
            s = sum(int(n[i]) * pesos[i] for i in range(t))
            r = s % 11
            if (0 if r < 2 else 11 - r) != int(n[t]):
                return False
        return True
    return False


def fmt_doc(doc):
    n = "".join(c for c in str(doc or "") if c.isdigit())
    if len(n) == 11:
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return str(doc or "")


# ----------------------------------------------------------------------------- dimensionamento e preço
def com_fator(v, fator):
    """Preço de catálogo com o acréscimo oculto do vendedor (arredonda para cima em R$ 10)."""
    v = float(v or 0)
    return v if abs(fator - 1) < 1e-9 else math.ceil(v * fator / 10) * 10


def dimensionar(d, cfg, fator=1.0):
    """Completa o orçamento `d` com o que é automático (painéis, inversor, preço...) e devolve uma cópia.
    `fator` = 1 + acréscimo oculto do vendedor dono do orçamento (vem do banco, nunca dos dados)."""
    d = dict(d or {})
    calc = cfg["calculo"]
    consumo = float(d.get("consumo") or 0)
    if not consumo and d.get("conta_rs"):
        consumo = float(d["conta_rs"]) / float(d.get("tarifa") or calc["tarifa"])
    consumo = max(consumo, 50.0)
    d["consumo"] = round(consumo)
    tipo = d.get("tipo") or "ongrid"
    d["tipo"] = tipo
    painel = achar(cfg["paineis"], d.get("painel_id")) or cfg["paineis"][0]
    d["painel_id"] = painel["id"]
    folga = float(d.get("folga_pct") or 0) / 100
    alvo_kwp = consumo * (1 + folga) / float(calc["kwh_por_kwp_mes"])
    n_auto = max(1, math.ceil(round(alvo_kwp * 1000 / painel["w"], 3)))
    n = int(d.get("n_paineis") or 0) if d.get("n_manual") else 0
    d["n_paineis"] = n or n_auto
    d["n_auto"] = n_auto
    kwp = d["n_paineis"] * painel["w"] / 1000
    # inversor: o menor do tipo com kW >= kWp/1,3 (ou o escolhido à mão)
    if tipo == "micro":
        micro = achar(cfg["inversores"], "deyemicro") or cfg["inversores"][0]
        inv = achar(cfg["inversores"], d.get("inversor_id")) if d.get("inv_manual") else micro
        qtd_inv = max(1, math.ceil(d["n_paineis"] / 4)) if inv and inv.get("tipo") == "micro" else 1
    else:
        candidatos = sorted([i for i in cfg["inversores"] if i.get("tipo") == tipo], key=lambda i: i["kw"])
        if not candidatos:
            candidatos = sorted([i for i in cfg["inversores"] if i.get("tipo") == "ongrid"], key=lambda i: i["kw"])
        escolha = next((i for i in candidatos if i["kw"] >= kwp / 1.3), None)
        qtd_inv = 1
        if not escolha:  # sistema grande: vários do maior
            escolha = candidatos[-1]
            qtd_inv = math.ceil(kwp / 1.3 / escolha["kw"])
        inv = achar(cfg["inversores"], d.get("inversor_id")) if d.get("inv_manual") else escolha
        inv = inv or escolha
        if d.get("inv_manual") and d.get("qtd_inversor"):
            qtd_inv = int(d["qtd_inversor"])
    d["inversor_id"] = inv["id"]
    d["qtd_inversor"] = qtd_inv
    d["estrutura_id"] = d.get("estrutura_id") or "ceramico"
    lig = d.get("ligacao") or ("Trifásico" if kwp > 12 else "Bifásico")
    d["ligacao"] = lig
    if not d.get("minimo_manual"):
        d["minimo"] = calc["minimo_tri"] if lig.startswith("Tri") else calc["minimo_mono"] if lig.startswith("Mono") else calc["minimo_bi"]
    d["tarifa"] = float(d.get("tarifa") or calc["tarifa"])
    d["grupo"] = d.get("grupo") or "Grupo B1 – Residencial"
    d["cabo_m"] = int(d.get("cabo_m") or min(600, max(20, round((10 + d["n_paineis"] * 3) / 10) * 10)))
    # preço sugerido
    p = cfg["preco"]
    base = p["fixo"] + p["por_kwp"] * kwp
    if tipo == "hibrido":
        base += p["adicional_hibrido"]
    if tipo == "micro":
        base += p["adicional_micro"]
    if d["estrutura_id"] == "solo":
        base += p["adicional_solo_por_kwp"] * kwp
    arr = p.get("arredondar") or 1
    base = math.ceil(base * fator / arr) * arr
    extras_total = 0.0
    itens = []
    for e in d.get("extras") or []:
        cat = achar(cfg["extras"], e.get("id")) or {}
        qtd = int(e.get("qtd") or 1)
        preco_un = float(e["preco"]) if e.get("preco") not in (None, "") else com_fator(cat.get("preco"), fator)
        nome = e.get("nome") or cat.get("nome") or "ITEM"
        itens.append({"id": e.get("id"), "nome": nome, "desc": e.get("desc") or cat.get("desc", ""),
                      "unid": e.get("unid") or cat.get("unid", "PC"), "icone": e.get("icone") or cat.get("icone", "protecao"),
                      "qtd": qtd, "preco": preco_un, "no_valor": e.get("no_valor", True)})
        if e.get("no_valor", True):
            extras_total += preco_un * qtd
    d["extras"] = itens
    d["preco_solar"] = base
    d["preco_extras"] = extras_total
    d["preco_sugerido"] = base + extras_total
    if d.get("valor_manual") and d.get("valor"):
        d["valor"] = float(d["valor"])
    else:
        d["valor"] = d["preco_sugerido"]
    d["desconto_pct"] = round((1 - d["valor"] / d["preco_sugerido"]) * 100, 2) if d["preco_sugerido"] else 0
    # opções de preço (ex.: sem bateria / com bateria)
    ops = [{"rotulo": d.get("rotulo_base") or ("Sem bateria" if tipo == "hibrido" and d.get("baterias") else "Investimento total"),
            "valor": d["valor"], "bateria": None}]
    for b in d.get("baterias") or []:
        cat = achar(cfg["baterias"], b.get("id")) or {}
        preco_b = float(b["preco"]) if b.get("preco") not in (None, "") else com_fator(cat.get("preco"), fator)
        qtd = int(b.get("qtd") or 1)
        nome = b.get("nome") or cat.get("nome", "BATERIA")
        ops.append({"rotulo": b.get("rotulo") or cat.get("rotulo") or ("Com " + nome.split("(")[0].replace("BATERIA DE LÍTIO", "bateria").strip().capitalize()),
                    "valor": d["valor"] + preco_b * qtd,
                    "bateria": {"id": b.get("id"), "nome": nome, "desc": b.get("desc") or cat.get("desc", ""), "qtd": qtd, "preco": preco_b}})
    d["opcoes"] = ops
    return d


# ----------------------------------------------------------------------------- finanças
def fator_fin(cfg):
    """Margem de segurança somada a TODA parcela de financiamento simulada (padrão 10%)."""
    return 1 + float(cfg["pagamento"]["financiamento"].get("margem_pct", 10) or 0) / 100


def financas(d, cfg):
    calc = cfg["calculo"]
    painel = achar(cfg["paineis"], d["painel_id"]) or cfg["paineis"][0]
    kwp = d["n_paineis"] * painel["w"] / 1000
    media = kwp * float(calc["kwh_por_kwp_mes"])
    ger = [round(p * media * 12 / sum(PERFIL)) for p in PERFIL]
    consumo, minimo, tarifa, valor = d["consumo"], d["minimo"], d["tarifa"], d["valor"]

    def simula_ano(fator, tar):
        cred, linhas, conta_com = 0, [], 0.0
        for m, g in zip(MESES, ger):
            g = g * fator
            saldo = g - consumo
            if saldo >= 0:
                cred += saldo
                falta = 0
            else:
                usa = min(cred, -saldo)
                cred -= usa
                falta = -saldo - usa
            fat = max(minimo, falta) * tar
            conta_com += fat
            linhas.append((m, consumo, g, max(saldo, 0), cred, consumo * tar, fat))
        return linhas, consumo * 12 * tar - conta_com

    ano1, econ1 = simula_ano(1.0, tarifa)
    fluxo, anos = [-valor], []
    acum, poup, fator = -valor, valor, 1.0
    for a in range(1, 26):
        if a > 1:
            fator *= (1 - calc["degrad"]) if a > 2 else (1 - calc["degrad1"])
        tar = tarifa * (1 + calc["reajuste_tarifa"]) ** (a - 1)
        _, econ = simula_ano(fator, tar)
        acum += econ
        poup *= 1 + calc["poupanca"]
        fluxo.append(econ)
        anos.append((a, tar, sum(ger) * fator, econ, acum, poup - valor))

    def vpl(t):
        return sum(f / (1 + t) ** i for i, f in enumerate(fluxo))

    lo, hi = -0.99, 5.0
    mid = 0.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if vpl(mid) > 0 else (lo, mid)
    s, pb = -valor, None
    for a, _t, _g, econ, _ac, _p in anos:
        if econ > 0 and s + econ >= 0:
            pb = (a - 1) * 12 + int(-s / econ * 12 + 0.999)
            break
        s += econ
    if pb is None:
        pb_txt = "acima de 25 anos"
    else:
        pb_txt = f"{pb // 12} ano{'s' if pb // 12 != 1 else ''}" + (f" e {pb % 12} {'mês' if pb % 12 == 1 else 'meses'}" if pb % 12 else "")
    mwh = sum(x[2] for x in anos) / 1000
    return {
        "kwp": kwp, "media": media, "ger": ger, "ger_max": max(ger), "ano1": ano1, "econ1": econ1, "anos": anos,
        "tir": mid, "vpl": vpl(calc["taxa_vpl"]), "payback_meses": pb, "payback_txt": pb_txt,
        "total25": anos[-1][4], "mwh25": mwh, "co2": mwh * calc["co2_t_por_mwh"],
        "conta_sem": consumo * tarifa, "conta_com": sum(l[6] for l in ano1) / 12,
    }


def resumo(d, cfg, fator=1.0):
    """Números para a tela do vendedor (sem montar o HTML)."""
    d = dimensionar(d, cfg, fator)
    f = financas(d, cfg)
    inv = achar(cfg["inversores"], d["inversor_id"]) or {}
    painel = achar(cfg["paineis"], d["painel_id"]) or {}
    fins = [x for x in cfg["financeiras"] if x.get("ativo")]
    melhor = min((pmt(d["valor"], x["taxa"], x["prazo"]) * fator_fin(cfg) for x in fins), default=None)
    return {
        "consumo": d["consumo"], "n_paineis": d["n_paineis"], "n_auto": d["n_auto"], "w_painel": painel.get("w"),
        "kwp": round(f["kwp"], 3), "kwp_txt": kwp_txt(f["kwp"]), "inversor": inv.get("curto"), "inversor_id": inv.get("id"),
        "qtd_inversor": d["qtd_inversor"], "ger_media": round(f["media"]), "ger_max": f["ger_max"],
        "econ_mes": round(f["econ1"] / 12, 2), "econ_ano": round(f["econ1"], 2), "conta_sem": round(f["conta_sem"], 2),
        "conta_com": round(f["conta_com"], 2), "payback_txt": f["payback_txt"], "payback_meses": f["payback_meses"],
        "tir_pct": round(f["tir"] * 100, 1), "total25": round(f["total25"], 2), "co2_t": round(f["co2"], 1),
        "preco_solar": d["preco_solar"], "preco_extras": d["preco_extras"], "preco_sugerido": d["preco_sugerido"],
        "valor": d["valor"], "desconto_pct": d["desconto_pct"], "minimo": d["minimo"], "ligacao": d["ligacao"],
        "cabo_m": d["cabo_m"], "area_m2": round(d["n_paineis"] * 2.38 * 1.13 * (1.8 if d["estrutura_id"] == "solo" else 1)),
        "opcoes": [{"rotulo": o["rotulo"], "valor": o["valor"]} for o in d["opcoes"]],
        "parcela_min": round(melhor, 2) if melhor else None,
        "doc_valido": validar_cpf_cnpj(d.get("cliente_doc")) if d.get("cliente_doc") else None,
    }


# ----------------------------------------------------------------------------- ícones e gráficos
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
        "pessoa": '<circle cx="12" cy="8" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 21c1-4.5 4.5-6.5 8-6.5s7 2 8 6.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    }[nome]
    return f'<svg viewBox="0 0 24 24" width="{t}" height="{t}" fill="currentColor" style="color:{cor}">{p}</svg>'


def nice_step(span, alvo=5):
    bruto = max(span / alvo, 1e-9)
    mag = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * mag:
            return m * mag
    return 10 * mag


def fmt_eixo(v):
    if abs(v) >= 1_000_000:
        return f"{brl(v / 1e6, 1)} mi"
    if abs(v) >= 10000:
        return f"{brl(v / 1000, 0)} mil"
    return brl(v, 0)


def reais_curto(v):
    if abs(v) >= 1_000_000:
        return f"R$ {brl(v / 1e6, 1)} milhões"
    return f"R$ {brl(v / 1000, 0)} mil"


def grafico_geracao(ger, consumo):
    W, H, ml, mb, mt = 680, 250, 54, 28, 14
    serie_c = [consumo] * 12
    topo = max(ger + serie_c) * 1.12
    passo = nice_step(topo)
    vmax = passo * (int(topo / passo) + 1)
    pw, ph = W - ml - 10, H - mb - mt
    g = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="Inter,Segoe UI,Arial" font-size="11">',
         '<defs><linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a76a8"/>'
         f'<stop offset="1" stop-color="{AZUL}"/></linearGradient></defs>']
    v = 0
    while v <= vmax:
        y = mt + ph - v / vmax * ph
        g.append(f'<line x1="{ml}" x2="{W-10}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRADE}"/>'
                 f'<text x="{ml-7}" y="{y+4:.1f}" text-anchor="end" fill="{TINTA2}">{fmt_eixo(v)}</text>')
        v += passo
    slot = pw / 12
    series = [(serie_c, AMARELO), (ger, "url(#gA)")]
    bw = slot * 0.32
    for i, m in enumerate(MESES):
        x0 = ml + i * slot + slot / 2 - (bw + 1) * len(series) / 2
        for j, (s_, cor) in enumerate(series):
            h = s_[i] / vmax * ph
            x = x0 + j * (bw + 2)
            g.append(f'<rect x="{x:.1f}" y="{mt+ph-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{cor}"/>')
        g.append(f'<text x="{ml+i*slot+slot/2:.1f}" y="{H-9}" text-anchor="middle" fill="{TINTA2}">{m}</text>')
    g.append(f'<line x1="{ml}" x2="{W-10}" y1="{mt+ph}" y2="{mt+ph}" stroke="{TINTA2}"/></svg>')
    return "".join(g)


def grafico_fluxo(valor, anos):
    W, H, ml, mb, mt = 680, 250, 64, 28, 14
    vals = [-valor] + [x[4] for x in anos]
    pou = [0] + [x[5] for x in anos]
    topo = max(max(vals), max(pou), 1)
    passo = nice_step(topo + valor, 6)
    vmin = -passo * (int(valor / passo) + 1)
    vmax = passo * (int(topo / passo) + 1)
    pw, ph = W - ml - 10, H - mb - mt
    Y = lambda v: mt + ph - (v - vmin) / (vmax - vmin) * ph  # noqa: E731
    g = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="Inter,Segoe UI,Arial" font-size="11">']
    v = vmin
    while v <= vmax + 1:
        g.append(f'<line x1="{ml}" x2="{W-10}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{GRADE}"/>'
                 f'<text x="{ml-7}" y="{Y(v)+4:.1f}" text-anchor="end" fill="{TINTA2}">{fmt_eixo(v)}</text>')
        v += passo
    slot = pw / 26
    bw = slot * 0.36
    for i, (a, b) in enumerate(zip(vals, pou)):
        cx = ml + i * slot + slot / 2
        for j, (vv, cor) in enumerate([(a, "#b42318" if a < 0 else AZUL2), (b, AMARELO)]):
            x = cx - bw - 1 + j * (bw + 2)
            y0, y1 = sorted([Y(0), Y(vv)])
            g.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1-y0,1):.1f}" rx="2" fill="{cor}"/>')
        if i % 5 == 0:
            g.append(f'<text x="{cx:.1f}" y="{H-9}" text-anchor="middle" fill="{TINTA2}">{i}</text>')
    g.append(f'<line x1="{ml}" x2="{W-10}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="{TINTA2}"/>'
             f'<text x="{W-10}" y="{Y(vals[-1])-6:.1f}" text-anchor="end" font-weight="700" fill="{TINTA}">{reais_curto(vals[-1])}</text></svg>')
    return "".join(g)


def svg_produto(tipo, marca="", w=625):
    if tipo == "painel":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="16" y="4" width="48" height="72" rx="2" fill="#1d3557" stroke="#9aa5b1" stroke-width="2"/>'
                + "".join(f'<line x1="16" x2="64" y1="{4+i*12}" y2="{4+i*12}" stroke="#4a6fa5"/>' for i in range(1, 6))
                + '<line x1="32" x2="32" y1="4" y2="76" stroke="#4a6fa5"/><line x1="48" x2="48" y1="4" y2="76" stroke="#4a6fa5"/>'
                + f'<rect x="22" y="33" width="36" height="14" rx="2" fill="#f2a900"/><text x="40" y="43.5" font-size="9" font-weight="700" text-anchor="middle" font-family="Arial" fill="#1f2933">{w}W</text></svg>')
    if tipo == "inversor":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="14" y="8" width="52" height="64" rx="6" fill="#f4f6f8" stroke="#9aa5b1"/>'
                '<rect x="24" y="20" width="32" height="16" rx="2" fill="#123b57"/><circle cx="40" cy="52" r="7" fill="#f2a900"/>'
                f'<text x="40" y="31" fill="#fff" font-size="9" text-anchor="middle" font-family="Arial">{esc(marca)}</text></svg>')
    if tipo == "ar":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="6" y="22" width="68" height="28" rx="6" fill="#f4f6f8" stroke="#9aa5b1"/>'
                '<rect x="12" y="40" width="56" height="4" rx="2" fill="#123b57"/><circle cx="62" cy="30" r="2.5" fill="#f2a900"/>'
                '<path d="M22 56c2 4-2 6 0 10M40 56c2 4-2 6 0 10M58 56c2 4-2 6 0 10" stroke="#2a76a8" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>')
    if tipo == "poste":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="36" y="8" width="8" height="68" rx="2" fill="#c5ccd3" stroke="#9aa5b1"/>'
                '<rect x="22" y="14" width="36" height="5" rx="2" fill="#9aa5b1"/><rect x="46" y="36" width="16" height="20" rx="2" fill="#123b57"/>'
                '<circle cx="54" cy="44" r="3" fill="#f2a900"/><rect x="26" y="74" width="28" height="4" rx="1" fill="#52606d"/></svg>')
    if tipo == "bateria":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="14" y="10" width="52" height="62" rx="5" fill="#f4f6f8" stroke="#9aa5b1"/>'
                '<rect x="20" y="18" width="40" height="8" rx="2" fill="#123b57"/>'
                + "".join(f'<rect x="24" y="{32+i*9}" width="32" height="6" rx="1.5" fill="{"#1a7f37" if i else "#9aa5b1"}"/>' for i in range(4))
                + '<path d="M44 20l-6 6h5l-3 5" stroke="#f2a900" stroke-width="1.6" fill="none"/></svg>')
    if tipo == "carro":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="22" y="10" width="36" height="50" rx="6" fill="#f4f6f8" stroke="#9aa5b1"/>'
                '<rect x="30" y="18" width="20" height="12" rx="2" fill="#123b57"/><path d="M42 34l-6 9h6l-4 8" stroke="#f2a900" stroke-width="2.4" fill="none"/>'
                '<path d="M40 60v8c0 4 6 4 10 4" stroke="#52606d" stroke-width="3" fill="none"/></svg>')
    if tipo == "limpeza":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><path d="M12 50h44l-6 20H18z" fill="#1d3557"/><path d="M50 10l10 4-14 34-8-3z" fill="#9aa5b1"/>'
                '<circle cx="62" cy="54" r="3" fill="#2a76a8"/><circle cx="68" cy="44" r="2" fill="#2a76a8"/><circle cx="60" cy="40" r="2" fill="#2a76a8"/></svg>')
    if tipo == "monitor":
        return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="20" y="8" width="40" height="64" rx="7" fill="#f4f6f8" stroke="#9aa5b1"/>'
                '<path d="M28 48l8-10 6 6 10-14" stroke="#1a7f37" stroke-width="3" fill="none" stroke-linecap="round"/><rect x="34" y="62" width="12" height="3" rx="1.5" fill="#9aa5b1"/></svg>')
    return ('<svg viewBox="0 0 80 80" width="58" height="58"><rect x="12" y="10" width="56" height="60" rx="4" fill="#f4f6f8" stroke="#9aa5b1"/>'
            + "".join(f'<rect x="{20+i*14}" y="24" width="10" height="26" rx="2" fill="#123b57"/><rect x="{22+i*14}" y="30" width="6" height="8" fill="#f2a900"/>' for i in range(3))
            + '</svg>')


# ----------------------------------------------------------------------------- HTML da proposta
CSS = f"""
@page {{ size: A4; margin: 0 }}
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact }}
body {{ margin:0; font-family:Inter,'Segoe UI',Calibri,Arial,sans-serif; color:{TINTA}; font-size:10pt; background:#fff }}
.pg {{ width:210mm; height:297mm; position:relative; padding:26mm 16mm 20mm; page-break-after:always; overflow:hidden; background:#fff }}
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
.consultor {{ display:flex; gap:3mm; align-items:center; background:{FUNDO}; border-radius:10px; padding:3mm 4mm; font-size:9pt; color:{TINTA2}; max-width:110mm }}
.consultor b {{ color:{AZUL}; font-size:10.5pt; display:block }}
.capa-rod {{ position:absolute; left:16mm; right:16mm; bottom:16mm; display:flex; justify-content:space-between; font-size:9.5pt;
  border-top:1px solid {GRADE}; padding-top:3mm; color:{TINTA2} }}
.capa .sede {{ position:absolute; bottom:8mm; left:16mm; right:16mm; text-align:center }}
.intro p {{ font-size:10.5pt; line-height:1.55; margin:0 }}
.tri {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3.5mm; margin-top:5mm }}
.pilar {{ background:{FUNDO}; border-radius:8px; padding:4mm; border-top:3px solid {AMARELO} }} .pilar h3 {{ margin-top:2mm }} .pilar p {{ margin:0; font-size:9pt; color:{TINTA2} }}
.parc img {{ width:125mm }}
.fotos {{ display:grid; grid-template-columns:repeat(3,1fr); gap:2.5mm }}
figure {{ margin:0; position:relative }} figure img {{ width:100%; height:36mm; object-fit:cover; border-radius:6px; display:block }}
figcaption {{ position:absolute; left:2mm; bottom:2mm; background:rgba(18,59,87,.85); color:#fff; font-size:7.5pt; padding:.6mm 2mm; border-radius:3px }}
.contato {{ display:flex; gap:5mm; align-items:center; margin-top:5mm; background:{FUNDO}; border-radius:8px; padding:3mm 5mm; font-size:9pt; line-height:1.5 }}
.contato img {{ height:16mm }}
.clibox {{ display:grid; grid-template-columns:1.6fr 1fr; gap:3.5mm; margin-bottom:2mm }}
.clibox div {{ border:1px solid {GRADE}; border-left:4px solid {AZUL2}; border-radius:6px; padding:3mm 4mm }}
.clibox span {{ display:block; font-size:7.8pt; text-transform:uppercase; letter-spacing:.1em; color:{TINTA2} }}
.clibox b {{ display:block; font-size:11pt; color:{AZUL}; margin:.6mm 0 }} .clibox small {{ font-size:8.5pt; color:{TINTA2} }}
.lista div {{ display:flex; gap:3mm; align-items:flex-start; padding:2mm 0; border-bottom:1px dashed {GRADE}; font-size:9.6pt }}
.lista svg {{ flex:none }}
.prod td {{ padding:1.4mm 2mm }} .pimg {{ width:24mm }} .pimg img {{ max-width:20mm; max-height:14mm; border-radius:4px }}
td.pn {{ text-align:left }} td.q {{ font-size:12pt; font-weight:700; color:{AZUL} }}
.preco {{ margin-top:5mm; display:flex; justify-content:flex-end; gap:4mm }}
.preco div {{ background:linear-gradient(135deg,{AZUL},{AZUL2}); color:#fff; border-radius:10px; padding:4.5mm 8mm; text-align:right; border-bottom:4px solid {AMARELO} }}
.preco span {{ font-size:9pt; letter-spacing:.12em; text-transform:uppercase; opacity:.85 }}
.preco b {{ font-size:24pt; display:block; margin:1mm 0 }} .preco small {{ font-size:8.5pt; opacity:.85 }}
.preco s {{ font-size:10pt; opacity:.7; display:block }}
.preco.multi {{ margin-top:4mm; gap:3mm }} .preco.multi div {{ flex:1; padding:3.5mm 4mm }}
.preco.multi b {{ font-size:17pt }} .preco.multi span {{ font-size:7.8pt; letter-spacing:.08em }} .preco.multi small {{ font-size:7.5pt }}
.prod.compacto td {{ padding:.7mm 2mm; font-size:8.4pt }} .prod.compacto .pimg img {{ max-height:9mm; max-width:16mm }}
.prod.compacto .pimg svg {{ width:34px; height:34px }} .prod.compacto td.q {{ font-size:10.5pt }} .prod.compacto .mut {{ font-size:7.6pt; line-height:1.3 }}
.c3 {{ grid-template-columns:repeat(3,1fr) }}
td.inv {{ color:#b42318; font-weight:600 }} td.luc {{ color:#1a7f37; font-weight:600 }}
.ret td {{ padding:.75mm 1.5mm; font-size:8.2pt }}
.destaque {{ background:#fdf3d6; border-left:4px solid {AMARELO}; border-radius:6px; padding:4mm 5mm; font-size:10.5pt; margin:2mm 0 }}
.etapas {{ display:grid; grid-template-columns:repeat(5,1fr); gap:2mm; margin:4mm 0 6mm; position:relative }}
.etapas:before {{ content:''; position:absolute; top:5.5mm; left:10%; right:10%; height:2px; background:{AMARELO} }}
.et {{ text-align:center; position:relative; font-size:8.3pt; color:{TINTA2} }}
.et .num {{ width:11mm; height:11mm; border-radius:50%; background:{AZUL}; color:#fff; font-weight:700; font-size:12pt;
  display:flex; align-items:center; justify-content:center; margin:0 auto 2mm; border:3px solid #fff; box-shadow:0 0 0 2px {AMARELO} }}
.et b {{ display:block; color:{AZUL}; font-size:9.3pt; margin-bottom:.5mm }}
.duas {{ display:grid; grid-template-columns:1fr 1fr; gap:3.5mm }}
.box {{ background:{FUNDO}; border-radius:8px; padding:3.5mm 4.5mm; font-size:9pt }}
.box ul {{ margin:0; padding-left:4.5mm }} .bancos {{ width:100%; margin-top:2.5mm }}
.aceite {{ margin-top:5mm; font-size:9.5pt }}
.ass {{ display:flex; gap:12mm; margin-top:14mm }} .ass div {{ flex:1; border-top:1.5px solid {TINTA}; padding-top:2mm; text-align:center; font-size:9pt; font-weight:600 }}
.ass small {{ font-weight:400; color:{TINTA2} }}
.obs {{ background:#eef4fa; border-left:4px solid {AZUL2}; border-radius:6px; padding:3mm 4mm; font-size:9pt; margin-top:3mm; white-space:pre-wrap }}
@media screen {{ body {{ background:#2b2f36 }} .pg {{ margin:10px auto; box-shadow:0 6px 30px rgba(0,0,0,.35) }} }}
"""


def montar_html(d_in, cfg, vendedor=None, num="", data=None, fator=1.0):
    """Devolve (html, resumo) da proposta completa."""
    cfg = mesclar(CONFIG_PADRAO, cfg or {})
    d = dimensionar(d_in, cfg, fator)
    F = financas(d, cfg)
    emp = cfg["empresa"]
    pag_cfg = mesclar(cfg["pagamento"], d.get("pagamento") or {})
    pag_cfg["financiamento"]["margem_pct"] = cfg["pagamento"]["financiamento"].get("margem_pct", 10)  # vendedor não muda
    painel = achar(cfg["paineis"], d["painel_id"]) or cfg["paineis"][0]
    inv = achar(cfg["inversores"], d["inversor_id"]) or cfg["inversores"][0]
    estr = achar(cfg["estruturas"], d["estrutura_id"]) or cfg["estruturas"][0]
    W = painel["w"]
    N = d["n_paineis"]
    KWP = F["kwp"]
    hoje = data or datetime.date.today()
    num = num or "RASCUNHO"
    TEL, SEDE = emp["telefone"], emp["sede"]
    validade = int(d.get("validade_dias") or emp.get("validade_dias") or 10)
    ops = d["opcoes"]
    multi = len(ops) > 1
    VALOR = d["valor"]
    paginas = []

    def pagina(corpo, classe=""):
        paginas.append((corpo, classe))

    def card(icone, valor, rotulo):
        return f'<div class="card">{ico(icone)}<div><div class="v">{valor}</div><div class="l">{rotulo}</div></div></div>'

    def titulo(t, sub=""):
        return f'<h1>{t}</h1>' + (f'<p class="sub">{sub}</p>' if sub else "")

    cli_nome = esc(d.get("cliente_nome")).upper()
    end_partes = [x for x in [d.get("cliente_endereco"), d.get("cliente_cidade"), ("UC " + d["cliente_uc"]) if d.get("cliente_uc") else ""] if x]
    cli_end = esc(" · ".join(end_partes))
    doc = d.get("cliente_doc")
    cli_doc = ("CPF: " if len("".join(c for c in str(doc) if c.isdigit())) == 11 else "CNPJ: ") + fmt_doc(doc) if doc else ""
    qtd_inv = d["qtd_inversor"]
    inv_curto = (f"{qtd_inv} × " if qtd_inv > 1 else "") + inv["curto"]
    GER_TXT = f"{brl(F['media'], 0)} kWh/mês"
    ECON_TXT, ECON_ROT = (f"R$ {brl(F['econ1']/1000,0)} mil", "Economia estimada no 1º ano") if F["econ1"] > 60000 \
        else (f"R$ {brl(F['econ1']/12,0)}", "Economia média por mês no 1º ano")
    AREA = round(N * 2.38 * 1.13 * (1.8 if d["estrutura_id"] == "solo" else 1.25 if N > 40 else 1))

    # 1. capa
    cli_capa = (f'<div class="cli"><span>Preparada para</span><b>{cli_nome}</b><small>{cli_end}</small></div>'
                if cli_nome else '<div class="cli"><span>Preparada para</span><b>______________________________________</b></div>')
    vend_capa = ""
    if vendedor and vendedor.get("nome"):
        vend_capa = (f'<div class="consultor">{ico("pessoa", AZUL2, 22)}<div>Seu consultor<b>{esc(vendedor["nome"])}</b>'
                     f'{esc(vendedor.get("telefone") or "")}</div></div>')
    pagina(f"""
  <div class="capa-foto" style="background-image:url('{b64('capa_foto.jpg')}')">
    <div class="capa-veu"></div>
    <img class="capa-logo" src="{b64('logo.jpg')}">
    <div class="capa-tit"><small>PROPOSTA COMERCIAL</small>Usina solar<br>fotovoltaica{'<br><span style="font-size:20pt;color:#f2a900">híbrida com bateria</span>' if d['tipo'] == 'hibrido' else ''}</div>
  </div>
  <div class="capa-info">
    {cli_capa}
    <div class="tags">
      <span class="tag">{ico('raio','#fff',14)} {kwp_txt(KWP)} kWp</span>
      <span class="tag">{ico('painel','#fff',14)} {N} painéis de {W} W</span>
      <span class="tag">{ico('inversor','#fff',14)} {esc(inv_curto)}</span>
      <span class="tag am">{ico('sol',TINTA,14)} {GER_TXT}</span>
    </div>
    {vend_capa}
    <div class="capa-rod"><div><b>Proposta {esc(num)}</b> · {hoje:%d/%m/%Y} · válida por {validade} dias</div>
    <div><b>{esc(emp['nome'])}</b> · Tel/WhatsApp {esc(TEL)}</div></div>
    <div class="sede">{esc(SEDE)}</div>
  </div>""", "capa")

    # 2. empresa
    pagina(f"""
  {titulo('Quem somos', esc(emp['nome']) + ' · soluções fotovoltaicas no Pará')}
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
  <div class="contato"><img src="{b64('logo.jpg')}"><div><b>{esc(emp['nome'])}</b> · CNPJ {esc(emp['cnpj'])}<br>
  {esc(emp['endereco'])}<br>Tel/WhatsApp: {esc(TEL)} · {esc(emp['email'])}</div></div>
""")

    # 3. sistema
    cli_box = ""
    if cli_nome:
        cli_box = (f'<div class="clibox"><div><span>Cliente</span><b>{cli_nome}</b><small>{cli_end or "&nbsp;"}{(" · " + esc(cli_doc)) if cli_doc else ""}</small></div>'
                   f'<div><span>Unidade consumidora</span><b>{esc(d["grupo"])}</b><small>Ligação {esc(d["ligacao"]).lower()}</small></div></div>')
    porque = d.get("porque") or porque_auto(d, cfg, F, inv, painel)
    obs = f'<div class="obs"><b>Observações:</b> {esc(d["observacoes"])}</div>' if d.get("observacoes") else ""
    pagina(f"""
  {titulo('Seu sistema solar', 'O que está sendo proposto, em resumo')}
  {cli_box}
  <div class="cards">
    {card('raio', f"{kwp_txt(KWP)} kWp", 'Potência instalada')}
    {card('painel', f"{N} × {W} W", 'Painéis de última geração')}
    {card('inversor', esc(inv_curto), 'Inversor híbrido: rede + bateria' if d['tipo'] == 'hibrido' else 'Microinversores: cada painel trabalha sozinho' if d['tipo'] == 'micro' else 'Inversor com monitoramento pelo celular')}
    {card('sol', f"{brl(F['media'],0)} kWh", 'Geração média estimada por mês')}
    {card('dinheiro', ECON_TXT, ECON_ROT)}
    {card('area', f"≈ {brl(AREA,0)} m²", 'Área de terreno necessária' if d['estrutura_id'] == 'solo' else 'Área necessária para os painéis')}
  </div>
  <h2>Conta de energia considerada</h2>
  <table><tr><th>Unidade</th><th>Ligação</th><th>Consumo (kWh/mês)</th><th>Consumo mínimo (kWh)</th><th>Preço do kWh (R$)</th></tr>
  <tr><td>{esc(d['grupo'])}</td><td>{esc(d['ligacao'])}</td><td>{brl(d['consumo'],0)}</td><td>{d['minimo']}</td><td>{brl(d['tarifa'])} *</td></tr></table>
  <p class="mut">* Valor médio do kWh com impostos. A unidade consumidora fica com 100% do crédito gerado.</p>
  <h2>Por que esta solução?</h2>
  <div class="lista">{''.join(f'<div>{ico("check",AZUL2,18)}<span>{esc(t)}</span></div>' for t in porque)}</div>
  {obs}
""")

    # 4. geração
    linhas_mes = "".join(
        f"<tr><td>{m}</td><td>{brl(c,0)}</td><td>{brl(g,0)}</td><td>{brl(cr,0)}</td><td>{brl(ac,0)}</td>"
        f"<td>R$ {brl(fs)}</td><td>R$ {brl(fc)}</td></tr>" for m, c, g, cr, ac, fs, fc in F["ano1"])
    a1 = F["ano1"]
    linhas_mes += (f'<tr class="tot"><td>Ano</td><td>{brl(d["consumo"]*12,0)}</td><td>{brl(sum(F["ger"]),0)}</td><td></td>'
                   f'<td>{brl(a1[-1][4],0)}</td><td>R$ {brl(sum(l[5] for l in a1))}</td><td>R$ {brl(sum(l[6] for l in a1))}</td></tr>')
    pagina(f"""
  {titulo('Geração de energia', 'Estimativa mês a mês no 1º ano')}
  <div class="painelg">{grafico_geracao(F['ger'], d['consumo'])}
  <div class="leg"><span><i style="background:{AMARELO}"></i>Consumo</span><span><i style="background:{AZUL2}"></i>Geração</span></div></div>
  <table><tr><th>Mês</th><th>Consumo (kWh)</th><th>Geração (kWh)</th><th>Crédito do mês</th><th>Crédito acumulado</th><th>Fatura sem sistema</th><th>Fatura com sistema</th></tr>{linhas_mes}</table>
  <p class="mut">Nos meses de menos sol a conta usa os créditos guardados; sem crédito, paga só a diferença. A fatura com sistema
  inclui o custo mínimo de disponibilidade ({d['minimo']} kWh). Valores estimados; a geração varia com o clima, sombras e a
  inclinação do local. Não considera a cobrança do Fio B prevista na Lei 14.300/2022 nem possíveis cobranças de ICMS sobre a TUSD.</p>
""")

    # 5. produtos
    produtos = [(svg_produto("painel", w=W), painel["nome"], painel.get("desc", ""), "PC", N, "")]
    produtos.append((svg_produto("inversor", inv.get("marca", "")), inv["nome"], inv.get("desc", ""), "PC", qtd_inv, ""))
    produtos.append((f'<img src="{b64(estr.get("img") or "prod_estrutura.jpg")}">', estr["nome"], estr.get("desc", ""), "KIT", -(-N // 4), ""))
    for e in d["extras"]:
        produtos.append((svg_produto(e["icone"]), e["nome"], e["desc"], e["unid"], e["qtd"], "" if e.get("no_valor", True) else "Cortesia"))
    produtos += [
        (f'<img src="{b64("prod_cabo_preto.jpg")}">', "CABO SOLAR NEXANS 0,6/1 kV PRETO", "Proteção UV para uso externo", "M", d["cabo_m"], ""),
        (f'<img src="{b64("prod_cabo_verm.jpg")}">', "CABO SOLAR NEXANS 0,6/1 kV VERMELHO", "Proteção UV para uso externo", "M", d["cabo_m"], ""),
        (f'<img src="{b64("prod_projeto.jpg")}">', "PROJETO DE ENGENHARIA", "Projeto elétrico, ART e homologação na Equatorial", "SV", 1, ""),
        (f'<img src="{b64("prod_instalacao.jpg")}">', "INSTALAÇÃO", "Equipe própria com NR-10 e NR-35", "SV", 1, ""),
    ]
    for o in ops[1:]:
        b = o["bateria"]
        produtos.append((svg_produto("bateria"), b["nome"], b["desc"], "PC", b["qtd"], f"Só na opção “{o['rotulo']}”"))
    linhas_prod = "".join(
        f'<tr><td class="pimg">{im}</td><td class="pn"><b>{esc(n)}</b><br><span class="mut">{esc(de)}</span>'
        f'{f"<br><b style=color:#1a7f37>{esc(nota)}</b>" if nota else ""}</td><td>{u}</td><td class="q">{brl(q,0)}</td></tr>'
        for im, n, de, u, q, nota in produtos)
    compacto = len(produtos) + (len(ops) - 1) * 2 > 10  # aperta a tabela para caber numa página
    desc_txt = ""
    if d["desconto_pct"] >= 0.5 and d.get("mostrar_desconto"):
        desc_txt = f'<s>de R$ {brl(d["preco_sugerido"])}</s>'
    caixa = "".join(
        f'<div><span>{esc(o["rotulo"])}</span>{desc_txt if i == 0 else ""}<b>R$ {brl(o["valor"])}</b><small>Material, projeto, homologação e instalação inclusos</small></div>'
        for i, o in enumerate(ops))
    pagina(f"""
  {titulo('Os produtos', 'Tudo o que está incluso nesta proposta')}
  <table class="prod{' compacto' if compacto else ''}"><tr><th></th><th style="text-align:left">Produto</th><th>Unid.</th><th>Qtde</th></tr>{linhas_prod}</table>
  <div class="preco{' multi' if multi else ''}">{caixa}</div>
""")

    # 6. pagamento (uma página por opção)
    fins = [x for x in cfg["financeiras"] if x.get("ativo")]
    if d.get("financeiras_ids"):
        fins = [x for x in cfg["financeiras"] if x["id"] in d["financeiras_ids"]]
    for o in ops:
        paginas.append((pagina_pagamento(o["valor"], o["rotulo"] if multi else "", pag_cfg, fins, d, F, titulo, cli_nome, cli_doc), ""))

    # 7. retorno
    linhas_ret = "".join(
        f'<tr><td class="{"inv" if ac < 0 else "luc"}">{"Investimento" if ac < 0 else "Lucro"}</td><td>{a}</td>'
        f"<td>{brl(t)}</td><td>{brl(g,0)}</td><td>{brl(e)}</td><td>{brl(ac)}</td><td>{brl(p)}</td></tr>"
        for a, t, g, e, ac, p in F["anos"])
    calc = cfg["calculo"]
    sub_ret = 'Quanto o sistema devolve ao longo de 25 anos'
    if multi:
        sub_ret += f' · calculado na opção “{esc(ops[0]["rotulo"])}” (R$ {brl(VALOR)}); a bateria traz energia na falta de luz, não aumenta a economia na conta'
    pagina(f"""
  {titulo('Retorno do investimento', sub_ret)}
  <div class="cards c3">
    {card('relogio', F['payback_txt'], 'Payback: tempo para o sistema se pagar')}
    {card('grafico', f"{brl(F['tir']*100,1)}% a.a.", 'TIR: rentabilidade ao ano')}
    {card('dinheiro', reais_curto(F['total25']), 'Resultado acumulado em 25 anos')}
  </div>
  <table class="ret"><tr><th>Status</th><th>Ano</th><th>Tarifa (R$/kWh)</th><th>Geração (kWh/ano)</th><th>Economia no ano (R$)</th><th>Acumulado (R$)</th><th>Se ficasse na poupança (R$)</th></tr>
  {linhas_ret}</table>
  <p class="mut">Reajuste da tarifa: {brl(calc['reajuste_tarifa']*100,0)}% ao ano · Painéis: perda de 1% no 1º ano e 0,4% ao ano depois, conforme fabricante ·
  Poupança: {brl(calc['poupanca']*100,2)}% ao ano sobre os mesmos R$ {brl(VALOR)} · VPL (taxa de {brl(calc['taxa_vpl']*100,0)}% a.a.): R$ {brl(F['vpl'])}.</p>
""")

    # 8. fluxo + ambiental
    pagina(f"""
  {titulo('Energia solar x poupança', 'Resultado acumulado ano a ano com o mesmo dinheiro')}
  <div class="painelg">{grafico_fluxo(VALOR, F['anos'])}
  <div class="leg"><span><i style="background:#b42318"></i>Investimento</span><span><i style="background:{AZUL2}"></i>Energia solar</span><span><i style="background:{AMARELO}"></i>Poupança</span></div></div>
  <div class="destaque">Em 25 anos a energia solar rende <b>{reais_curto(F['total25'])}</b>; o mesmo dinheiro na poupança renderia
  <b>{reais_curto(F['anos'][-1][5])}</b>. São <b>{brl(F['total25']/max(F['anos'][-1][5],1),0)} vezes</b> mais.</div>
  <h2>Retorno ambiental em 25 anos</h2>
  <div class="cards c3 verde">
    {card('nuvem', f"{brl(F['co2'],0)} t", 'de CO₂ que deixam de ser emitidas')}
    {card('arvore', brl(round(F['co2']*7.13),0), 'árvores seriam necessárias para retirar esse CO₂')}
    {card('folha', f"{brl(F['mwh25'],0)} MWh", 'de energia limpa gerada no período')}
  </div>
""")

    # 9. etapas + condições + assinatura
    etapas = [("Visita técnica", "Medição do local e confirmação do projeto"), ("Projeto e ART", "Engenharia elétrica e documentação"),
              ("Homologação", "Pedido de acesso na Equatorial"), ("Instalação", "Montagem por equipe própria"),
              ("Ligação", "Vistoria, troca do medidor e geração")]
    linha_et = "".join(f'<div class="et"><div class="num">{i+1}</div><b>{t}</b><span>{de}</span></div>' for i, (t, de) in enumerate(etapas))
    nao_cob = ["Obras civis (parede, reboco etc.)", "Adequação do padrão de entrada de energia", "Taxa mínima da concessionária"]
    ids_extras = {e.get("id") for e in d["extras"]}
    if "poste" in ids_extras or "padrao" in ids_extras:
        nao_cob[1] = "Outras adequações do padrão de entrada (o que está na lista de produtos já está incluso)"
    if d["estrutura_id"] == "solo":
        nao_cob[0] = "Limpeza, terraplenagem e cerca do terreno"
    if KWP > 75:
        nao_cob.append("Adequações exigidas pela Equatorial para minigeração (acima de 75 kW), se houver")
    formas = resumo_formas(pag_cfg, fins)
    vend_ass = ""
    if vendedor and vendedor.get("nome"):
        vend_ass = f'<p class="mut" style="margin-top:3mm">Consultor(a) responsável: <b>{esc(vendedor["nome"])}</b>{" · " + esc(vendedor.get("telefone")) if vendedor.get("telefone") else ""}</p>'
    pagina(f"""
  {titulo('Como funciona', 'Do contrato à energia gerada')}
  <div class="etapas">{linha_et}</div>
  <div class="duas">
    <div class="box"><h3>{ico('relogio',AZUL2,18)} Prazo de entrega</h3>{esc(emp.get('prazo_entrega'))}</div>
    <div class="box"><h3>{ico('dinheiro',AZUL2,18)} Formas de pagamento</h3>{formas}
    <img src="{b64('bancos.jpg')}" class="bancos"></div>
    <div class="box"><h3>{ico('escudo',AZUL2,18)} Garantias</h3><ul><li>Painéis: 30 anos de desempenho (fabricante)</li>
    <li>{esc(inv.get('garantia'))}</li><li>Instalação: {esc(emp.get('garantia_instalacao') or '1 ano')}</li></ul></div>
    <div class="box"><h3>{ico('area',AZUL2,18)} Não incluso</h3><ul>{''.join(f'<li>{t}</li>' for t in nao_cob)}</ul></div>
  </div>
  <p class="aceite">Estando de acordo com os produtos, valores e termos desta proposta, {esc(emp['nome'])} e o(a) cliente firmam a proposta.</p>
  <div class="ass"><div>{esc(emp.get('responsavel'))}<br><small>{esc(emp['nome'])} · CNPJ {esc(emp['cnpj'])}</small></div>
  <div>{cli_nome or 'CLIENTE'}<br><small>{esc(cli_doc) or 'CPF/CNPJ: ____________________'}</small></div></div>
  {vend_ass}
  <p class="mut" style="margin-top:5mm">Local e data: ______________________, ____/____/______</p>
""")

    total = len(paginas)
    logo = b64("logo.jpg")
    corpo = ""
    for i, (c, classe) in enumerate(paginas, 1):
        rod = "" if classe == "capa" else (
            f'<div class="topo"><img src="{logo}"><span>Proposta {esc(num)}</span></div>'
            f'<div class="rod">{esc(emp["nome"])} · Tel/WhatsApp {esc(TEL)} · página {i} de {total}<div class="sede">{esc(SEDE)}</div></div>')
        corpo += f'<section class="pg {classe}">{rod}{c}</section>'
    html = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Proposta {esc(num)} – {esc(emp["nome"])}</title><style>{CSS}</style></head><body>{corpo}</body></html>')
    res = resumo(d_in, cfg, fator)
    res["paginas"] = total
    return html, res


def porque_auto(d, cfg, F, inv, painel):
    n, w = d["n_paineis"], painel["w"]
    out = [f"Gera cerca de {brl(F['media'],0)} kWh por mês para um consumo de {brl(d['consumo'],0)} kWh: cobre a conta e paga só a taxa mínima."]
    out.append(f"{n} painéis de {w} W ({kwp_txt(F['kwp'])} kWp): menos painéis para a mesma energia, menos peso e menos furos no telhado.")
    if d["tipo"] == "hibrido":
        out.append("Inversor híbrido: funciona ligado à rede hoje e aceita bateria a qualquer momento, sem trocar nada.")
        if d.get("baterias"):
            out.append("Com bateria, a casa continua com energia quando falta luz da Equatorial (geladeira, iluminação, internet).")
    elif d["tipo"] == "micro":
        out.append("Microinversores: sombra ou sujeira em um painel não derruba a geração dos outros, e não há alta tensão passando pela casa.")
    ars = [e for e in d["extras"] if e.get("icone") == "ar"]
    if ars:
        q = sum(e["qtd"] for e in ars)
        out.append(("Um ar-condicionado inverter incluso" if q == 1 else f"{q} ar-condicionados inverter inclusos")
                   + ": mais conforto, com a energia vindo do próprio sol.")
    out.append("Tecnologia N-type: perde menos rendimento no calor do Pará e envelhece mais devagar (cerca de 0,4% ao ano).")
    out.append(f"{inv['curto']} com acompanhamento da geração pelo aplicativo.")
    return out


def resumo_formas(pag, fins):
    partes = []
    if pag["avista"].get("ativo"):
        partes.append("À vista" + (f" com {brl(pag['avista']['desconto_pct'],0)}% de desconto" if pag["avista"].get("desconto_pct") else ""))
    if pag["direto"].get("ativo"):
        p = pag["direto"]
        partes.append(f"parcelamento direto ({p['pct1']}% em {p['n1']}×; o restante em {p['boleto_n']}× no boleto ou {p['cartao_n']}× no cartão)")
    if pag["cartao"].get("ativo"):
        partes.append(f"cartão em até {pag['cartao']['n']}×")
    if pag["financiamento"].get("ativo") and fins:
        partes.append(f"financiamento em até {max(f['prazo'] for f in fins)}× (ver página de pagamento)")
    return " · ".join(partes) or "A combinar"


def pagina_pagamento(valor, rotulo, pag, fins, d, F, titulo, cli_nome, cli_doc):
    blocos = []
    fm = 1 + float(pag['financiamento'].get('margem_pct', 10) or 0) / 100
    pf = lambda pv, i, n: pmt(pv, i, n) * fm  # noqa: E731  parcela simulada já com a margem de segurança
    if pag["avista"].get("ativo"):
        dpct = float(pag["avista"].get("desconto_pct") or 0)
        blocos.append(f"""<div class="box" style="display:flex;justify-content:space-between;align-items:center">
      <div><h3>{ico('dinheiro',AZUL2,18)} À vista</h3><span class="mut">PIX ou transferência na assinatura</span></div>
      <div style="text-align:right">{f'<s class="mut">R$ {brl(valor)}</s><br>' if dpct else ''}<b style="font-size:16pt;color:{AZUL}">R$ {brl(valor*(1-dpct/100))}</b>
      {f'<br><span style="color:#1a7f37;font-weight:700">{brl(dpct,0)}% de desconto</span>' if dpct else ''}</div></div>""")
    if pag["direto"].get("ativo"):
        p = pag["direto"]
        pct1 = float(p["pct1"]) / 100
        p1v, p2v = valor * pct1, valor * (1 - pct1)
        n1, nb, nc = int(p["n1"]), int(p["boleto_n"]), int(p["cartao_n"])
        a = p1v / n1
        blocos.append(f"""<div class="box"><h3>{ico('dinheiro',AZUL2,18)} Parcelamento direto</h3>
      <table><tr><th>Parte</th><th>Valor</th><th>Como paga</th></tr>
      <tr><td>1ª parte ({brl(pct1*100,0)}%)</td><td>R$ {brl(p1v)}</td><td><b>{n1}× de R$ {brl(a)}</b> (única opção)</td></tr>
      <tr><td rowspan="2">2ª parte ({brl(100-pct1*100,0)}%)<br><small>escolha uma</small></td><td rowspan="2">R$ {brl(p2v)}</td><td><b>{nb}× de R$ {brl(p2v/nb)}</b> no boleto</td></tr>
      <tr><td>ou <b>{nc}× de R$ {brl(p2v/nc)}</b> no cartão</td></tr></table>
      <table style="margin-top:2mm"><tr><th>2ª parte em</th><th>Meses 1 a {nb}</th><th>Meses {nb+1} a {nc}</th><th>Meses {nc+1} a {n1}</th></tr>
      <tr><td>Boleto {nb}×</td><td>R$ {brl(a+p2v/nb)}</td><td>R$ {brl(a)}</td><td>R$ {brl(a)}</td></tr>
      <tr><td>Cartão {nc}×</td><td>R$ {brl(a+p2v/nc)}</td><td>R$ {brl(a+p2v/nc)}</td><td>R$ {brl(a)}</td></tr></table>
      <p class="mut" style="margin:1.5mm 0 0">Economia média estimada na conta de luz: <b>R$ {brl(F['econ1']/12,0)} por mês</b> já no 1º ano.</p></div>""")
    if pag["cartao"].get("ativo"):
        c = pag["cartao"]
        n, j = int(c["n"]), float(c.get("juros_am") or 0)
        blocos.append(f"""<div class="box" style="display:flex;justify-content:space-between;align-items:center">
      <div><h3>{ico('dinheiro',AZUL2,18)} Cartão de crédito</h3><span class="mut">{'Com juros de ' + brl(j*100,2) + '% a.m. da operadora' if j else 'Sem juros'}</span></div>
      <b style="font-size:14pt;color:{AZUL}">{n}× de R$ {brl(pmt(valor, j, n))}</b></div>""")
    if pag["entrada"].get("ativo") and fins:
        e = float(pag["entrada"]["pct"]) / 100
        f0 = fins[0]
        blocos.append(f"""<div class="box" style="display:flex;justify-content:space-between;align-items:center">
      <div><h3>{ico('dinheiro',AZUL2,18)} Entrada + financiamento</h3><span class="mut">Entrada de {brl(e*100,0)}% e o restante pela {esc(f0['nome'].split(' –')[0])}</span></div>
      <div style="text-align:right">Entrada <b>R$ {brl(valor*e)}</b><br><b style="font-size:13pt;color:{AZUL}">+ {f0['prazo']}× de R$ {brl(pf(valor*(1-e), f0['taxa'], f0['prazo']))}</b></div></div>""")
    fin_html = ""
    if pag["financiamento"].get("ativo") and fins:
        linhas = "".join(
            f"<tr><td class='pn'><b>{esc(b['nome'])}</b><br><span class='mut'>{esc(b.get('obs',''))}</span></td><td>{b['prazo']}×</td><td>{brl(b['taxa']*100,2)}% a.m.</td>"
            f"<td>{b.get('carencia',0)} meses</td><td class='q' style='font-size:11pt'>R$ {brl(pf(valor, b['taxa'], b['prazo']))}</td></tr>" for b in fins)
        prazos = [p for p in pag["financiamento"].get("prazos_tabela") or [] if p <= max(b["prazo"] for b in fins)]
        tab_prazos = ""
        if prazos and d.get("tabela_prazos", True):
            cab = "".join(f"<th>{p}×</th>" for p in prazos)
            lin = "".join(
                f"<tr><td class='pn'><b>{esc(b['nome'].split(' –')[0])}</b></td>" + "".join(
                    f"<td>{'R$ ' + brl(pf(valor, b['taxa'], p), 0) if p <= b['prazo'] else '–'}</td>" for p in prazos) + "</tr>" for b in fins)
            tab_prazos = f'<table style="margin-top:2mm;font-size:8pt"><tr><th style="text-align:left">Parcela simulada por prazo*</th>{cab}</tr>{lin}</table>'
        cli_txt = f" · cliente {cli_nome}" if cli_nome else ""
        fin_html = f"""<h2 style="margin-top:4mm">Simulação de financiamento <span style="font-size:9pt;color:#b42318;font-weight:600">· valores apenas simulados</span></h2>
  <p class="sub" style="margin:0 0 2mm">Valor financiado: R$ {brl(valor)}{cli_txt}{' · ' + esc(cli_doc) if cli_doc else ''} · no maior prazo de cada linha</p>
  <table class="prod"><tr><th style="text-align:left">Financeira</th><th>Prazo</th><th>Juros</th><th>Carência</th><th>Parcela simulada*</th></tr>{linhas}</table>
  {tab_prazos}
  <div class="destaque" style="font-size:9pt;margin-top:2.5mm;border-left-color:#b42318"><b>* Atenção: isto é apenas uma simulação, não é
  uma oferta nem aprovação de crédito.</b> A taxa e o valor final da parcela só são definidos pela financeira depois da análise do
  CPF do(a) cliente e <b>podem subir</b> conforme o score de crédito, IOF, seguro e tarifas. As taxas usadas são as de mercado no
  dia desta proposta.</div>"""
    return f"""
  {titulo('Formas de pagamento' + (' – ' + esc(rotulo) if rotulo else ''), f'Investimento de R$ {brl(valor)} · escolha a que cabe melhor no seu orçamento')}
  <div style="display:grid;gap:3mm">{''.join(blocos)}</div>
  {fin_html}
"""
