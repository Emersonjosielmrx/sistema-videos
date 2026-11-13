"""Gera as CÓPIAS do Editor de Reels com mais recursos de edição, sem mexer no original (fluxo y3ckq7OSPtYWWxZo):
  V2 Dinâmico (/webhook/editor-reel-v2) e V3 Premium (/webhook/editor-reel-v3).
Parte do fluxo do original (../editor/fluxo_editor.json, gerado por ../editor/gera_editor.py), troca caminhos, chaves
do Redis, nome e títulos, e só os nós 🧩 Prepara o pedido à IA, 🧩 Lê a direção e 🧩 Monta a edição (arquivos daqui).
Uso: python gera_versoes.py  ->  fluxo_v2.json e fluxo_v3.json (importar com ../n8n6.py importa <arquivo>)"""
import json, uuid
from pathlib import Path
import exemplos_reais  # V5+: vídeos reais das solares como exemplo
import cards_svg  # V6: cards em SVG
import envio_rapido  #página sem nó de código + envio que responde na hora e tenta de novo (falha de conexão do cliente, 02/11)

AQUI = Path(__file__).parent
ORIG = (AQUI.parent / "editor" / "fluxo_editor.json").read_text(encoding="utf-8")
VERSOES = [
    (2, "V2 Dinâmico", "jump cut de zoom, abertura grande, palavras-chave, efeitos sonoros, flash, cor"),
    (3, "V3 Premium", "tudo da V2 + emojis nas palavras-chave, zoom rápido e glitch"),
    (4, "V4 MIX", "legenda MIX + cards da propaganda: pergunta, aula, cartão final"),
    (5, "V5 MIX exemplos reais", "V4 MIX com os vídeos reais da Advance e da Globo Solar como exemplo"),
    (6, "V6 Cards modernos", "V5 com cards em SVG: cantos redondos, degradê, brilho, sombra e animação de entrada"),
]
for nivel, rotulo, resumo in VERSOES:
    t = ORIG.replace("editor-reel", f"editor-reel-v{nivel}").replace("edr:", f"ed{nivel}:")
    t = t.replace("Editor de Reels com IA</title>", f"Editor de Reels com IA · {rotulo}</title>")
    t = t.replace("✂️ Editor de Reels com IA</h1>", f"✂️ Editor de Reels com IA · {rotulo}</h1>")
    w = envio_rapido.aplica(json.loads(t), nivel)
    if nivel >= 5:
        w = exemplos_reais.aplica(w, nivel)
    if nivel >= 6:
        w = cards_svg.aplica(w, nivel)
    w["name"] = f"Editor de Reels com IA · {rotulo} ({resumo})"
    codigos = {"🧩 Prepara o pedido à IA": "prepara_ia.js", "🧩 Lê a direção": "le_direcao.js", "🧩 Monta a edição": "monta_edicao.js"}
    for n in w["nodes"]:
        n["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"editor-v{nivel}|{n['name']}"))
        if "webhookId" in n:
            n["webhookId"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"editor-v{nivel}|webhook|{n['name']}"))
        if n["name"] in codigos:
            n["parameters"]["jsCode"] = (AQUI / codigos[n["name"]]).read_text(encoding="utf-8").replace("__NIVEL__", str(nivel))
        if n["type"] == "n8n-nodes-base.stickyNote" and n["name"] == "Nota · Comece aqui":
            n["parameters"]["content"] = n["parameters"]["content"].replace(
                "# ✂️ EDITOR DE REELS COM IA (VÍDEO GRAVADO → REEL PRONTO)",
                f"# ✂️ EDITOR DE REELS COM IA · {rotulo.upper()} (VÍDEO GRAVADO → REEL PRONTO)\n"
                f"🆕 **Esta versão:** {resumo}. Sai em **1080x1920**.")
    assert "editor-reel\"" not in json.dumps(w) and "edr:" not in json.dumps(w)
    assert sum(1 for n in w["nodes"] if n["name"] in codigos) == 3
    (AQUI / f"fluxo_v{nivel}.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", nivel, w["name"], len(w["nodes"]), "nós")
