r"""relatorio_ronda.py — monta SOZINHO o relatório completo da ronda de hora em hora (12/11, dona: "não está pondo no
relatório tudo que eu pedi; falta o status do vigia e do melhorador; pode criar scripts que já peguem isso automático
toda vez pra não gastar tantos tokens").

Lê só arquivos locais (nada de laço sobre contas, nenhum IP tocado): logs dos longos/capas, status.json da central do
Kaggle, progresso no Drive (1 cat por arquivo, só os 3 da série), uso_maquinas, celulares, Flow, vigia, melhoradores,
pesquisador, Instagram. Cada número sai com "desde a última ronda" e "hoje"; o horário da ronda fica em
estado\relatorio_ronda.json (a próxima compara com ele). Seções na ordem da memória feedback_formato_ronda.md.

    python relatorio_ronda.py            # imprime o relatório (markdown) e grava a hora da ronda
    python relatorio_ronda.py --nao-gravar
"""
import json
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "relatorio_ronda.json"
COLAB = Path(r"D:\recapd-ambientes\producao\colab")
CFG = Path(r"D:\recapd-ambientes\producao\config")
PESQ = Path(r"D:\hipercool-materiais\pesquisador_melhorias")
FLOW = Path(r"D:\flow-imagens\logs\geracoes.jsonl")
RCLONE = r"D:\tools\rclone.exe"
STATUS = "https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json"
SERIE = [("13", "20261027_000000_PReloN5HWSI", "PReloN5HWSI"), ("14", "20261027_000001_pnX8RlSn7Yk", "pnX8RlSn7Yk"),
         ("15", "20261027_000002_oLBasz5H1-4", "oLBasz5H1-4")]
_SEM = 0x08000000

agora = datetime.now()
hoje = agora.strftime("%d/%m")
try:
    ultima = datetime.fromisoformat(json.loads(EST.read_text(encoding="utf-8"))["em"])
except (OSError, ValueError, KeyError):
    ultima = agora - timedelta(hours=1)


def _t_log(linha):
    """'[12/11 19:32] ...' -> datetime (ano atual) ou None."""
    m = re.match(r"\[(\d\d)/(\d\d) (\d\d):(\d\d)", linha)
    return datetime(agora.year, int(m.group(2)), int(m.group(1)), int(m.group(3)), int(m.group(4))) if m else None


def _linhas(arq, rx):
    """[(datetime, linha)] do log que casam com rx, só de hoje."""
    out = []
    try:
        for l in Path(arq).read_text(encoding="utf-8", errors="ignore").splitlines():
            if l.startswith(f"[{hoje}") and re.search(rx, l):
                t = _t_log(l)
                if t:
                    out.append((t, l))
    except OSError:
        pass
    return out


def _conta(itens):
    return sum(1 for t, _ in itens if t >= ultima), len(itens)


def _json(p, padrao=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return padrao


def _rc_cat(caminho):
    try:
        r = subprocess.run([RCLONE, "cat", caminho], capture_output=True, text=True, timeout=60, creationflags=_SEM,
                           encoding="utf-8", errors="replace")
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:  # noqa: BLE001
        return None


def _rc_lsf(caminho):
    try:
        r = subprocess.run([RCLONE, "lsf", caminho], capture_output=True, text=True, timeout=60, creationflags=_SEM,
                           encoding="utf-8", errors="replace")
        return r.stdout.split() if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def sec_numeros():
    post = _linhas(COLAB / "postar_longos.log", r"\s+ok: https://")
    capas = _linhas(COLAB / "capas_depois.log", r"aplicada no Studio: RESULTADO: \{\"(capa|teste_ab)\": \"(enviada|ok)")
    cel = []
    for l in (BASE / "logs" / "celulares.log").read_text(encoding="utf-8", errors="ignore").splitlines() \
            if (BASE / "logs" / "celulares.log").exists() else []:
        t = _t_log(l)
        if t and l.startswith(f"[{hoje}") and ": ok em" in l and "[teste" not in l:
            cel.append((t, l))
    flow = []
    for l in _flow_hoje():
        flow.append((datetime.fromisoformat(l["quando"][:19]), l))
    links = [re.search(r"https://\S+", l).group(0) for t, l in post if t >= ultima]
    p1, p2 = _conta(post)
    c1, c2 = _conta(capas)
    e1, e2 = _conta(cel)
    f1, f2 = _conta(flow)
    livre = _disco()
    out = ["## 📊 Números", "| | Desde a última ronda | Hoje |", "|---|---|---|",
           f"| Longos postados | {p1}{' — ' + ', '.join(links) if links else ''} | {p2} |",
           f"| Capas aplicadas | {c1} | {c2} |",
           f"| Renders nos celulares/STI | {e1} | {e2} |",
           f"| Imagens do Flow | {f1} | {f2} |",
           f"| Disco D livre | {livre} | — |"]
    v = _json(COLAB / "views_longos.json", {})
    if v:
        top = sorted(v.items(), key=lambda kv: -(kv[1].get("views") or 0))[:3]
        out.append("")
        out.append("Longos que mais rendem: " + "; ".join(f"{x.get('canal', '?')} {x.get('views')} views ({k})"
                                                       for k, x in top))
    return out


def _disco():
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-c", "[math]::Round((Get-PSDrive D).Free/1GB,1)"],
                           capture_output=True, text=True, timeout=30, creationflags=_SEM)
        return f"{r.stdout.strip()} GB"
    except Exception:  # noqa: BLE001
        return "?"


def _flow_hoje():
    out = []
    dia = agora.strftime("%Y-%m-%d")
    try:
        with open(FLOW, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 3_000_000))
            for l in f.read().decode("utf-8", "ignore").splitlines()[1:]:
                try:
                    d = json.loads(l)
                except ValueError:
                    continue
                if str(d.get("quando", "")).startswith(dia):
                    out.append(d)
    except OSError:
        pass
    return out


def sec_serie():
    out = ["## 🔥 Medieval Age (série da dona)"]
    st = _status()
    pedidos = {p["titulo"][:4]: p for p in (st or {}).get("pedidos", [])}
    postados = {x.get("nome", "")[:11] for x in (_json(COLAB / "longos_postados.json", {}) or {}).get("postados", [])}
    for parte, pid, vid in SERIE:
        if vid in postados:
            url = next((x.get("url") for x in _json(COLAB / "longos_postados.json", {})["postados"]
                        if x.get("nome", "").startswith(vid)), "")
            out.append(f"- Parte {parte}: ✅ POSTADA {url}")
            continue
        try:  # 12/11: ficha já baixada = pronta e esperando a postagem (a pasta saiu da fila do Kaggle)
            if any(d.name.startswith(vid) for d in Path(r"D:\hipercool-materiais\animes recap\na_nuvem").iterdir()):
                out.append(f"- Parte {parte}: ✅ PRONTA, esperando postar (ficha no PC)")
                continue
        except OSError:
            pass
        arqs = _rc_lsf(f"manhwa-drive:colab_recap/fila/{pid}") or []
        quem = next((a[13:-5] for a in arqs if a.startswith("em_andamento_")), None)
        prog = _rc_cat(f"manhwa-drive:colab_recap/progresso_{quem}.json") if quem else None
        if prog and prog.get("pid") == pid:
            out.append(f"- Parte {parte}: {prog.get('pct')}% — {prog.get('fase')} ({quem}, progresso no Drive "
                       f"{prog.get('em', '')[11:16]} UTC)")
        elif "pronto.json" in arqs:
            out.append(f"- Parte {parte}: pronta no Kaggle, descendo pro Drive/postagem")
        else:
            p = pedidos.get(f"({parte})")
            out.append(f"- Parte {parte}: {p['pct']}% {p['situacao']}" if p else f"- Parte {parte}: na fila")
    tarefas = []
    for parte, _, _ in SERIE:
        r = subprocess.run(["schtasks", "/query", "/tn", f"PostarMedieval{parte}", "/fo", "csv", "/nh"],
                           capture_output=True, text=True, timeout=20, creationflags=_SEM)
        if r.returncode == 0 and r.stdout.strip():
            c = r.stdout.strip().split('","')
            tarefas.append(f"{parte}: próxima {c[1] if len(c) > 1 else '?'}")
    if tarefas:
        out.append("- Postagem automática (pública + aviso): " + " | ".join(tarefas))
    return out


_ST = None


def _status():
    global _ST
    if _ST is None:
        try:
            with urllib.request.urlopen(STATUS, timeout=20) as r:
                _ST = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            _ST = {}
    return _ST


def sec_kaggle():
    st = _status()
    out = ["## 🎮 Kaggle"]
    if not st:
        return out + ["- central sem resposta"]
    rod = [g["conta"] for g in st.get("gpus", []) if g.get("conta")]
    out.append(f"- Rodando: {len(rod)} ({', '.join(rod) or 'nenhuma'}) | {st.get('verificadas', '?')} verificadas | "
               f"atualizado {st.get('atualizado', '?')}")
    for p in st.get("pedidos", [])[:8]:
        out.append(f"  - {p['pct']}% {p['situacao'][:45]} — {p['titulo'][:60]}")
    try:
        r = subprocess.run(["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", "hermes-prod",
                            "grep -v kernelworkerstatus.running /opt/recap_central/central.log | tail -40 | "
                            "grep -i 'proxy\\|descansa\\|banid\\|401\\|erro' | tail -4"],
                           capture_output=True, text=True, timeout=40, creationflags=_SEM, encoding="utf-8",
                           errors="replace")
        al = [l.strip()[:160] for l in r.stdout.splitlines() if l.strip()]
        if al:
            out.append("- Alertas da central: " + " / ".join(al))
    except Exception:  # noqa: BLE001
        pass
    return out


def sec_frentes():
    out = ["## 🌍 Outras línguas e 📈 mais vistos"]
    for pid, lg in (("20261027_000010_PDPOK7xOyas", "vietnamita"), ("20261027_000011_dLd0uCJVaEc", "inglês")):
        arqs = _rc_lsf(f"manhwa-drive:colab_recap/fila/{pid}")
        est = ("pronto" if arqs and "pronto.json" in arqs else "renderizando" if arqs and any(
            a.startswith("em_andamento") for a in arqs) else "na fila" if arqs else "saiu da fila (pronto/postado)")
        out.append(f"- Longo em {lg}: {est}")
    fp = _json(CFG / "fontes_prioridade.json", {}) or {}
    vs = fp.get("videos", [])
    out.append(f"- Lista de prioridade: {len(vs)} vídeos ({sum(1 for v in vs if v.get('parecido'))} parecidos com "
               f"campeões, {sum(1 for v in vs if v.get('canal_destino') == 'novo_ia_agora_h3n')} pro InventoReact)")
    return out


def sec_maquinas():
    out = ["## 📱 Máquinas (hora / dia)"]
    try:
        r = subprocess.run([sys.executable, str(BASE / "uso_maquinas.py"), "resumo"], capture_output=True, text=True,
                           timeout=120, creationflags=_SEM, encoding="utf-8", errors="replace", cwd=str(BASE))
        out += ["```"] + [l for l in r.stdout.splitlines() if l.strip()][-9:] + ["```"]
    except Exception as e:  # noqa: BLE001
        out.append(f"- uso_maquinas falhou ({type(e).__name__})")
    st = (_json(BASE / "estado" / "celulares_stats.json", {}) or {}).get(agora.strftime("%Y-%m-%d"), {})
    if st:
        out.append("- Renders hoje: " + ", ".join(f"{h} {v['ok']} ok/{v['falhas']} falhas" for h, v in st.items()))
    por = Counter((d.get("onde") or str(d.get("via") or "").split(":")[-1]).lower() for d in _flow_hoje())
    if por:
        out.append("- Flow hoje por máquina: " + ", ".join(f"{k} {n}" for k, n in por.most_common()))
    return out


def sec_capas():
    out = ["## 🖼️ Capas"]
    fila = _json(COLAB / "capas_depois.json", []) or []
    c = Counter(x.get("estado") for x in fila)
    out.append(f"- Fila: {c.get('pendente', 0)} pendentes, {c.get('feito', 0)} feitas, {c.get('sem_capa', 0)} sem capa")
    tempos = [int(m.group(1)) for _, l in _linhas(COLAB / "capas_depois.log", r"capa\(s\) em (\d+) min")
              for m in [re.search(r"capa\(s\) em (\d+) min", l)] if m]
    if tempos:
        out.append(f"- Tempo por capa hoje: {min(tempos)}–{max(tempos)} min (média {sum(tempos) // len(tempos)})")
    falhas = _linhas(COLAB / "capas_depois.log", r"NÃO confirmou|erro|falharam")
    f1, f2 = _conta(falhas)
    out.append(f"- Falhas do Studio/geração: {f1} desde a última, {f2} hoje")
    return out


def sec_vigia_melhorador():
    out = ["## 🛡️ Vigia e 🧠 Melhoradores"]
    vg = _json(BASE / "estado" / "vigilancia.json", {}) or {}
    dia = vg.get("dia") or {}
    casos = []
    try:
        for l in (BASE / "estado" / "vigilancia_casos.jsonl").read_text(encoding="utf-8").splitlines()[-400:]:
            d = json.loads(l)
            if datetime.fromisoformat(d["em"]) >= agora.replace(hour=0, minute=0):
                casos.append(d)
    except (OSError, ValueError, KeyError):
        pass
    passos = Counter(d.get("passo") for d in casos)
    novos = [d for d in casos if datetime.fromisoformat(d["em"]) >= ultima]
    out.append(f"- Vigilância (VigilanciaSistema): {dia.get('consertos', 0)} consertos hoje | passos hoje: "
               + (", ".join(f"{k} {n}" for k, n in passos.most_common()) or "nenhum")
               + f" | {len(novos)} eventos desde a última")
    ult = [d for d in casos if d.get("passo") in ("consertou", "conserto", "falso", "dona", "falhou")][-3:]
    for d in ult:
        out.append(f"  - {d['em'][11:16]} {d.get('categoria')}: {d.get('passo')} — {str(d.get('resumo', ''))[:110]}")
    va = sorted((BASE / "logs").glob("vigia_agente_*.log"))
    if va:
        txt = va[-1].read_text(encoding="utf-8", errors="ignore")
        m = re.findall(r"STATUS:\s*(\S+)", txt)
        out.append(f"- Vigia agente: última rodada {va[-1].stem[-13:]} — STATUS {m[-1] if m else '?'}")
    for nome, arq in (("Melhorador central", BASE / "logs" / "melhorador_central.log"),
                      ("Melhorador dos longos", COLAB / "melhorador_longo.log")):
        try:
            ls = arq.read_text(encoding="utf-8", errors="ignore").splitlines()
            hj = [l for l in ls if l.startswith(f"[{hoje}")]
            mud = [l for l in hj if re.search(r"aplic|mudou|implant|conserto|vencedor|promov", l, re.I)]
            out.append(f"- {nome}: última {hj[-1][1:12] if hj else '—'} | {len(mud)} mudanças hoje | "
                       f"{(hj[-1][14:] if hj else '')[:120]}")
        except OSError:
            out.append(f"- {nome}: sem log")
    return out


def sec_pesquisador():
    out = ["## 🔎 Pesquisador"]
    painel = (PESQ / "PAINEL_PESQUISADOR.md")
    try:
        t = painel.read_text(encoding="utf-8")
        m = re.search(r"Motor: \*\*(\w+)\*\*.*?teto hoje: \*\*(\d+)\*\*", t)
        lin = re.search(rf"\| {agora:%Y-%m-%d} \| (\d+) \| (\d+) \|", t)
        out.append(f"- Motor {m.group(1) if m else '?'} | hoje {lin.group(1) if lin else '?'} pesquisas, "
                   f"{lin.group(2) if lin else '?'} ok")
    except OSError:
        pass
    for linha in ("LONGOS", "CAPAS"):
        try:
            t = (PESQ / "ENTREGAS" / f"{linha}.md").read_text(encoding="utf-8")
            out.append(f"- Caixa {linha}: {t.count('## [ ] PENDENTE')} pendente(s)")  # 13/11: só os blocos, não as instruções
        except OSError:
            pass
    try:
        reg = [json.loads(l) for l in (PESQ / "motor_registro.jsonl").read_text(encoding="utf-8").splitlines()[-300:]]
        desc = sum(len(r.get("repos", [])) for r in reg if r.get("evento") == "descarte_auto"
                   and str(r.get("em", r.get("quando", ""))) >= agora.strftime("%Y-%m-%d"))
        out.append(f"- Descartes automáticos (lixo filtrado) hoje: {desc}")
    except (OSError, ValueError):
        pass
    return out


def sec_redes():
    """12/11 dona: "vamos adicionar os dados dos Shorts, Instagram e TikTok; quero eliminar o outro chat e ficar só com
    esse". Shorts = uploads_ledger.jsonl (tipo short); TikTok/Instagram = logs do dia do postador."""
    out = ["## 📲 Shorts, TikTok e Instagram"]
    led = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
    sh, por_canal = [], Counter()
    try:
        with open(led, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 2_000_000))
            for l in f.read().decode("utf-8", "ignore").splitlines()[1:]:
                try:
                    d = json.loads(l)
                except ValueError:
                    continue
                ts = str(d.get("ts", ""))[:19]
                if ts.startswith(agora.strftime("%Y-%m-%d")) and d.get("tipo") != "completo":
                    t = datetime.fromisoformat(ts)
                    sh.append((t, d))
                    por_canal[d.get("canal", "?")] += 1
    except OSError:
        pass
    s1, s2 = _conta(sh)
    out.append(f"- Shorts no YouTube (subidos/agendados): {s1} desde a última | {s2} hoje em {len(por_canal)} canais")
    if por_canal:
        out.append("  - mais hoje: " + ", ".join(f"{c} {n}" for c, n in por_canal.most_common(6)))
    logs = Path(r"D:\postador-de-videos\logs")
    tk = logs / f"tiktok_{agora:%Y%m%d}.log"
    ok_tk, err_tk = [], []
    try:
        for l in tk.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"\[(\d\d):(\d\d):\d\d\]\s+(OK #\d+ \(([^)]+)\)|.*(FALHOU|ERRO|falhou))", l)
            if m:
                t = agora.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
                (ok_tk if "OK #" in l else err_tk).append((t, m.group(4) or l[11:90]))
    except OSError:
        pass
    k1, k2 = _conta(ok_tk)
    e1, e2 = _conta(err_tk)
    out.append(f"- TikTok: {k1} postados desde a última | {k2} hoje ({len({c for _, c in ok_tk})} contas) | "
               f"falhas {e1}/{e2}")
    try:
        resumo = [l for l in (logs / "tiktok_auto.log").read_text(encoding="utf-8", errors="ignore")
                  .splitlines()[-40:] if "deslogados" in l or "sem postar hoje" in l]
        if resumo:
            out.append("  - " + " | ".join(r[11:].strip() for r in resumo[-2:]))
    except OSError:
        pass
    ig_ok, ig_err = [], []
    try:
        # o log do Instagram não tem data na linha: lê de trás pra frente e para quando a hora "volta" (virou o dia)
        ls = (logs / "instagram_auto.log").read_text(encoding="utf-8", errors="ignore").splitlines()
        anterior = 24 * 60
        for l in reversed(ls):
            m = re.match(r"\[(\d\d):(\d\d):\d\d\]", l)
            if not m:
                continue
            minuto = int(m.group(1)) * 60 + int(m.group(2))
            if minuto > anterior + 5:  # hora maior que a da linha seguinte = linha de ontem
                break
            anterior = minuto
            r = re.search(r"=== RESUMO Instagram: postados (\d+) \| erros (\d+)", l)
            if r:
                t = agora.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
                ig_ok += [t] * int(r.group(1))
                ig_err += [t] * int(r.group(2))
    except OSError:
        pass
    i1 = sum(1 for t in ig_ok if t >= ultima)
    out.append(f"- Instagram: {i1} postados desde a última | {len(ig_ok)} nas rodadas de hoje | erros "
               f"{sum(1 for t in ig_err if t >= ultima)}/{len(ig_err)}")
    try:
        trav = [l for l in (logs / "instagram_auto.log").read_text(encoding="utf-8", errors="ignore")
                .splitlines()[-300:] if re.search(r"verifica|challenge|bloquead|checkpoint|suspens", l, re.I)]
        if trav:
            out.append(f"  - ⚠️ Instagram pedindo verificação/travado: {trav[-1][11:160]}")
    except OSError:
        pass
    return out


def sec_insta_http():
    out = ["## 📸 Instagram e 🌐 navegador sem navegador"]
    try:
        ls = [json.loads(l) for l in (BASE / "estado" / "instagram_publico.jsonl").read_text(encoding="utf-8")
              .splitlines()[-200:] if l.strip() and l.strip() != "null"]
        hj = [d for d in ls if str(d.get("em", "")).startswith(agora.strftime("%Y-%m-%d"))]
        out.append(f"- Instagram (contas de IA): {len(hj)} leituras hoje"
                   + (f"; última {hj[-1].get('conta')}: {hj[-1].get('seguidores')} seguidores" if hj else ""))
    except OSError:
        out.append("- Instagram: sem leitura")
    vias = Counter(str(d.get("via") or "chrome").split(":")[0] for d in _flow_hoje())
    if vias:
        out.append("- Flow por via hoje: " + ", ".join(f"{k} {n}" for k, n in vias.most_common()))
    # 12/11 (chat CURTOS): estado da troca automática de rota do Flow (veo\beta\vigia_flow.py, tarefa VigiaFlow)
    try:
        vf = json.loads(Path(r"D:\veo\beta\logs\vigia_flow.json").read_text(encoding="utf-8"))
        ri = (vf.get("rotas") or {}).get("imagem") or {}
        ja, u2 = ri.get("janela") or {}, vf.get("ultimas_2h") or {}
        nome = {"ligado": "SEM NAVEGADOR", "teste": "TESTANDO a volta", "desligado": "PELA TELA (sem navegador quebrou)"}
        out.append(f"- Rota do Flow (imagem): {nome.get(ri.get('estado'), ri.get('estado', '?'))} — 30 min: "
                   f"{ja.get('ok', '?')}/{ja.get('pedidos', '?')} ok; 2 h: {u2.get('http_ok', 0)} sem navegador + "
                   f"{u2.get('tela_ok', 0)} tela" + ("  ⚠️ AS DUAS ROTAS PARADAS" if u2 and not u2.get('http_ok')
                                                     and not u2.get('tela_ok') else ""))
    except (OSError, ValueError):
        out.append("- Rota do Flow: vigia sem leitura")
    return out


def main(gravar):
    partes = [f"# Relatório completo — {agora:%d/%m, %H:%M}",
              f"_(desde a última ronda = desde {ultima:%d/%m %H:%M})_"]
    for f in (sec_numeros, sec_serie, sec_kaggle, sec_frentes, sec_maquinas, sec_capas, sec_vigia_melhorador,
              sec_pesquisador, sec_redes, sec_insta_http):
        try:
            partes += [""] + f()
        except Exception as e:  # noqa: BLE001 — uma seção quebrada não derruba o relatório
            partes += ["", f"## {f.__name__}: falhou ({type(e).__name__}: {str(e)[:120]})"]
    partes += ["", "## 🛠️ O que consertei / 🙋 Só você / 🔜 Em seguida",
               "_(o chat preenche: consertos desta hora, pendências da dona e próximos passos)_"]
    print("\n".join(partes))
    if gravar:
        EST.write_text(json.dumps({"em": agora.isoformat(timespec="seconds")}), encoding="utf-8")


if __name__ == "__main__":
    main("--nao-gravar" not in sys.argv)
