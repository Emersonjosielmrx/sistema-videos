"""teste_placar_ajustado.py — o placar dos testes A/B não pode dar vencedor só porque um braço caiu mais vezes no
horário nobre. Dados inventados, sem ler o D:, sem rede.   python teste_placar_ajustado.py
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import placar_variantes as pv  # noqa: E402

TESTE = "teste_inventado_xyz"   # não existe em variantes.TESTES: cai no padrão A/B


def _linhas(efeito_b=1.0, noite_a=0.3, noite_b=0.7, n=240, semente=3):
    """Canal fraco (noite ~1.000 views, dia ~6) e canal médio (noite ~1.500, dia ~300). O braço B cai mais à noite
    (noite_b) do que o A (noite_a); efeito_b multiplica as views do B (1.0 = o teste não faz diferença nenhuma)."""
    r = random.Random(semente)
    base = datetime(2026, 11, 1, tzinfo=pv.BR)
    out = []
    for k in range(n):
        canal = "fraco" if k % 2 else "medio"
        braco = "B" if r.random() < 0.5 else "A"
        noite = r.random() < (noite_b if braco == "B" else noite_a)
        hora = r.choice((21, 22)) if noite else r.choice((9, 12, 15, 18))
        centro = {("fraco", True): 1000, ("fraco", False): 6, ("medio", True): 1500, ("medio", False): 300}[(canal, noite)]
        v = centro * r.lognormvariate(0, 0.5) * (efeito_b if braco == "B" else 1.0)
        pub = base + timedelta(days=k // 8, hours=hora)
        out.append(dict(vid=f"v{k}", canal=canal, canal_id=canal, pasta="x", pub=pub.isoformat(), idade_h=100.0,
                        V=round(v), medido=True, pct=None, bracos={TESTE: braco},
                        elegivel=round(v) >= pv.ELEGIVEL, log_rel=None))
    return pv.ajustar_por_periodo(out)


def test_razao_ajustada():
    ls = _linhas()
    noite = [x for x in ls if x["noite"]]
    dia = [x for x in ls if not x["noite"]]
    assert noite and dia and all(0.125 <= x["rz"] <= 8 for x in ls)
    # dentro de cada período a razão fica em volta de 1 — o horário saiu da conta
    for grupo in (noite, dia):
        acima = sum(x["acima"] for x in grupo) / len(grupo)
        assert 0.35 <= acima <= 0.65, acima
    sem = pv.ajustar_por_periodo([dict(canal="c", pub=None, V=10, medido=True), dict(canal="c", pub="2026-11-01T21:00:00-03:00", V=None, medido=False)])
    assert all(x["rz"] is None for x in sem)


def test_braco_que_so_caiu_a_noite_nao_vence():
    ls = _linhas(efeito_b=1.0)
    r = pv.placar(ls, {})[TESTE]
    assert r["p_melhor_que_ref_500"]["B"] >= 0.95, r["p_melhor_que_ref_500"]        # a conta antiga dava vencedor
    assert 0.1 <= r["p_melhor_que_ref_ajustado"]["B"] <= 0.9, r["p_melhor_que_ref_ajustado"]   # a ajustada não
    assert "PRONTO" not in r["estado"] and not r["sugestao"], (r["estado"], r["sugestao"])


def test_efeito_de_verdade_continua_aparecendo():
    ls = _linhas(efeito_b=1.8, noite_a=0.5, noite_b=0.5)
    r = pv.placar(ls, {})[TESTE]
    assert r["p_melhor_que_ref_ajustado"]["B"] >= 0.95, r["p_melhor_que_ref_ajustado"]
    assert "PRONTO" in r["estado"] and "B" in r["sugestao"], (r["estado"], r["sugestao"])


def test_braco_bom_que_so_saiu_de_dia_aparece():
    # B é melhor (1.8x) mas quase só saiu de dia: na conta antiga parecia PIOR que o A
    ls = _linhas(efeito_b=1.8, noite_a=0.7, noite_b=0.1)
    r = pv.placar(ls, {})[TESTE]
    assert r["p_melhor_que_ref_500"]["B"] <= 0.2, r["p_melhor_que_ref_500"]
    assert r["p_melhor_que_ref_ajustado"]["B"] >= 0.95, r["p_melhor_que_ref_ajustado"]


def test_relatorio_sai():
    ls = _linhas()
    md = pv.relatorio_md(pv.placar(ls, {}), ls, "2026-11-13 12:00")
    assert "AJUSTADO pelo horário" in md and "acima do grupo" in md


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                fn()
                print(f"ok    {nome}")
            except AssertionError as err:
                falhas += 1
                print(f"FALHA {nome}: {err!r}"[:700])
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
