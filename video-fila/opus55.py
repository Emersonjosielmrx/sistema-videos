"""Modo 2 do Opus 5.5 — ASSUMIR (24/10, plano PLANO_OPUS55_CAMADAS.md).

Com o botão "Opus 5.5 ASSUMIR LIGAR" (arquivo estado\\opus55_ASSUMIU), enquanto houver cota nas contas Claude (medidor
cota_claude.py), TODOS os papéis das melhorias (busca, plano, críticos, revisores) rodam no Opus 5.5 pela rota do VS Code
com esforço máximo, no mesmo fluxo de sempre (guarda de comandos, desfazer, vigia e auditoria valendo). Sem cota, acima
do teto do dia, ou com o botão desligado, o motor volta sozinho ao Kiro + Gemini ("devolve o controle").
Reserva: nunca usa a última fatia da semana (opus55_reserva_pct) — é da dona no VS Code.
Também avisa a dona (1x por dia) quando há token quase vencendo, pra ela decidir ligar.
"""
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
FLAG = BASE / "estado" / "opus55_ASSUMIU"
MODELO = "cc/claude-opus-5-5"
PADRAO = {"opus55_reserva_pct": 15, "opus55_pedidos_dia_max": 10, "opus55_esforco": "max", "opus55_cota_min": 10}


def ligado():
    return FLAG.exists()


def ligar():
    FLAG.parent.mkdir(parents=True, exist_ok=True)
    FLAG.write_text(f"ligado em {datetime.now():%d/%m %H:%M}", encoding="utf-8")
    return ("Opus 5.5 ASSUMIU as melhorias: enquanto houver cota (guardando a sua reserva), todos os papéis rodam no "
            "Opus 5.5 com raciocínio máximo. Sem cota ou no teto do dia, volta sozinho ao Kiro + Gemini.")


def desligar():
    FLAG.unlink(missing_ok=True)
    return "Opus 5.5 DESLIGADO das melhorias: o pedido que estiver rodando termina; os próximos voltam ao Kiro + Gemini."


def _cota(c, e):
    """Leitura da cota Claude, refeita no máximo a cada opus55_cota_min minutos (ssh só leitura)."""
    import cota_claude
    d = cota_claude.atual(max_min=30)
    o = e.setdefault("opus55", {})
    if (not d or time.time() - float(o.get("cota_lida", 0)) > float(c.get("opus55_cota_min", 10)) * 60):
        o["cota_lida"] = time.time()
        bruto = cota_claude.ler()
        if bruto is not None:
            d = cota_claude.resumir(bruto)
            cota_claude.gravar(d)
    return d


def ativo(c, e):
    """(True, motivo) se os pedidos agora devem ir pro Opus 5.5."""
    c = dict(PADRAO, **c)
    o = e.setdefault("opus55", {})
    hoje = datetime.now().strftime("%Y-%m-%d")
    if o.get("dia") != hoje:
        o.update(dia=hoje, pedidos=0, aviso_quase=o.get("aviso_quase"))
    if not ligado():
        return False, "desligado"
    d = _cota(c, e)
    if not d:
        return False, "sem leitura da cota Claude"
    if int(o.get("pedidos", 0)) >= int(c["opus55_pedidos_dia_max"]):
        return False, f"teto de {c['opus55_pedidos_dia_max']} pedidos hoje"
    if int(d.get("com_cota") or 0) < 1:
        return False, "nenhuma conta Claude com cota agora"
    reserva = float(c["opus55_reserva_pct"]) / 100 * float(d.get("ativas") or 0)
    if float(d.get("semana_contas_livres") or 0) <= reserva:
        return False, f"só sobra a reserva da dona ({d.get('semana_contas_livres')} de {reserva:.2f})"
    return True, f"{d['com_cota']} conta(s) com cota"


def ajustar(kw, c, e):
    """Chamado pelo _pedir do motor: se o modo está ativo, o pedido vai pro Opus 5.5 (e conta no teto)."""
    try:
        ok, motivo = ativo(c, e)
    except Exception as ex:  # noqa: BLE001 — na dúvida, fluxo normal
        ok, motivo = False, f"erro ({type(ex).__name__})"
    e.setdefault("opus55", {})["motivo"] = motivo
    if not ok:
        return kw
    e["opus55"]["pedidos"] = int(e["opus55"].get("pedidos", 0)) + 1
    return dict(kw, modelo=MODELO, rota="vscode", esforco=dict(PADRAO, **c)["opus55_esforco"], pensar=False)


def aviso_quase_vencendo(c, e, avisar):
    """1x por dia: se há token quase vencendo e o modo está desligado, sugere ligar."""
    import cota_claude
    d = cota_claude.atual(max_min=60)
    o = e.setdefault("opus55", {})
    hoje = datetime.now().strftime("%Y-%m-%d")
    if d and int(d.get("quase_vencendo") or 0) > 0 and not ligado() and o.get("aviso_quase") != hoje:
        o["aviso_quase"] = hoje
        avisar(f"Tem cota do Opus 5.5 quase vencendo ({d['quase_vencendo']} conta(s) com 30%+ da semana sobrando e "
               "renovando em até 24 h). Se quiser aproveitar, aperte \"Opus 5.5 ASSUMIR LIGAR\" na área de trabalho.")


def status_txt(c, e):
    o = e.get("opus55") or {}
    return (f"Opus 5.5 ASSUMIR: {'LIGADO' if ligado() else 'desligado'} | hoje {o.get('pedidos', 0)} pedido(s)"
            + (f" | agora: {o.get('motivo')}" if o.get("motivo") else ""))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ("ligar", "desligar"):
        print(ligar() if sys.argv[1] == "ligar" else desligar())
