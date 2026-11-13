# -*- coding: utf-8 -*-
r"""melhorador_central.py — UM sistema que melhora TODOS os vídeos analisando o que vai saindo (dona 29/10/2026).

Pedido: "hoje tem chats abertos analisando vídeo, um sentinela que manda 'continue' quando volta token, e um
melhorador por linha — mas eles trabalham separados, um sai depois outro; quero centralizar: um sistema único que
melhore todos os vídeos analisando os vídeos que vão saindo, trabalho contínuo sempre que tem tokens."

Como funciona (Fable 29/10 — FABLE_DECISOES.md D12; nada dos 4 melhoradores é reescrito, cada um continua com a sua
análise → decisão → alavancas com faixa → revisor → desfazer):
  1. FEED ÚNICO: vídeos dos últimos 7 dias de todas as linhas (ledger do postador, _postados dos produtos, júris) com
     os DADOS REAIS: elegibilidade no feed (continuaram 100% e < 10 views = não mostrado), % assistido, impressões,
     curva de retenção, QA (qa.json), "faltou" (faltou.json), views/curtidas do Instagram (medidas).
  2. BRIEF POR LINHA (estado\central\brief_<linha>.md) com esses números e as regras D1 (o que decide views), injetado
     entre marcas nas LIÇÕES que cortes/longo já leem a cada decisão; produtos/ccv leem o arquivo (apontado no prompt).
  3. PRESSÃO: cada linha ganha uma nota = vídeos novos sem análise + QA/faltou graves + resultado medido ruim; roda SÓ a
     linha com mais pressão (1 por passada, com prioridade baixa de CPU, timeout), nunca duas ao mesmo tempo.
  4. TOKENS: antes de rodar, 1 teste de 5 tokens no gateway (ia_reserva.testar): sem modelo vivo = espera a próxima
     passada; voltou = segue. É isso que substitui o "continue" nos chats: aqui não há chat, é tarefa do Windows.
  5. BOTÃO ÚNICO: controle.json projeto "melhorador_central" (ligar/desligar). Modo "sombra" (padrão): cada linha
     decide e anota, não aplica. Modo "aplicar": liga as 4 linhas de uma vez (controle + configs delas) e elas aplicam
     com as travas próprias. Desligar o central desliga as 4.

    python melhorador_central.py status | brief | volta [--simular] | --rodar 9 | ligar [--aplicar] | desligar
Tarefa: MelhoradorCentral (a cada 10 min, escondida, --rodar 9). Log: logs\melhorador_central.log
Estado: estado\central\estado.json. Config: config\melhorador_central.json.
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — regra da dona: nenhum processo filho abre janela na tela
import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
CFG = BASE / "config" / "melhorador_central.json"
PASTA = BASE / "estado" / "central"
ESTADO = PASTA / "estado.json"
TRAVA = PASTA / "central.lock"
LOG = BASE / "logs" / "melhorador_central.log"
LOGS_LINHA = BASE / "logs" / "melhorador_central"
POST = Path(r"D:\postador-de-videos")
RECAPD = Path(r"D:\recapd-ambientes\producao")
PY_RECAPD = RECAPD / "venv" / "Scripts" / "python.exe"
PY_VEO = Path(r"D:\veo\venv\Scripts\python.exe")
BAIXA = BASE / "baixa_prioridade.py"
MARCA_INI, MARCA_FIM = "<!-- central:inicio -->", "<!-- central:fim -->"
LINHA = BASE / "linhas" / "CENTRAL"  # a "linha" do central: conversa com a dona, pedidos dela, histórico, decisões
PEDIDOS = LINHA / "PEDIDOS_DONA.md"
HISTORICO = LINHA / "HISTORICO.md"
MODELOS_CFG = BASE / "config" / "modelos_central.json"
SESSOES_CHAT = Path(os.path.expanduser("~")) / ".claude-vscode" / "sessions"
# 29/10 (dona): "usar o Argon quando eu estiver gastando o Opus no chat; quando não, o Opus; botões para mudar e até
# usar os 2". Cada CONJUNTO é o que as 4 linhas recebem (env CENTRAL_MODELOS) por papel: analista (vê quadros: Gemini),
# decisor (quem escolhe a mudança), revisor (quem veta). "ambos" = Argon decide, Opus revisa (gasta pouco Opus).
MODELOS_PADRAO = {
    "_leia": "modo: argon | opus | ambos | auto. auto = Opus quando a dona NÃO está num chat (sessão do VS Code ativa "
             "nos últimos 'chat_min' minutos) E há cota CC (cota_claude.atual com_cota >= 1); senão Argon. Os conjuntos "
             "vão por papel para os melhoradores das linhas (env CENTRAL_MODELOS). Nunca Kiro.",
    "modo": "argon",
    "chat_min": 30,
    "conjuntos": {
        "argon": {"analista": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"],
                  "decisor": ["gemini-4-argon", "argon-pro", "agy/gemini-3.8-flash-high"],
                  "revisor": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"]},
        "opus": {"analista": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"],
                 "decisor": ["cc/claude-opus-5-5", "gemini-4-argon", "agy/gemini-3.8-flash-high"],
                 "revisor": ["cc/claude-opus-5-5", "agy/gemini-3.8-flash-high"]},
        "ambos": {"analista": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"],
                  "decisor": ["gemini-4-argon", "argon-pro", "agy/gemini-3.8-flash-high"],
                  "revisor": ["cc/claude-opus-5-5", "agy/gemini-3.8-flash-high"]},
    },
}


def modelos_cfg():
    d = _ler(MODELOS_CFG, {})
    if not d:
        _gravar(MODELOS_CFG, MODELOS_PADRAO)
        return dict(MODELOS_PADRAO)
    out = dict(MODELOS_PADRAO)
    out.update(d)
    out["conjuntos"] = {**MODELOS_PADRAO["conjuntos"], **(d.get("conjuntos") or {})}
    return out


def dona_no_chat(minutos=30):
    """A dona está usando um chat do VS Code agora? (sessão interativa com status != idle mexida há < minutos)."""
    try:
        lim = time.time() - minutos * 60
        for f in SESSOES_CHAT.glob("*.json"):
            if f.stat().st_mtime < lim:
                continue
            s = _ler(f, {})
            if s.get("kind") == "interactive" and s.get("status") not in (None, "idle", "exited", "archived"):
                return True
    except OSError:
        pass
    return False


def cota_opus():
    try:
        import cota_claude
        d = cota_claude.atual(max_min=60) or {}
        return int(d.get("com_cota") or 0), d
    except Exception:  # noqa: BLE001
        return 0, {}


def modo_modelos():
    """(modo pedido, modo em vigor, motivo, conjunto)."""
    mc = modelos_cfg()
    pedido = mc.get("modo", "argon")
    vigor, motivo = pedido, "escolhido no painel"
    if pedido == "auto":
        chat = dona_no_chat(mc.get("chat_min", 30))
        cota, _ = cota_opus()
        if chat:
            vigor, motivo = "argon", "a dona está num chat (Opus é dela agora)"
        elif cota < 1:
            vigor, motivo = "argon", "sem cota CC (Opus) agora"
        else:
            vigor, motivo = "opus", f"dona fora do chat e {cota} conta(s) CC com cota"
    conj = mc["conjuntos"].get(vigor) or mc["conjuntos"]["argon"]
    # 30/10 (dona: "o Argon, o Sonnet web, aí pode colocar o Kiro Sonnet 4.5, depois o Gemini 3.8 e o Argon Pro"): o Kiro
    # só passa com modelos_central.json "kiro_liberado": true (antes: nunca)
    if not mc.get("kiro_liberado"):
        conj = {p: [m for m in ms if not str(m).startswith(("kr/", "kiro"))] for p, ms in conj.items()}
    conj = {p: list(ms) for p, ms in conj.items()}
    mc_kiro = bool(mc.get("kiro_liberado"))
    os.environ["CENTRAL_KIRO_OK"] = "1" if mc_kiro else "0"
    return pedido, vigor, motivo, conj
SEM_JANELA = 0x08000000
PADRAO = {
    "_leia": "Melhorador central (dona 29/10): um só sistema para todas as linhas. ligado = controle.json projeto "
             "'melhorador_central'. modo: sombra (decide, não aplica) | aplicar (liga os 4 melhoradores de vez). "
             "pausa_min entre passadas; max_min_linha = teto de cada rodada de linha; dias_feed = janela do feed.",
    "modo": "sombra",
    "min_medidos_aplicar": 20,  # 29/10: linha com menos vídeos medidos (elegíveis) que isso só sugere, nunca aplica
    "pausa_min": 10,
    "max_min_linha": 35,
    "dias_feed": 7,
    "ram_min_gb": 2.5,
    "modelos_teste": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"],
    "linhas": {
        "cortes": {"nome": "Cortes (Shorts de parceiro)", "licoes": r"D:\video-fila\linhas\CORTES\LICOES.md",
                   "cwd": str(RECAPD), "sombra": [str(PY_RECAPD), r"bin\cortes_melhorador.py", "--forcar"],
                   "aplicar": [str(PY_RECAPD), r"bin\cortes_melhorador.py", "--forcar"],
                   "cfg_sombra": str(RECAPD / "bin" / "cortes_melhorador.json"), "controle": "melhorador_cortes"},
        "longo": {"nome": "Recap longo", "licoes": r"D:\video-fila\linhas\LONGOS\LICOES.md",
                  "cwd": str(RECAPD), "sombra": [str(PY_RECAPD), r"colab\melhorador_longo.py", "--forcar", "--so-analisar"],
                  "aplicar": [str(PY_RECAPD), r"colab\melhorador_longo.py", "--forcar"], "controle": "melhorador_longo"},
        "produtos": {"nome": "Produtos (Reels)", "licoes": "", "cwd": str(POST / "bin"),
                     "sombra": [sys.executable, "-m", "produto.melhorador", "--ensaio"],
                     "aplicar": [sys.executable, "-c", "from produto import melhorador as m; m.ciclo(False)"],
                     "cfg_ligado": str(POST / "config" / "melhorador_produtos.json")},
        "ccv": {"nome": "Claude Code Video", "licoes": "", "cwd": r"D:\claude-code-video",
                "sombra": [sys.executable, "melhorador.py", "--sombra"],
                "aplicar": [sys.executable, "melhorador.py"],
                "cfg_ligado": r"D:\claude-code-video\config_melhorador.json"},
        # hipercool ainda não tem melhorador próprio: entra no feed e ganha brief (quem mexer nele lê), sem rodada
        "hipercool": {"nome": "Hipercool (manhwa narrado)", "licoes": r"D:\hipercool-videos\docs\BRIEF_CENTRAL.md",
                      "cwd": r"D:\hipercool-videos", "sombra": None, "aplicar": None},
        "veo": {"nome": "Veo / manhwa-react", "licoes": r"D:\veo\beta\BRIEF_CENTRAL.md", "cwd": r"D:\veo\beta",
                "sombra": None, "aplicar": None},
    },
}


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def cfg():
    c = _ler(CFG, {})
    if not c:
        _gravar(CFG, PADRAO)
        return dict(PADRAO)
    out = dict(PADRAO)
    out.update(c)
    out["linhas"] = {**PADRAO["linhas"], **(c.get("linhas") or {})}
    return out


def modo_tokens():
    """09/11 (dona): modo do vigia de tokens da VPS 157 (modo_tokens.py): 'gastar' = alguém mais usa as contas ou a
    janela de 5 h vai virar com saldo -> roda várias linhas de uma vez; 'poupar' = só nós -> só linha com pressão alta;
    'esgotado' = não roda. Sem resposta = 'normal' (comportamento de antes). Desligar: MELHORADOR_MODO_TOKENS=0."""
    if os.environ.get("MELHORADOR_MODO_TOKENS", "1") == "0":
        return {"modo": "normal"}
    try:
        chave = Path(r"D:\vps157\painel_creditos.chave").read_text(encoding="utf-8").strip()
        with urllib.request.urlopen(f"http://157.173.207.22:20172/modo?k={chave}", timeout=15) as r:
            d = json.loads(r.read().decode("utf-8"))
        idade = (datetime.now().astimezone() - datetime.fromisoformat(d["em"])).total_seconds()
        return d if idade < 1800 else {"modo": "normal"}  # leitura velha (cron parado) = como antes
    except Exception:  # noqa: BLE001
        return {"modo": "normal"}


def ligado():
    try:
        import controle
        return controle.ligado("melhorador_central", "producao")[0] and \
            "melhorador_central" in (controle._ler().get("projetos") or {})
    except Exception:  # noqa: BLE001
        return False


# ─── feed único ─────────────────────────────────────────────────────────────────────────────────────────────────
def _ledger(dias):
    lim = datetime.now().astimezone() - timedelta(days=dias)
    out = {}
    try:
        for ln in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8").splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            try:
                if datetime.fromisoformat((r.get("ts") or "").replace("Z", "+00:00")) < lim:
                    continue
            except ValueError:
                continue
            if r.get("video_id"):
                out[r["video_id"]] = r
    except OSError:
        pass
    return out


def _linha_do(r):
    p, t = r.get("projeto") or "", r.get("tipo") or ""
    if p == "parceiro":  # ledger de 7 dias (29/10): parceiro/short = Cortes; parceiro/completo = recap longo
        return "longo" if t in ("completo", "deitado") else "cortes"
    if p == "hipercool":
        return "hipercool"
    if p in ("anime", "recap") and t != "short":
        return "longo"
    if p == "manhwa-react":
        return "veo"
    if p == "ccv":
        return "ccv"
    return p or "outro"


def feed(c):
    """{linha: [video]} com os dados reais de cada vídeo dos últimos dias."""
    dias = c.get("dias_feed", 7)
    med = _ler(POST / "config" / "telegram_estado.json", {}).get("medidas_48h") or {}
    ms = _ler(POST / "_analise" / "metricas_studio.json", {})
    out = defaultdict(list)
    for vid, r in _ledger(dias).items():
        s = ms.get(vid) or {}
        rl = s.get("ret_lista") or {}
        pasta = Path(r["caminho"]).parent if r.get("caminho") else None
        qa = _ler(pasta / "qa.json", {}) if pasta else {}
        faltou = _ler(pasta / "faltou.json", {}) if pasta else {}
        vp = rl.get("views_periodo")
        cont = s.get("continuaram")
        elegivel = None
        if vp is not None:
            elegivel = not (vp < 10 and (cont or 0) >= 99)
        v = {"vid": vid, "canal": r.get("canal_slug") or r.get("canal"), "ts": r.get("ts"), "tipo": r.get("tipo"),
             "views48": (med.get(vid) or {}).get("views"), "views_periodo": vp, "continuaram": cont,
             "pct_media": s.get("pct_media"), "impressoes": s.get("impressoes") or rl.get("impressoes"),
             "ctr": s.get("ctr") or rl.get("ctr"), "ret_meio": s.get("ret_meio"), "ret_fim": s.get("ret_fim"),
             "elegivel": elegivel, "qa_ok": qa.get("ok"), "qa_problemas": qa.get("problemas") or [],
             "faltou": list(faltou.keys()), "pasta": str(pasta) if pasta else None, "titulo": (r.get("titulo") or "")[:70]}
        out[_linha_do(r)].append(v)
    # produtos: _postados com medidas do Instagram
    lim = datetime.now() - timedelta(days=dias)
    for conta in sorted(p for p in Path(r"D:\video-fila\produto_fila").glob("*/_postados")):
        for arq in conta.glob("*.json"):
            side = _ler(arq, {})
            try:
                q = datetime.fromisoformat(side.get("postado_em") or "")
            except ValueError:
                continue
            if q < lim:
                continue
            m = (side.get("medidas") or {}).get("instagram") or {}
            out["ccv" if side.get("ccv") else "produtos"].append({"vid": arq.stem, "canal": conta.parent.name, "ts": side.get("postado_em"),
                                    "views48": m.get("views"), "curtidas": m.get("curtidas"), "variante": side.get("variante"),
                                    "nota_juri": (side.get("lapidar") or {}).get("nota") if isinstance(side.get("lapidar"), dict) else None,
                                    "elegivel": (None if m.get("views") is None else m["views"] >= 20),
                                    "qa_ok": None, "qa_problemas": [], "faltou": [], "pasta": str(arq.parent), "titulo": (side.get("titulo") or "")[:70]})
    return out


def _med(lst):
    lst = [x for x in lst if x is not None]
    return round(statistics.median(lst), 1) if lst else None


def resumo_linha(nome, vids):
    n = len(vids)
    eleg = [v for v in vids if v.get("elegivel") is True]
    nao = [v for v in vids if v.get("elegivel") is False]
    sem = [v for v in vids if v.get("elegivel") is None]
    por_canal = defaultdict(list)
    for v in vids:
        por_canal[v.get("canal")].append(v)
    qa_ruim = [v for v in vids if v.get("qa_ok") is False]
    faltou = [v for v in vids if v.get("faltou")]
    return {"linha": nome, "n": n, "elegiveis": len(eleg), "nao_elegiveis": len(nao), "sem_medida": len(sem),
            "pct_media_elegiveis": _med([v.get("pct_media") for v in eleg]), "views48_med": _med([v.get("views48") for v in vids]),
            "qa_ruim": len(qa_ruim), "faltou": len(faltou),
            "canais": {k: {"n": len(g), "elegiveis": sum(1 for v in g if v.get("elegivel") is True),
                           "pct": _med([v.get("pct_media") for v in g if v.get("elegivel") is True]),
                           "views48": _med([v.get("views48") for v in g])} for k, g in por_canal.items()},
            "melhores": sorted(eleg, key=lambda v: -(v.get("views48") or 0))[:3],
            "piores_qa": [(v["vid"], v["qa_problemas"][:2]) for v in qa_ruim[:3]],
            "faltou_lista": [(v["vid"], v["faltou"]) for v in faltou[:3]]}


REGRAS_D1 = """## O QUE DECIDE VIEWS (dado medido em 29/10 — FABLE_DECISOES.md D1; vale mais que gosto e que nota de júri)
- 60% dos Shorts NÃO entram no lote de teste do feed ("continuaram" 100% com < 10 views = o YouTube mostrou a 2–5
  pessoas e parou). Gancho/efeito/mascote não mudam isso: esses vídeos não são vistos. Não aprenda regra com eles.
- Quem entra no lote para em 1.000–1.500 views. O que leva ao 2º lote é ASSISTIR INTEIRO (% assistido ≥ 65%):
  os 5 que passaram de 2.000 têm 13–24 s e 64–89% assistido; os do platô, 50–75 s e 44%. "Continuaram" (deslizou)
  é igual nos dois grupos — não é a alavanca.
- Logo: priorize duração curta (15–25 s), final que emenda no início (loop), 1 acontecimento por vídeo. Qualquer
  mudança que ALONGUE o vídeo começa com peso negativo.
- Para comparar A/B: só vídeos elegíveis (views_periodo ≥ 20); métrica primária pct_media, depois log(views/mediana
  do canal). Nunca promover por nota de júri sozinha."""


def brief(c, fd=None):
    """Escreve estado\\central\\brief_<linha>.md e injeta nas LIÇÕES de quem lê (entre marcas)."""
    fd = fd or feed(c)
    PASTA.mkdir(parents=True, exist_ok=True)
    resumos = {}
    for linha, lc in c["linhas"].items():
        vids = fd.get(linha, [])
        r = resumo_linha(linha, vids)
        resumos[linha] = r
        txt = [f"# Brief do melhorador central — {lc['nome']} — {datetime.now():%d/%m %H:%M}", "",
               f"Vídeos nos últimos {c.get('dias_feed', 7)} dias: {r['n']} | elegíveis (receberam o lote do feed): {r['elegiveis']} | "
               f"NÃO elegíveis: {r['nao_elegiveis']} | sem medida ainda: {r['sem_medida']}",
               f"% assistido mediano (só elegíveis): {r['pct_media_elegiveis']} | views 48 h mediana: {r['views48_med']} | "
               f"QA com problema: {r['qa_ruim']} | saíram com parte faltando (IA caiu): {r['faltou']}", "", "## Por canal"]
        for k, g in sorted(r["canais"].items(), key=lambda kv: -(kv[1]["views48"] or 0)):
            txt.append(f"- {k}: n {g['n']}, elegíveis {g['elegiveis']}, % assistido {g['pct']}, views48 {g['views48']}")
        if r["melhores"]:
            txt += ["", "## Os que mais renderam (copiar a estrutura, não o texto)"]
            txt += [f"- {v['vid']} {v.get('canal')}: views48 {v.get('views48')}, % assistido {v.get('pct_media')}, "
                    f"continuaram {v.get('continuaram')} — {v.get('titulo')}" for v in r["melhores"]]
        if r["piores_qa"]:
            txt += ["", "## QA (defeito objetivo, sem IA)"] + [f"- {vid}: {'; '.join(p)}" for vid, p in r["piores_qa"]]
        if r["faltou_lista"]:
            txt += ["", "## Saíram sem parte (a IA falhou)"] + [f"- {vid}: {', '.join(p)}" for vid, p in r["faltou_lista"]]
        txt += ["", REGRAS_D1]
        try:  # 29/10: saúde do "navegador sem navegador" (HTTP) — se caiu, o melhorador deve saber/propor
            sd = _ler(Path(r"D:\projeto-navegador-sem-navegador\relatorios\saida\saude.json"), {})
            if sd.get("_resumo"):
                mortos = [f"{s} {c}" for s, cs in sd.items() if not s.startswith("_") for c, r in cs.items() if r.get("vivo") is False]
                txt += ["", f"## SEM NAVEGADOR (HTTP) — saúde em {sd.get('_em', '')[5:16]}: "
                        + ", ".join(f"{s} {v['vivos']}/{v['total']}" for s, v in sd["_resumo"].items())
                        + (f" | MORTOS: {', '.join(mortos[:12])}" if mortos else "")]
        except Exception:  # noqa: BLE001
            pass
        try:  # 29/10 (dona: "nenhum canal pode ficar sem postar"): filas de reuso TikTok/Instagram baixas ou vazias
            filas = (_ler(POST / "config" / "telegram_estado.json", {}).get("filas") or {})
            baixas = [f"{k} ({v.get('n')})" for k, v in filas.items() if isinstance(v, dict) and v.get("nivel") in ("baixa", "vazia")]
            if baixas:
                txt += ["", "## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)",
                        ", ".join(baixas[:30])]
        except Exception:  # noqa: BLE001
            pass
        if linha == "longo":  # 30/10 (Fable): pedidos da dona conferidos no log de cada longo pronto (conferir_pedidos.py)
            try:
                linhas_conf = Path(r"D:\video-fila\linhas\LONGOS\conferencias.jsonl").read_text(encoding="utf-8").splitlines()
                conf = [json.loads(l) for l in linhas_conf if l.strip()][-5:]
                if conf:
                    txt += ["", "## PEDIDOS DA DONA QUE NÃO SAÍRAM NOS ÚLTIMOS LONGOS (conferido no log do render; corrigir a causa)"]
                    txt += [f"- {x['ficha'][:40]}: {x['ok']}/{x['total']} ok — faltou: {', '.join(x['faltando']) or 'nada'}"
                            for x in conf]
            except (OSError, ValueError):
                pass
            try:  # 30/10: resultado das variantes A/B/C... por fator (melhorador_longo._resumo_variantes)
                ab_md = Path(r"D:\video-fila\linhas\LONGOS\AB_RESULTADOS.md")
                if ab_md.exists():
                    txt += ["", "## VARIANTES DOS LONGOS (views/h e % assistido por fator; só fixar com 4+ vídeos por variante)"]
                    txt += [l for l in ab_md.read_text(encoding="utf-8").splitlines() if l.startswith("|")][2:40]
                obras_md = Path(r"D:\video-fila\linhas\LONGOS\OBRAS_CONTINUAR.md")  # 30/10: % assistido -> continuar a obra?
                if obras_md.exists():
                    txt += ["", "## OBRAS: CONTINUAR OU NÃO (48 h+, 20+ views, 30%+ assistido)"]
                    txt += [l for l in obras_md.read_text(encoding="utf-8").splitlines() if l.startswith("|")][2:30]
            except OSError:
                pass
        try:  # pedidos/opiniões da dona (escritos pela conversa) valem para TODAS as linhas e mais que o júri
            itens = [l for l in PEDIDOS.read_text(encoding="utf-8", errors="replace").splitlines() if l.startswith("- ")]
            if itens:
                txt += ["", "## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)",
                        *itens[-40:]]
        except OSError:
            pass
        corpo = "\n".join(txt) + "\n"
        (PASTA / f"brief_{linha}.md").write_text(corpo, encoding="utf-8")
        lic = Path(lc.get("licoes") or "")
        if lic.is_file():
            bloco = f"{MARCA_INI}\n{corpo}{MARCA_FIM}"
            t = lic.read_text(encoding="utf-8", errors="replace")
            if MARCA_INI in t and MARCA_FIM in t:
                t = re.sub(re.escape(MARCA_INI) + r".*?" + re.escape(MARCA_FIM), lambda _m: bloco, t, flags=re.S)
            else:
                t = t.rstrip() + "\n\n" + bloco + "\n"
            lic.write_text(t, encoding="utf-8")
    return resumos


# ─── pressão e escolha ──────────────────────────────────────────────────────────────────────────────────────────
def _novos_desde(fd, linha, desde):
    try:
        t0 = datetime.fromisoformat(desde)
    except (TypeError, ValueError):
        return len(fd.get(linha, []))
    n = 0
    for v in fd.get(linha, []):
        try:
            ts = datetime.fromisoformat(str(v.get("ts") or "").replace("Z", "+00:00"))
            if ts.replace(tzinfo=None) >= t0.replace(tzinfo=None):
                n += 1
        except ValueError:
            continue
    return n


def escolher(c, fd, resumos, est):
    notas = {}
    for linha, r in resumos.items():
        ult = (est.get("rodadas") or {}).get(linha, {}).get("em")
        novos = _novos_desde(fd, linha, ult) if ult else r["n"]
        ruim = 0.0
        if r["elegiveis"] and r["pct_media_elegiveis"] is not None:
            ruim += max(0.0, (65 - r["pct_media_elegiveis"]) / 65)
        if r["n"]:
            ruim += r["nao_elegiveis"] / r["n"]
        rodando_cedo = ult and datetime.now() - datetime.fromisoformat(ult) < timedelta(hours=1)
        # 30/10 (Fable): sem vídeo novo a nota vinha só do "ruim" e a linha rodava de hora em hora sobre os MESMOS
        # vídeos (ccv: 6 rodadas seguidas "ESPERAR" com o mesmo diagnóstico, tokens à toa). Sem novo = só depois de
        # c["horas_sem_novo"] (6 h, tempo de as métricas mudarem).
        sem_novidade = novos == 0 and ult and datetime.now() - datetime.fromisoformat(ult) < timedelta(
            hours=float(c.get("horas_sem_novo", 6)))
        nota = 3 * min(novos, 10) / 10 + 2 * (r["qa_ruim"] + r["faltou"]) + 2 * ruim
        if rodando_cedo or sem_novidade or (novos == 0 and r["n"] == 0) or not c["linhas"].get(linha, {}).get("sombra"):
            nota = 0.0  # sem comando = linha só de brief (hipercool: a melhoria dele é pelo chat/docs, por ora)
        notas[linha] = {"nota": round(nota, 2), "novos": novos, "ruim": round(ruim, 2), "cedo": bool(rodando_cedo)}
    ordem = sorted(notas, key=lambda k: -notas[k]["nota"])
    return (ordem[0] if ordem and notas[ordem[0]]["nota"] > 0 else None), notas


# ─── travas: tokens, RAM, lock ──────────────────────────────────────────────────────────────────────────────────
def ia_viva(c):
    try:
        import ia_reserva
    except Exception:  # noqa: BLE001
        return "sem ia_reserva (assume viva)"
    for m in c.get("modelos_teste") or []:
        try:
            erro = ia_reserva.testar(m)
        except Exception as e:  # noqa: BLE001
            erro = f"{type(e).__name__}"
        if not erro:
            return m
        log(f"  modelo {m}: {str(erro)[:80]}")
    return None


def ram_livre_gb():
    try:
        import ctypes
        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        s = MS()
        s.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
        return s.ullAvailPhys / 1e9
    except Exception:  # noqa: BLE001
        return 99.0


def _pegar_trava():
    PASTA.mkdir(parents=True, exist_ok=True)
    d = _ler(TRAVA, {})
    if d and time.time() - float(d.get("em", 0)) < 3 * 3600:
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(d.get("pid") or 0))
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return False
        except Exception:  # noqa: BLE001
            return False
    _gravar(TRAVA, {"pid": os.getpid(), "em": time.time()})
    return True


def _soltar_trava():
    try:
        TRAVA.unlink(missing_ok=True)
    except OSError:
        pass


# ─── rodar uma linha ────────────────────────────────────────────────────────────────────────────────────────────
def rodar_linha(linha, c, est, simular=False, medidos=None):
    lc = c["linhas"][linha]
    aplicar = c.get("modo") == "aplicar"
    # 29/10 (Fable, item 9 do CORTES_10): linha com poucos vídeos MEDIDOS (elegíveis no feed, views ≥ 20) só sugere,
    # mesmo com o central em "aplicar" — a nota do júri não prevê views (provado), então sem medida real não se aplica.
    minimo = c.get("min_medidos_aplicar", 20)
    if aplicar and medidos is not None and medidos < minimo:
        aplicar = False
        log(f"  {linha}: central em APLICAR, mas só {medidos} vídeo(s) medido(s) < {minimo}: esta linha roda em sombra (só sugere)")
    cmd = list(lc["aplicar" if aplicar else "sombra"])
    cmd_final = [sys.executable, str(BAIXA), *cmd]
    log(f"  {linha}: {'APLICAR' if aplicar else 'sombra'} -> {' '.join(cmd)}")
    if simular:
        return {"linha": linha, "simulado": True, "cmd": cmd}
    LOGS_LINHA.mkdir(parents=True, exist_ok=True)
    arq_log = LOGS_LINHA / f"{linha}_{datetime.now():%Y%m%d_%H%M%S}.log"
    t0 = time.time()
    pedido, vigor, motivo, conj = modo_modelos()
    log(f"  modelos: {vigor} ({motivo}) decisor={conj.get('decisor')} revisor={conj.get('revisor')}")
    env = {**os.environ, "PYTHONUTF8": "1", "MELHORADOR_CENTRAL": "1", "CENTRAL_BRIEF": str(PASTA / f"brief_{linha}.md"),
           "CENTRAL_MODELOS": json.dumps(conj), "CENTRAL_MODO": vigor}
    try:
        with arq_log.open("w", encoding="utf-8") as f:
            r = subprocess.run(cmd_final, cwd=lc["cwd"], stdout=f, stderr=subprocess.STDOUT, env=env,
                               timeout=c.get("max_min_linha", 35) * 60, creationflags=SEM_JANELA)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = "timeout"
    seg = round(time.time() - t0)
    try:
        cauda = arq_log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:]
    except OSError:
        cauda = []
    est.setdefault("rodadas", {})[linha] = {"em": datetime.now().isoformat(timespec="seconds"), "rc": rc, "s": seg,
                                           "log": str(arq_log), "modo": "aplicar" if aplicar else "sombra",
                                           "modelos": vigor, "decisor": conj.get("decisor")}
    est.setdefault("historico", []).append({"em": est["rodadas"][linha]["em"], "linha": linha, "rc": rc, "s": seg})
    est["historico"] = est["historico"][-200:]
    log(f"  {linha}: rc={rc} em {seg} s | {' | '.join(x[:90] for x in cauda)}")
    try:  # histórico legível (a conversa com a dona lê isto)
        HISTORICO.parent.mkdir(parents=True, exist_ok=True)
        with HISTORICO.open("a", encoding="utf-8") as f:
            f.write(f"- {datetime.now():%d/%m %H:%M} | {linha} | {'APLICAR' if aplicar else 'sombra'} | rc {rc} | {seg} s | "
                    f"{' | '.join(x[:120] for x in cauda)}\n")
    except OSError:
        pass
    return est["rodadas"][linha]


def volta(simular=False, forcar=False):
    c = cfg()
    if not forcar and not ligado():
        log("central DESLIGADO (controle.json projeto melhorador_central) — nada a fazer")
        return None
    if not _pegar_trava():
        log("outra passada rodando — saio")
        return None
    try:
        est = _ler(ESTADO, {})
        fd = feed(c)
        resumos = brief(c, fd)
        linha, notas = escolher(c, fd, resumos, est)
        est["ultima_volta"] = datetime.now().isoformat(timespec="seconds")
        est["notas"] = notas
        log("pressão: " + ", ".join(f"{k} {v['nota']} (novos {v['novos']}, ruim {v['ruim']}{', cedo' if v['cedo'] else ''})"
                                     for k, v in sorted(notas.items(), key=lambda kv: -kv[1]['nota'])))
        if not linha:
            log("nada com pressão agora")
            _gravar(ESTADO, est)
            return None
        if not simular:
            ram = ram_livre_gb()
            if ram < c.get("ram_min_gb", 2.5):
                log(f"RAM livre {ram:.1f} GB < {c.get('ram_min_gb')}: espero a próxima passada")
                _gravar(ESTADO, est)
                return None
            vivo = ia_viva(c)
            if not vivo:
                est["sem_ia_desde"] = est.get("sem_ia_desde") or est["ultima_volta"]
                log("nenhum modelo vivo no gateway: espero (volta sozinho quando houver)")
                _gravar(ESTADO, est)
                return None
            if est.get("sem_ia_desde"):
                log(f"IA voltou ({vivo}); estava sem desde {est['sem_ia_desde']}")
                est["sem_ia_desde"] = None
        mt = modo_tokens()
        est["modo_tokens"] = mt
        if mt.get("modo") == "esgotado":
            log(f"tokens esgotados ({mt.get('motivo')}): espero")
            _gravar(ESTADO, est)
            return None
        if mt.get("modo") == "poupar" and notas.get(linha, {}).get("nota", 0) < c.get("nota_poupar", 1.0):
            log(f"modo poupar ({mt.get('motivo')}): {linha} com pressão {notas[linha]['nota']} < "
                f"{c.get('nota_poupar', 1.0)} — fica pra depois")
            _gravar(ESTADO, est)
            return None
        linhas = [linha]
        if mt.get("modo") == "gastar":  # outra pessoa usando / janela de 5 h virando: gasta de uma vez
            linhas += [k for k, v in sorted(notas.items(), key=lambda kv: -kv[1]["nota"])
                       if k != linha and v["nota"] > 0][:2]
            log(f"modo GASTAR ({mt.get('motivo')}): rodo {', '.join(linhas)}")
        r = None
        for ln in linhas:
            r = rodar_linha(ln, c, est, simular, medidos=(resumos.get(ln) or {}).get("elegiveis"))
            _gravar(ESTADO, est)
            if not simular:
                _avisar(ln, r, notas, resumos)
        return r
    finally:
        _soltar_trava()


def _avisar(linha, r, notas, resumos):
    try:
        import avisos
        rs = resumos.get(linha, {})
        txt = (f"🧭 Melhorador central: rodou {linha} ({r.get('modo')}, rc {r.get('rc')}, {r.get('s')} s). "
               f"{rs.get('n')} vídeos/7 d, {rs.get('elegiveis')} elegíveis, % assistido {rs.get('pct_media_elegiveis')}, "
               f"QA ruim {rs.get('qa_ruim')}, faltou {rs.get('faltou')}. Pressão: " +
               ", ".join(f"{k} {v['nota']}" for k, v in sorted(notas.items(), key=lambda kv: -kv[1]['nota'])))
        avisos.enviar(txt, origem="melhorador central", importante=False, chave=f"central:{linha}:{r.get('em', '')[:13]}")
    except Exception as e:  # noqa: BLE001
        log(f"aviso não saiu ({type(e).__name__})")


# ─── botão único ────────────────────────────────────────────────────────────────────────────────────────────────
def ligar(aplicar=False):
    import controle
    c = cfg()
    c["modo"] = "aplicar" if aplicar else "sombra"
    _gravar(CFG, c)
    controle.mudar("melhorador_central", "producao", True, f"dona ligou o central ({c['modo']})")
    if aplicar:
        for linha, lc in c["linhas"].items():
            if lc.get("controle"):
                controle.mudar(lc["controle"], "producao", True, "ligado pelo melhorador central (aplicar)")
            if lc.get("cfg_sombra"):
                d = _ler(lc["cfg_sombra"], {})
                d["sombra"] = False
                _gravar(lc["cfg_sombra"], d)
            if lc.get("cfg_ligado"):
                d = _ler(lc["cfg_ligado"], {})
                d["ligado"] = True
                if linha == "produtos":
                    d["modo"] = "aplicar"
                _gravar(lc["cfg_ligado"], d)
    log(f"central LIGADO ({c['modo']})")


def desligar():
    import controle
    c = cfg()
    controle.mudar("melhorador_central", "producao", False, "dona desligou o central")
    for linha, lc in c["linhas"].items():
        if lc.get("controle"):
            controle.mudar(lc["controle"], "producao", False, "desligado pelo melhorador central")
        if lc.get("cfg_sombra"):
            d = _ler(lc["cfg_sombra"], {})
            d["sombra"] = True
            _gravar(lc["cfg_sombra"], d)
        if lc.get("cfg_ligado"):
            d = _ler(lc["cfg_ligado"], {})
            d["ligado"] = False
            _gravar(lc["cfg_ligado"], d)
    log("central DESLIGADO (e as 4 linhas)")


def mudar_modelos(modo):
    if modo not in ("argon", "opus", "ambos", "auto"):
        raise ValueError("modo tem de ser argon | opus | ambos | auto")
    mc = modelos_cfg()
    mc["modo"] = modo
    mc["mudado_em"] = datetime.now().isoformat(timespec="seconds")
    _gravar(MODELOS_CFG, mc)
    log(f"modelos: modo {modo}")
    return modo_modelos()


def status():
    c, est = cfg(), _ler(ESTADO, {})
    pedido, vigor, motivo, conj = modo_modelos()
    print(f"ligado={ligado()} modo={c.get('modo')} | modelos: {pedido} -> {vigor} ({motivo}) | decisor {conj.get('decisor')}")
    print(f"última volta {est.get('ultima_volta')} | sem IA desde {est.get('sem_ia_desde')}")
    for k, v in (est.get("notas") or {}).items():
        r = (est.get("rodadas") or {}).get(k, {})
        print(f"  {k:<9} pressão {v.get('nota'):>5} novos {v.get('novos'):>3} ruim {v.get('ruim'):>4} | última rodada {r.get('em')} rc={r.get('rc')} {r.get('s')}s")


def main(a):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "status" in a:
        status()
    elif "brief" in a:
        rs = brief(cfg())
        for k, r in rs.items():
            print(f"{k:<9} n {r['n']:>3} elegíveis {r['elegiveis']:>3} não {r['nao_elegiveis']:>3} sem {r['sem_medida']:>3} | pct {r['pct_media_elegiveis']} | views48 {r['views48_med']} | qa {r['qa_ruim']} faltou {r['faltou']}")
        print(f"briefs em {PASTA}")
    elif "modelos" in a:  # python melhorador_central.py modelos [argon|opus|ambos|auto]
        alvo = next((x for x in a if x in ("argon", "opus", "ambos", "auto")), None)
        if alvo:
            mudar_modelos(alvo)
        pedido, vigor, motivo, conj = modo_modelos()
        print(f"modo pedido: {pedido} | em vigor: {vigor} ({motivo})")
        for p, ms in conj.items():
            print(f"  {p:<9} {ms}")
    elif "ligar" in a:
        ligar("--aplicar" in a)
    elif "desligar" in a:
        desligar()
    elif "--rodar" in a:
        minutos = float(a[a.index("--rodar") + 1]) if len(a) > a.index("--rodar") + 1 else 9
        fim = time.time() + minutos * 60
        while True:
            volta()
            if time.time() + cfg().get("pausa_min", 10) * 60 > fim:
                break
            time.sleep(cfg().get("pausa_min", 10) * 60)
    else:
        volta(simular="--simular" in a, forcar="--forcar" in a)


if __name__ == "__main__":
    main(sys.argv[1:])
