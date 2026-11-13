"""vigilancia.py — vigilância 24 h em camadas (04/11/2026, dona). Tarefa VigilanciaSistema, de 10 em 10 min, oculta.

Dona 04/11: "ter o máximo de conferência que não dependa de IA (é só código) ... 1 vigia deve usar o Gemini 3.8 Flash,
que temos ilimitado, 24 h junto com o medidor; aí adicionamos IA para o consertador e devemos ter um medidor pra ver qual
modelo se dá melhor ... Sonnet web e Argon renovam de 5 em 5 h ... 1min+Sonnet web ... Kiro Sonnet 4.5 não renova mas tem
grande quantidade no mês e é estável ... o Opus é opcional: se os outros derem conta, blz; se não, o Opus permanece; o
próprio Opus conserta/avalia se precisa dele; em último caso o Opus 5.5. Guardar logs de tudo." Revisor reprovou =
DESFAZ sozinho e avisa (dona 04/11).

CAMADA 0 — medidores (código puro, sem IA, toda volta): ritmo de postagem (TikTok/Instagram/solares x mediana 7 dias),
  mesmo erro repetido nos logs (postagem e produção), reel solar perdido (clipe APROVADO e montagem morreu), desktop
  parado com canal abaixo do alvo, canal com 0 dia de reserva. Cada achado = um ALARME com chave (repetido < 6 h não
  abre caso novo; reaparecido < 24 h depois de consertado = "voltou", conta contra quem consertou).
CAMADA 1 — vigia (agy/gemini-3.8-flash-high, ilimitado): confirma se o alarme é real e acha a causa (arquivo + linha) —
  painel_ia "pergunta". Falso alarme = caso fechado sem gastar o consertador.
CAMADA 2 — consertador: o melhor do PLACAR entre CONSERTADORES que estiver com token agora (ia_reserva.testar; quem
  voltou a ter token entra na hora, como o sentinela). Começa revezando até cada um ter AMOSTRA casos; depois vai o de
  maior nota (aprovado pelo revisor e não voltou em 24 h). painel_ia "propor" + auto_aplicar (backup + desfazer).
CAMADA 3 — revisor (antigravity/claude-opus-4-6-thinking): lê o diff + o alarme e devolve aprovado/motivo/se o Opus
  ainda é necessário nesta categoria. Reprovado = painel_ia.desfazer + aviso. Categoria com DISPENSA aprovações seguidas
  nas últimas 10 (e nada voltou) = revisão dispensada nela (o Opus sai); voltou = o Opus volta. Opus 4.6 sem token =
  cc/claude-opus-5-5 (último caso).
Logs: estado\\vigilancia_casos.jsonl (cada passo), estado\\vigilancia.json (casos abertos + placar), VIGILANCIA.md.
    python vigilancia.py            # uma volta
    python vigilancia.py --simular  # só os medidores (não abre caso, não chama IA)
    python vigilancia.py placar     # notas de cada modelo por categoria
"""
import json
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "vigilancia.json"
CASOS = BASE / "estado" / "vigilancia_casos.jsonl"
DOC = BASE / "VIGILANCIA.md"
sys.path.insert(0, str(BASE))
sys.path.insert(0, r"D:\postador-de-videos\bin")

VIGIA = "agy/gemini-3.8-flash-high"
CONSERTADORES = ["cw/claude-sonnet-5-5", "gemini-4-argon", "1minopus-sonnetweb", "kr/claude-sonnet-4.5"]
SEM_TESTE = set()
# 04/11: o Argon e o misto 1min+Sonnet só existem na ROTA DO VS CODE (proxy 20133); pelo gateway padrão o 1min dava
# "Unable to determine provider" e o painel caía no Kiro (4 consertos gastaram Kiro sem contar), e o teste do Argon
# estourava 60 s (ele leva ~30 s) — nunca entrava. Esses vão com rota="vscode" e são testados por ela (prazo maior).
ROTA_VSCODE = {"gemini-4-argon", "1minopus-sonnetweb"}
ARQ_ROTA_VSCODE = Path(r"C:\Users\Haylla\Desktop\Claude VS Code - Trocar Modelo\settings_5_OPUS-5.5_NORMAL.json")
TESTE_VALE_S = 1800  # resultado do teste de disponibilidade vale 30 min (o Argon leva ~30 s pra responder)
# 04/11 dona: "o Opus 5.5 não precisa estar nessa conta; o 4.6 já deve servir — o 5.5 vai ser usado NO CHAT pra avaliar
# os outros, inclusive as correções do 4.6". Sem o 4.6 com token = o conserto espera a volta dele.
REVISORES = ["antigravity/claude-opus-4-6-thinking"]
AMOSTRA = 3          # casos por consertador antes de escolher pelo placar
DISPENSA = 9         # aprovações nas últimas 10 da categoria (e nada voltou) = revisão do Opus dispensada nela
CASOS_DIA_MAX = 12   # teto de consertos automáticos por dia (todos os modelos)
KIRO_DIA_MAX = 30    # 04/11 dona: Kiro renova 1x/mês e a quantidade é muito grande (o vigia antigo rodou o mês quase todo)
REPETIDO_H, VOLTOU_H = 6, 24
REGRAS_CONSERTO = (
    "REGRAS QUE NÃO SE QUEBRAM: nunca 2 contas no mesmo IP (nem em teste); nada abre janela na tela (rodar_oculto.vbs, "
    "CREATE_NO_WINDOW); não mexer nos workers do PC2 (hipercool); nunca postar público direto (agendado); 1080p mínimo; "
    "não mexer em video-fila\\vigilancia.py, painel_ia.py, avisos.py, ia_reserva.py. Conserte a CAUSA, com o MENOR "
    "diff possível, e prove com log/teste real que funcionou.")


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def _ler():
    try:
        return json.loads(EST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"casos": {}, "placar": {}, "alarmes": {}, "dia": {}}


def _gravar(d):
    EST.parent.mkdir(exist_ok=True)
    tmp = EST.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(EST)


def _registro(caso, passo, **extra):
    CASOS.parent.mkdir(exist_ok=True)
    with open(CASOS, "a", encoding="utf-8") as f:
        f.write(json.dumps({"em": _agora(), "caso": caso.get("id"), "categoria": caso.get("categoria"), "passo": passo,
                            **extra}, ensure_ascii=False) + "\n")


def _avisar(texto, importante=True):
    try:
        import avisos
        avisos.enviar("<b>Vigilância</b>\n" + texto, "vigilancia", importante=importante)
    except Exception:  # noqa: BLE001
        pass


# ───────────────────────── CAMADA 0: medidores (sem IA) ─────────────────────────
def _norm(t):
    return re.sub(r"\d+", "N", t)[:100]


def med_postagem(agora):
    import vigia_postagem as vp
    out = []
    for nome, (hoje, normal) in (("tiktok", vp.ritmo(vp._ledger("tiktok_auto_posted.json"), agora)),
                                 ("instagram", vp.ritmo(vp._ledger("instagram_auto_posted.json"), agora)),
                                 ("solares", vp.solares(agora))):
        if normal >= 5 and hoje < 0.5 * normal:
            out.append({"chave": f"ritmo:{nome}", "categoria": f"postagem-{nome}", "projeto": "msenergy" if nome == "solares"
                        else "postador", "titulo": f"{nome}: {hoje} posts até {agora:%H:%M}, normal ~{normal:.0f}",
                        "evidencia": f"ledger/logs de {nome}: hoje {hoje} x mediana 7 dias {normal}"})
    for plat, motivo, n in vp.erros_repetidos(agora):
        out.append({"chave": f"erro:{plat}:{motivo[:60]}", "categoria": f"postagem-{plat}", "projeto": "postador",
                    "titulo": f"{plat}: mesmo erro {n}x em 6 h", "evidencia": f"logs\\{plat}_{agora:%Y%m%d}.log: {motivo}"})
    return out


def med_solar_perdido(agora):
    """Clipe do Veo APROVADO e a montagem morreu logo depois (03/11: CPU 100% matou ffmpeg/ffprobe)."""
    out = []
    for f in Path(r"D:\ms-energy\logs").glob("reel_*.log"):
        try:
            linhas = f.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]
        except OSError:
            continue
        for i, l in enumerate(linhas):
            if "[QA] clipe APROVADO" in l:
                h = re.match(r"\[(\d\d):(\d\d):(\d\d)\]", l.strip())
                if not h:
                    continue
                quando = agora.replace(hour=int(h.group(1)), minute=int(h.group(2)), second=int(h.group(3)))
                if quando > agora:
                    quando -= timedelta(days=1)
                if (agora - quando).total_seconds() > 3 * 3600:  # só as últimas 3 h (o log tem só a hora)
                    continue
                prox = linhas[i + 1:i + 15]
                if any("PUBLICADO" in x or "[QA] final APROVADO" in x for x in prox):
                    continue
                erro = next((x for x in prox if "ERRO:" in x), None)
                if erro:
                    out.append({"chave": f"solar_perdido:{f.stem}:{_norm(erro)[:50]}", "categoria": "solar-montagem",
                                "projeto": "msenergy", "titulo": f"{f.stem}: clipe do Veo aprovado e a montagem morreu",
                                "evidencia": f"{f}: {l.strip()[:120]} → {erro.strip()[:200]}"})
    return out[-3:]


def med_desktop_parado(agora):
    f = BASE / "logs" / f"controlador_{agora:%Y%m%d}.log"
    try:
        linhas = f.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]
    except OSError:
        return []
    estados = [l for l in linhas if "| desktop:" in l][-4:]
    nada = [l for l in linhas if "desktop:" in l and "nada pra disparar" in l][-4:]
    if len(estados) >= 4 and all("desktop: LIVRE" in l for l in estados) and len(nada) >= 3:
        return [{"chave": "<SEGREDO_REMOVIDO>", "categoria": "maquina-ociosa", "projeto": "geral",
                 "titulo": "desktop LIVRE 4 voltas seguidas e nada disparado",
                 "evidencia": f"{f}: " + " || ".join(x.strip()[:110] for x in nada[-2:])}]
    return []


def med_reserva_zero(agora):
    try:
        r = subprocess.run([r"D:\hipercool-materiais\python\venv\Scripts\python.exe", str(BASE / "reserva_status.py")],
                           capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
                           creationflags=0x08000000)
    except Exception:  # noqa: BLE001
        return []
    zerados = re.findall(r"^\s*0\.0 dias\s+(\S+).*agendados=\s*0\s+prontos=\s*0", r.stdout, re.M)
    return [{"chave": f"reserva_zero:{c}", "categoria": "reserva-canal", "projeto": "cortes",
             "titulo": f"canal {c} com 0 vídeo agendado e 0 pronto (regra: nenhum canal 1 dia sem postar)",
             "evidencia": "reserva_status.py: " + c} for c in zerados]


def med_erro_producao(agora):
    out = []
    for f, proj in ((Path(r"D:\hipercool-materiais\anime") / f"_parceiro_{agora:%Y%m%d}.log", "cortes"),
                    (Path(r"D:\ms-energy\logs") / "gerar_diario.log", "msenergy")):
        try:
            linhas = f.read_text(encoding="utf-8", errors="ignore").splitlines()[-1500:]
        except OSError:
            continue
        c = Counter(_norm(re.sub(r"^.*?(ERROR|ERRO)\W+", "", l)) for l in linhas if re.search(r"\b(ERROR|ERRO)\b", l))
        for motivo, n in c.most_common(2):
            if n >= 5:
                out.append({"chave": f"erro_prod:{f.stem}:{motivo[:60]}", "categoria": f"producao-{proj}",
                            "projeto": proj, "titulo": f"{f.name}: mesmo erro {n}x", "evidencia": f"{f}: {motivo}"})
    return out


def med_qa_shorts(agora):
    """04/11 (pesquisa da madrugada, item qc-skill — sem instalar nada): cada Short já sai com qa.json (pretos,
    congelados, mudos, volume). Ninguém olhava: qa.json das últimas 2 h com ok=false/problemas = alarme."""
    out = []
    limite = time.time() - 2 * 3600
    for q in Path(r"D:\hipercool-materiais\animes recap\shorts").glob("*/qa.json"):
        try:
            if q.stat().st_mtime < limite:
                continue
            j = json.loads(q.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("ok") is False or j.get("problemas"):
            out.append({"chave": f"qa:{q.parent.name}", "categoria": "qualidade-short", "projeto": "cortes",
                        "titulo": f"Short {q.parent.name} saiu com problema de qualidade",
                        "evidencia": f"{q}: {json.dumps({k: j.get(k) for k in ('problemas', 'pretos', 'congelados', 'mudos', 'loudness_lufs')}, ensure_ascii=False)[:300]}"})
    return out


def med_qa_longos(agora):
    """04/11 (claude-38/claude-49): o QA dos LONGOS roda no Kaggle e o qa.json vem para animes recap\\na_nuvem\\<nome>\\
    (mesmo formato do dos Shorts); o postar_longos só avisa e posta assim mesmo. qa.json das últimas 6 h com problema."""
    out = []
    limite = time.time() - 6 * 3600
    for q in Path(r"D:\hipercool-materiais\animes recap\na_nuvem").glob("*/qa.json"):
        try:
            if q.stat().st_mtime < limite:
                continue
            j = json.loads(q.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("ok") is False or j.get("problemas"):
            out.append({"chave": f"qa_longo:{q.parent.name}", "categoria": "qualidade-longo", "projeto": "cortes",
                        "titulo": f"longo {q.parent.name} saiu com problema de qualidade",
                        "evidencia": f"{q}: {json.dumps({k: j.get(k) for k in ('problemas', 'pretos', 'congelados', 'mudos', 'loudness_lufs')}, ensure_ascii=False)[:300]}"})
    return out


def med_capas_longos(agora):
    """04/11 (dona: "temos problemas de capa que não sai direito"): longo subido nos últimos 3 dias sem as capas B/C do
    teste A/B (thumbs_ab < 2) ou aberto há 24 h+ sem acabamento (extras_ledger: A/B + comentário fixado). Achado na
    madrugada: o extras_ledger ignorava o projeto longo_recap — nenhum longo tinha recebido o teste A/B."""
    out = []
    led = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
    try:
        est = json.loads(Path(r"D:\postador-de-videos\_analise\extras_ledger.json").read_text(encoding="utf-8"))
        linhas = led.read_text(encoding="utf-8").splitlines()[-400:]
    except (OSError, ValueError):
        return out
    for l in linhas:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r.get("projeto") != "longo_recap" or not r.get("video_id"):
            continue
        try:
            ts = datetime.fromisoformat(str(r.get("ts"))[:19])
            pub = datetime.fromisoformat(str(r.get("publish_at") or r.get("ts"))[:19].replace("Z", ""))
        except ValueError:
            continue
        if agora - ts > timedelta(days=3):
            continue
        try:
            ficha = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError):
            ficha = {}
        if len(ficha.get("thumbs_ab") or []) < 2:
            out.append({"chave": f"capas_ab:{r['video_id']}", "categoria": "capa-longo", "projeto": "cortes",
                        "titulo": f"longo {r['video_id']} ({r.get('canal')}) sem as capas B/C do teste A/B",
                        "evidencia": f"{r.get('caminho')} postar.json thumbs_ab={ficha.get('thumbs_ab')}"})
        if agora - pub > timedelta(hours=27) and r["video_id"] not in est:  # publish_at em UTC: folga de 3 h
            out.append({"chave": f"acabamento:{r['video_id']}", "categoria": "capa-longo", "projeto": "postador",
                        "titulo": f"longo {r['video_id']} aberto há 24 h+ sem acabamento (A/B + comentário fixado)",
                        "evidencia": f"extras_ledger.json sem {r['video_id']} (publish_at {r.get('publish_at')})"})
    return out


MEDIDORES = (med_postagem, med_solar_perdido, med_desktop_parado, med_reserva_zero, med_erro_producao, med_qa_shorts,
             med_capas_longos, med_qa_longos)


def medir(agora):
    achados = []
    for m in MEDIDORES:
        try:
            achados += m(agora)
        except Exception as e:  # noqa: BLE001 — um medidor quebrado não derruba os outros
            achados.append({"chave": f"medidor_quebrado:{m.__name__}", "categoria": "vigilancia", "projeto": "geral",
                            "titulo": f"medidor {m.__name__} quebrou", "evidencia": f"{type(e).__name__}: {e}"})
    return achados


# ───────────────────────── placar ─────────────────────────
def _nota(placar, modelo, cat=None):
    p = placar.get(modelo, {})
    linhas = [v for k, v in p.items() if cat is None or k == cat]
    t = sum(x.get("tentativas", 0) for x in linhas)
    bom = sum(x.get("aprovados", 0) - x.get("voltou", 0) for x in linhas)
    return t, (bom / t if t else 0.0)


def _pontuar(d, modelo, cat, campo, n=1):
    d["placar"].setdefault(modelo, {}).setdefault(cat, {"tentativas": 0, "aprovados": 0, "reprovados": 0, "voltou": 0,
                                                         "falhou": 0})[campo] += n


def _testar_vscode(modelo):
    """None = respondeu pela rota do VS Code; senão o erro."""
    import urllib.request
    vs = json.loads(ARQ_ROTA_VSCODE.read_text(encoding="utf-8"))
    ev = {x["name"]: x["value"] for x in vs["claudeCode.environmentVariables"]}
    base, tok = ev["ANTHROPIC_BASE_URL"].rstrip("/"), ev["ANTHROPIC_AUTH_TOKEN"]
    corpo = json.dumps({"model": modelo, "max_tokens": 5, "messages": [{"role": "user", "content": "responda só: ok"}]})
    req = urllib.request.Request(base + "/v1/messages", corpo.encode(), {
        "Content-Type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": tok,
        "Authorization": "Bearer " + tok})
    try:
        urllib.request.urlopen(req, timeout=200).read()
        return None
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:120]}"


def _volta_em(modelo):
    """04/11 (dona: "não precisa ficar 5 h fora; fica até o aviso de que o token voltou — os monitores já sabem a hora"):
    timestamp de quando o modelo volta a ter token. Antigravity (Opus 4.6) e Claude (Opus 5.5): a hora REAL de volta
    das contas no OmniRoute (sentinela_credito); com conta com crédito = 10 min. Sonnet web: conta em 429 sai 10 min.
    Argon: cota da conta volta em < 1 h. Kiro (conta-gota) e 1min (visita diária): virada do dia (00:05)."""
    agora = time.time()
    prov = "antigravity" if modelo.startswith("antigravity/") else "claude" if modelo.startswith("cc/") else None
    if prov:
        try:
            sys.path.insert(0, "D:\\")
            import sentinela_credito as sc
            r = sc.consultar(prov)
            if r.get("com_credito", 0) > 0:
                return agora + 600
            vs = [datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp() for v in r.get("voltas") or []]
            futuras = [v for v in vs if v > agora]
            if futuras:
                return min(futuras) + 60
        except Exception:  # noqa: BLE001
            pass
        return agora + 1800
    if modelo.startswith("cw/") or modelo == "1minopus-sonnetweb":
        # 04/11 dona: o 1min é só REFORÇO do Sonnet 5.5 web (planeja); acabou o 1min no dia, o combo segue com o
        # Sonnet web — então o combo volta junto com o Sonnet web (10 min), não na virada do dia
        return agora + 600
    if modelo == "gemini-4-argon":
        return agora + 2700
    if modelo.startswith("kr/"):
        # 04/11 dona: "o Kiro é diferente: vira 1 vez por mês e a quantidade é muito grande" — renova dia 1, 00:00 UTC
        from datetime import timezone as _tz
        u = datetime.now(_tz.utc)
        prox = (u.replace(day=1, hour=0, minute=5, second=0, microsecond=0) + timedelta(days=32)).replace(day=1)
        return prox.timestamp()
    if modelo.startswith("1min"):  # crédito da visita diária
        amanha = datetime.now().replace(hour=0, minute=5, second=0, microsecond=0) + timedelta(days=1)
        return amanha.timestamp()
    return agora + 1800


def _disponivel(modelo, d):
    if time.time() < d.get("fora", {}).get(modelo, 0):
        return False
    import ia_reserva
    if ia_reserva.eh_kiro(modelo) and d["dia"].get("kiro", 0) >= KIRO_DIA_MAX:
        return False
    cache = d.setdefault("teste", {}).get(modelo)
    if cache and cache[1] and time.time() - cache[0] < TESTE_VALE_S:
        return True  # só o "tem token" fica guardado; sem token = fora ATÉ A HORA DE VOLTA (abaixo)
    try:
        ok = (_testar_vscode(modelo) if modelo in ROTA_VSCODE else ia_reserva.testar(modelo)) is None
    except Exception:  # noqa: BLE001
        ok = False
    d["teste"][modelo] = [time.time(), ok]
    if not ok:
        d.setdefault("fora", {})[modelo] = _volta_em(modelo)
    return ok


def escolher_consertador(d, cat):
    vivos = [m for m in CONSERTADORES if _disponivel(m, d)]
    if not vivos:
        return None
    pouca = [m for m in vivos if _nota(d["placar"], m)[0] < AMOSTRA]
    if pouca:  # revezamento até cada um ter a amostra (o Kiro por último: ele acaba no mês)
        return sorted(pouca, key=lambda m: (_nota(d["placar"], m)[0], m.startswith("kr/")))[0]
    return max(vivos, key=lambda m: (_nota(d["placar"], m, cat)[1] if _nota(d["placar"], m, cat)[0] else
                                     _nota(d["placar"], m)[1], not m.startswith("kr/")))


def revisao_dispensada(cat):
    """Últimas 10 revisões da categoria: >= DISPENSA aprovadas e nenhuma que voltou = o Opus sai dela."""
    ult = []
    try:
        for l in CASOS.read_text(encoding="utf-8").splitlines():
            j = json.loads(l)
            if j.get("categoria") == cat and j.get("passo") in ("aprovado", "desfeito", "voltou"):
                ult.append(j["passo"])
    except (OSError, ValueError):
        return False
    ult = ult[-10:]
    return len(ult) >= 10 and ult.count("aprovado") >= DISPENSA and "voltou" not in ult


# ───────────────────────── casos (camadas 1-3) ─────────────────────────
def abrir_casos(d, achados, agora):
    for a in achados:
        ch = a["chave"]
        ult = d["alarmes"].get(ch)
        if ult and (agora - datetime.fromisoformat(ult["em"])).total_seconds() < REPETIDO_H * 3600:
            continue
        # reapareceu < 24 h depois de um conserto aprovado = voltou (conta contra quem consertou)
        for c in d["casos"].values():
            if c.get("chave") == ch and c.get("etapa") == "aprovado" and c.get("fim") and \
                    (agora - datetime.fromisoformat(c["fim"])).total_seconds() < VOLTOU_H * 3600:
                _pontuar(d, c["consertador"], c["categoria"], "voltou")
                c["etapa"] = "voltou"
                _registro(c, "voltou")
                _avisar(f"⚠️ voltou em menos de 24 h: {c['titulo']} (consertado por {c['consertador']})")
        d["alarmes"][ch] = {"em": agora.isoformat(timespec="seconds"), "titulo": a["titulo"]}
        cid = f"{agora:%Y%m%d_%H%M%S}_{len(d['casos'])}"
        caso = {**a, "id": cid, "etapa": "vigia", "aberto": agora.isoformat(timespec="seconds")}
        d["casos"][cid] = caso
        _registro(caso, "aberto", titulo=a["titulo"], evidencia=a["evidencia"][:300])


def _job(jid):
    import painel_ia
    return painel_ia.ler(jid) or {}


def andar(d, caso):
    """Avança UM passo do caso (os pedidos do painel são assíncronos: cada volta olha o que terminou)."""
    import painel_ia
    et = caso["etapa"]
    if et == "vigia":
        j = painel_ia.pedir("pergunta", (
            f"ALARME DA VIGILÂNCIA (medidor sem IA): {caso['titulo']}\nEVIDÊNCIA: {caso['evidencia']}\n\n"
            "Confirme lendo os logs/arquivos de verdade se o problema é REAL e ainda acontece. Ache a CAUSA (arquivo e "
            "linha). Termine com uma linha 'VEREDITO: REAL' ou 'VEREDITO: FALSO' e, se real, 'CAUSA: <arquivo:linha — "
            "explicação curta>'.\nLIMITE: no máximo 10 leituras de arquivo/log/comando; depois disso PARE e responda com "
            "o que já achou (na dúvida, VEREDITO: REAL com a melhor CAUSA provável). Sem resposta final = trabalho perdido."),
            projeto=caso["projeto"], origem="vigilancia", modelo=VIGIA, voltas=45)
        caso.update(etapa="vigia_rodando", job_vigia=j["id"])
        _registro(caso, "vigia", job=j["id"], modelo=VIGIA)
    elif et == "vigia_rodando":
        j = _job(caso["job_vigia"])
        if j.get("status") in ("fila", "rodando"):
            return
        txt = j.get("resposta") or ""
        if j.get("status") != "terminou" or "VEREDITO" not in txt.upper():
            caso["etapa"] = "vigia"  # vigia não concluiu: tenta de novo na próxima volta
            caso["tentativas_vigia"] = caso.get("tentativas_vigia", 0) + 1
            if caso["tentativas_vigia"] >= 3:
                caso["etapa"] = "consertar"  # 3 vezes sem veredito: segue pro consertador com a evidência crua
            return
        if re.search(r"VEREDITO:\W*FALSO", txt, re.I):
            caso.update(etapa="falso", fim=_agora())
            _registro(caso, "falso", resumo=txt[-300:])
            return
        caso["diagnostico"] = (re.findall(r"CAUSA:.*", txt) or [txt[-1500:]])[-1][:1500]
        caso["etapa"] = "consertar"
        _registro(caso, "real", diagnostico=caso["diagnostico"][:300])
    elif et == "consertar":
        if d["dia"].get("consertos", 0) >= CASOS_DIA_MAX:
            return
        m = escolher_consertador(d, caso["categoria"])
        if not m:
            caso["esperando_token"] = _agora()  # nenhum com token: a próxima volta testa de novo (sentinela)
            return
        j = painel_ia.pedir("consertar", (
            f"CONSERTO PEDIDO PELA VIGILÂNCIA.\nPROBLEMA: {caso['titulo']}\nEVIDÊNCIA: {caso['evidencia']}\n"
            f"DIAGNÓSTICO DO VIGIA: {caso.get('diagnostico') or '(sem diagnóstico)'}\n\n{REGRAS_CONSERTO}"),
            projeto=caso["projeto"], origem="vigilancia", auto_aplicar=True, modelo=m,
            rota="vscode" if m in ROTA_VSCODE else None)
        caso.update(etapa="consertando", job_propor=j["id"], consertador=m, tentativa_em=_agora())
        d["dia"]["consertos"] = d["dia"].get("consertos", 0) + 1
        if m.startswith("kr/"):
            d["dia"]["kiro"] = d["dia"].get("kiro", 0) + 1
        _registro(caso, "consertando", modelo=m, job=j["id"])
    elif et == "consertando":
        p = _job(caso["job_propor"])
        if p.get("status") in ("fila", "rodando"):
            return
        usado = p.get("modelo") or caso["consertador"]
        if usado != caso["consertador"]:  # o painel caiu pra reserva: não conta pro candidato, tenta de novo
            # sem token de verdade (o teste passou e o pedido não): fora ATÉ A HORA DE VOLTA (monitor/regra do provedor)
            d.setdefault("fora", {})[caso["consertador"]] = _volta_em(caso["consertador"])
            d.setdefault("teste", {}).pop(caso["consertador"], None)
            caso["etapa"] = "consertar"
            _registro(caso, "sem_token", pedido=caso["consertador"], usado=usado)
            return
        aid = p.get("aplicado_em")
        if not aid:
            if p.get("status_ia") in ("OK",):  # o consertador achou que não há o que mudar
                caso.update(etapa="sem_mudanca", fim=_agora())
                _registro(caso, "sem_mudanca", modelo=usado, resumo=(p.get("resposta") or "")[-300:])
                return
            _pontuar(d, usado, caso["categoria"], "tentativas")
            _pontuar(d, usado, caso["categoria"], "falhou")
            caso.update(etapa="consertar", falhas=caso.get("falhas", 0) + 1)
            _registro(caso, "falhou", modelo=usado, status=p.get("status"), detalhe=str(p.get("detalhe"))[:200])
            if caso["falhas"] >= 3:
                caso.update(etapa="dona", fim=_agora())
                _avisar(f"❌ 3 consertos falharam: {caso['titulo']} — precisa de você/sessão forte")
            return
        a = _job(aid)
        if a.get("status") in ("fila", "rodando"):
            return
        _pontuar(d, usado, caso["categoria"], "tentativas")
        if a.get("status") != "terminou" or not a.get("manifesto"):
            _pontuar(d, usado, caso["categoria"], "falhou")
            caso.update(etapa="consertar", falhas=caso.get("falhas", 0) + 1)
            _registro(caso, "aplicar_falhou", modelo=usado, status=a.get("status"))
            return
        caso.update(job_aplicar=aid, etapa="revisar")
        _registro(caso, "aplicado", modelo=usado, job=aid, arquivos=list((a.get("manifesto") or {}).keys()))
    elif et == "revisar":
        if revisao_dispensada(caso["categoria"]):
            _pontuar(d, caso["consertador"], caso["categoria"], "aprovados")
            caso.update(etapa="aprovado", fim=_agora(), revisor="dispensado")
            _registro(caso, "aprovado", revisor="dispensado (categoria confiável)")
            _avisar(f"✅ consertado por {caso['consertador']} (revisão dispensada nesta categoria): {caso['titulo']}",
                    importante=False)
            return
        rev = next((m for m in REVISORES if _disponivel(m, d)), None)
        if not rev:
            return  # espera o Opus voltar (o conserto fica no ar; a volta seguinte tenta)
        diffs = "\n".join(f"### {x['arquivo']}\n{x['diff'][:6000]}" for x in painel_ia.mudancas(caso["job_aplicar"]))
        j = painel_ia.pedir("pergunta", (
            f"REVISÃO FINAL de um conserto automático.\nPROBLEMA: {caso['titulo']}\nEVIDÊNCIA: {caso['evidencia']}\n"
            f"CONSERTADOR: {caso['consertador']}\nDIFF:\n{diffs[:9000]}\n\n{REGRAS_CONSERTO}\n\nConfira no código e nos "
            "logs se o conserto resolve a CAUSA sem quebrar outra coisa. Responda SÓ estas 3 linhas no fim:\n"
            "APROVADO: sim|não\nMOTIVO: <curto>\nOPUS_NECESSARIO: sim|não (esta categoria ainda precisa de revisão forte?)"),
            projeto=caso["projeto"], origem="vigilancia", modelo=rev, voltas=25)
        caso.update(etapa="revisando", job_revisor=j["id"], revisor=rev)
        _registro(caso, "revisando", revisor=rev, job=j["id"])
    elif et == "revisando":
        j = _job(caso["job_revisor"])
        if j.get("status") in ("fila", "rodando"):
            return
        txt = j.get("resposta") or ""
        ap = re.findall(r"APROVADO:\W*(sim|não|nao)", txt, re.I)
        if j.get("status") != "terminou" or not ap:
            caso["etapa"] = "revisar"
            return
        motivo = (re.findall(r"MOTIVO:\s*(.*)", txt) or [""])[-1][:300]
        caso["opus_necessario"] = (re.findall(r"OPUS_NECESSARIO:\W*(sim|não|nao)", txt, re.I) or ["?"])[-1].lower()
        if ap[-1].lower() == "sim":
            _pontuar(d, caso["consertador"], caso["categoria"], "aprovados")
            caso.update(etapa="aprovado", fim=_agora(), motivo_revisor=motivo)
            _registro(caso, "aprovado", revisor=j.get("modelo"), motivo=motivo, opus_necessario=caso["opus_necessario"])
            _avisar(f"✅ consertado por {caso['consertador']}, aprovado por {j.get('modelo')}: {caso['titulo']}\n{motivo}",
                    importante=False)
        else:
            _pontuar(d, caso["consertador"], caso["categoria"], "reprovados")
            try:
                painel_ia.desfazer(caso["job_aplicar"], forcar=True, quem=f"revisor {j.get('modelo')}")
                desfeito = "desfeito"
            except Exception as e:  # noqa: BLE001
                desfeito = f"NÃO desfez ({e})"
            caso.update(etapa="consertar", motivo_revisor=motivo, falhas=caso.get("falhas", 0) + 1)
            _registro(caso, "desfeito", revisor=j.get("modelo"), motivo=motivo, resultado=desfeito)
            _avisar(f"↩️ conserto de {caso['consertador']} REPROVADO por {j.get('modelo')} e {desfeito}: "
                    f"{caso['titulo']}\nMotivo: {motivo}")


FECHADAS = ("falso", "aprovado", "voltou", "sem_mudanca", "dona")


def placar_txt(d):
    out = []
    for m in CONSERTADORES:
        t, n = _nota(d["placar"], m)
        cats = ", ".join(f"{c}: {v['aprovados']}/{v['tentativas']} (voltou {v['voltou']})"
                         for c, v in (d["placar"].get(m) or {}).items())
        out.append(f"- **{m}**: {t} casos, nota {n:.0%}" + (f" — {cats}" if cats else ""))
    return "\n".join(out)


def escrever_doc(d, achados):
    abertos = [c for c in d["casos"].values() if c["etapa"] not in FECHADAS]
    fechados = sorted((c for c in d["casos"].values() if c["etapa"] in FECHADAS), key=lambda c: c.get("fim", ""))[-15:]
    DOC.write_text(
        f"# Vigilância 24 h — {_agora()}\n\n(gerado por vigilancia.py; detalhe em estado\\vigilancia_casos.jsonl)\n\n"
        f"## Alarmes desta volta ({len(achados)})\n" + "\n".join(f"- {a['titulo']}" for a in achados) +
        f"\n\n## Casos abertos ({len(abertos)})\n" + "\n".join(f"- [{c['etapa']}] {c['titulo']} "
                                                              f"({c.get('consertador') or '-'})" for c in abertos) +
        "\n\n## Últimos fechados\n" + "\n".join(f"- [{c['etapa']}] {c['titulo']} — {c.get('consertador') or '-'}"
                                                 f" / {c.get('revisor') or '-'}" for c in fechados) +
        f"\n\n## Placar dos consertadores\n{placar_txt(d)}\n", encoding="utf-8")


def main(simular=False):
    agora = datetime.now()
    achados = medir(agora)
    if simular:
        for a in achados:
            print(f"[{a['categoria']}] {a['titulo']}\n    {a['evidencia'][:200]}")
        print(f"{len(achados)} alarme(s)")
        return
    d = _ler()
    if d["dia"].get("data") != agora.date().isoformat():
        d["dia"] = {"data": agora.date().isoformat()}
    abrir_casos(d, achados, agora)
    for caso in sorted(d["casos"].values(), key=lambda c: c["aberto"]):
        if caso["etapa"] in FECHADAS:
            continue
        try:
            andar(d, caso)
        except Exception as e:  # noqa: BLE001
            _registro(caso, "erro_interno", erro=f"{type(e).__name__}: {str(e)[:200]}")
        _gravar(d)
    # guarda só os 300 casos mais novos
    if len(d["casos"]) > 300:
        for k in sorted(d["casos"])[:-300]:
            d["casos"].pop(k)
    _gravar(d)
    escrever_doc(d, achados)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "placar":
        print(placar_txt(_ler()))
    else:
        main(simular="--simular" in sys.argv)
