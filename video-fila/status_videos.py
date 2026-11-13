"""status_videos.py — status ÚNICO dos projetos de vídeo (dono 18/10/2026: "funcionarem como um só").

Uma tela só: liga/desliga de cada projeto (controle.py + botões antigos), cada canal do cadastro único
(D:\\postador-de-videos\\config\\canais.json) com o que subiu hoje / teto / próximos agendados / quem postou,
tarefas agendadas de vídeo (última execução e resultado) e a fila de render.

    python status_videos.py            # tudo
    python status_videos.py canais     # só os canais
    python status_videos.py html       # gera painel_web\\status.html (abrir no navegador; 22/10)
O Telegram ("status" no bot) usa canais_curto() e controle_curto().
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, r"D:\postador-de-videos\bin")
TAREFAS = ("ControladorVideos", "Hipercool", "Anime", "Parceiro", "ManhwaReact", "MSEnergy", "PostadorDeVideos",
           "TikTokRodadaExtra", "NotificarTelegram", "PainelCanais", "VigiaVideos", "VozClonada",
           "BackupDriveVideos", "BackupCachesHipercool", "AtualizarYtDlp", "VigiaMelhorias")
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# 22/10: códigos do agendador traduzidos (a tela mostrava "2147946720" cru)
TASK_RES = {"0": "ok", "267009": "rodando", "267011": "nunca", "267014": "encerrada pelo agendador",
            "1": "falhou (1)", "2147946720": "anterior ainda rodava", "2147942402": "arquivo não achado",
            "2147943645": "pulou (sem rede/uso)"}
# 22/10 (HUB-12): tarefa desabilitada DE PROPÓSITO porque outro processo assumiu o papel — a tela mostrava
# "Disabled" seco e parecia produção parada, quando o controlador dispara tudo (13+ disparos/dia).
ABSORVIDAS = {"AnimeOcioso": "ControladorVideos", "AnimeRecapMonitor": "VigiaVideos (vigia_geral)",
              "AnimeRecapNoturno": "ControladorVideos", "HipercoolFila": "ControladorVideos",
              "ParceiroKaijinre-Producao": "ControladorVideos", "VigiaMelhorias": "VigiaVideos (vigia_geral)",
              "HipercoolVigia": "VigiaVideos (vigia_geral)"}
AVISOS_JSONL = BASE / "estado" / "avisos.jsonl"
PAINEL_HTML = BASE / "painel_web" / "status.html"


def controle_txt():
    import controle
    return controle.painel()


def controlador_txt():
    import controlador
    return controlador.status_txt()


def controlador_curto():
    import controlador
    est = controlador._ler_estado()
    ult = est.get("ultima_rodada", "?")
    pc1 = est.get("pc1") or "—"
    pc2 = est.get("pc2") or "—"
    return f"última={ult[11:16] if len(ult) > 11 else ult} PC1={pc1} PC2={pc2}"


def controle_curto():
    import controle
    off = [f"{p} {e}" for p in controle.PROJETOS for e in controle.ETAPAS if not controle.ligado(p, e)[0]]
    return "desligado: " + ", ".join(off) if off else "tudo ligado"


def _canais():
    """[(chave, entrada do cadastro, canal das credenciais, registros de hoje, agendados futuros)] dos canais ativos."""
    import politica
    cad = politica.cadastro()
    creds = {c["id"]: c for c in politica.carregar_creds()}
    regs = politica._ler_ledger()
    agora = politica.agora()
    out = []
    for k, x in cad.items():
        c = next((creds[i] for i in x.get("creds") or [] if i in creds), None)
        if not c or politica.motivo_bloqueio(c):
            continue
        meus = [r for r in regs if politica._do_canal(r, c)]
        hoje = [r for r in meus if politica._dt(r["ts"]).date() == agora.date()]
        futuros = sorted(t for t in (politica._dt(r.get("publish_at")) for r in meus) if t and t > agora)
        out.append((k, x, c, hoje, futuros))
    return out


def canais_txt():
    import politica
    teto_up = politica.politica()["max_uploads_por_canal_dia"]
    linhas = [f"{'canal':22} {'dono':12} abrem hoje  subidos hoje  agendados  próx. publicação  quem subiu hoje"]
    for k, x, c, hoje, futuros in _canais():
        quem = {}
        for r in hoje:
            q = f"{r.get('projeto') or '?'}{'/' + r['tipo'] if r.get('tipo') else ''}"
            quem[q] = quem.get(q, 0) + 1
        prox = futuros[0].astimezone().strftime("%d/%m %H:%M") if futuros else "-"
        vazio = " VAZIO HOJE" if politica.canal_vazio_hoje(c) else ""
        linhas.append(f"{k[:22]:22} {str(x.get('dono'))[:12]:12} {_abrem_hoje(politica, c)}/{politica.teto_canal(c):<9} "
                      f"{len(hoje)}/{teto_up:<11} {len(futuros):<10} {prox:17} "
                      f"{', '.join(f'{q}×{n}' for q, n in quem.items()) or '-'}{vazio}")
    return "\n".join(linhas)


def _abrem_hoje(politica, c):
    local = politica._hora_local(c)
    return sum(1 for t in politica._publicacoes(c) if t.astimezone(local.tzinfo).date() == local.date())


def canais_curto():
    import politica
    vazios, cheios, n = [], [], 0
    for k, x, c, hoje, futuros in _canais():
        n += 1
        if politica.canal_vazio_hoje(c):
            vazios.append(k)
        if _abrem_hoje(politica, c) >= politica.teto_canal(c):
            cheios.append(k)
    txt = f"{n} canais ativos"
    if vazios:
        txt += f"; SEM post hoje: {', '.join(vazios)}"
    if cheios:
        txt += f"; teto do dia atingido: {', '.join(cheios)}"
    return txt


def _tarefas_rows():
    """[(tarefa, estado, última, resultado traduzido, próxima, resultado cru)] das tarefas de vídeo."""
    filtro = " -or ".join(f"$_.TaskName -like '{p}*'" for p in TAREFAS)
    ps = (f"Get-ScheduledTask | Where-Object {{ {filtro} }} | ForEach-Object {{ $i = $_ | Get-ScheduledTaskInfo; "
          "$u = if ($i.LastRunTime) { $i.LastRunTime.ToString('dd/MM HH:mm') } else { '-' }; "
          "$n = if ($i.NextRunTime) { $i.NextRunTime.ToString('dd/MM HH:mm') } else { '-' }; "
          "'{0}|{1}|{2}|{3}|{4}' -f $_.TaskName, $_.State, $u, $i.LastTaskResult, $n }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=90,
                       encoding="utf-8", errors="replace", creationflags=_SEM_JANELA)
    rows = []
    for l in sorted(r.stdout.splitlines()):
        p = l.split("|")
        if len(p) == 5:
            rows.append((p[0], p[1], p[2], TASK_RES.get(p[3], p[3]), p[4], p[3]))
    return rows


def tarefas_txt():
    try:
        rows = _tarefas_rows()
    except Exception as e:  # noqa: BLE001
        return f"(tarefas indisponíveis: {e})"
    linhas = [f"{'tarefa':28} {'estado':9} {'última':12} {'resultado':24} próxima"]
    for t, est, ult, res, prox, _cru in rows:
        if est == "Disabled" and t in ABSORVIDAS:
            est, prox = "absorvida", f"-> {ABSORVIDAS[t]}"
        linhas.append(f"{t[:28]:28} {est:9} {ult:12} {res:24} {prox}")
    return "\n".join(linhas)


def erros_txt(horas=24):
    """O que deu errado nas últimas N horas: avisos importantes do portão (estado\\avisos.jsonl)
    e tarefa agendada cujo último resultado não foi ok/rodando/nunca (22/10, pro painel)."""
    from datetime import timedelta
    corte = datetime.now() - timedelta(hours=horas)
    linhas = []
    try:
        for l in AVISOS_JSONL.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]:
            try:
                a = json.loads(l)
            except ValueError:
                continue
            if not a.get("importante") or a.get("situacao") == "repetido":
                continue
            try:
                em = datetime.fromisoformat(a.get("em", ""))
            except ValueError:
                continue
            if em < corte:
                continue
            texto = " / ".join(x.strip() for x in str(a.get("texto", "")).splitlines() if x.strip())[:180]
            linhas.append(f"{em:%d/%m %H:%M} [{a.get('origem', '?')}] {texto}")
    except OSError as e:
        linhas.append(f"(avisos indisponíveis: {e})")
    try:
        ruins = [(t, est, ult, res) for t, est, ult, res, _p, cru in _tarefas_rows()
                 if cru not in ("0", "267009", "267011") and est != "Disabled"]
        linhas += [f"tarefa {t}: {res} (última {ult}, estado {est})" for t, est, ult, res in ruins]
    except Exception as e:  # noqa: BLE001
        linhas.append(f"(tarefas indisponíveis: {e})")
    return "\n".join(linhas[-30:]) if linhas else "nada nas últimas 24 h"


def topflop_txt(n=5):
    """Vídeos que mais e menos renderam (views na 1ª leitura de 48 h, placar comum)."""
    d = json.loads(Path(r"D:\postador-de-videos\_analise\aprendizado_global.json").read_text(encoding="utf-8"))

    def fmt(x):
        pub = str(x.get("pub", ""))[5:16].replace("T", " ").replace("-", "/")
        return f"{x.get('views', 0):>6}  {str(x.get('canal', '?'))[:22]:22} {pub:11}  {str(x.get('titulo', ''))[:70]}"
    linhas = [f"TOP {n} (views em 48 h, últimos {d.get('janela_dias', 30)} dias):"]
    linhas += [fmt(x) for x in (d.get("top") or [])[:n]]
    linhas.append(f"PIORES {n}:")
    linhas += [fmt(x) for x in (d.get("piores") or [])[:n]]
    return "\n".join(linhas)


def maquinas_txt():
    """As 3 máquinas (PC1/PC2/desktop): livre/ocupado, motivo e render em andamento. SSH: pode levar ~30 s."""
    import maquinas
    linhas = []
    for h, m in maquinas.medir_todos().items():
        estado = "DESLIGADO" if m.get("desligado") else ("LIVRE" if m.get("ocioso") else "OCUPADO")
        extra = ""
        if m.get("cpu") is not None:
            extra = f" | cpu {m.get('cpu')}% ram {m.get('ram_gb')} GB disco {m.get('disco_gb')} GB"
        linhas.append(f"{h:8} {estado:9} {m.get('motivo', '')}{extra}")
    return "\n".join(linhas)


def placar_txt():
    """Placar comum (views em 48 h): por projeto/tipo, por idioma e por origem."""
    d = json.loads(Path(r"D:\postador-de-videos\_analise\aprendizado_global.json").read_text(encoding="utf-8"))
    linhas = [f"atualizado {d.get('atualizado', '?')} (últimos {d.get('janela_dias', 30)} dias)"]
    for chave in ("por_projeto_tipo", "por_idioma", "por_origem"):
        dim = d.get(chave) or {}
        if dim:
            linhas.append(f"{chave}: " + ", ".join(f"{k} n={v['n']} med={v['mediana']} ≥5000={v.get('pct_5000', '?')}%"
                                                   for k, v in sorted(dim.items(), key=lambda kv: -kv[1]["mediana"])))
    return "\n".join(linhas)


def render_txt():
    import fila_render
    c = fila_render._cfg()
    rod, esp = fila_render._ler("rodando", c.get("max_h", 6)), fila_render._ler("esperando", 24)
    txt = "renderizando: " + (", ".join(f"{d['projeto']} ({d['rotulo'][:40]})" for _p, d in rod) or "nada")
    if esp:
        txt += "\nesperando: " + ", ".join(f"{d['projeto']} ({d['rotulo'][:30]})" for _p, d in esp)
    return txt + f"\nprioridade: {c.get('prioridade')}"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def gerar_html():
    """Gera painel_web\\status.html — o status único numa página pra abrir no navegador (22/10, pedido do
    dono: 'painel'). Estático: rode de novo (ou o STATUS_PAINEL.bat) pra atualizar. Só leitura, não posta nada."""
    secoes = [("O que deu errado (24 h)", erros_txt, "erro"), ("Liga/desliga", controle_txt, ""),
              ("Controlador", controlador_txt, ""), ("Canais hoje", canais_txt, ""),
              ("Tarefas agendadas", tarefas_txt, ""), ("Render (PC1)", render_txt, ""),
              ("Máquinas (PC1/PC2/desktop)", maquinas_txt, ""), ("Top/Flop (views em 48 h)", topflop_txt, ""),
              ("Placar (48 h)", placar_txt, "")]
    cards = []
    for titulo, f, classe in secoes:
        try:
            corpo = f()
        except Exception as e:  # noqa: BLE001
            corpo, classe = f"(falhou: {type(e).__name__}: {e})", "erro"
        if classe == "erro" and corpo.strip() == "nada nas últimas 24 h":
            classe = ""
        cards.append(f'<section class="card {classe}"><h2>{_esc(titulo)}</h2><pre>{_esc(corpo)}</pre></section>')
    try:
        resumo = f"{controle_curto()} · {canais_curto()}"
    except Exception as e:  # noqa: BLE001
        resumo = f"(resumo falhou: {e})"
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Projetos de vídeo</title>
<style>
:root {{ --fundo:#12151c; --carta:#1a1f2a; --texto:#d8dee9; --fraco:#8a93a6; --erro:#3a1f24; --borda:#2a3140; }}
body {{ background:var(--fundo); color:var(--texto); font-family:Segoe UI,system-ui,sans-serif; margin:16px; }}
h1 {{ font-size:1.25rem; margin:0 0 2px; }}
.sub {{ color:var(--fraco); margin:0 0 14px; font-size:.9rem; }}
.card {{ background:var(--carta); border:1px solid var(--borda); border-radius:10px; padding:10px 14px; margin:0 0 12px; }}
.card.erro {{ background:var(--erro); border-color:#6b2a35; }}
h2 {{ font-size:.95rem; margin:0 0 6px; color:#9ecbff; }}
.card.erro h2 {{ color:#ff9e9e; }}
pre {{ margin:0; white-space:pre; overflow-x:auto; font:12px/1.5 Consolas,monospace; }}
</style></head><body>
<h1>Projetos de vídeo — um só sistema</h1>
<p class="sub">gerado em {datetime.now():%d/%m/%Y %H:%M} · {_esc(resumo)} · atualize rodando STATUS_PAINEL.bat</p>
{''.join(cards)}
</body></html>"""
    PAINEL_HTML.parent.mkdir(parents=True, exist_ok=True)
    PAINEL_HTML.write_text(html, encoding="utf-8")
    return PAINEL_HTML


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    so = sys.argv[1] if len(sys.argv) > 1 else ""
    if so == "html":
        print(gerar_html())
        return
    partes = [("LIGA/DESLIGA", controle_txt), ("CONTROLADOR", controlador_txt), ("CANAIS HOJE", canais_txt),
              ("TAREFAS", tarefas_txt), ("RENDER (PC1)", render_txt), ("PLACAR (48 h)", placar_txt),
              ("ERROS (24 h)", erros_txt), ("TOP/FLOP (48 h)", topflop_txt)]
    print(f"Status dos projetos de vídeo — {datetime.now():%d/%m %H:%M}")
    for titulo, f in partes:
        if so and not titulo.lower().startswith(so.lower()):
            continue
        print(f"\n== {titulo}")
        try:
            print(f())
        except Exception as e:  # noqa: BLE001
            print(f"(falhou: {type(e).__name__}: {e})")


if __name__ == "__main__":
    main()
