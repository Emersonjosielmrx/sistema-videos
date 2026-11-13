"""
LiciBot-IA · simulador.py
"Se eu tiver R$ X para investir, quanto ganho e em quanto tempo?" — usando o lance que o PRÓPRIO robô daria
numa disputa automática, não o valor estimado do edital.

Para cada licitação aberta que a IA aprovou (MEI/CPF; AMIGO_SOLAR fica de fora: o investimento é do parceiro):
  custo          = o que a IA estimou para entregar (compra do produto, ferramentas, horas)
  lance_minimo   = menor preço que o robô aceita: cobre o custo, os impostos da carteira e a margem mínima
  preco_provavel = quanto o vencedor costuma cobrar (estimado × (1 - desconto real dos vencedores na gaveta))
  o robô disputa até o lance_minimo; ganha se o lance_minimo ficar abaixo do preco_provavel
  lance_robo     = preco_provavel - 1% (bate o provável vencedor sem descer abaixo do lance_minimo)
  chance         = viabilidade da IA (0–100) ajustada pela folga entre preco_provavel e lance_minimo
  lucro          = lance_robo - custo - impostos
  dinheiro preso = custo, do início da entrega até o órgão pagar (prazo por esfera)

A carteira é montada pelo melhor lucro esperado por real investido e por dia, respeitando o dinheiro que cabe ao
mesmo tempo. O dinheiro volta quando o órgão paga e é reinvestido nas licitações seguintes (linha do tempo).
Tudo é estimativa: serve para decidir, não é promessa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import database as db
from config import CPF_ENCARGO_COMPARACAO, DESCONTO_PADRAO, INSS_ALIQUOTA_PF, INSS_TETO, MEI_DAS_MENSAL

# dias até o órgão pagar depois da entrega (Lei 14.133 art. 141 + IN SEGES 77/2022 para o federal)
PAGAMENTO_DIAS = {"F": 15, "E": 35, "D": 35, "M": 45, "N": 45}
ENTREGA_DIAS = {"produto": 15, "servico": 30, "obra": 60}


@dataclass
class Parametros:
    capital: float = 10_000.0          # dinheiro disponível para investir
    margem_min: float = 0.15           # margem mínima sobre o custo que o robô aceita (15%)
    dias: int = 180                    # horizonte da simulação
    carteiras: tuple = ("MEI", "CPF")
    tipos: tuple = ("produto", "servico")
    nota_min: float = 0
    chance_min: float = 0.03           # ignora licitação com chance de ganhar abaixo disso
    reinvestir: bool = True
    entrega_produto_dias: int = 15
    pagamento_extra_dias: int = 0      # atraso a mais que você quer considerar (prudência)
    horas_mes: float = 120             # horas por mês que você tem para fazer serviços (diagramação, vídeo...)
    valor_hora: float = 80             # quanto vale 1 h do seu trabalho (estima as horas de cada serviço)
    # A "viabilidade" da IA não é chance de ganhar calibrada: em pregão com muitos concorrentes a chance real
    # costuma ser bem menor. Multiplica a chance da IA até o robô ter histórico próprio de vitórias.
    realismo: float = 0.3


@dataclass
class Oportunidade:
    numero: str
    objeto: str
    orgao: str
    uf: str
    carteira: str
    tipo: str
    esfera: str
    fecha: str
    estimado: float
    custo: float
    lance_minimo: float
    preco_provavel: float
    lance_robo: float
    disputa: bool
    chance: float
    lucro: float
    lucro_esperado: float
    dias_preso: int
    roi: float                      # lucro / custo
    roi_dia: float                  # lucro esperado / custo / dias preso
    link: str
    motivo: str = ""


MARGEM_MAX_CREDIVEL = 3.0     # lucro > 300% do custo = dado errado (custo subestimado), não oportunidade


def valor_atendido(e: dict[str, Any]) -> float:
    """Valor estimado só dos itens que a IA disse que atendemos (o mesmo valor_base da análise)."""
    import json as _j
    try:
        atendidos = set((_j.loads(e.get("json_ia") or "{}") or {}).get("itens_que_atendemos") or [])
    except ValueError:
        atendidos = set()
    if atendidos:
        with db.conexao() as c:
            v = c.execute("SELECT coalesce(sum(valor_total),0) FROM itens_edital WHERE numero_controle=? "
                          "AND numero_item IN (%s)" % ",".join("?" * len(atendidos)),
                          (e["numero_controle"], *atendidos)).fetchone()[0]
        if v:
            return float(v)
    return float(e.get("valor_estimado") or 0)


def _impostos(carteira: str, lance: float) -> float:
    """Custo de imposto sobre o lance. MEI: DAS fixo (1 mês por contrato). CPF: o órgão tira os 20% da IN 116
    e o resto paga INSS 11% (até o teto) e IRRF (simplificado: alíquota efetiva estimada)."""
    if carteira == "MEI":
        return MEI_DAS_MENSAL
    if carteira == "CPF":
        bruto = lance / (1 + CPF_ENCARGO_COMPARACAO)
        inss = min(bruto * INSS_ALIQUOTA_PF, INSS_TETO * INSS_ALIQUOTA_PF)
        irrf = max(0.0, (bruto - inss) * 0.275 - 908.73) if bruto > 7350 else 0.0
        return (lance - bruto) + inss + irrf
    return 0.0


def _lance_minimo(carteira: str, custo: float, margem: float) -> float:
    """Menor lance que deixa custo × (1 + margem) depois dos impostos (busca simples, os impostos crescem com o lance)."""
    alvo = custo * (1 + margem)
    lance = max(alvo, 1.0)
    for _ in range(40):
        liquido = lance - _impostos(carteira, lance)
        if liquido >= alvo:
            break
        lance *= 1.03
    return round(lance, 2)


def avaliar(e: dict[str, Any], p: Parametros, descontos: dict[str, dict[str, float]]) -> Oportunidade:
    from config import GAVETA_TIPO
    tipo = GAVETA_TIPO.get(e["gaveta"], "servico")
    hist = descontos.get(e["gaveta"]) or {}
    desconto = hist["mediana"] if hist.get("n", 0) >= 8 else DESCONTO_PADRAO.get(e["gaveta"], 0.2)

    # o custo da IA é dos itens que atendemos; o preço também tem que ser só desses itens (num registro de preços
    # de R$ 5 mi em que só um pen drive serve, comparar o custo do pen drive com os R$ 5 mi dá lucro de milhões)
    estimado = valor_atendido(e)
    custo = e["custo_estimado"] or 0
    if not custo and e.get("valor_lance"):
        custo = e["valor_lance"] * 0.5                        # sem estimativa de custo: conservador
    preco_provavel = estimado * (1 - desconto)
    lance_min = _lance_minimo(e["carteira"], custo, p.margem_min)
    disputa = estimado > 0 and lance_min <= preco_provavel
    lance_robo = max(lance_min, preco_provavel * 0.99) if disputa else lance_min

    # chance: a IA dá a viabilidade; folga de preço aumenta, lance colado no limite diminui
    base = (e["score_viabilidade"] or 0) / 100
    folga = (preco_provavel - lance_min) / preco_provavel if preco_provavel > 0 else -1
    chance = 0.0 if not disputa else max(0.0, min(0.95, base * (0.6 + min(folga, 0.4)) * p.realismo))

    lucro = lance_robo - custo - _impostos(e["carteira"], lance_robo)
    entrega = p.entrega_produto_dias if tipo == "produto" else ENTREGA_DIAS.get(tipo, 30)
    dias = entrega + PAGAMENTO_DIAS.get(e["esfera_id"] or "N", 45) + p.pagamento_extra_dias
    roi = lucro / custo if custo else 0.0

    motivo = ""
    if not estimado:
        motivo = "orçamento sigiloso: sem preço de referência"
    elif custo and lucro / custo > MARGEM_MAX_CREDIVEL:
        motivo = f"margem de {lucro / custo:.0%} sobre o custo não é crível (custo da IA provavelmente subestimado)"
    elif not disputa:
        motivo = f"lance mínimo do robô (R$ {lance_min:,.0f}) acima do preço provável (R$ {preco_provavel:,.0f})"
    elif chance < p.chance_min:
        motivo = f"chance de ganhar baixa ({chance:.0%})"

    return Oportunidade(
        numero=e["numero_controle"], objeto=(e["objeto_compra"] or "")[:160], orgao=e["razao_social"] or "",
        uf=e["uf"] or "", carteira=e["carteira"], tipo=tipo, esfera=e["esfera_id"] or "N",
        fecha=e["data_encerramento"], estimado=round(estimado, 2), custo=round(custo, 2),
        lance_minimo=lance_min, preco_provavel=round(preco_provavel, 2), lance_robo=round(lance_robo, 2),
        disputa=disputa, chance=round(chance, 3), lucro=round(lucro, 2), lucro_esperado=round(lucro * chance, 2),
        dias_preso=dias, roi=round(roi, 3), roi_dia=round((lucro * chance) / custo / dias, 5) if custo and dias else 0,
        link=e["link_pncp"], motivo=motivo)


@dataclass
class Resultado:
    parametros: Parametros
    escolhidas: list[Oportunidade] = field(default_factory=list)
    fora: list[Oportunidade] = field(default_factory=list)
    linha_tempo: list[dict] = field(default_factory=list)
    investido_total: float = 0
    lucro_esperado: float = 0
    lucro_se_ganhar_todas: float = 0
    pico_preso: float = 0
    fim_dias: int = 0


def simular(p: Parametros) -> Resultado:
    """Ordena por lucro esperado/real/dia e aloca o capital no tempo: cada licitação prende o custo do dia em que
    fecha até o pagamento; com reinvestir, o dinheiro (+ lucro esperado) volta e pode entrar nas seguintes."""
    descontos = db.descontos_historicos()
    with db.conexao() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT * FROM editais WHERE status='analisado' AND carteira IN (%s) "
            "AND data_encerramento > datetime('now','localtime') AND coalesce(decisao,'')!='ignorar' "
            "AND nota_final >= ?" % ",".join("?" * len(p.carteiras)), (*p.carteiras, p.nota_min))]
    ops = [avaliar(e, p, descontos) for e in rows]
    ops = [o for o in ops if o.tipo in p.tipos]

    validas = [o for o in ops if not o.motivo and o.custo > 0 and o.lucro > 0]
    fora = [o for o in ops if o not in validas]
    validas.sort(key=lambda o: -o.roi_dia)

    hoje = datetime.now()
    caixa = p.capital
    retornos: list[tuple[datetime, float]] = []   # (quando o dinheiro volta, custo + lucro esperado)
    escolhidas: list[Oportunidade] = []
    eventos: list[dict] = []

    # o tempo anda por semana: as que fecham na mesma semana disputam o caixa; as mais rentáveis primeiro
    semanas: dict[int, list[Oportunidade]] = {}
    for o in validas:
        d = (datetime.fromisoformat(o.fecha[:19]) - hoje).days
        if d <= p.dias:
            semanas.setdefault(d // 7, []).append(o)
        else:
            o.motivo = "fecha depois do período simulado"
            fora.append(o)
    horas_mes: dict[int, float] = {}       # mês -> horas de trabalho já comprometidas em serviços
    for semana in sorted(semanas):
        inicio_semana = hoje + timedelta(days=semana * 7)
        if p.reinvestir:
            caixa += sum(v for q, v in retornos if q <= inicio_semana)
            retornos = [(q, v) for q, v in retornos if q > inicio_semana]
        pior_caso = 0.0                     # se ganhar TODAS as disputadas nesta semana, quanto sai do caixa
        for o in sorted(semanas[semana], key=lambda o: -o.roi_dia):
            # o dinheiro só sai quando ganha; mas a semana inteira ganha tem que caber no caixa
            if pior_caso + o.custo > caixa:
                o.motivo = "não cabe no dinheiro se ganhar todas as da mesma semana"
                fora.append(o)
                continue
            if o.tipo == "servico":
                horas = o.lance_robo / max(p.valor_hora, 1)
                mes = semana // 4
                if horas_mes.get(mes, 0) + horas * o.chance > p.horas_mes:
                    o.motivo = f"sem horas de trabalho livres nesse mês (~{horas:.0f} h)"
                    fora.append(o)
                    continue
                horas_mes[mes] = horas_mes.get(mes, 0) + horas * o.chance
            pior_caso += o.custo
            inicio = datetime.fromisoformat(o.fecha[:19])
            volta = inicio + timedelta(days=o.dias_preso)
            gasto_medio = o.custo * o.chance          # em média, só paga o custo das que ganha
            retornos.append((volta, gasto_medio + o.lucro_esperado))
            escolhidas.append(o)
            eventos.append({"data": inicio, "investe": gasto_medio, "recebe": 0.0, "lucro": 0.0})
            eventos.append({"data": volta, "investe": 0.0, "recebe": gasto_medio, "lucro": o.lucro_esperado})
        caixa -= sum(o.custo * o.chance for o in escolhidas if o in semanas[semana])

    # linha do tempo: caixa, dinheiro preso e patrimônio a cada evento
    eventos.sort(key=lambda x: x["data"])
    caixa_t, preso, linha, pico, fim = p.capital, 0.0, [], 0.0, 0
    for ev in eventos:
        caixa_t += -ev["investe"] + ev["recebe"] + ev["lucro"]
        preso += ev["investe"] - ev["recebe"]
        pico = max(pico, preso)
        dia = (ev["data"] - hoje).days
        fim = max(fim, dia)
        linha.append({"data": ev["data"].strftime("%Y-%m-%d"), "dia": dia, "caixa": round(caixa_t, 2),
                      "preso": round(max(preso, 0), 2), "patrimonio": round(caixa_t + max(preso, 0), 2)})

    return Resultado(parametros=p, escolhidas=escolhidas, fora=fora, linha_tempo=linha,
                     investido_total=round(sum(o.custo * o.chance for o in escolhidas), 2),
                     lucro_esperado=round(sum(o.lucro_esperado for o in escolhidas), 2),
                     lucro_se_ganhar_todas=round(sum(o.lucro for o in escolhidas), 2),
                     pico_preso=round(pico, 2), fim_dias=fim)


def para_json(r: Resultado) -> dict[str, Any]:
    from dataclasses import asdict
    p = r.parametros
    ganho_pct = r.lucro_esperado / p.capital if p.capital else 0
    meses = max(r.fim_dias, 1) / 30
    return {
        "parametros": asdict(p),
        "resumo": {
            "licitacoes": len(r.escolhidas),
            "vitorias_esperadas": round(sum(o.chance for o in r.escolhidas), 1),
            "investido_total": r.investido_total,
            # faixa: pessimista = metade das vitórias esperadas; otimista = ganha todas que disputar
            "lucro_pessimista": round(r.lucro_esperado * 0.5, 2),
            "chance_media": round(sum(o.chance for o in r.escolhidas) / len(r.escolhidas), 3) if r.escolhidas else 0,
            "lucro_esperado": r.lucro_esperado, "lucro_se_ganhar_todas": r.lucro_se_ganhar_todas,
            "pico_preso": r.pico_preso, "dias_ate_receber_tudo": r.fim_dias,
            "retorno_sobre_capital": round(ganho_pct, 4),
            "retorno_ao_mes": round(ganho_pct / meses, 4) if meses else 0,
            "giro": round(r.investido_total / p.capital, 2) if p.capital else 0,
            "fora_por_motivo": _contar([o.motivo.split(" (")[0].split(":")[0] for o in r.fora]),
        },
        "escolhidas": [asdict(o) for o in r.escolhidas],
        "fora": [asdict(o) for o in sorted(r.fora, key=lambda o: -o.lucro_esperado)[:200]],
        "linha_tempo": r.linha_tempo,
    }


def _contar(itens: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in itens:
        out[i] = out.get(i, 0) + 1
    return dict(sorted(out.items(), key=lambda x: -x[1]))


if __name__ == "__main__":
    import argparse
    import json
    a = argparse.ArgumentParser(description="Simula quanto R$ X renderia disputando no automático")
    a.add_argument("--capital", type=float, default=10_000)
    a.add_argument("--margem", type=float, default=0.15)
    a.add_argument("--dias", type=int, default=180)
    args = a.parse_args()
    res = para_json(simular(Parametros(capital=args.capital, margem_min=args.margem, dias=args.dias)))
    print(json.dumps(res["resumo"], ensure_ascii=False, indent=2))
