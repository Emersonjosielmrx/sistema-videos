"""melhorador_longo.py — o MELHORADOR do recap LONGO (dona 26–27/10: "uma cópia do sistema de melhoria só pro vídeo
longo, que faz exatamente o que você faz aqui: vê o vídeo feito e faz a próxima versão melhor e mais viral; fica
pronto e só liga no meu sinal").

Diferente do melhoria_continua.py (motor genérico que sorteia projeto e mexe em código), este é guiado pelo VÍDEO:
  1. ANALISA cada longo novo (sempre seguro): júri Gemini por amostra + movimento (juri_longo.py), áudio (LUFS e
     silêncios), duração x frases, render.json (vozes, Kokoro, marca d'água) -> relatório em
     D:\\video-fila\\linhas\\LONGOS\\videos\\<id>.md e 1 linha no evolucao.jsonl.
  2. VIGIA as mudanças anteriores: nota média dos vídeos feitos depois de uma mudança caiu mais que `piora_desfaz`
     -> desfaz sozinho (volta o backup) e anota em DECISOES.md.
  3. A cada `lote` vídeos novos, o DECISOR (camadas de modelo do json) lê o prompt treinado
     (linhas\\LONGOS\\PROMPT_MELHORADOR.md) + LICOES + relatórios e devolve: ALAVANCAS (só as permitidas, com tipo e
     faixa conferidos aqui), PROPOSTAS de código (PROPOSTAS.md + fila) e recados pro MURAL. Lê PEDIDOS_DONA.md.
  4. CONSERTA código (27/10): 1 proposta por volta, com o modelo de código de `codigo.modelo`, numa caixa isolada;
     diff pequeno e válido vai pro real com backup, sobe pras GPUs e é vigiado como as alavancas.
  5. GPUs (27/10): central parada = mata rclone preso na VPS; 0 GPU há 6 h = avisa a dona 1x por dia.

Camadas (dona 27/10, 15:40): nada de Opus nem Kiro (`modelos_desligados`). Analista (júri com quadros) = Gemini 3.8;
decisor = Argon puro com prazo curto e, se demorar, Gemini 3.8. Conversa com a dona: conversar_melhorador.py.

LIGA/DESLIGA: controle.json projeto "melhorador_longo" etapa "producao" (painel :8790). Desligado = não faz nada.
    python melhorador_longo.py            # 1 volta (tarefa RecapMelhoradorLongo)
    python melhorador_longo.py --forcar   # roda mesmo desligado (teste)
    python melhorador_longo.py --so-analisar
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import juri_longo  # noqa: E402  (já põe o sem_janela no Windows)

CFG = AQUI / "melhorador_longo.json"
LINHA = Path(r"D:\video-fila\linhas\LONGOS")
ESTADO = LINHA / "melhorador_estado.json"
RELATORIOS = LINHA / "videos"
PROMPT = LINHA / "PROMPT_MELHORADOR.md"
LICOES = LINHA / "LICOES.md"
PROPOSTAS = LINHA / "PROPOSTAS.md"
PEDIDOS = LINHA / "PEDIDOS_DONA.md"  # 27/10: pedidos extras da dona entram em toda decisão (o que o chat fazia)
DECISOES = LINHA / "DECISOES.md"
MURAL = Path(r"D:\video-fila\linhas\MURAL.md")
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
TMP = Path(r"D:\hipercool-materiais\_melhorador_longo")
RCLONE = r"D:\tools\rclone.exe"
ARQS = {"longo.json": AQUI.parent / "config" / "longo.json", "teste_narradores.json": AQUI / "teste_narradores.json"}
LOG = AQUI / "melhorador_longo.log"


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M}] {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def ligado():
    try:
        sys.path.insert(0, r"D:\video-fila")
        import controle
        return controle.ligado("melhorador_longo", "producao")[0]
    except Exception:  # noqa: BLE001 — sem controle = desligado (seguro)
        return False


# ── camadas de modelo ──────────────────────────────────────────────────────────────────────────────────────────────
def _vivo(modelo):
    try:
        return "ok" in juri_longo.chamar("Responda só: ok", LINHA, "ping", timeout=120, max_turnos=3, modelo=modelo).lower()
    except Exception:  # noqa: BLE001
        return False


def modelos(camada, c):
    """[(modelo, turnos, segundos)] da camada, sem os desligados (dona 27/10: nada de Opus/Kiro por agora).
    29/10 (Fable, D14): pelo melhorador CENTRAL a camada vem dele (env CENTRAL_MODELOS, botão do painel); nunca Kiro."""
    try:
        cm = json.loads(os.environ.get("CENTRAL_MODELOS") or "{}").get(camada) or []
    except ValueError:
        cm = []
    if cm:
        # 30/10: o central já filtrou o Kiro (só passa com modelos_central.json kiro_liberado; dona 30/10 liberou)
        return [(m, 30, 900) for m in cm if os.environ.get("CENTRAL_KIRO_OK") == "1" or not str(m).startswith(("kr/", "kiro"))]
    fora = [p.lower() for p in c.get("modelos_desligados", []) + c.get("proibidos", [])]
    saida = []
    for item in c["camadas"].get(camada, []):
        m, turnos = item[0], item[1]
        if any(p in m.lower() for p in fora):
            continue
        saida.append((m, turnos, item[2] if len(item) > 2 else 900))
    return saida


def decisor(c):
    for m, turnos, prazo in modelos("decisor", c):
        if _vivo(m):
            return m, turnos, prazo
        log(f"decisor {m} não respondeu — próximo da camada")
    return None, None, None


# ── análise de 1 vídeo ─────────────────────────────────────────────────────────────────────────────────────────────
def _audio(mp4):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", "120", "-t", "300", "-i", str(mp4), "-vn", "-af",
                        "ebur128=framelog=quiet,silencedetect=noise=-45dB:d=0.4", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    lufs = None
    for l in r.stderr.splitlines()[::-1]:
        if l.strip().startswith("I:") and "LUFS" in l:
            lufs = float(l.split()[1])
            break
    return {"lufs_5min": lufs, "silencios_5min": r.stderr.count("silence_start")}


def _mp4_da_ficha(ficha):
    """Cópia local do vídeo: a da pasta de acompanhamento (alimentador) ou baixa do Drive pra TMP."""
    for p in Path(r"D:\hipercool-materiais\recap-longos-prontos").glob(f"*{ficha.name[:11]}*.mp4"):
        if "SEM_NOMES" not in p.name:
            return p, False
    d = _ler(ficha / "nuvem.json", {})
    if not d.get("drive"):
        return None, False
    TMP.mkdir(parents=True, exist_ok=True)
    # 06/11: o longo tem até 7,5 GB e o .partial de download interrompido ficava (7,1 GB parado desde 14:46) — o D
    # caiu a 4,8 GB e o abastecedor do Kaggle parou ("< 6 GB"). Limpa partial velho e só baixa com folga de 6 GB.
    import shutil as _sh
    import time as _t
    for velho in TMP.glob("*.partial"):
        if _t.time() - velho.stat().st_mtime > 1800:
            velho.unlink(missing_ok=True)
    try:
        tam = json.loads(subprocess.run([RCLONE, "lsjson", d["drive"]], capture_output=True, text=True,
                                        timeout=120).stdout or "[{}]")[0].get("Size") or 0
    except Exception:  # noqa: BLE001
        tam = 8 * 2**30
    tam = max(tam, 8 * 2**30)  # 06/11 22:08: baixou 8 GB e o D foi a 2,6 GB — o longo tem até 8 GB; nunca contar menos
    # o analista só precisa de uma AMOSTRA do longo: sem 14 GB livres (8 do vídeo + 6 de folga) não baixa
    if _sh.disk_usage(TMP).free - tam < 6 * 2**30:
        log(f"{ficha.name}: sem espaço no D pra baixar o longo ({tam / 2**30:.1f} GB; deixo 6 GB livres) — pula")
        return None, False
    alvo = TMP / f"{ficha.name[:40]}.mp4"
    r = subprocess.run([RCLONE, "copyto", d["drive"], str(alvo)], capture_output=True, text=True)
    return (alvo, True) if r.returncode == 0 and alvo.exists() else (None, False)


def analisar(ficha, c):
    mp4, temporario = _mp4_da_ficha(ficha)
    if not mp4:
        log(f"{ficha.name}: sem vídeo (nem local nem no Drive) — pula")
        return None
    res = None
    try:
        res = juri_longo.julgar(mp4, ficha, modelos=[(m, t) for m, t, _ in modelos("analista", c)])
        res["audio"] = _audio(mp4)
        render = _ler(ficha / "render.json", {})
        rot = ficha / "roteiro.txt"
        frases = sum(1 for l in rot.read_text(encoding="utf-8").splitlines() if l.strip()) if rot.exists() else 0
        res["s_por_frase"] = round(res["duracao_s"] / frases, 2) if frases else None
        res["render"] = {k: render.get(k) for k in ("voz_clonada", "voz_base", "vozes_lista", "kokoro_nuvem", "applio_ok",
                                                    "marca_site", "fim")}
        res["ficha"] = ficha.name
        _gravar(ficha / "juri.json", res)
        RELATORIOS.mkdir(parents=True, exist_ok=True)
        linhas = [f"# {ficha.name} — nota {res.get('nota')} ({datetime.now():%d/%m %H:%M})",
                  f"- duração {res['duracao_s'] / 60:.1f} min, {res['s_por_frase']} s/frase, áudio {res['audio']}",
                  f"- movimento por trecho: {res['movimento']} (parados: {res['parados']})",
                  f"- render: {res['render']}"]
        for v in res.get("juri", []):
            linhas.append(f"\n## {v['foco']} — {v['nota']} ({v.get('modelo')})")
            linhas += [f"- [{p.get('gravidade')}] {p.get('problema')} → {p.get('como_corrigir')}" for p in v["problemas"][:6]]
        (RELATORIOS / f"{ficha.name[:50]}.md").write_text("\n".join(linhas), encoding="utf-8")
        log(f"{ficha.name}: nota {res.get('nota')} | parados {res['parados']} | {res['audio']}")
        return res
    finally:
        if temporario:
            Path(mp4).unlink(missing_ok=True)
        if res and res.get("pasta"):
            shutil.rmtree(res["pasta"], ignore_errors=True)


# ── alavancas, vigia e desfazer ────────────────────────────────────────────────────────────────────────────────────
def _valor_ok(spec, v):
    t = spec["tipo"]
    if t == "bool":
        return isinstance(v, bool)
    if t == "int":
        return isinstance(v, int) and not isinstance(v, bool) and spec["min"] <= v <= spec["max"]
    if t == "str":
        return str(v) in spec.get("valores", [])
    return False


def aplicar_alavanca(chave, valor, porque, est, c, modelo):
    spec = c["alavancas"].get(chave)
    if not spec or not _valor_ok(spec, valor):
        log(f"alavanca recusada (fora da lista/faixa): {chave}={valor!r}")
        return False
    arq_nome, caminho = chave.split(":", 1)
    arq = ARQS[arq_nome]
    dados = _ler(arq, None)
    if dados is None:
        return False
    alvo, partes = dados, caminho.split(".")
    for p in partes[:-1]:
        alvo = alvo.setdefault(p, {})
    antes = alvo.get(partes[-1])
    if antes == valor:
        return False
    bkp = arq.with_name(f"{arq.name}.bak_{datetime.now():%Y%m%d_%H%M%S}_melhorador")
    shutil.copy2(arq, bkp)
    alvo[partes[-1]] = valor
    _gravar(arq, dados)
    notas = [v["nota"] for v in est["videos"].values() if v.get("nota") is not None][-3:]
    est["mudancas"].append({"em": datetime.now().isoformat(timespec="seconds"), "chave": chave, "antes": antes,
                            "depois": valor, "porque": porque, "backup": str(bkp), "modelo": modelo,
                            "nota_antes": round(sum(notas) / len(notas), 2) if notas else None, "estado": "vigiando"})
    _decisao(f"[melhorador {modelo}] {chave}: {antes!r} -> {valor!r} — {porque}. Desfazer: copiar {bkp.name}")
    log(f"alavanca aplicada: {chave} {antes!r} -> {valor!r}")
    return True


def subir_pacote():
    """27/10: as GPUs do Kaggle usam o código/config do pacote no Drive — mudança feita aqui só vale depois disto
    (antes a alavanca mudava o config\\longo.json do PC e o Kaggle nunca via)."""
    r = subprocess.run([sys.executable, "-X", "utf8", str(AQUI / "montar_pacote.py"), "--codigo"], capture_output=True,
                       text=True, timeout=1800, cwd=str(AQUI))
    ok = "pacote ok" in (r.stdout + r.stderr)
    log("pacote subiu pras GPUs" if ok else f"pacote NÃO subiu: {(r.stdout + r.stderr)[-300:]}")
    return ok


def vigiar(est, c):
    mexeu = False
    for m in est["mudancas"]:
        if m["estado"] != "vigiando" or m.get("nota_antes") is None:
            continue
        depois = [v["nota"] for v in est["videos"].values()
                  if v.get("nota") is not None and (v.get("render_fim") or "") > m["em"]]
        if len(depois) < c.get("videos_para_julgar_mudanca", 2):
            continue
        media = sum(depois) / len(depois)
        if media < m["nota_antes"] - c.get("piora_desfaz", 1.0):
            arq = Path(m["arquivo"]) if m.get("arquivo") else ARQS[m["chave"].split(":", 1)[0]]
            shutil.copy2(m["backup"], arq)
            mexeu = True
            m["estado"] = f"desfeita (nota {m['nota_antes']} -> {media:.2f})"
            _decisao(f"[melhorador] DESFEITA {m['chave']} ({m['antes']!r}<-{m['depois']!r}): nota caiu "
                     f"{m['nota_antes']} -> {media:.2f}")
        else:
            m["estado"] = f"mantida (nota {m['nota_antes']} -> {media:.2f})"
        log(f"mudança {m['chave']}: {m['estado']}")
    if mexeu:
        subir_pacote()


def _decisao(texto):
    try:
        s = DECISOES.read_text(encoding="utf-8")
        cab = "# LONGOS — decisões (mais nova em cima)\n"
        corpo = s[len(cab):] if s.startswith(cab) else s
        DECISOES.write_text(cab + f"\n- {datetime.now():%d/%m %H:%M} {texto}\n" + corpo, encoding="utf-8")
    except OSError:
        pass


def _mural(recado):
    s = MURAL.read_text(encoding="utf-8").splitlines(keepends=True)
    s.insert(2, f"{datetime.now():%d/%m %H:%M} | de LONGOS (melhorador) | para TODAS | {recado}\n")
    MURAL.write_text("".join(s), encoding="utf-8")


# ── desempenho real no YouTube (28/10: "máximo de views" — o júri sozinho não sabe o que dá view) ─────────────────
POSTADOS = AQUI / "longos_postados.json"
EXPERIMENTO = LINHA / "experimento.json"


def desempenho(est):
    """Views e tempo médio assistido de cada longo postado (API do painel :8790, que lê o YouTube ao vivo e a retenção
    do Studio). Grava em est["videos"][ficha]["yt"] e devolve {ficha: yt}. Painel fora = segue sem."""
    import urllib.request
    post = _ler(POSTADOS, {}).get("postados", [])
    if not post:
        return {}
    try:
        with urllib.request.urlopen("http://127.0.0.1:8790/api/ranking?dias=60", timeout=120) as r:
            rank = {v["id"]: v for v in json.loads(r.read().decode("utf-8")).get("videos", [])}
    except Exception as e:  # noqa: BLE001
        log(f"desempenho: painel :8790 não respondeu ({type(e).__name__})")
        return {}
    saida = {}
    for p in post:
        yid = str(p.get("url", "")).rstrip("/").split("/")[-1].split("?")[0]
        v = rank.get(yid)
        if not v or v.get("views") is None:
            continue
        try:
            horas = max(1.0, (datetime.now() - datetime.fromisoformat(p["em"])).total_seconds() / 3600)
        except (KeyError, ValueError):
            horas = None
        # 29/10 noite (Fable): duração do registro da postagem quando o vídeo não passou pela análise
        dur = (est["videos"].get(p["nome"], {}) or {}).get("duracao_s") or p.get("duracao_s")
        yt = {"yt": yid, "canal": p.get("canal_nome"), "views": v["views"], "likes": v.get("likes"),
              "coment": v.get("comentarios"), "dur_media_s": v.get("dur_media"),
              "assistido_pct": round(100 * float(v["dur_media"]) / dur, 1) if v.get("dur_media") and dur else None,
              "horas_no_ar": round(horas, 1) if horas else None,
              "views_h": round(v["views"] / horas, 3) if horas else None, "lido": datetime.now().isoformat("T", "minutes")}
        est["videos"].setdefault(p["nome"], {"ficha": p["nome"]})["yt"] = yt
        saida[p["nome"]] = yt
    if saida:
        log("desempenho: " + " | ".join(f"{k[:11]} {y['views']} views {y.get('assistido_pct')}%" for k, y in saida.items()))
        try:
            _resumo_variantes(post, saida)
        except Exception as e:  # noqa: BLE001
            log(f"resumo das variantes falhou ({type(e).__name__}: {e})")
        try:
            _obras_continuar(post, saida)
        except Exception as e:  # noqa: BLE001
            log(f"obras a continuar falhou ({type(e).__name__}: {e})")
    return saida


OBRAS_MD = LINHA / "OBRAS_CONTINUAR.md"
CONT_MIN_VIEWS, CONT_MIN_PCT, CONT_MIN_H = 20, 30.0, 48


def _obras_continuar(post, saida):
    """30/10 (dona: "muito importante medir quanto as pessoas assistem pra saber se aquela obra deve ter um capítulo
    novo ou não"): por longo postado -> título original (a obra), canal, views, % assistido, horas no ar e o veredito.
    CONTINUAR = 48 h+ no ar, views >= 20 (passou do 1º lote do feed — régua D1) e % assistido >= 30. Abaixo disso,
    "pouco dado". linhas\\LONGOS\\OBRAS_CONTINUAR.md (o central e a conversa leem; o alimentador pode priorizar)."""
    linhas = [f"# Obras: continuar ou não — {datetime.now():%d/%m %H:%M}", "",
              f"CONTINUAR = {CONT_MIN_H} h+ no ar, {CONT_MIN_VIEWS}+ views e {CONT_MIN_PCT:.0f}%+ assistido. "
              "Menos que isso = pouco dado (não decide).", "",
              "| obra (título original) | canal | views | % assistido | horas | veredito |", "|---|---|---|---|---|---|"]
    for p in sorted(post, key=lambda x: x.get("em", ""), reverse=True):
        y = saida.get(p.get("nome"))
        if not y:
            continue
        h, v, pct = y.get("horas_no_ar") or 0, y.get("views") or 0, y.get("assistido_pct")
        if h < CONT_MIN_H or v < CONT_MIN_VIEWS or pct is None:
            ver = "pouco dado"
        elif pct >= CONT_MIN_PCT:
            ver = "**CONTINUAR**"
        else:
            ver = "parar (assistem pouco)"
        titulo = (p.get("titulo_original") or p.get("nome", "")[12:].replace("_", " "))[:70]
        linhas.append(f"| {titulo} | {p.get('canal_nome')} | {v} | {pct if pct is not None else '—'} | {h:.0f} | {ver} |")
    OBRAS_MD.write_text("\n".join(linhas) + "\n", encoding="utf-8")


AB_MD = LINHA / "AB_RESULTADOS.md"


def _resumo_variantes(post, saida):
    """30/10 (dona: variantes A/B/C... de tudo que é gosto; decidir pelas views): agrupa os longos postados por fator ×
    variante ("ab" e "narradores_modo" do longos_postados.json) -> n, views/h mediana, % assistido mediano.
    Grava linhas\\LONGOS\\AB_RESULTADOS.md (o central e a conversa leem). Só aponta vencedor com n >= 4 por variante e
    vídeos com >= 48 h no ar (antes disso as views ainda estão subindo)."""
    from statistics import median
    grupos = {}
    for p in post:
        y = saida.get(p.get("nome"))
        if not y or (y.get("horas_no_ar") or 0) < 48:
            continue
        pares = list((p.get("ab") or {}).items()) + ([("narradores_modo", p["narradores_modo"])]
                                                     if p.get("narradores_modo") else [])
        for fator, var in pares:
            grupos.setdefault(fator, {}).setdefault(var, []).append(y)
    linhas = [f"# Resultados das variantes dos LONGOS — {datetime.now():%d/%m %H:%M}", "",
              "Só longos com 48 h+ no ar. Vencedor só com 4+ vídeos em CADA variante do fator (antes disso é ruído).", "",
              "| fator | variante | n | views/h (mediana) | % assistido (mediana) |", "|---|---|---|---|---|"]
    for fator in sorted(grupos):
        for var in sorted(grupos[fator]):
            ys = grupos[fator][var]
            vh = [y["views_h"] for y in ys if y.get("views_h") is not None]
            pa = [y["assistido_pct"] for y in ys if y.get("assistido_pct") is not None]
            vh_txt = f"{median(vh):.2f}" if vh else "—"
            pa_txt = f"{median(pa):.1f}" if pa else "—"
            linhas.append(f"| {fator} | {var} | {len(ys)} | {vh_txt} | {pa_txt} |")
        ok = all(len(v) >= 4 for v in grupos[fator].values()) and len(grupos[fator]) >= 2
        if ok:
            melhor = max(grupos[fator], key=lambda k: median([y["views_h"] for y in grupos[fator][k]
                                                                  if y.get("views_h") is not None] or [0]))
            linhas.append(f"| **{fator}** | **vence {melhor}** (views/h) | | | |")
    if not grupos:
        linhas.append("| (nenhum longo com variantes e 48 h+ no ar ainda) | | | | |")
    AB_MD.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    log(f"variantes: {sum(len(v) for v in grupos.values())} grupos em {len(grupos)} fatores -> {AB_MD.name}")


# ── teste A/B (28/10: o GOSTO é decidido pelas views, não por opinião) ──────────────────────────────────────────────
def _exp_valido(e, c):
    """A e B só com chaves de alavanca (sem o prefixo do arquivo) e valores na faixa; 1 diferença ao menos."""
    if not isinstance(e, dict) or not e.get("nome"):
        return False
    for lado in ("A", "B"):
        for k, v in (e.get(lado) or {}).items():
            spec = c["alavancas"].get(f"longo.json:{k}")
            if not spec or not _valor_ok(spec, v):
                log(f"experimento recusado: {lado}.{k}={v!r} fora das alavancas")
                return False
    return (e.get("A") or {}) != (e.get("B") or {})


def abrir_experimento(e, est, c, modelo):
    atual = _ler(EXPERIMENTO, {})
    if atual.get("ativo"):
        return False
    if not _exp_valido(e, c):
        return False
    novo = {"nome": str(e["nome"])[:40], "hipotese": str(e.get("hipotese", ""))[:400], "A": e.get("A") or {},
            "B": e.get("B") or {}, "ativo": True, "enviados": {"A": 0, "B": 0}, "modelo": modelo,
            "aberto": datetime.now().isoformat(timespec="seconds")}
    _gravar(EXPERIMENTO, novo)
    est.setdefault("experimentos", []).append({k: novo[k] for k in ("nome", "hipotese", "A", "B", "aberto")})
    _decisao(f"[melhorador {modelo}] EXPERIMENTO aberto '{novo['nome']}': A={novo['A']} x B={novo['B']} — {novo['hipotese']}")
    log(f"experimento aberto: {novo['nome']} B={novo['B']}")
    return True


def julgar_experimento(est, c):
    """Lado com 'videos_por_lado' vídeos analisados (render.json traz experimento/variante) -> decide e fecha."""
    e = _ler(EXPERIMENTO, {})
    if not e.get("ativo"):
        return
    ce = c.get("experimento") or {}
    lados = {"A": [], "B": []}
    for nome, v in est["videos"].items():
        r = _ler(FICHAS / nome / "render.json", {})
        if r.get("experimento") == e["nome"] and r.get("variante") in lados and v.get("nota") is not None:
            lados[r["variante"]].append({"nota": v["nota"], "views_h": (v.get("yt") or {}).get("views_h"),
                                         "seg": r.get("segundos")})
    n = int(ce.get("videos_por_lado", 2))
    if min(len(lados["A"]), len(lados["B"])) < n:
        log(f"experimento {e['nome']}: A {len(lados['A'])} / B {len(lados['B'])} vídeos analisados (precisa {n})")
        return

    def media(lado, k):
        xs = [x[k] for x in lados[lado] if x.get(k) is not None]
        return sum(xs) / len(xs) if len(xs) == len(lados[lado]) else None

    na, nb = media("A", "nota"), media("B", "nota")
    va, vb = media("A", "views_h"), media("B", "views_h")
    sa, sb = media("A", "seg"), media("B", "seg")
    if sa and sb and sb > sa * float(ce.get("render_max", 1.4)):
        vence, porque = "A", f"B deixou o render {sb / sa:.1f}x mais lento"
    elif vb is not None and va is not None and va > 0 and vb >= va * float(ce.get("views_fator", 1.3)) and nb >= na - 0.5:
        vence, porque = "B", f"views/h {va:.2f} -> {vb:.2f}"
    elif nb >= na + float(ce.get("nota_min", 0.3)) and (vb is None or va is None or vb >= va):
        vence, porque = "B", f"júri {na:.2f} -> {nb:.2f}" + (f", views/h {va:.2f} -> {vb:.2f}" if vb is not None else "")
    else:
        vence, porque = "A", f"B não ganhou (júri {na:.2f} x {nb:.2f}; views/h {va} x {vb})"
    e.update(ativo=False, vencedor=vence, porque=porque, fechado=datetime.now().isoformat(timespec="seconds"),
             resultado={"A": lados["A"], "B": lados["B"]})
    _gravar(EXPERIMENTO, e)
    hist = LINHA / "experimentos.jsonl"
    with open(hist, "a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    _decisao(f"[melhorador] EXPERIMENTO '{e['nome']}' fechado: vence {vence} ({porque})")
    log(f"experimento {e['nome']}: vence {vence} ({porque})")
    if vence == "B":
        feitas = sum(aplicar_alavanca(f"longo.json:{k}", v, f"venceu o teste A/B '{e['nome']}': {porque}", est, c,
                                      "experimento") for k, v in e["B"].items())
        if feitas:
            subir_pacote()


# ── decisão por lote ───────────────────────────────────────────────────────────────────────────────────────────────
def decidir(est, c):
    escolhidos = modelos("decisor", c)
    if not escolhidos:
        log("nenhum decisor disponível — só análise nesta volta")
        return
    ultimos = [v for v in est["videos"].values() if v.get("nota") is not None][-c.get("lote", 3):]
    rels = []
    for v in ultimos:
        p = RELATORIOS / f"{v['ficha'][:50]}.md"
        if p.exists():
            rels.append(p.read_text(encoding="utf-8")[:4000])
    atuais = {k: _ler(a, {}) for k, a in ARQS.items()}
    resumo_mud = [{k: x[k] for k in ("em", "chave", "antes", "depois", "estado")} for x in est["mudancas"][-8:]]
    prompt = (PROMPT.read_text(encoding="utf-8")
              + ("\n\n## LIÇÕES\n" + LICOES.read_text(encoding="utf-8")[:4000] if LICOES.exists() else "")
              + "\n\n## ALAVANCAS PERMITIDAS (chave: tipo/faixa)\n" + json.dumps(c["alavancas"], ensure_ascii=False)
              + "\n\n## VALORES ATUAIS\n" + json.dumps({"longo.json": {k: atuais["longo.json"].get(k) for k in
                                                                       ("cta", "mascote", "capitulos", "efeitos",
                                                                        "resumo")},
                                                        "teste_narradores.json": {k: atuais["teste_narradores.json"].get(k)
                                                                                  for k in ("por_video", "continuo")}},
                                                       ensure_ascii=False)[:3000]
              + ("\n\n## PEDIDOS DA DONA (valem acima de tudo; o que não der pra fazer com alavanca vira PROPOSTA)\n"
                 + PEDIDOS.read_text(encoding="utf-8")[:4000] if PEDIDOS.exists() else "")
              + "\n\n## DESEMPENHO NO YOUTUBE (vale mais que o júri)\n" + json.dumps(
                  {k[:40]: {**v["yt"], "nota_juri": v.get("nota"), "render_s": v.get("render_s"),
                            "variante": v.get("variante")} for k, v in est["videos"].items() if v.get("yt")},
                  ensure_ascii=False)[:4000]
              + "\n\n## EXPERIMENTO ATIVO (não abra outro se 'ativo' for true)\n"
              + json.dumps({k: v for k, v in _ler(EXPERIMENTO, {}).items() if k != "resultado"}, ensure_ascii=False)
              + "\n\n## EXPERIMENTOS JÁ FECHADOS\n" + "\n".join(
                  (LINHA / "experimentos.jsonl").read_text(encoding="utf-8").splitlines()[-6:]
                  if (LINHA / "experimentos.jsonl").exists() else [])[:3000]
              + "\n\n## MUDANÇAS RECENTES E O QUE ACONTECEU\n" + json.dumps(resumo_mud, ensure_ascii=False)
              + "\n\n## RELATÓRIOS DOS ÚLTIMOS VÍDEOS\n" + "\n\n".join(rels))
    # 27/10: Argon (prazo curto) e, se demorar/falhar, o próximo da camada (Gemini 3.8 por 2 rotas)
    r = m = None
    for m, turnos, prazo in escolhidos:
        try:
            r = juri_longo.chamar_json(prompt, LINHA, "decidir", timeout=prazo, max_turnos=turnos, modelo=m)
            break
        except Exception as e:  # noqa: BLE001
            log(f"decisor {m} falhou/demorou ({str(e)[:150]}) — próximo da camada")
    if r is None:
        return
    est["decisoes"].append({"em": datetime.now().isoformat(timespec="seconds"), "modelo": m, "resposta": r})
    log(f"decisor {m}: {str(r.get('diagnostico', ''))[:300]}")
    feitas = 0
    for a in r.get("alavancas") or []:
        if feitas >= c.get("max_mudancas_por_lote", 2):
            break
        if aplicar_alavanca(str(a.get("chave")), a.get("valor"), str(a.get("porque", ""))[:300], est, c, m):
            feitas += 1
    if feitas:
        subir_pacote()
    if r.get("experimento"):
        abrir_experimento(r["experimento"], est, c, m)
    novas = r.get("propostas") or []
    if novas:
        with open(PROPOSTAS, "a", encoding="utf-8") as f:
            for p in novas:
                f.write(f"\n## {datetime.now():%d/%m %H:%M} [{p.get('tipo')}] {p.get('titulo')} ({m})\n"
                        f"- prova: {p.get('prova')}\n- onde: {p.get('onde')}\n- como testar: {p.get('como_testar')}\n")
                est.setdefault("propostas", []).append({**{k: p.get(k) for k in ("tipo", "titulo", "prova", "onde",
                                                                                 "como_testar")},
                                                        "em": datetime.now().isoformat(timespec="seconds"),
                                                        "modelo": m, "estado": "nova"})
    for rec in (r.get("mural") or [])[:2]:
        _mural(str(rec)[:300])


# ── conserto de código (dona 27/10: "quando corrigir código ele tem que fazer, com o modelo que eu passar") ──────────
def _arquivo_da_proposta(onde, c):
    """Acha o arquivo real citado em 'onde' (ex.: 'bin/fx_music.py add_background_music') nas pastas permitidas."""
    import re
    raiz = AQUI.parent
    for nome in re.findall(r"[\w\-]+\.(?:py|json)", str(onde or "")):
        for pasta in c["codigo"].get("pastas", ["bin", "colab", "config"]):
            p = raiz / pasta / nome
            if p.exists():
                return p
    return None


def _valido(p):
    if p.suffix == ".json":
        try:
            json.loads(p.read_text(encoding="utf-8"))
            return True
        except ValueError:
            return False
    r = subprocess.run([sys.executable, "-m", "py_compile", str(p)], capture_output=True, text=True)
    return r.returncode == 0


def consertar_codigo(est, c):
    """1 proposta 'nova' por volta: o modelo de código conserta numa CÓPIA (caixa_gemini, isolada do original); se o
    diff for pequeno e o arquivo continuar válido, vai pro real com backup, sobe pras GPUs e fica 'vigiando' (nota cair
    = vigiar() volta o backup). Grande demais/inválido/sem arquivo = fica pra sessão forte (PROPOSTAS.md)."""
    cod = c.get("codigo") or {}
    if not cod.get("ligado") or not cod.get("modelo"):
        return
    if any(f in cod["modelo"].lower() for f in c.get("modelos_desligados", [])):
        log(f"modelo de código {cod['modelo']} está desligado — conserto parado")
        return
    p = next((x for x in est.get("propostas", []) if x.get("estado") == "nova"), None)
    if not p:
        return
    real = _arquivo_da_proposta(p.get("onde"), c)
    if not real:
        p["estado"] = "sem arquivo achado — sessão forte"
        return
    import caixa_gemini
    tarefa = (f"Conserto pedido pelo melhorador do recap longo: {p.get('titulo')}\nProva do problema: {p.get('prova')}\n"
              f"Onde: {p.get('onde')}\nComo testar: {p.get('como_testar')}\n"
              "Regras: mudança mínima, não mude o que funciona, quem chama as funções continua igual, sem palavrão.")
    pasta = caixa_gemini.caixa(f"melhorador_{real.stem}", tarefa, [str(real)],
                               modelos=[(cod["modelo"], cod.get("turnos", 40))], texto=bool(cod.get("texto")))
    nova = pasta / real.name
    linhas = sum(1 for l in (pasta / "gemini.diff").read_text(encoding="utf-8").splitlines()
                 if l[:1] in "+-" and l[:3] not in ("+++", "---"))
    if not linhas:
        p["estado"] = "modelo não mudou nada"
    elif linhas > cod.get("max_linhas", 60):
        p["estado"] = f"diff grande ({linhas} linhas) — sessão forte decide ({pasta})"
    elif not _valido(nova):
        p["estado"] = f"cópia ficou inválida — não aplicado ({pasta})"
    else:
        bkp = real.with_name(f"{real.name}.bak_{datetime.now():%Y%m%d_%H%M%S}_melhorador")
        shutil.copy2(real, bkp)
        shutil.copy2(nova, real)
        if not _valido(real):
            shutil.copy2(bkp, real)
            p["estado"] = "quebrou no real — voltou o backup"
        else:
            notas = [v["nota"] for v in est["videos"].values() if v.get("nota") is not None][-3:]
            est["mudancas"].append({"em": datetime.now().isoformat(timespec="seconds"),
                                    "chave": f"codigo:{real.parent.name}/{real.name}", "arquivo": str(real),
                                    "antes": None, "depois": p.get("titulo"), "porque": p.get("prova"),
                                    "backup": str(bkp), "modelo": cod["modelo"], "caixa": str(pasta),
                                    "nota_antes": round(sum(notas) / len(notas), 2) if notas else None,
                                    "estado": "vigiando"})
            p["estado"] = f"aplicado ({linhas} linhas, {pasta.name})"
            _decisao(f"[melhorador código {cod['modelo']}] {real.name}: {p.get('titulo')} ({linhas} linhas). "
                     f"Desfazer: copiar {bkp.name}")
            subir_pacote()
    log(f"conserto '{p.get('titulo')}': {p['estado']}")


# ── GPUs do Kaggle (dona 27/10: "ele tem que resolver as coisas da GPU também") ─────────────────────────────────────
STATUS_URL = "https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json"


def cuidar_gpus(est, c):
    """Lê a central (status.json). Central parada > 20 min = mata rclone preso na VPS (1 ssh). GPU sem conta há mais
    de 6 h = avisa a dona 1x por dia com a lista do que falta (cota da semana / telefone). A cota volta sozinha: a
    central re-testa cada conta 12 h depois de marcar."""
    import urllib.request
    g = est.setdefault("gpu", {})
    try:
        with urllib.request.urlopen(STATUS_URL, timeout=30) as r:
            s = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        log(f"gpu: status da central não abriu ({type(e).__name__})")
        return
    agora = datetime.now()
    try:
        visto = datetime.strptime(f"{agora.year}/{s['atualizado']}", "%Y/%d/%m %H:%M")
        parada_min = (agora - visto).total_seconds() / 60
    except (KeyError, ValueError):
        parada_min = 0
    if parada_min > 20:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "hermes-prod",
                            "ps -eo pid,etimes,cmd | awk '/rclone/ && !/awk/ && $2>1800 {print $1}' | xargs -r kill; "
                            "echo ok"], capture_output=True, text=True, timeout=120)
        log(f"gpu: central parada há {parada_min:.0f} min — rclone preso morto na VPS ({r.stdout.strip()[-40:]})")
    com_conta = sum(1 for x in s.get("gpus", []) if x.get("conta"))
    g["ultimas"] = {"em": agora.isoformat(timespec="seconds"), "com_conta": com_conta, "total": s.get("gpus_total")}
    if com_conta:
        g.pop("sem_conta_desde", None)
        return
    g.setdefault("sem_conta_desde", agora.isoformat(timespec="seconds"))
    horas = (agora - datetime.fromisoformat(g["sem_conta_desde"])).total_seconds() / 3600
    if horas >= 6 and g.get("avisou_dia") != agora.strftime("%Y-%m-%d"):
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"Recap longo: nenhuma GPU do Kaggle trabalhando há {horas:.0f} h. As contas verificadas "
                          f"estão sem cota de GPU da semana (volta sozinha). Para voltar antes: verificar o telefone de "
                          f"mais contas Kaggle. Vídeos prontos esperando postagem não param.", "recap-longo",
                          importante=True)
            g["avisou_dia"] = agora.strftime("%Y-%m-%d")
        except Exception as e:  # noqa: BLE001
            log(f"gpu: aviso falhou ({e})")
    log(f"gpu: 0 de {s.get('gpus_total')} com conta há {horas:.1f} h")


# ── volta ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def volta(forcar=False, so_analisar=False):
    if not forcar and not ligado():
        return
    c = _ler(CFG, {})
    est = _ler(ESTADO, {"videos": {}, "mudancas": [], "decisoes": []})
    novas = sorted((f for f in FICHAS.glob("*/render.json")
                    if f.parent.name not in est["videos"] and f.stat().st_mtime > datetime(2026, 10, 26, 19).timestamp()),
                   key=lambda f: f.stat().st_mtime)
    for rj in novas[:1]:  # 1 vídeo por volta: a análise leva ~10 min
        res = analisar(rj.parent, c)
        est["videos"].setdefault(rj.parent.name, {}).update(
            {"ficha": rj.parent.name, "nota": (res or {}).get("nota"), "duracao_s": (res or {}).get("duracao_s"),
             "render_fim": _ler(rj, {}).get("fim"), "render_s": _ler(rj, {}).get("segundos"),
             "variante": _ler(rj, {}).get("variante"), "analisado": datetime.now().isoformat()})
        est.setdefault("desde_decisao", 0)
        est["desde_decisao"] += 1
    desempenho(est)
    vigiar(est, c)
    julgar_experimento(est, c)
    cuidar_gpus(est, c)
    if not so_analisar and est.get("desde_decisao", 0) >= c.get("lote", 3):
        decidir(est, c)
        est["desde_decisao"] = 0
    if not so_analisar:
        consertar_codigo(est, c)
    _gravar(ESTADO, est)


def pedir_codigo(titulo, onde, oque):
    """Pedido de conserto direto (chat de conversa / dona): entra na fila de propostas como 'nova'."""
    est = _ler(ESTADO, {"videos": {}, "mudancas": [], "decisoes": []})
    est.setdefault("propostas", []).append({"tipo": "pedido", "titulo": titulo, "prova": oque, "onde": onde,
                                            "como_testar": "", "em": datetime.now().isoformat(timespec="seconds"),
                                            "modelo": "dona", "estado": "nova"})
    _gravar(ESTADO, est)
    print(f"na fila do conserto: {titulo} ({onde})")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--pedir-codigo"]:  # python melhorador_longo.py --pedir-codigo "título" "arquivo.py" "o que"
        pedir_codigo(*sys.argv[2:5])
    else:
        volta(forcar="--forcar" in sys.argv, so_analisar="--so-analisar" in sys.argv)
