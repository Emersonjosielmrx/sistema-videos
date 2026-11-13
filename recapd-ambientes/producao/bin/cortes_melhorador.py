# -*- coding: utf-8 -*-
"""cortes_melhorador.py — o MELHORADOR dos CORTES (dona 26-27/10/2026: "uma cópia do sistema de melhoria só pro vídeo
curto, que faz exatamente o que você faz aqui: vê o vídeo feito e faz a próxima versão melhor e mais viral; fica
pronto e só liga no meu sinal"). Mesmo desenho do colab\\melhorador_longo.py (linha LONGOS).

Guiado pelo VÍDEO (não sorteia projeto nem mexe em código):
  1. A ANÁLISE já é do cortes_juri.py (tarefa Cortes_Juri): movimento em todo Short e júri Gemini em 1 a cada 4 ->
     linhas\\CORTES\\evolucao.jsonl + juri\\<pasta>\\juri.json.
  2. VIGIA as mudanças anteriores: nota média dos Shorts julgados depois da mudança caiu mais que `piora_desfaz` ->
     desfaz sozinho (volta o valor de antes) e anota no DECISOES.md.
  3. A cada `lote` Shorts julgados (e no mínimo `intervalo_h` desde a última mudança), o DECISOR (camadas de modelo do
     json) lê o PROMPT_MELHORADOR.md + LICOES.md + júris + APRENDIDO.md + opinião da dona e devolve ALAVANCAS (só as
     do cortes_ajustes.json, tipo/faixa conferidos aqui), PROPOSTAS de código (PROPOSTAS.md, nunca aplicadas) e recados
     pro MURAL. Modo SOMBRA (padrão): decide mas não aplica — vai pro SOMBRA.md pra comparar com a sessão Claude.

LIGA/DESLIGA: controle.json projeto "melhorador_cortes" etapa "producao" (painel :8790). Desligado = não faz nada.
    python cortes_melhorador.py            # 1 volta (tarefa Cortes_Melhorador, desabilitada até a dona ligar)
    python cortes_melhorador.py --forcar   # roda mesmo desligado (teste)
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import cortes_juri as cj  # noqa: E402

CFG = AQUI / "cortes_melhorador.json"
AJUSTES = AQUI / "cortes_ajustes.json"
LINHA = Path(r"D:\video-fila\linhas\CORTES")
ESTADO = LINHA / "melhorador_estado.json"
PROMPT = LINHA / "PROMPT_MELHORADOR.md"
LICOES = LINHA / "LICOES.md"
PROPOSTAS = LINHA / "PROPOSTAS.md"
SOMBRA = LINHA / "SOMBRA.md"
DECISOES = LINHA / "DECISOES.md"
MURAL = Path(r"D:\video-fila\linhas\MURAL.md")
LOG = LINHA / "melhorador.log"


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
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def ligado():
    try:
        sys.path.insert(0, r"D:\video-fila")
        import controle
        return controle.ligado("melhorador_cortes", "producao")[0]
    except Exception:  # noqa: BLE001 — sem controle = desligado (seguro)
        return False


# ── camadas de modelo (mesma regra do melhorador_longo) ────────────────────────────────────────────────────────────
def modelos(c):
    # 29/10 (Fable, D14): rodando pelo melhorador CENTRAL, a cadeia do decisor vem dele (botão Argon/Opus/ambos do
    # painel) — env CENTRAL_MODELOS {"decisor": [...]} ; fora do central, tudo como antes
    try:
        cm = json.loads(os.environ.get("CENTRAL_MODELOS") or "{}").get("decisor") or []
    except ValueError:
        cm = []
    if cm:
        # 30/10: o central já filtrou o Kiro (só passa com modelos_central.json kiro_liberado; dona 30/10 liberou)
        return [(m, 30) for m in cm if os.environ.get("CENTRAL_KIRO_OK") == "1" or not m.startswith(("kr/", "kiro"))]
    hoje = datetime.now().strftime("%Y-%m-%d")
    lista = (c["camadas"].get("argon", []) if c.get("argon_liberado") else []) + list(c["camadas"]["decisor"])
    out = []
    for m, turnos in lista:
        if c.get("so_gemini_hoje") and "gemini" not in m:
            continue
        if m.startswith("kr/") and hoje < c.get("kiro_a_partir_de", "9999"):
            continue
        out.append((m, turnos))
    return out


# ── alavancas, vigia e desfazer ────────────────────────────────────────────────────────────────────────────────────
def _validar(spec, op, valor, atual):
    """Novo valor da alavanca ou None (recusada)."""
    t = spec["tipo"]
    if t == "float":
        try:
            v = float(valor)
        except (TypeError, ValueError):
            return None
        return round(v, 3) if spec["min"] <= v <= spec["max"] else None
    if t == "str":
        return valor if valor in spec.get("valores", []) else None
    if t == "lista_str":
        atual = list(atual or [])
        if op == "remove":
            return [x for x in atual if x != valor] if valor in atual else None
        if op == "add" and isinstance(valor, str) and 10 <= len(valor.strip()) <= spec.get("max_chars", 200) \
                and valor.strip() not in atual and len(atual) < spec.get("max_itens", 10):
            return atual + [valor.strip()]
    return None


def _decisao(texto):
    s = DECISOES.read_text(encoding="utf-8") if DECISOES.exists() else ""
    cab = "# CORTES — DECISÕES (mais nova em cima)\n"
    corpo = s[len(cab):] if s.startswith(cab) else s
    DECISOES.write_text(cab + f"\n- {datetime.now():%d/%m %H:%M} {texto}\n" + corpo, encoding="utf-8")


def aplicar(a, est, c, modelo, notas_antes):
    chave = str(a.get("chave"))
    spec = c["alavancas"].get(chave)
    if not spec:
        log(f"alavanca fora da lista: {chave}")
        return False
    campo = chave.split(":", 1)[1]
    aj = _ler(AJUSTES, None)
    if aj is None:
        return False
    antes = aj.get(campo)
    novo = _validar(spec, a.get("op", "set"), a.get("valor"), antes)
    if novo is None or novo == antes:
        log(f"alavanca recusada (tipo/faixa/duplicada): {chave} {a.get('op')} {a.get('valor')!r}")
        return False
    porque = str(a.get("porque", ""))[:300]
    if c.get("sombra"):
        with open(SOMBRA, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now():%d/%m %H:%M} [{modelo}] APLICARIA {campo}: {antes!r} -> {novo!r}\n"
                    f"- porque: {porque}\n- veredito da sessão Claude: (preencher: concordo / discordo e por quê)\n")
        est["uso"].setdefault(modelo, {"decisoes": 0, "aplicadas": 0, "desfeitas": 0, "sombra": 0})["sombra"] += 1
        return True
    aj[campo] = novo
    aj.setdefault("historico", []).append({"em": datetime.now().isoformat(timespec="minutes"), "quem": f"melhorador {modelo}",
                                           "chave": campo, "antes": antes, "depois": novo, "porque": porque})
    _gravar(AJUSTES, aj)
    est["mudancas"].append({"em": datetime.now().isoformat(timespec="seconds"), "campo": campo, "antes": antes,
                            "depois": novo, "porque": porque, "modelo": modelo, "estado": "vigiando",
                            "nota_antes": round(sum(notas_antes) / len(notas_antes), 2) if notas_antes else None})
    est["uso"].setdefault(modelo, {"decisoes": 0, "aplicadas": 0, "desfeitas": 0, "sombra": 0})["aplicadas"] += 1
    _decisao(f"[MELHORADOR {modelo}] {campo}: {antes!r} -> {novo!r} — {porque}")
    _sync_pc2()
    log(f"alavanca aplicada: {campo} {antes!r} -> {novo!r}")
    return True


def _sync_pc2():
    try:
        sys.path.insert(0, r"D:\video-fila")
        import pc2_recapd
        log(pc2_recapd.sincronizar_bin()[1])
    except Exception as e:  # noqa: BLE001
        log(f"sync PC2 falhou: {e}")


def _julgados():
    """[(id, data, nota)] dos Shorts com júri, do mais antigo pro mais novo."""
    out = []
    if cj.EVOL.exists():
        for l in cj.EVOL.read_text("utf-8").splitlines():
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get("nota") is not None:
                out.append((d["id"], d["data"], float(d["nota"])))
    return out


def vigiar(est, c):
    jul = _julgados()
    for m in est["mudancas"]:
        if m["estado"] != "vigiando" or m.get("nota_antes") is None:
            continue
        depois = [n for _i, d, n in jul if d > m["em"]]
        if len(depois) < c.get("videos_para_julgar_mudanca", 3):
            continue
        media = sum(depois) / len(depois)
        if media < m["nota_antes"] - c.get("piora_desfaz", 0.5):
            aj = _ler(AJUSTES, {})
            aj[m["campo"]] = m["antes"]
            aj.setdefault("historico", []).append({"em": datetime.now().isoformat(timespec="minutes"), "quem": "melhorador (desfez)",
                                                   "chave": m["campo"], "antes": m["depois"], "depois": m["antes"],
                                                   "porque": f"nota caiu {m['nota_antes']} -> {media:.2f}"})
            _gravar(AJUSTES, aj)
            m["estado"] = f"desfeita (nota {m['nota_antes']} -> {media:.2f})"
            est["uso"].setdefault(m["modelo"], {"decisoes": 0, "aplicadas": 0, "desfeitas": 0, "sombra": 0})["desfeitas"] += 1
            _decisao(f"[MELHORADOR] DESFEITA {m['campo']} ({m['depois']!r} -> {m['antes']!r}): nota caiu "
                     f"{m['nota_antes']} -> {media:.2f}")
            _sync_pc2()
        else:
            m["estado"] = f"mantida (nota {m['nota_antes']} -> {media:.2f})"
        log(f"mudança {m['campo']}: {m['estado']}")


# ── decisão por lote ───────────────────────────────────────────────────────────────────────────────────────────────
def _resumo_juri(pasta):
    j = _ler(cj.JURI / pasta / "juri.json", {})
    linhas = [f"### {pasta} — nota {j.get('nota')}"]
    for v in j.get("verificadores", []):
        linhas.append(f"- {v['foco']} {v['nota']}: " + " | ".join(
            f"[{p.get('gravidade')}] {p.get('quadro')} {p.get('problema')}" for p in v["problemas"][:4]))
    return "\n".join(linhas)[:2500]


def _prompt(est, c):
    jul = _julgados()
    ultimos = [i for i, _d, _n in jul[-c.get("lote", 4):]]
    aj = _ler(AJUSTES, {})
    atuais = {k.split(":", 1)[1]: aj.get(k.split(":", 1)[1]) for k in c["alavancas"]}
    mud = [{k: x[k] for k in ("em", "campo", "antes", "depois", "estado")} for x in est["mudancas"][-8:]]
    dono = cj._opiniao_nova()
    prompt = (PROMPT.read_text(encoding="utf-8")
              + ("\n\n## LIÇÕES\n" + LICOES.read_text(encoding="utf-8")[:4000] if LICOES.exists() else "")
              + ("\n\n## OPINIÃO DA DONA (vale mais que o júri)\n" + dono if dono else "")
              + "\n\n## ALAVANCAS PERMITIDAS (chave: tipo/faixa)\n" + json.dumps(c["alavancas"], ensure_ascii=False)
              + "\n\n## VALORES ATUAIS\n" + json.dumps(atuais, ensure_ascii=False)[:3000]
              + "\n\n## MUDANÇAS RECENTES E O QUE ACONTECEU\n" + json.dumps(mud, ensure_ascii=False)
              + ("\n\n## REGRAS DO APRENDIZ (júri do lote)\n" + cj.APRENDIDO.read_text("utf-8")[:3000]
                 if cj.APRENDIDO.exists() else "")
              + "\n\n## JÚRI DOS ÚLTIMOS SHORTS\n" + "\n\n".join(_resumo_juri(p) for p in ultimos))
    return prompt, ultimos, jul


def bancada(modelos_teste):
    """27/10 (dona): mesmo pedido e mesmo lote pra cada modelo, em paralelo; nada é aplicado. -> linhas\\CORTES\\bancada\\"""
    from concurrent.futures import ThreadPoolExecutor
    import time
    c = _ler(CFG, {})
    est = _ler(ESTADO, {"mudancas": [], "decisoes": [], "uso": {}})
    prompt, ultimos, _jul = _prompt(est, c)
    aj = _ler(AJUSTES, {})
    pasta = LINHA / "bancada" / datetime.now().strftime("%Y%m%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)

    def um(m):
        t = time.time()
        try:
            r, erro = cj.chamar_json(prompt, LINHA, m, timeout=1500, max_turnos=30), None
        except Exception as e:  # noqa: BLE001
            r, erro = {}, str(e)[:300]
        val = []
        for a in r.get("alavancas") or []:
            spec = c["alavancas"].get(str(a.get("chave")))
            campo = str(a.get("chave")).split(":", 1)[-1]
            ok = bool(spec) and _validar(spec, a.get("op", "set"), a.get("valor"), aj.get(campo)) not in (None, aj.get(campo))
            val.append({"chave": a.get("chave"), "op": a.get("op"), "valor": a.get("valor"), "passa_trava": ok})
        out = {"modelo": m, "segundos": round(time.time() - t), "erro": erro, "lote": ultimos, "alavancas_trava": val,
               "resposta": r}
        _gravar(pasta / (m.replace("/", "_") + ".json"), out)
        log(f"bancada {m}: {out['segundos']} s, erro={erro}, alavancas={[(v['chave'], v['passa_trava']) for v in val]}")
        return out

    with ThreadPoolExecutor(len(modelos_teste)) as ex:
        res = list(ex.map(um, modelos_teste))
    log(f"bancada gravada em {pasta}")
    return res


def decidir(est, c):
    prompt, ultimos, jul = _prompt(est, c)
    r = m = None
    tentados = []
    # 27/10 (dona): só Argon (prazo curto) e reserva Gemini 3.8 — sem Opus/Kiro; falhou/demorou = o próximo da lista
    for m, turnos in modelos(c):
        try:
            r = cj.chamar_json(prompt, LINHA, m, timeout=int(c.get("prazo_argon_s", 360)) if "argon" in m else 900,
                               max_turnos=turnos)
            break
        except Exception as e:  # noqa: BLE001
            log(f"decisor {m} falhou/demorou: {str(e)[:200]} — próximo da lista")
            tentados.append((m, e))
            r = None
    if not r:
        log("nenhum decisor respondeu — nada nesta volta")
        # 30/10 (Fable; regra da dona 29/10 21:30 "se todos falharem, tem que estar no log pra acionarmos mais
        # modelos"): esta linha não registrava — o modelos_esgotados.jsonl ficou vazio com a fila acabando
        try:
            import sys as _s
            _s.path.insert(0, r"D:\video-fila")
            import modelos_esgotados
            modelos_esgotados.registrar("cortes", "decisor", tentados)
        except Exception:  # noqa: BLE001
            pass
        return
    est["uso"].setdefault(m, {"decisoes": 0, "aplicadas": 0, "desfeitas": 0, "sombra": 0})["decisoes"] += 1
    est["decisoes"].append({"em": datetime.now().isoformat(timespec="seconds"), "modelo": m, "lote": ultimos,
                            "resposta": r})
    log(f"decisor {m}: {str(r.get('diagnostico', ''))[:300]}")
    if c.get("sombra"):
        with open(SOMBRA, "a", encoding="utf-8") as f:
            f.write(f"\n# {datetime.now():%d/%m %H:%M} — {m} (lote {', '.join(ultimos)})\n"
                    f"- diagnóstico: {r.get('diagnostico')}\n")
    feitas = 0
    notas_antes = [n for _i, _d, n in jul[-3:]]
    # 29/10: o central chama com --forcar a cada pressão; sem isto a mesma regra mudou 2x em 70 min (18:15 e 19:26)
    # antes de 1 Short ser julgado com a 1ª. Chave ainda "vigiando" = não mexe de novo.
    vigiando = {m["campo"] for m in est["mudancas"] if m["estado"] == "vigiando"}
    for a in r.get("alavancas") or []:
        if feitas >= c.get("max_mudancas_por_lote", 2):
            break
        if str(a.get("chave")).split(":", 1)[-1] in vigiando:
            log(f"alavanca adiada (mudança anterior ainda em vigia): {a.get('chave')}")
            continue
        if aplicar(a, est, c, m, notas_antes):
            feitas += 1
    for p in r.get("propostas") or []:
        with open(SOMBRA if c.get("sombra") else PROPOSTAS, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now():%d/%m %H:%M} PROPOSTA [{p.get('tipo')}] {p.get('titulo')} ({m})\n"
                    f"- prova: {p.get('prova')}\n- onde: {p.get('onde')}\n- como testar: {p.get('como_testar')}\n")
    if not c.get("sombra"):
        for rec in (r.get("mural") or [])[:2]:
            s = MURAL.read_text(encoding="utf-8").splitlines(keepends=True)
            s.insert(3, f"- {datetime.now():%d/%m %H:%M} | de CORTES (melhorador) | para TODAS | {str(rec)[:300]}\n")
            MURAL.write_text("".join(s), encoding="utf-8")
    est["ultima_decisao"] = datetime.now().isoformat(timespec="seconds")
    est["julgados_na_decisao"] = len(jul)


# ── volta ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def volta(forcar=False):
    if not forcar and not ligado():
        return
    c = _ler(CFG, {})
    est = _ler(ESTADO, {"mudancas": [], "decisoes": [], "uso": {}})
    vigiar(est, c)
    jul = _julgados()
    novos = len(jul) - est.get("julgados_na_decisao", 0)
    ult = est.get("ultima_decisao")
    cedo = ult and datetime.now() - datetime.fromisoformat(ult) < timedelta(hours=c.get("intervalo_h", 6))
    if forcar or (novos >= c.get("lote", 4) and not cedo):
        decidir(est, c)
    else:
        log(f"sem decisão: {novos} Short(s) julgado(s) novos (lote {c.get('lote', 4)})"
            + (f", última decisão {ult}" if cedo else ""))
    _gravar(ESTADO, est)


if __name__ == "__main__":
    if "--bancada" in sys.argv:  # python cortes_melhorador.py --bancada m1,m2,...
        bancada(sys.argv[sys.argv.index("--bancada") + 1].split(","))
    else:
        volta(forcar="--forcar" in sys.argv)
