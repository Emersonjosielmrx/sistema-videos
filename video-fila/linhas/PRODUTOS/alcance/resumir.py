"""Junta contas.json (coletar_alcance.py) com a origem de cada conta (criada pelo robô? quando? logada onde?) e escreve
RESUMO.md para o Fable (tarefa 10). Rodar depois do coletar_alcance.py."""
import json
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CFG = Path(r"D:\postador-de-videos\config")


def ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def chave(d, *ks):
    for k in ks:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return None


def main():
    dados = ler(AQUI / "contas.json", {}).get("contas", {})
    local, nb = ler(CFG / "instagram_local.json", {}), ler(CFG / "instagram_notebooks.json", {})
    criar = ler(CFG / "instagram_criar_fila.json", {})
    por_arroba = {(v.get("arroba") or k): v for k, v in criar.items() if isinstance(v, dict)}
    marcas = (ler(CFG / "marcas_instagram.json", {}).get("contas") or {})
    linhas, origem = [], {}
    for conta, r in dados.items():
        p = r.get("perfil") or {}
        c = por_arroba.get(conta) or {}
        onde = (["PC1"] if conta in local else []) + [m for m, x in (nb.get(f"ig_{conta}") or {}).items()
                                                       if "logado" in str((x or {}).get("resultado"))]
        o = {"criada_pelo_robo": bool(c), "criada_em": datetime.fromtimestamp(c["t"]).strftime("%d/%m") if c.get("t")
             else None, "logada_em": onde, "marca": (marcas.get(conta) or {}).get("marca")}
        origem[conta] = o
        linhas.append((r.get("grupo"), conta, chave(p, "seguidores", "followers", "follower_count"),
                       chave(p, "seguindo", "following", "following_count"), chave(p, "posts", "media_count"),
                       chave(p, "profissional", "is_professional_account", "is_business_account"),
                       r.get("n_reels"), r.get("views_mediana"), r.get("views_max"), r.get("curtidas_total"),
                       o["criada_em"] or "-", ",".join(onde) or "-", r.get("erro", "")[:60]))
    (AQUI / "contas_origem.json").write_text(json.dumps(origem, ensure_ascii=False, indent=1), "utf-8")
    cab = ("grupo", "conta", "seguidores", "seguindo", "posts", "profissional", "reels lidos", "views mediana",
           "views máx", "curtidas (12 reels)", "criada (robô)", "logada em", "erro")
    md = ["# Alcance das contas de Instagram — dados para a tarefa 10 do Fable (linha PRODUTOS)",
          f"Coletado {datetime.now():%d/%m %H:%M} por `coletar_alcance.py` (perfil + 12 últimos Reels por conta) e "
          "`resumir.py`. Bruto: `contas.json`, `contas_origem.json`. Controle = contas da casa que NÃO são anúncio.",
          "", "| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for l in sorted(linhas, key=lambda x: (x[0] != "produto", x[1])):
        md.append("| " + " | ".join("" if v is None else str(v) for v in l) + " |")
    (AQUI / "RESUMO.md").write_text("\n".join(md) + "\n", "utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
