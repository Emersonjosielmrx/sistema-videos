"""29/10 (Fable, LONGOS_13 2.2/2.3): pedidos que já estavam na fila do Drive ANTES das regras de narradores por grupo
(29/10 17h) carregam a lista velha (10 vozes de jogo/terciárias, Patrick Estrela, Moana abrindo). Foi assim que o
Top Fighter (OLYsz, pedido de 27/10) saiu "todo mundo falando como a Moana" no render de 29/10. Este script troca,
NO PRÓPRIO pedido.json da fila (sem subir vídeo de novo), a lista de narradores pela escolha por grupos de agora
(cliente._narradores_por_grupo) e acrescenta as vozes extras (personagens + mascote) que o Kaggle baixa do cache.
Só pedidos LIVRES (sem em_andamento); quem já tem "grupos" no carimbo não muda.

    python corrigir_pedidos_fila.py            # mostra o que mudaria
    python corrigir_pedidos_fila.py --aplicar  # grava
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cliente  # noqa: E402

RC = r"D:\tools\rclone.exe"
FILA = cliente.FILA
APLICAR = "--aplicar" in sys.argv


def rc(*a, entrada=None):
    r = subprocess.run([RC, *a], input=entrada, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(f"rclone {a[0]} falhou: {r.stderr[-300:]}")
    return r.stdout


def vozes_extra():
    try:
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "longo.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    p, m = cfg.get("personagens") or {}, (cfg.get("mascote") or {}).get("voz_clone")
    if not (p.get("ligado") or m):
        return []
    return list(dict.fromkeys([v for v in (p.get("vozes_m") or []) + (p.get("vozes_f") or [])
                               + (p.get("vozes_monstro") or []) + [m] if v]))


def main():
    pedidos = cliente._pedidos()
    extra = vozes_extra()
    t = None
    mudou = 0
    for pid in sorted(pedidos):
        arqs = pedidos[pid]
        if "pedido.json" not in arqs:
            continue
        if any(a.startswith("em_andamento") or a in ("pronto.json", "erro.json") for a in arqs):
            print(f"{pid}: em andamento/pronto — não mexo")
            continue
        pedido = cliente._pedido_json(pid) or {}
        if not pedido.get("vozes_lista"):
            print(f"{pid}: sem revezamento — não mexo")
            continue
        if "grupos" in str(pedido.get("teste_narradores", "")):
            print(f"{pid}: já é por grupos ({', '.join(pedido['vozes_lista'])})")
            continue
        t, vozes = cliente._teste_narradores()
        if not vozes:
            raise SystemExit("teste_narradores: sem vozes por grupo (Drive/pth?)")
        print(f"{pid}: {pedido.get('titulo', '')[:50]}\n   antes: {', '.join(pedido['vozes_lista'])}\n   agora: {', '.join(vozes)}")
        pedido.update(vozes_lista=vozes, voz_clonada=vozes[0], voz_clonada_base=pedido.get("voz_clonada_base") or "misto",
                      teste_narradores=f"vídeo {len(t.get('videos', [])) + 1} do revezamento (grupos 29/10, corrigido na fila)")
        if extra and not pedido.get("vozes_extra"):
            pedido["vozes_extra"] = extra
        if APLICAR:
            rc("rcat", f"{FILA}/{pid}/pedido.json", entrada=json.dumps(pedido, ensure_ascii=False))
            vids = t.setdefault("videos", [])
            antigo = next((v for v in vids if v.get("pid") == pid), None)
            if antigo:
                antigo["vozes"] = vozes
            else:
                vids.append({"pid": pid, "vozes": vozes})
            cliente.TESTE_NARRADORES.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
            cliente._PEDIDO_CACHE.pop(pid, None)
            mudou += 1
    print(f"{'gravados' if APLICAR else 'mudariam'}: {mudou} pedido(s)" + ("" if APLICAR else " (rode com --aplicar)"))


if __name__ == "__main__":
    main()
