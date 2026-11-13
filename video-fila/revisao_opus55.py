"""Modo 1 do Opus 5.5 — REVISAR AGORA (botão da área de trabalho; 24/10, plano PLANO_OPUS55_CAMADAS.md).

"preparar" monta o dossiê das melhorias aplicadas desde a última revisão (mesmo formato da auditoria final) em
estado\\opus55\\revisao_<data>.md e imprime o caminho; o botão (opus55_revisar.ps1) abre o Claude Code com o Opus 5.5
nesse dossiê, numa janela onde a dona lê o relatório e pergunta o que quiser. Só lê: nada aqui muda arquivo de projeto.
Uso: python revisao_opus55.py preparar [--seco] [--max N]
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
PASTA = BASE / "estado" / "opus55"
MARCA = PASTA / "ultima_revisao.json"

INSTRUCAO = """# REVISÃO DO OPUS 5.5 (pedida pela dona pelo botão)
Você é a camada final de revisão das melhorias contínuas automáticas dos projetos de vídeo da dona. Abaixo estão as
aplicações feitas desde a última revisão, já filtradas pelas outras camadas (Kiro + Gemini: busca em dupla, críticos do
plano, 3 revisores; e a auditoria do Opus 4.6 quando ele estava no ar). Use o CHECKLIST do começo do dossiê.
Pode abrir arquivos e logs pra conferir. A dona pediu que você RESOLVA SOZINHO, sem pedir permissão: o que estiver
errado, corrija ou volte como estava (editando o arquivo; o backup de cada edição é guardado e dá pra desfazer pelo
painel). Siga o PROIBIDO e as regras da dona (a guarda bloqueia o resto). O que não for arquivo (mídia, postagem,
conta, dinheiro) NÃO faça: só diga o que precisa. Confira o que corrigiu (py_compile/teste).
ENTREGUE, em pt-BR simples, nesta ordem:
1. Resumo de 3 linhas (quantas olhou, quantas OK, quantas com problema).
2. Tabela: aplicação | projeto | o que fez | veredito (OK / CORRIGI / VOLTEI / DONA DECIDE) | por quê (curto).
3. Para cada problema: a prova e o que você fez (arquivo e o que mudou).
4. Padrões: o que as outras camadas deixaram passar e uma regra/lição sugerida pra elas.
Depois do relatório, fique à disposição: a dona pode contestar ou perguntar.
"""


def _itens(max_itens):
    import melhoria_continua as m
    import painel_ia
    e = m._estado()
    desde = 0.0
    try:
        desde = float(json.loads(MARCA.read_text(encoding="utf-8")).get("ts", 0))
    except (OSError, ValueError):
        desde = time.time() - 48 * 3600  # primeira vez: últimas 48 h
    ents = []
    vistos = set()
    for f in reversed(e.get("feitos") or []):
        jid = f.get("job")
        if not jid or jid in vistos:
            continue
        j = painel_ia.ler(jid) or {}
        if j.get("tipo") != "aplicar":
            continue
        try:
            quando = datetime.fromisoformat(j.get("fim") or j["criado"]).timestamp()
        except (KeyError, ValueError):
            continue
        if quando < desde:
            continue
        vistos.add(jid)
        ent = dict((e.get("auditar") or {}).get(jid) or {})
        ent.setdefault("job", jid)
        ent.setdefault("prio", 1)
        ent.setdefault("motivos", ["revisão pelo botão"])
        ent.setdefault("revisores", {})
        if j.get("desfeito_em"):
            ent["motivos"] = list(ent["motivos"]) + [f"JÁ DESFEITA em {j['desfeito_em'][:16]}"]
        if ent.get("veredito"):
            ent["motivos"] = list(ent["motivos"]) + [f"auditoria Opus 4.6: {ent['veredito'].get('veredito')}"]
        ents.append(ent)
        if len(ents) >= max_itens:
            break
    return ents


def preparar(seco=False, max_itens=8):
    import auditoria_final as af
    import melhoria_continua as m
    ents = _itens(max_itens)
    c = dict(m.cfg(), opus_dossie_max_chars=90000)
    corpo = af.montar_dossie(m._estado(), c, ents, "revisão do Opus 5.5") if ents else "(nenhuma aplicação nova desde a última revisão)"
    texto = INSTRUCAO + "\n" + af.SISTEMA_JUIZ.split("VEREDITOS:")[0] + "\n" + corpo
    texto = af._limpo(texto) if hasattr(af, "_limpo") else texto  # sem chave/cookie no dossiê
    PASTA.mkdir(parents=True, exist_ok=True)
    arq = PASTA / f"revisao_{datetime.now():%Y%m%d_%H%M%S}.md"
    if not seco:
        arq.write_text(texto, encoding="utf-8")
        MARCA.write_text(json.dumps({"ts": time.time(), "arquivo": str(arq), "itens": [x["job"] for x in ents]}),
                         encoding="utf-8")
    return arq, len(ents), len(texto)


def criar_job(arq):
    """Pedido do painel pra esta sessão de chat (status "chat": a fila não pega). Dá à sessão o backup de cada edição
    (desfazer pelo painel) e a guarda de comandos. Devolve (id, arquivo de settings dos hooks)."""
    import painel_ia
    jid = f"{datetime.now():%Y%m%d_%H%M%S}_op55"
    job = {"id": jid, "tipo": "aplicar", "pedido": f"Revisão do Opus 5.5 (botão): {arq}", "projeto": "geral",
           "contexto": "", "origem": "melhoria", "status": "chat", "criado": painel_ia._agora(), "passos": [],
           "resposta": "", "status_ia": None, "detalhe": "sessão de chat do Opus 5.5 (botão REVISAR)", "sessao": None,
           "cwd": str(PASTA), "modelo": "cc/claude-opus-5-5"}
    painel_ia._gravar(job)
    cfg = PASTA / f"{jid}_hooks.json"
    cfg.write_text(json.dumps(painel_ia._hooks(job)), encoding="utf-8")
    return jid, cfg


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1 and sys.argv[1] == "preparar":
        mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 8
        arq, n, tam = preparar("--seco" in sys.argv, mx)
        jid, hooks = criar_job(arq) if "--seco" not in sys.argv else ("", "")
        print(f"{arq}|{n}|{tam}|{jid}|{hooks}")
    else:
        print(__doc__)
