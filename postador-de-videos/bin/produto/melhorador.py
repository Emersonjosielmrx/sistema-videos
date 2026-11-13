r"""MELHORADOR automático da linha PRODUTOS (27/10, dono: "faça uma cópia do sistema de melhorias para os vídeos de
Veo com produtos, com o objetivo de fazer exatamente o que você está fazendo aqui: ver o vídeo feito e fazer a
próxima versão melhor, mais viral; construa agora mas não ligue; vá melhorando com as suas experiências; ele assume
o seu lugar no apertar de um botão").

Cópia ENXUTA e SEGURA do D:\video-fila\melhoria_continua.py (papéis separados + revisor adversário + desfazer):
  1. coleta (Python, sem IA): vídeo novo da linha, júri Gemini (produto_lapidar.jsonl), movimento por cena,
     OPINIOES.txt do dono (vitrine), histórico de notas, placar das variações, ajustes e regras atuais;
  2. ANALISTA (modelo barato) olha a folha de 12 quadros + dados e lista os achados;
  3. DECISOR (o MELHOR modelo disponível) escolhe até 2 mudanças, SÓ entre ações seguras: botões numéricos com
     faixa (produto\ajustes.py), ligar/desligar/pesar formatos, regra curta para o roteirista
     (config\produto_regras_roteiro.md) ou para o editor (seção MELHORADOR do remotion\EDITOR.md). Código Python
     NUNCA é mexido: vira "ideia_codigo" anotada no ESTADO da linha (o Gemini tem histórico de quebrar o sistema);
  4. REVISOR adversário (outro modelo) veta o que não tem prova/fere regra; o Python confere faixa e regras fixas;
  5. aplica com backup (modo "aplicar") ou só anota (modo "ensaio"); registra no DECISOES da linha;
  6. VIGIA: se a nota do júri cair >= desfazer_se_cair nos 2 vídeos seguintes, desfaz sozinho.
Modelos: config\melhorador_produtos.json "cadeia" (ordem por papel; pula desligado, sem cota ou que falhou há pouco;
cc/ só com cota do Claude Pro acima da reserva do dono). Cada chamada vai pro placar dos modelos (útil ou não).

    python -m produto.melhorador --ensaio [video.json]   # roda 1 ciclo SEM aplicar (teste; funciona desligado)
    python -m produto.melhorador --ciclo                 # o que a tarefa roda (só se "ligado")
    python -m produto.melhorador --status | --ligar | --desligar
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
from produto import ajustes, motor  # noqa: E402

RAIZ = BIN.parent
CONFIG = RAIZ / "config" / "melhorador_produtos.json"
PROMPTS = RAIZ / "config" / "melhorador"
LINHA = Path(r"D:\video-fila\linhas\PRODUTOS")
ESTADO = LINHA / "melhorador_estado.json"
LOG = LINHA / "melhorador.log"
BACKUP = LINHA / "melhorador_backup"
TRABALHO = Path(r"D:\video-fila\produto_tmp\melhorador")
FILA = Path(r"D:\video-fila\produto_fila")
TESTES = Path(r"D:\ms-energy\_diag\teste_misto")
HIST_JURI = RAIZ / "logs" / "produto_lapidar.jsonl"
OPINIOES = Path(r"D:\hipercool-materiais\produtos_ultimo_video\OPINIOES.txt")
REGRAS_ROTEIRO = RAIZ / "config" / "produto_regras_roteiro.md"
EDITOR_MD = RAIZ / "remotion" / "EDITOR.md"
INI, FIM = "<!-- MELHORADOR:INICIO -->", "<!-- MELHORADOR:FIM -->"
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
TAREFA = "MelhoradorProdutos"

# texto de regra que tenta afrouxar segurança = barrado no Python (o revisor é IA e pode deixar passar)
# 27/10: "garant" sozinho barrava "garantir contraste" (regra boa do Gemini) -> só promessa de garantia
_REGRA_PERIGOSA = re.compile(r"\d+\s*%|pre[cç]o|r\$|gr[aá]tis|\bgarantia\b|\bgarantid[oa]s?\b|resultado\s+garantido|"
                             r"prazo|em\s+minutos|telefone|whats\s*app\s*\(|"
                             r"\bsite\b|concorr|concession|antonio|pode\s+(cobrir|tapar)\s+o\s+rosto|ignore|"
                             r"desconsidere|sem\s+zona|fora\s+da\s+zona|letra\s+menor\s+que", re.I)


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(p)


def cfg():
    return _ler(CONFIG, {})


def _estado():
    e = _ler(ESTADO, {})
    for k, v in (("vistos", []), ("aplicadas", []), ("ideias_codigo", []), ("modelos", {}),
                 ("indisponivel", {}), ("opinioes_lidas", 0)):
        e.setdefault(k, v)
    return e


# ───────────────────────────── 1. coleta (sem IA) ─────────────────────────────

def _videos():
    """Vídeos da linha (json ao lado do mp4), mais novo por último."""
    achados = []
    for pasta in [p for p in FILA.iterdir() if p.is_dir() and not p.name.startswith("_molde")] + [TESTES]:
        for sub in (pasta, pasta / "_postados"):
            if sub.exists():
                achados += [j for j in sub.glob("*.json") if j.with_suffix(".mp4").exists()]
    return sorted(achados, key=lambda p: p.stat().st_mtime)


def _juri(nome):
    try:
        linhas = [json.loads(x) for x in HIST_JURI.read_text("utf-8").splitlines() if x.strip()]
    except OSError:
        return None, []
    deste = [x for x in linhas if x.get("video") == nome]
    return (deste[-1] if deste else None), linhas[-12:]


def _opinioes_novas(e):
    try:
        t = OPINIOES.read_text("utf-8")
    except OSError:
        return "", 0
    corpo = t.split("\n\n", 1)[1] if "\n\n" in t else ""
    return corpo[e.get("opinioes_lidas", 0):].strip(), len(corpo)


def _regras_roteiro():
    try:
        return [x[2:].strip() for x in REGRAS_ROTEIRO.read_text("utf-8").splitlines() if x.startswith("- ")]
    except OSError:
        return []


def _regras_editor():
    t = EDITOR_MD.read_text("utf-8")
    if INI not in t:
        return []
    meio = t.split(INI, 1)[1].split(FIM, 1)[0]
    return [x[2:].strip() for x in meio.splitlines() if x.startswith("- ")]


def _folha(mp4, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    try:
        dur = float(subprocess.run([FF.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries",
                                    "format=duration", "-of", "csv=p=0", str(mp4)],
                                   capture_output=True, text=True, timeout=60).stdout.strip())
    except ValueError:
        dur = 30.0
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp4), "-vf",
                    f"fps={12 / max(dur, 1):.4f},scale=270:480,tile=4x3", "-frames:v", "1", str(pasta / "folha.jpg")],
                   check=True, timeout=300)


def coletar(js, e):
    side = _ler(js, {})
    nome = js.with_suffix(".mp4").name
    juri, hist = _juri(nome)
    opinioes, _ = _opinioes_novas(e)
    from produto import variacoes
    vig = [a for a in e["aplicadas"] if a.get("vigiando")]
    return {
        "video": nome, "conta": side.get("conta"), "marca": side.get("marca"), "titulo": side.get("titulo"),
        "formato": side.get("variante"), "veo_total": side.get("veo_total"), "voz": side.get("voz"),
        # 29/10: sem isto o analista acreditava no júri ("corte seco") com o efeito de transição no vídeo
        "efeito_transicao": side.get("efeito_transicao"), "voz_clonada": side.get("voz_clonada"),
        "status": "teste" if TESTES in js.parents else ("reprovado" if "_revisar" in str(js) else "fila/postado"),
        "juri": {k: (juri or {}).get(k) for k in ("nota", "notas", "movimento", "graves", "reprovar", "motivo")},
        "juri_problemas": [{"foco": v["foco"], **{k: p.get(k) for k in ("gravidade", "cena", "problema",
                                                                         "como_corrigir")}}
                           for v in (juri or {}).get("verificadores", []) for p in v.get("problemas", [])
                           if p.get("gravidade") in ("grave", "media")][:25],
        "historico_notas": [{"video": h.get("video"), "conta": h.get("conta"), "formato": h.get("variante"),
                             "nota": h.get("nota"), "notas": h.get("notas")} for h in hist],
        "opinioes": opinioes, "ajustes": ajustes.todos(),
        "regras_atuais": {"roteiro": _regras_roteiro(), "editor": _regras_editor()},
        "placar_formatos": variacoes.contagem(),
        "vigiando": [{"mudanca": a["mudanca"], "desde": a["quando"]} for a in vig],
    }


# ───────────────────────────── modelos (cadeia por papel) ─────────────────────────────

def _cota_cc(c):
    try:
        spec = importlib.util.spec_from_file_location("cota_claude_ccv", r"D:\claude-code-video\cota_claude.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        d = mod.decidir(c.get("cc_custo_pontos", 6), True)
        return bool(d.get("ligar")), d.get("motivo", "")
    except Exception as ex:  # noqa: BLE001
        return False, f"cota ilegível ({type(ex).__name__})"


def _disponivel(m, c, e):
    if m in c.get("modelos_desligados", []):
        return False, "desligado na config"
    ate = e["indisponivel"].get(m)
    if ate and datetime.fromisoformat(ate) > datetime.now():
        return False, f"falhou há pouco (volta {ate[11:16]})"
    if m.startswith("cc/"):
        return _cota_cc(c)
    if not motor.responde(m, 90 if "argon" in m else 60):  # 27/10: chave esfriando = 4–5 min por pedido
        return False, "não respondeu ao teste rápido"
    return True, ""


def _placar(e, m, papel, ok, seg, erro=None):
    p = e["modelos"].setdefault(m, {})
    q = p.setdefault(papel, {"chamadas": 0, "ok": 0, "falhas": 0, "segundos": 0, "propostas": 0, "aprovadas": 0,
                             "mantidas": 0, "desfeitas": 0, "ultimo_erro": None})
    q["chamadas"] += 1
    q["ok" if ok else "falhas"] += 1
    q["segundos"] += round(seg)
    if erro:
        q["ultimo_erro"] = str(erro)[:160]


def _chamar(papel, prompt, pasta, c, e, evitar=None):
    """(resposta_json, modelo) pelo 1º modelo disponível da cadeia do papel; (None, None) se nenhum respondeu."""
    cadeia = list(c.get("cadeia", {}).get(papel, []))
    try:  # 29/10 (Fable, D14): pelo melhorador CENTRAL a cadeia do papel vem dele (botão Argon/Opus/ambos); nunca Kiro
        cm = json.loads(os.environ.get("CENTRAL_MODELOS") or "{}").get(papel) or []
        if cm:
            cadeia = [m for m in cm if not str(m).startswith(("kr/", "kiro"))]
    except ValueError:
        pass
    if evitar and len(cadeia) > 1:  # revisor: de preferência OUTRO modelo, não o que decidiu
        cadeia = [m for m in cadeia if m != evitar] + [m for m in cadeia if m == evitar]
    tentados = []  # 29/10 (dona): fila inteira sem resposta fica registrada para acionarmos mais modelos
    for m in cadeia:
        ok, motivo = _disponivel(m, c, e)
        if not ok:
            log(f"  [{papel}] pulo {m}: {motivo}")
            tentados.append((m, f"pulado: {motivo}"))
            continue
        t0 = time.time()
        try:
            prazo = c.get("argon_prazo_s", 360) if "argon" in m else 900  # dono 27/10: Argon curto, demorou -> Gemini
            r = motor.chamar_json(prompt, pasta, f"melhorador_{papel}", modelo=m, timeout=prazo, max_turnos=14)
            _placar(e, m, papel, True, time.time() - t0)
            log(f"  [{papel}] {m} respondeu em {time.time() - t0:.0f} s")
            return r, m
        except (motor.MotorErro, motor.SemCota) as ex:
            _placar(e, m, papel, False, time.time() - t0, ex)
            e["indisponivel"][m] = (datetime.now() + timedelta(hours=c.get("indisponivel_h", 2))).isoformat(
                timespec="seconds")
            log(f"  [{papel}] {m} falhou ({type(ex).__name__}: {str(ex)[:120]}) — tento o próximo")
            tentados.append((m, f"{type(ex).__name__}: {str(ex)[:100]}"))
    try:  # fila inteira sem resposta: registra (e avisa uma vez) para acionarmos mais modelos
        sys.path.append(r"D:\video-fila")
        import modelos_esgotados
        modelos_esgotados.registrar("produtos", papel, tentados, cadeia)
        import avisos
        avisos.enviar(f"Melhorador dos produtos ({papel}): nenhum modelo da fila respondeu ({', '.join(cadeia)}). "
                      "Precisa de mais um modelo na fila.", "melhorador central", importante=True,
                      chave=f"esgotado:produtos:{papel}")
    except Exception:  # noqa: BLE001 — registro nunca derruba o melhorador
        pass
    return None, None


# ───────────────────────────── validação + aplicação ─────────────────────────────

def validar(mu):
    """Erro (texto) ou None. Confere em Python o que o revisor (IA) pode ter deixado passar."""
    from produto import variacoes
    a, alvo, valor = mu.get("acao"), mu.get("alvo") or "", mu.get("valor")
    if a == "ajuste":
        if alvo not in ajustes.BOTOES:
            return f"botão desconhecido: {alvo}"
        _, mn, mx, _ = ajustes.BOTOES[alvo]
        try:
            v = float(valor)
        except (TypeError, ValueError):
            return "valor não é número"
        if not mn <= v <= mx:
            return f"{alvo}={v} fora da faixa {mn}–{mx}"
        atual = ajustes.valor(alvo)
        if abs(v - atual) > (mx - mn) * 0.35:
            return f"pulo grande demais ({atual} -> {v}): no máximo 35% da faixa por vez"
    elif a in ("desligar_variante", "ligar_variante", "peso_variante"):
        if alvo not in variacoes.VARIANTES:
            return f"formato desconhecido: {alvo}"
        if a == "desligar_variante":
            fora = set(ajustes.valor("variantes_desligadas")) | {alvo}
            if len([v for v in variacoes.VARIANTES if v not in fora]) < 3:
                return "sobrariam menos de 3 formatos no sorteio"
        if a == "peso_variante":
            try:
                if not 0.3 <= float(valor) <= 3.0:
                    return "peso fora de 0.3–3.0"
            except (TypeError, ValueError):
                return "peso não é número"
    elif a in ("regra_roteiro", "regra_editor"):
        t = str(valor or "").strip()
        if not 15 <= len(t) <= 220:
            return "regra precisa de 15 a 220 caracteres"
        perigo = _REGRA_PERIGOSA.search(t)
        # 29/10: "deixe 10% de respiro no topo" (regra de LAYOUT do editor) era vetada como número inventado — vetou a
        # mudança certa em 2 modelos do teste. % só barra regra de ROTEIRO; o texto da tela já tem trava própria
        # (editor.problemas_texto barra % na tela)
        if perigo and a == "regra_editor" and re.fullmatch(r"\d+\s*%", perigo.group(0)):
            perigo = _REGRA_PERIGOSA.search(re.sub(r"\d+\s*%", "", t))
        if perigo:
            return f"regra mexe em assunto de segurança/fatos: {perigo.group(0)}"
        atuais = _regras_roteiro() if a == "regra_roteiro" else _regras_editor()
        if len(atuais) >= cfg().get("max_regras", 20):
            return "já tem regras demais: remova uma antes"
    elif a == "remover_regra":
        if not str(valor or "").strip():
            return "diga qual regra remover"
    elif a != "ideia_codigo":
        return f"ação não permitida: {a}"
    return None


def _backup(arquivos, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    salvos = []
    for arq in arquivos:
        arq = Path(arq)
        if arq.exists():
            shutil.copy2(arq, pasta / arq.name)
        salvos.append({"arquivo": str(arq), "existia": arq.exists()})
    return salvos


def _escrever_regras(tipo, regras):
    linhas = "".join(f"- {r}\n" for r in regras)
    if tipo == "roteiro":
        REGRAS_ROTEIRO.write_text(linhas, "utf-8")
        return
    t = EDITOR_MD.read_text("utf-8")
    antes, resto = t.split(INI, 1)
    depois = resto.split(FIM, 1)[1]
    EDITOR_MD.write_text(f"{antes}{INI}\n{linhas}{FIM}{depois}", "utf-8")


def aplicar(mu, e, base):
    """Aplica 1 mudança com backup. Devolve o registro (ou None para ideia_codigo)."""
    a, alvo, valor = mu["acao"], mu.get("alvo") or "", mu.get("valor")
    if a == "ideia_codigo":
        e["ideias_codigo"].append({"quando": datetime.now().isoformat(timespec="seconds"), "ideia": str(valor),
                                   "motivo": mu.get("motivo"), "prova": mu.get("prova")})
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    arqs = [ajustes.ARQ] if a in ("ajuste", "desligar_variante", "ligar_variante", "peso_variante") else \
        [REGRAS_ROTEIRO, EDITOR_MD]
    salvos = _backup(arqs, BACKUP / ts)
    if arqs == [ajustes.ARQ]:
        d = _ler(ajustes.ARQ, {})
        if a == "ajuste":
            d[alvo] = float(valor)
        elif a == "desligar_variante":
            d["variantes_desligadas"] = sorted(set(d.get("variantes_desligadas", [])) | {alvo})
        elif a == "ligar_variante":
            d["variantes_desligadas"] = [v for v in d.get("variantes_desligadas", []) if v != alvo]
        else:
            d.setdefault("pesos_variantes", {})[alvo] = float(valor)
        _gravar(ajustes.ARQ, d)
    elif a in ("regra_roteiro", "regra_editor"):
        tipo = "roteiro" if a == "regra_roteiro" else "editor"
        atuais = _regras_roteiro() if tipo == "roteiro" else _regras_editor()
        _escrever_regras(tipo, atuais + [str(valor).strip()])
    elif a == "remover_regra":
        alvo_txt = str(valor).strip().lower()[:60]
        for tipo, atuais in (("roteiro", _regras_roteiro()), ("editor", _regras_editor())):
            novas = [r for r in atuais if alvo_txt not in r.lower()]
            if len(novas) != len(atuais):
                _escrever_regras(tipo, novas)
    return {"quando": datetime.now().isoformat(timespec="seconds"), "mudanca": mu, "backup": str(BACKUP / ts),
            "arquivos": salvos, "video_base": base["video"], "nota_base": base["juri"].get("nota"),
            "notas_depois": [], "vigiando": True}


def desfazer(reg, motivo):
    for s in reg["arquivos"]:
        arq, cop = Path(s["arquivo"]), Path(reg["backup"]) / Path(s["arquivo"]).name
        if s["existia"] and cop.exists():
            shutil.copy2(cop, arq)
        elif not s["existia"]:
            arq.unlink(missing_ok=True)
    reg["vigiando"], reg["desfeita"] = False, motivo
    log(f"  [vigia] DESFEITA: {reg['mudanca'].get('acao')} {reg['mudanca'].get('alvo') or reg['mudanca'].get('valor')}"
        f" — {motivo}")


def vigiar(e, dados, c):
    """Notas dos vídeos que saíram DEPOIS da mudança: caiu = desfaz; 2 vídeos sem cair = mantida."""
    nota = dados["juri"].get("nota")
    if nota is None:
        return
    for reg in e["aplicadas"]:
        if not reg.get("vigiando") or dados["video"] == reg["video_base"] or dados["video"] in reg["notas_depois"]:
            continue
        reg["notas_depois"].append(dados["video"])
        base = reg.get("nota_base")
        modelo = reg.get("modelo_decisor")
        if base is not None and nota <= base - c.get("desfazer_se_cair", 0.5):
            desfazer(reg, f"nota caiu {base} -> {nota} ({dados['video']})")
            if modelo:
                e["modelos"].setdefault(modelo, {}).setdefault("decisor", {}).setdefault("desfeitas", 0)
                e["modelos"][modelo]["decisor"]["desfeitas"] += 1
        elif len(reg["notas_depois"]) >= 2:
            reg["vigiando"], reg["mantida"] = False, True
            if modelo:
                e["modelos"].setdefault(modelo, {}).setdefault("decisor", {}).setdefault("mantidas", 0)
                e["modelos"][modelo]["decisor"]["mantidas"] += 1


def _decisoes(linhas):
    arq = LINHA / "DECISOES.md"
    try:
        t = arq.read_text("utf-8")
    except OSError:
        t = "# Linha PRODUTOS — decisões\n\n"
    i = t.find("\n- ")  # entra antes da 1ª decisão (o cabeçalho tem 3 linhas)
    i = len(t) if i < 0 else i + 1
    arq.write_text(t[:i] + "".join(f"- {l}\n" for l in linhas) + t[i:], "utf-8")


# ───────────────────────────── ciclo ─────────────────────────────

def ciclo(ensaio, js=None, so_modelo=None):
    c, e = cfg(), _estado()
    if so_modelo:  # teste de um modelo só em todos os papéis (27/10: "hoje vá testando com o Gemini")
        c["cadeia"] = {p: [so_modelo] for p in ("analista", "decisor", "revisor")}
    if js is None:
        novos = [v for v in _videos() if str(v) not in e["vistos"]]
        if not novos:
            log("nada novo")
            return None
        js = novos[-1]
    js = Path(js)
    log(f"=== {'ENSAIO' if ensaio else 'CICLO'}: {js.name}")
    dados = coletar(js, e)
    if not ensaio:
        vigiar(e, dados, c)
    pasta = TRABALHO / js.stem
    shutil.rmtree(pasta, ignore_errors=True)
    _folha(js.with_suffix(".mp4"), pasta)
    _gravar(pasta / "dados.json", dados)

    # 2) analista
    analise, m_an = _chamar("analista", (PROMPTS / "analista.md").read_text("utf-8"), pasta, c, e)
    if analise is None:
        log("  sem analista disponível — paro o ciclo (nada mudou)")
        _gravar(ESTADO, e)
        return None
    achados = analise.get("achados") or []
    log(f"  [analista] {len(achados)} achado(s): {analise.get('resumo', '')[:160]}")

    # 3) decisor
    from produto import variacoes
    botoes = "; ".join(f"{n} (agora {ajustes.valor(n)}, faixa {b[1]}–{b[2]}: {b[3]})" for n, b in ajustes.BOTOES.items())
    # replace, não .format: o prompt tem chaves de JSON de exemplo
    dec_prompt = (PROMPTS / "decisor.md").read_text("utf-8").replace("{max_mudancas}", str(c.get("max_mudancas", 2))) \
        .replace("{botoes}", botoes).replace("{variantes}", ", ".join(variacoes.VARIANTES))
    dec_prompt += "\n\nACHADOS DO ANALISTA:\n" + json.dumps(achados, ensure_ascii=False, indent=1) + \
        "\n\nDADOS (também em dados.json nesta pasta):\n" + json.dumps(
            {k: dados[k] for k in ("video", "formato", "juri", "opinioes", "ajustes", "regras_atuais",
                                   "placar_formatos", "vigiando")}, ensure_ascii=False)
    decisao, m_dec = _chamar("decisor", dec_prompt, pasta, c, e)
    mudancas = ((decisao or {}).get("mudancas") or [])[:c.get("max_mudancas", 2)]
    if m_dec:
        e["modelos"][m_dec]["decisor"]["propostas"] += len(mudancas)
    log(f"  [decisor] {m_dec}: {len(mudancas)} mudança(s) proposta(s)")

    # 4) revisor + validação em Python
    aprovadas = []
    if mudancas:
        rev_prompt = (PROMPTS / "revisor.md").read_text("utf-8") + "\n\nMUDANÇAS:\n" + json.dumps(
            list(enumerate(mudancas)), ensure_ascii=False, indent=1) + "\n\nACHADOS:\n" + json.dumps(
            achados, ensure_ascii=False)[:6000]
        rev, m_rev = _chamar("revisor", rev_prompt, pasta, c, e, evitar=m_dec)
        votos = {v.get("indice"): v for v in (rev or {}).get("votos", [])}
        for i, mu in enumerate(mudancas):
            v = votos.get(i)
            if rev is None or not v or not v.get("aprovada"):
                mu["vetada"] = (v or {}).get("motivo") or "sem revisor disponível"
                continue
            erro = validar(mu)
            if erro:
                mu["vetada"] = f"Python: {erro}"
                continue
            aprovadas.append(mu)
        if m_dec:
            e["modelos"][m_dec]["decisor"]["aprovadas"] += len(aprovadas)
        for mu in mudancas:
            log(f"  {'APROVADA' if mu in aprovadas else 'vetada'}: {mu.get('acao')} {mu.get('alvo') or ''} "
                f"{str(mu.get('valor'))[:80]} — {mu.get('vetada') or mu.get('motivo', '')[:100]}")

    # 5) aplica (ou só anota no ensaio)
    linhas = []
    for mu in aprovadas:
        txt = f"{mu.get('acao')} {mu.get('alvo') or ''} = {str(mu.get('valor'))[:160]} | {mu.get('motivo', '')[:140]}"
        if ensaio:
            linhas.append(f"{datetime.now():%d/%m %H:%M} | [MELHORADOR ensaio — NÃO aplicado] {txt} | modelo {m_dec}")
            continue
        reg = aplicar(mu, e, dados)
        if reg:
            reg["modelo_decisor"] = m_dec
            e["aplicadas"].append(reg)
        linhas.append(f"{datetime.now():%d/%m %H:%M} | [MELHORADOR] {txt} | prova: {str(mu.get('prova'))[:100]} | "
                      f"modelo {m_dec} | desfazer: python -m produto.melhorador --desfazer-ultima")
    if linhas:
        _decisoes(linhas)
    if not ensaio:
        e["vistos"].append(str(js))
        _, total = _opinioes_novas(e)
        e["opinioes_lidas"] = total
    e["ultimo_ciclo"] = {"quando": datetime.now().isoformat(timespec="seconds"), "video": js.name, "ensaio": ensaio,
                         "modelos": {"analista": m_an, "decisor": m_dec}, "achados": achados,
                         "mudancas": mudancas, "aprovadas": len(aprovadas)}
    _gravar(ESTADO, e)
    log(f"=== fim: {len(aprovadas)} aprovada(s){' (ensaio: nada aplicado)' if ensaio else ''}")
    return e["ultimo_ciclo"]


CAIXA = LINHA / "caixa"


def foto_codigo():
    """Foto do código ANTES de a sessão forte mexer (27/10: a caixa copiou o código 2 h depois e o executor achou a
    mudança real já pronta). Devolve a pasta da foto; passe para caixa_codigo(base=...)."""
    pasta = CAIXA / ("base_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    pasta.mkdir(parents=True)
    for p in (BIN / "produto").glob("*.py"):
        shutil.copy2(p, pasta / p.name)
    return pasta


def caixa_codigo(ideia, modelo=None, base=None):
    r"""27/10 (dono: "deixe o Gemini numa caixa separada... faz uma cópia do que ele vai mexer no código e põe ele pra
    mexer sem chance de quebrar o original"): o EXECUTOR implementa a ideia numa CÓPIA de produto\*.py (sem Bash, só
    edita dentro da pasta da caixa); sai o diff + checagem de sintaxe para comparar com a mudança real."""
    import ast
    import difflib
    c = cfg()
    modelo = modelo or (c.get("cadeia", {}).get("executor") or ["agy/gemini-3.8-flash-high"])[0]
    pasta = CAIXA / datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # %f: caixas em paralelo no mesmo segundo
    (pasta / "produto").mkdir(parents=True)
    originais = {p.name: p for p in (Path(base) if base else BIN / "produto").glob("*.py")}
    for p in originais.values():
        shutil.copy2(p, pasta / "produto" / p.name)
    (pasta / "IDEIA.md").write_text(ideia, "utf-8")
    prompt = (PROMPTS / "executor.md").read_text("utf-8").replace("{ideia}", ideia)
    t0 = time.time()
    so_editar = ("Read,Write,Edit,Glob,Grep", "Bash,WebFetch,WebSearch,Agent")  # sem Bash: não sai da caixa
    try:
        resp = motor.chamar(prompt, pasta, "melhorador_executor", timeout=2700, max_turnos=60, modelo=modelo,
                            ferramentas=so_editar, aceitar_limite=True)
    except (motor.MotorErro, motor.SemCota) as ex:
        resp = f"FALHOU: {ex}"
    diffs, quebrados = [], []
    for nome, orig in originais.items():
        nova = (pasta / "produto" / nome).read_text("utf-8")
        velha = orig.read_text("utf-8")
        if nova != velha:
            diffs += difflib.unified_diff(velha.splitlines(True), nova.splitlines(True), f"original/{nome}",
                                          f"caixa/{nome}")
            try:
                ast.parse(nova)
            except SyntaxError as ex:
                quebrados.append(f"{nome}: {ex}")
                continue
            # 27/10: compilar não basta (a linha `durs = [...]` sumiu e só quebrou rodando) -> pyflakes
            r = subprocess.run([sys.executable, "-m", "pyflakes", str(pasta / "produto" / nome)],
                               capture_output=True, text=True)
            graves = [l for l in r.stdout.splitlines() if re.search(r"undefined name|referenced before assignment|"
                                                                     r"undefined local", l)]
            if graves:
                quebrados.append(f"{nome}: {graves[0][-160:]}")
    (pasta / "diff.patch").write_text("".join(diffs), "utf-8")
    disse_feito = bool(re.search(r'"feito"\s*:\s*true', str(resp)))
    res = {"quando": datetime.now().isoformat(timespec="seconds"), "modelo": modelo, "ideia": ideia,
           "segundos": round(time.time() - t0), "resposta": str(resp)[-800:], "linhas_diff": len(diffs),
           "quebrados": quebrados, "pasta": str(pasta), "base": str(base) if base else "código atual",
           "resposta_falsa": disse_feito and not diffs}
    e = _estado()
    q = e["modelos"].setdefault(modelo, {}).setdefault("executor", {"caixas": 0, "falsas": 0, "quebradas": 0})
    q["caixas"] = q.get("caixas", 0) + 1
    q["falsas"] = q.get("falsas", 0) + int(res["resposta_falsa"])
    q["quebradas"] = q.get("quebradas", 0) + int(bool(quebrados))
    _gravar(ESTADO, e)
    _gravar(pasta / "resultado.json", res)
    log(f"[caixa] {modelo}: {len(diffs)} linhas de diff, {len(quebrados)} arquivo(s) quebrado(s), "
        f"{res['segundos']} s — {pasta}")
    return res


def _tarefa(ligar):
    acao = "/ENABLE" if ligar else "/DISABLE"
    r = subprocess.run(["schtasks", "/Change", "/TN", TAREFA, acao], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def main(a):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--ensaio" in a:
        alvo = next((x for x in a if x.endswith(".json")), None)
        so = a[a.index("--modelo") + 1] if "--modelo" in a else None
        ciclo(True, alvo, so)
    elif "--ciclo" in a:
        if not cfg().get("ligado"):
            print("melhorador DESLIGADO (config\\melhorador_produtos.json) — nada a fazer")
            return
        trava = TRABALHO / ".rodando"
        if trava.exists() and time.time() - trava.stat().st_mtime < 3 * 3600:
            print("outro ciclo rodando")
            return
        trava.parent.mkdir(parents=True, exist_ok=True)
        trava.write_text(datetime.now().isoformat(), "utf-8")
        try:
            ciclo(cfg().get("modo") != "aplicar")
        finally:
            trava.unlink(missing_ok=True)
    elif "--caixa" in a:
        ideia = a[a.index("--caixa") + 1]
        so = a[a.index("--modelo") + 1] if "--modelo" in a else None
        base = a[a.index("--base") + 1] if "--base" in a else None
        print(json.dumps(caixa_codigo(ideia, so, base), ensure_ascii=False, indent=1))
    elif "--foto" in a:
        print(foto_codigo())
    elif "--desfazer-ultima" in a:
        e = _estado()
        reg = next((r for r in reversed(e["aplicadas"]) if not r.get("desfeita")), None)
        if reg:
            desfazer(reg, "pedido manual")
            _gravar(ESTADO, e)
    elif "--ligar" in a or "--desligar" in a:
        ligar = "--ligar" in a
        d = cfg()
        d["ligado"] = ligar
        if ligar and "--aplicar" in a:
            d["modo"] = "aplicar"
        _gravar(CONFIG, d)
        ok, msg = _tarefa(ligar)
        print(f"melhorador {'LIGADO' if ligar else 'DESLIGADO'} (modo {d.get('modo')}); tarefa {TAREFA}: "
              f"{'ok' if ok else msg}")
    else:  # status
        c, e = cfg(), _estado()
        print(f"ligado={c.get('ligado')} modo={c.get('modo')} | aplicadas={len(e['aplicadas'])} "
              f"(vigiando {sum(1 for r in e['aplicadas'] if r.get('vigiando'))}) | ideias de código="
              f"{len(e['ideias_codigo'])}")
        for m, papeis in e["modelos"].items():
            for p, q in papeis.items():
                print(f"  {m:42} {p:9} chamadas {q.get('chamadas')} ok {q.get('ok')} falhas {q.get('falhas')} "
                      f"propostas {q.get('propostas')} aprovadas {q.get('aprovadas')} mantidas {q.get('mantidas')} "
                      f"desfeitas {q.get('desfeitas')}")


if __name__ == "__main__":
    main(sys.argv[1:])
