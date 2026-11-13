# -*- coding: utf-8 -*-
"""gerar_config.py — monta config\\clientes.json do Painel de Clientes.

  - clientes: config\\clientes_manuais.json (Açaí O Precioso, MS Energy, a outra solar quando entrar);
  - produtos: cada página de venda de D:\\landings-produtos\\conteudo.json (site <slug>.opus-sem-limites.com.br e o
    WhatsApp de venda) + o Instagram do produto em D:\\postador-de-videos\\config\\marcas_instagram.json (campo
    "produto"). Produto com Instagram e sem página (ex.: Hermes Call) também entra.
Rodado pelo publicar.py; sozinho: python gerar_config.py (só mostra o resumo e grava o arquivo).
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MANUAIS = RAIZ / "config" / "clientes_manuais.json"
SAIDA = RAIZ / "config" / "clientes.json"
LANDINGS = Path(r"D:\landings-produtos\conteudo.json")
MARCAS = Path(r"D:\postador-de-videos\config\marcas_instagram.json")
PRODUTOS_IG = Path(r"D:\postador-de-videos\config\instagram_produtos.json")
CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
DOMINIO = "opus-sem-limites.com.br"
NOMES_PRODUTO = {"hermes_call": "Hermes Call"}


def _ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def gerar():
    manuais = _ler(MANUAIS, {}).get("clientes") or []
    lp = _ler(LANDINGS, {})
    zap = str(lp.get("whatsapp") or "").strip()
    marcas = (_ler(MARCAS, {}).get("contas") or {})
    insta_produto = {}
    for conta, m in marcas.items():
        if m.get("produto"):
            insta_produto.setdefault(m["produto"], []).append((conta, m))
    produtos, vistos = [], set()
    for p in lp.get("produtos") or []:
        pid = p.get("id")
        if not pid or not p.get("slug"):
            continue
        contas = insta_produto.get(pid, [])
        cor = contas[0][1].get("cor") if contas else "#10b981"
        produtos.append({"id": pid, "nome": p.get("nome") or pid, "tipo": "produto", "cor": cor, "cidade": "",
                         "instagram": [c for c, _ in contas], "sites": [f"{p['slug']}.{DOMINIO}"],
                         "site": f"https://{p['slug']}.{DOMINIO}/",
                         "whatsapp": f"https://wa.me/{zap}" if zap else "", "ativo": True})
        vistos.add(pid)
    for pid, contas in insta_produto.items():
        if pid in vistos:
            continue
        produtos.append({"id": pid, "nome": contas[0][1].get("marca") or NOMES_PRODUTO.get(pid, pid), "tipo": "produto",
                         "cor": contas[0][1].get("cor") or "#10b981", "cidade": "", "instagram": [c for c, _ in contas],
                         "sites": [], "site": "", "whatsapp": f"https://wa.me/{zap}" if zap else "", "ativo": True})
    ids = [c["id"] for c in manuais]
    clientes = manuais + [p for p in produtos if p["id"] not in ids]
    # contas da casa: as da lista manual + todas as nossas de Instagram (não contam como contato de cliente)
    ignorar = {str(x).strip().lstrip("@").lower() for x in (_ler(MANUAIS, {}).get("ignorar") or []) if str(x).strip()}
    ignorar |= {c.lower() for c in marcas}
    for c in _ler(CREDS, []):
        nome = str(c.get("name") or "").lower().replace("instagram", "").strip()
        if nome:
            ignorar.add(nome)
    for g in _ler(PRODUTOS_IG, {}).get("grupos") or []:
        if g.get("arroba"):
            ignorar.add(g["arroba"].lower())
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({"_leia": "GERADO pelo gerar_config.py — editar config\\clientes_manuais.json",
                                 "ignorar": sorted(ignorar), "clientes": clientes}, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    return clientes


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for c in gerar():
        print(f"{'ativo' if c.get('ativo', True) else 'desligado':9} {c['tipo']:8} {c['id']:18} {c['nome']:32} "
              f"IG={','.join(c['instagram']) or '-':24} sites={','.join(c['sites']) or '-'}")
