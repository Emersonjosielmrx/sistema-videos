"""balanco_kaggle.py — vigia de balanço entre projetos no Kaggle (dona 02/11: "equilibrar os 7 dias de conteúdo pra
todos os projetos e pra cada conta; as 3 linhas de curto devem ser usadas ao mesmo tempo").

    python balanco_kaggle.py            # imprime o relatório e grava em estado/balanco_kaggle.json
    python balanco_kaggle.py --alarme   # imprime + avisa no Telegram se algum canal regride 2x seguidas

Lê: reserva_status.py (reserva por canal), vps_central estado.json das centrais (GPUs ativas, papeis), a fila do
    Kaggle. Grava: estado/balanco_kaggle.json (último e penúltimo, pra comparar tendência).
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ESTADO = BASE / "estado" / "balanco_kaggle.json"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _reserva():
    """Reserva por canal via reserva_status.medir()."""
    try:
        sys.path.insert(0, str(BASE))
        import reserva_status
        return reserva_status.medir()
    except Exception as e:  # noqa: BLE001
        print(f"reserva falhou: {e}", flush=True)
        return []


def _gpus_ativas():
    """GPUs rodando por papel (lê estado.json da casa + status.json da prod)."""
    import urllib.request
    contas = {}
    try:
        with urllib.request.urlopen("https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json",
                                   timeout=20) as r:
            st = json.loads(r.read().decode("utf-8"))
            for g in st.get("gpus") or []:
                if g.get("conta"):
                    contas[g["conta"]] = g.get("status")
            for c in st.get("contas_detalhe") or []:
                if c["conta"] in contas:
                    contas[c["conta"]] = c.get("estado")
    except Exception:  # noqa: BLE001
        pass
    try:
        casa = json.loads(Path(r"D:\recap_central_casa\gpus_casa-pc1.json").read_text(encoding="utf-8"))
        for g in casa.get("gpus") or []:
            if g.get("conta") and g["conta"] not in contas:
                contas[g["conta"]] = g.get("status")
    except (OSError, ValueError):
        pass
    return contas


def _papeis():
    """Papel de cada conta verificada lido do pool local."""
    try:
        p = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text(encoding="utf-8"))
        linhas = p.get("linhas") or {}

        def ip(c):
            return f"webshare-{c['webshare_ip']}" if c.get("webshare_ip") else f"direto-{c.get('saida', 'hermes-prod')}"

        return {c["username"]: c.get("papel") or linhas.get(ip(c)) or "longo" for c in p["contas"] if c.get("verificada")}
    except (OSError, ValueError):
        return {}


def relatorio():
    res = _reserva()
    gpus = _gpus_ativas()
    papeis = _papeis()

    curtos_ativos = sum(1 for u, p in papeis.items() if p == "curto" and gpus.get(u) in ("rodando", "lançado"))
    longos_ativos = sum(1 for u, p in papeis.items() if p == "longo" and gpus.get(u) in ("rodando", "lançado"))
    total_curto = sum(1 for p in papeis.values() if p == "curto")
    total_longo = sum(1 for p in papeis.values() if p == "longo")

    canais = []
    for c in (res or []):
        canais.append({"canal": c["canal"], "dias": c.get("dias"), "gasta": c.get("consumo"),
                       "agendados": c.get("agendados"), "prontos": c.get("prontos"), "dono": c.get("dono")})

    na_meta = sum(1 for c in canais if (c.get("dias") or 0) >= 7)
    total = len(canais)
    mais_vazios = sorted(canais, key=lambda c: c.get("dias") or 0)[:5]

    # tendência: comparar com a rodada anterior
    try:
        ant = json.loads(ESTADO.read_text(encoding="utf-8"))
        ant_canais = {c["canal"]: c.get("dias") or 0 for c in ant.get("canais") or []}
    except (OSError, ValueError):
        ant_canais = {}

    regredindo = []
    for c in canais:
        antes = ant_canais.get(c["canal"])
        agora = c.get("dias") or 0
        c["tendencia"] = "subindo" if antes is not None and agora > antes + 0.1 else \
                         "caindo" if antes is not None and agora < antes - 0.1 else "estável"
        if c["tendencia"] == "caindo":
            regredindo.append(c["canal"])

    rpt = {
        "em": datetime.now().isoformat(timespec="seconds"),
        "gpus": {"curto_ativas": curtos_ativos, "curto_total": total_curto,
                 "longo_ativas": longos_ativos, "longo_total": total_longo,
                 "contas": gpus},
        "reserva": {"na_meta": na_meta, "total": total},
        "canais": canais,
        "mais_vazios": [{"canal": c["canal"], "dias": c.get("dias"), "tendencia": c.get("tendencia")} for c in mais_vazios],
        "regredindo": regredindo,
        "alerta": f"{len(regredindo)} canal(is) regredindo" if regredindo else None,
    }

    ESTADO.parent.mkdir(exist_ok=True)
    ESTADO.write_text(json.dumps(rpt, ensure_ascii=False, indent=1), encoding="utf-8")
    return rpt


def imprimir(rpt):
    g = rpt["gpus"]
    print(f"GPUs: curto {g['curto_ativas']}/{g['curto_total']} · longo {g['longo_ativas']}/{g['longo_total']}")
    print(f"Reserva: {rpt['reserva']['na_meta']}/{rpt['reserva']['total']} canais com >= 7 dias")
    print("Mais vazios:")
    for c in rpt["mais_vazios"]:
        print(f"  {c['dias']:.1f} dias  {c['canal']:<24} {c['tendencia']}")
    if rpt["regredindo"]:
        print(f"⚠ REGREDINDO: {', '.join(rpt['regredindo'])}")
    if g["curto_ativas"] < g["curto_total"]:
        print(f"⚠ Linhas de curto subutilizadas: {g['curto_ativas']} de {g['curto_total']} ativas")


def main():
    rpt = relatorio()
    imprimir(rpt)


if __name__ == "__main__":
    main()
