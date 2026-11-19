"""19/11 (dona via claude-f1: "os próximos longos com narradores top, momo, mike etc." + Fish é o padrão): pedidos de
longo LIVRES na fila do Drive que ainda levam narrador SEM referencia_fish (solemsun, moana, thomas_shelby...) ganham
a escolha nova (cliente._narradores_por_grupo: só quem tem Fish, momo/mike abrindo). Pedido em andamento/pronto não muda.
A abertura com fala real (intro_voz.*) só é mantida se o narrador dela continuar na lista.
    python fila_so_fish.py            # mostra
    python fila_so_fish.py --aplicar  # grava
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import cliente  # noqa: E402
import anime_voz_clonada  # noqa: E402
from corrigir_pedidos_fila import rc  # noqa: E402

APLICAR = "--aplicar" in sys.argv


def main():
    com_ref = anime_voz_clonada._vozes_com_fish()
    pedidos = cliente._pedidos()
    mudou = 0
    for pid in sorted(pedidos):
        arqs = pedidos[pid]
        if "pedido.json" not in arqs or any(a.startswith("em_andamento") or a in ("pronto.json", "erro.json")
                                            for a in arqs):
            continue
        pedido = cliente._pedido_json(pid) or {}
        antes = pedido.get("vozes_lista") or []
        sem = [v for v in antes if v not in com_ref]
        if not antes or not sem:
            continue
        t, vozes = cliente._teste_narradores()
        if not vozes:
            raise SystemExit("sem vozes por grupo")
        intro = "intro_voz.json" in arqs
        if intro:
            try:
                iv = json.loads(rc("cat", f"{cliente.FILA}/{pid}/intro_voz.json")).get("voz")
            except ValueError:
                iv = None
            if iv in com_ref:  # a abertura é de um narrador com Fish: ele continua abrindo
                vozes = [iv] + [v for v in vozes if v != iv]
        print(f"{pid}: {pedido.get('titulo', '')[:50]}\n   antes: {', '.join(antes)} (sem Fish: {', '.join(sem)})"
              f"\n   agora: {', '.join(vozes)}")
        pedido.update(vozes_lista=vozes, voz_clonada=vozes[0], narradores_fish="19/11 trocado pra só Fish")
        if APLICAR:
            rc("rcat", f"{cliente.FILA}/{pid}/pedido.json", entrada=json.dumps(pedido, ensure_ascii=False))
            vids = t.setdefault("videos", [])
            antigo = next((v for v in vids if v.get("pid") == pid), None)
            if antigo:
                antigo["vozes"] = vozes
            else:
                vids.append({"pid": pid, "vozes": vozes})
            t.pop("_modo", None)
            cliente.TESTE_NARRADORES.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
            cliente._PEDIDO_CACHE.pop(pid, None)
        mudou += 1
    print(f"{'gravados' if APLICAR else 'mudariam'}: {mudou}")


if __name__ == "__main__":
    main()
