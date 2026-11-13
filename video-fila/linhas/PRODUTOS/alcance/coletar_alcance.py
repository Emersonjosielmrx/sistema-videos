"""Dados de ALCANCE das contas de Instagram (tarefa 10 do Fable, PRODUTOS_onde_parei_e_o_que_nao_vejo.md): por que os
Reels de produto ficam em 0–2 views. Por conta: perfil (seguidores, seguindo, posts, profissional, categoria, bio/link)
e os últimos Reels (views, curtidas, comentários, data). Compara contas de PRODUTO com contas da casa que NÃO são
anúncio (controle). Cuidado com o Instagram: 2 chamadas por conta, 25 s entre contas, para tudo no 1º 401/403/429.

    D:\\veo\\venv\\Scripts\\python.exe coletar_alcance.py      (precisa do curl_cffi do venv do Veo)
Saída: contas.json (bruto) e RESUMO.md nesta pasta.
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.instagram.web import InstagramWeb  # noqa: E402

PRODUTO = ["inovarecom.ia", "futebolcom.ia2", "sintetizerisada", "disparoemmassa.ia", "followupia.ia", "vpsblindada.ia",
           "fabricademarketing.ia", "crmchatwoot.ia", "mentoriasia.ia", "landingpageia.ia", "gestaodegrupos.ia",
           "agentesdeia.ia", "superchatia.ia"]
CONTROLE = ["_lucrocomia_", "recenas.ia", "msenergycap"]


def _plano(d, *ks):
    for k in ks:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


def um(conta):
    ig = InstagramWeb(conta, perfil_cofre=f"ig_{conta}")
    p = ig.perfil_info() or {}
    time.sleep(4)
    rs = ig.reels(quantos=12) or []
    vs = [r.get("views") for r in rs if isinstance(r.get("views"), int)]
    return {"perfil": p, "reels": rs, "n_reels": len(rs),
            "views_mediana": statistics.median(vs) if vs else None, "views_max": max(vs) if vs else None,
            "curtidas_total": sum(r.get("curtidas") or 0 for r in rs)}


def main():
    saida, ant = AQUI / "contas.json", {}
    try:
        ant = json.loads(saida.read_text("utf-8"))
    except (OSError, ValueError):
        pass
    res = ant.get("contas", {})
    alvo = PRODUTO + CONTROLE
    if "--faltam" in sys.argv:  # só as que ainda não foram lidas (ou deram erro)
        alvo = [c for c in alvo if c not in res or res[c].get("erro")]
    for i, conta in enumerate(alvo):
        if i:
            time.sleep(25)
        try:
            res[conta] = {"grupo": "produto" if conta in PRODUTO else "controle", "lido": datetime.now().isoformat(
                timespec="seconds"), **um(conta)}
            r = res[conta]
            print(f"{conta}: seguidores={_plano(r['perfil'], 'seguidores', 'followers')} reels={r['n_reels']} "
                  f"views mediana={r['views_mediana']} max={r['views_max']}", flush=True)
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {str(e)[:160]}"
            res[conta] = {"grupo": "produto" if conta in PRODUTO else "controle", "erro": msg}
            print(f"{conta}: ERRO {msg}", flush=True)
            if any(c in msg for c in ("401", "403", "429")):
                print("Instagram recusou: paro aqui (não arriscar as contas)")
                break
        saida.write_text(json.dumps({"atualizado": datetime.now().isoformat(timespec="seconds"), "contas": res},
                                    ensure_ascii=False, indent=1, default=str), "utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
