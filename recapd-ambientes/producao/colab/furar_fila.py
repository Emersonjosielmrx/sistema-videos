r"""furar_fila.py — manda UM longo pro Kaggle NA FRENTE da fila (12/11, dona: "prioridade na parte 13 do Medieval Age").

O alimentador só manda pedido novo quando a fila tem menos pedidos que GPUs; com 14 pedidos pra 14 GPUs a parte 13 nunca
entrava. Aqui: prepara (baixa + roteiro, igual ao alimentador) e envia com pid "20261027_000000_<id>" — o trabalhador pega
o 1º pedido livre por NOME, então este é o próximo a renderizar. Marca em alimentar_estado.json "enviados" (o
alimentador não manda de novo). O pronto volta pela rotina normal (cliente.py alimentar recolhe e põe no Drive).

    python furar_fila.py PReloN5HWSI        # parte 13
    python furar_fila.py pnX8RlSn7Yk 1      # parte 14 (logo atrás)
"""
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import cliente  # noqa: E402


def main(vid, ordem=0):
    p = cliente.preparar(f"https://www.youtube.com/watch?v={vid}")
    pid = f"20261027_{ordem:06d}_{vid}"  # ordem: 0 = parte 13, 1 = 14, 2 = 15 (o nome decide a vez)
    # 12/11: item da fontes_prioridade com canal_destino (garimpar_parecidos) leva o canal junto -> posta só nele
    extra = {k: p[k] for k in ("vid", "titulo", "nome", "url")}
    try:
        cfg = json.loads((AQUI.parent / "config" / "fontes_prioridade.json").read_text(encoding="utf-8"))
        item = next((v for v in cfg.get("videos", []) if v.get("id") == vid), {})
        extra.update({k: item[k] for k in ("canal_destino", "tema", "tipo") if item.get(k)})
    except (OSError, ValueError):
        pass
    cliente.enviar(p["work"], p["video"], p["roteiro"], p["titulo"], extra, pid=pid)
    if extra.get("canal_destino"):
        print(f"canal de destino: {extra['canal_destino']} ({extra.get('tema')})", flush=True)
    arq = AQUI / "alimentar_estado.json"
    est = json.loads(arq.read_text(encoding="utf-8-sig"))
    est.setdefault("enviados", {})[vid] = time.time()
    arq.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"enviado na frente: {pid} — {p['titulo'][:80]}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
