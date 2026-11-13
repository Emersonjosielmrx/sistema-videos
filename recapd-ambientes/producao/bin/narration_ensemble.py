"""narration_ensemble.py — geração de narração por ENSEMBLE auto-melhorável.

Arquitetura (pedida pelo usuário, estilo n8n auto-tuning):
  1. GERA N candidatos de roteiro, cada um com um (modelo, prompt) diferente.
  2. AUDITOR (Claude, lê os balões das imagens) nota a fidelidade de cada candidato
     e produz o roteiro FINAL editado — locução por painel, fiel ao que cada painel
     mostra. Corrige o desalinhamento que o Gemini sozinho causa.
  3. PLACAR: registra a nota de cada (modelo, prompt) em narration_scoreboard.json.
  4. AUTO-MELHORIA: a cada AUDIT_EVERY auditorias, o pior prompt é reescrito pelo
     auditor (Claude) com base nos erros observados, e a prioridade passa pros
     melhores. Assim o sistema melhora sozinho com o tempo.

RESILIENTE: se o Claude cair (key expira em dias), cai pra Gemini-only usando o
melhor prompt do placar — o vídeo nunca deixa de ser gerado.
"""
import json
import os
import re
from pathlib import Path

import gemini_llm
import claude_client

PROJECT_DIR = Path(__file__).resolve().parent.parent
SCOREBOARD = PROJECT_DIR / "workspace" / "narration_scoreboard.json"
PROMPTS_FILE = PROJECT_DIR / "workspace" / "narration_prompts.json"
AUDIT_EVERY = int(os.environ.get("ENSEMBLE_AUDIT_EVERY", "5"))


# ── Prompts iniciais (semente). O auto-tuning reescreve os piores com o tempo. ──
_SEED_PROMPTS = {
    "fiel_balao": (
        "Você é narrador(a) BR de recap de manhwa. Para CADA painel, na ordem, gere "
        "UMA locução. REGRA CRÍTICA: a locução de um painel deve corresponder ao que "
        "AQUELE painel mostra e aos balões DAQUELE painel — nunca adiante nem atrase "
        "falas entre painéis. REGRA DE VOZ: se o painel tem fala/diálogo, é o "
        "PERSONAGEM que fala (1ª pessoa, a fala dele direto) — a MAIORIA das locuções "
        "deve ser de personagem. Use Narrador SÓ em painel de pura ação/cenário sem "
        "diálogo ou num momento-chave de virada. Identifique o personagem por nome ou "
        "rótulo estável (Rapaz/Garota/Velho) — nunca o genérico 'Personagem'. 8-40 "
        "palavras. NUNCA narre onomatopeias (DING DONG, POP) como fala — ação ou omita."
    ),
    "dramatico": (
        "Você é um narrador de recap viral de manhwa. Gere UMA locução por painel, "
        "na ordem exata. Cada locução reflete fielmente o conteúdo daquele painel "
        "específico (balões e ação). Tom dramático, ganchos, gírias BR. REGRA DE VOZ: "
        "painel com diálogo = o PERSONAGEM fala a própria fala (1ª pessoa); narrador é "
        "minoria, só cobre ação sem fala ou momento-chave. Personagem por nome/rótulo, "
        "nunca 'Personagem'. 8-40 palavras. Não invente "
        "falas que não estão no painel; não troque falas de painel."
    ),
    "conciso": (
        "Narrador BR objetivo de manhwa. UMA locução curta por painel, alinhada ao "
        "painel correspondente. REGRA DE VOZ: fala do balão = dita pelo PERSONAGEM "
        "daquele painel em 1ª pessoa (maioria das locuções); narrador só em ação sem "
        "diálogo. Sem onomatopeias como fala. Mantenha a ordem 1:1 com os painéis."
    ),
}

# modelos a usar como geradores (além do Claude). Gemini usa rotação interna.
# 2026-07-07: Gemini 2.5 bloqueia manhwa +18 (PROHIBITED_CONTENT). Só Claude funciona.
_GEN_MODELS = []  # gemini desativado — sempre bloqueia conteúdo manhwa


def _load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_prompts():
    p = _load_json(PROMPTS_FILE, None)
    if not p:
        p = dict(_SEED_PROMPTS)
        _save_json(PROMPTS_FILE, p)
    return p


def _scoreboard():
    return _load_json(SCOREBOARD, {"runs": 0, "entries": {}})


def _record(board, combo_key, nota):
    e = board["entries"].setdefault(combo_key, {"n": 0, "soma": 0.0, "media": 0.0})
    e["n"] += 1
    e["soma"] += nota
    e["media"] = round(e["soma"] / e["n"], 2)


def _parse_numbered(text, n):
    """Extrai n locuções de um texto numerado/linha-a-linha. Aceita 'persona|texto'
    ou 'P1: texto' ou '1. texto'."""
    if not text:
        return None
    linhas = []
    for ln in text.splitlines():
        ln = ln.strip()
        ln = re.sub(r"^[Pp]?\d+[\.\):\-]\s*", "", ln)
        if ln and not ln.startswith("#") and not ln.startswith("```"):
            linhas.append(ln)
    return linhas[:n] if len(linhas) >= n else (linhas or None)


def _gemini_candidate(images, prompt, n):
    sys = prompt + f"\n\nResponda APENAS as {n} locuções, uma por linha, no formato " \
                   "'persona|texto'. Exatamente {} linhas.".format(n)
    user = f"{n} painéis na ordem. Gere o roteiro."
    txt = gemini_llm.generate_from_images(images, user, system=sys,
                                          max_tokens=4096, max_attempts=8)
    return _parse_numbered(txt, n)


def _claude_candidate(images, prompt, n):
    if not claude_client.is_available():
        return None
    content = []
    for i, b in enumerate(images):
        content.append({"type": "text", "text": f"--- PAINEL {i+1} ---"})
        content.append(claude_client._img_block(b))
    content.append({"type": "text", "text":
        prompt + f"\n\nResponda APENAS as {n} locuções, uma por linha, formato "
        f"'persona|texto'. Exatamente {n} linhas, uma por painel na ordem."})
    txt = claude_client._post([{"role": "user", "content": content}],
                              max_tokens=4096, temperature=0.5)
    return _parse_numbered(txt, n)


def _strip_refusal(texto):
    """Remove a frase de recusa da IA que tenha vazado pro texto final, preservando
    a parte boa que vem antes (ex: 'O hall é maior. Não consigo ler a imagem...' →
    'O hall é maior.'). Se sobrar nada útil, devolve string vazia."""
    if not texto:
        return texto
    # acha o início de qualquer trecho de recusa e corta dali pra frente
    m = claude_client._REFUSAL_PATTERNS.search(texto)
    if not m:
        return texto
    # volta até o fim da frase anterior (. ! ?) pra não cortar no meio de palavra
    head = texto[:m.start()]
    corte = max(head.rfind('.'), head.rfind('!'), head.rfind('?'))
    limpo = head[:corte + 1].strip() if corte >= 0 else head.strip()
    return limpo


def _normalize(locs, n):
    """Garante n entradas no formato (persona, texto)."""
    out = []
    for item in (locs or []):
        if "|" in item:
            persona, texto = item.split("|", 1)
        else:
            persona, texto = "Narrador", item
        texto = _strip_refusal(texto.strip())
        out.append((persona.strip() or "Narrador", texto))
    while len(out) < n:
        out.append(("Narrador", "E a história continua..."))
    return out[:n]


def _as_nota(raw):
    """Extrai um número 0-10 de qualquer formato que o auditor devolva:
    número, string '8', ou dict {'nota':8} / {'candidato':0,'score':8}."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        m = re.search(r"\d+(?:\.\d+)?", raw)
        return float(m.group()) if m else 5.0
    if isinstance(raw, dict):
        for k in ("nota", "score", "fidelidade", "value", "n"):
            if k in raw and isinstance(raw[k], (int, float, str)):
                return _as_nota(raw[k])
        # primeiro valor numérico que achar
        for v in raw.values():
            if isinstance(v, (int, float)):
                return float(v)
    return 5.0


def _coverage_check(final_locs, balloons_per_panel):
    """Passo final (estilo n8n): garante que a locução de cada painel cobre as FALAS
    daquele painel. Conservador: só anexa diálogo SUBSTANCIAL (>=4 palavras reais)
    que ficou totalmente ausente — nunca onomatopeias (essas o clean_for_tts remove
    no TTS). Evita poluir a narração com ruído."""
    import difflib
    ONOMATO = re.compile(
        r"^(ding|dong|ding[\s-]?dong|pop|tada|tcharam|uh+|ah+|oh+|hai|ei|olá|"
        r"bang|boom|slam|beep|thud|tum|tec|clack|click|plim|toc|crash|woosh|whoosh|"
        r"haa+|hii+|nng+|ann+|eup|barf|baaa+rf)[\s\W]*$", re.IGNORECASE)
    out = []
    for i, (persona, texto) in enumerate(final_locs):
        balloons = balloons_per_panel[i] if i < len(balloons_per_panel) else []
        faltando = []
        tnorm = re.sub(r"[^\wà-ÿ ]", " ", texto.lower())
        for b in balloons:
            bclean = re.sub(r"\[n\]", "", b).strip()
            # ignora recusa da IA que tenha escapado (nunca vira narração)
            if claude_client.is_refusal(bclean):
                continue
            # ignora balão curto ou onomatopeia
            palavras = [w for w in re.sub(r"[^\wà-ÿ ]", " ", bclean.lower()).split()
                        if len(w) > 2]
            if len(palavras) < 4 or ONOMATO.match(bclean):
                continue
            bnorm = " ".join(palavras)
            hit = sum(1 for w in palavras if w in tnorm)
            ratio = difflib.SequenceMatcher(None, bnorm, tnorm).ratio()
            # considera coberto se metade das palavras significativas já aparecem
            if hit < len(palavras) * 0.5 and ratio < 0.4:
                faltando.append(bclean)
        if faltando:
            extra = " ".join(faltando)
            extra = extra[0].upper() + extra[1:].lower() if extra else extra
            texto = texto.rstrip(" .!?") + ". " + extra
        out.append((persona, texto))
    return out


BATCH_SIZE = int(os.environ.get("ENSEMBLE_BATCH", "18"))


def gerar_narracao_ensemble(titulo, panel_paths, jpeg_loader, narrator_gender="F", _lote=False):
    """Gera o roteiro final alinhado. Retorna lista de dicts
    {persona, gender, text, cena} alinhada 1:1 com panel_paths, ou None se tudo falhar.

    jpeg_loader: função path->bytes (reusa _jpeg_bytes do pipeline).

    LOTES (2026-07-03): enviar TODOS os painéis numa chamada só estourava o max_tokens →
    o modelo truncava a resposta, o _normalize preenchia o resto com "E a história continua..."
    (loop) E o desalinhamento deslocava as falas desde o início. Agora processa em lotes de
    BATCH_SIZE painéis; cada lote passa pelo ensemble completo (candidatos+auditoria) e concatena,
    mantendo o alinhamento 1:1. _lote=True é a chamada interna por lote (não re-divide)."""
    n = len(panel_paths)
    # divide em lotes p/ não truncar (só na chamada externa)
    if not _lote and n > BATCH_SIZE:
        ng = "M" if (narrator_gender or "F").upper() == "M" else "F"
        todas = []
        for start in range(0, n, BATCH_SIZE):
            chunk = panel_paths[start:start + BATCH_SIZE]
            print(f"  [ensemble] lote {start+1}-{start+len(chunk)}/{n}", flush=True)
            parte = gerar_narracao_ensemble(titulo, chunk, jpeg_loader, narrator_gender, _lote=True)
            if parte is None or len(parte) != len(chunk):
                # lote falhou → placeholder SÓ nesse lote, preservando alinhamento dos demais
                parte = [{"persona": "Narrador", "gender": ng,
                          "text": "E a história continua...", "cena": ""} for _ in chunk]
            todas.extend(parte)
        return todas[:n]

    images = [jpeg_loader(p) for p in panel_paths]
    prompts = _get_prompts()
    board = _scoreboard()

    # 1. GERA candidatos: cada (modelo, prompt) é um candidato
    candidatos = []   # lista de (combo_key, [(persona,texto),...])
    for pname, ptext in prompts.items():
        if _GEN_MODELS:
            g = _gemini_candidate(images, ptext, n)
            if g:
                candidatos.append((f"gemini::{pname}", _normalize(g, n)))
        c = _claude_candidate(images, ptext, n)
        if c:
            candidatos.append((f"claude::{pname}", _normalize(c, n)))

    if not candidatos:
        print("  [ensemble] nenhum candidato gerado (quota/credenciais?)", flush=True)
        return None

    # 1b. VERDADE DOS PAINÉIS: lê os balões de cada painel (Haiku, leve) e faz MERGE
    # de múltiplas leituras — assim nenhum balão se perde. É a base da auditoria.
    balloons_per_panel = []
    if claude_client.is_available():
        for b in images:
            r1 = claude_client.read_balloons(b)
            # 2ª leitura p/ merge (pega balões que a 1ª perdeu)
            r2 = claude_client.read_balloons(b)
            merged = claude_client.merge_balloons([r1, r2])
            balloons_per_panel.append(merged)
        got = sum(1 for x in balloons_per_panel if x)
        print(f"  [ensemble] verdade lida: {got}/{n} painéis com balões", flush=True)

    # 2. AUDITORIA por TEXTO (verdade + candidatos) — leve, sem reenviar imagens
    final_locs = None
    if claude_client.is_available() and balloons_per_panel:
        cand_lists = [["{}|{}".format(p, t) for p, t in lst] for _, lst in candidatos]
        audit = claude_client.audit_with_truth(balloons_per_panel, cand_lists)
        if audit and audit.get("locucoes_finais"):
            final_locs = _normalize(audit["locucoes_finais"], n)
            notas = audit.get("notas", [])
            for idx, (combo_key, _) in enumerate(candidatos):
                raw = notas[idx] if idx < len(notas) else 5
                _record(board, combo_key, _as_nota(raw))
            print(f"  [ensemble] auditado(verdade): notas={notas} melhor={audit.get('melhor_indice')}", flush=True)
            # 2b. CHECK DE COBERTURA: garante que cada locução final menciona o
            # conteúdo dos balões daquele painel; senão, anexa o que faltou.
            final_locs = _coverage_check(final_locs, balloons_per_panel)

    # 3. Sem auditor: usa o candidato do melhor combo no placar (ou o 1º)
    if final_locs is None:
        def media(ck):
            return board["entries"].get(ck, {}).get("media", 5.0)
        candidatos.sort(key=lambda c: media(c[0]), reverse=True)
        final_locs = candidatos[0][1]
        print(f"  [ensemble] sem auditor — usando melhor do placar: {candidatos[0][0]}", flush=True)

    # 4. AUTO-MELHORIA periódica
    board["runs"] = board.get("runs", 0) + 1
    if board["runs"] % AUDIT_EVERY == 0:
        _auto_tune(board, prompts, images)
    _save_json(SCOREBOARD, board)

    ng = "M" if (narrator_gender or "F").upper() == "M" else "F"
    locucoes = []
    for persona, texto in final_locs:
        pl = persona.lower()
        gender = ng if pl in ("narrador", "narradora", "narrator") else None
        locucoes.append({"persona": persona, "gender": gender, "text": texto, "cena": ""})
    return locucoes


def _auto_tune(board, prompts, images):
    """Reescreve o PIOR prompt usando o Claude, com base na média do placar.
    O melhor prompt vira referência; o pior é regenerado pra tentar superá-lo."""
    if not claude_client.is_available():
        return
    # agrupa médias por nome de prompt (ignora o modelo)
    by_prompt = {}
    for combo, e in board["entries"].items():
        if "::" in combo:
            _, pname = combo.split("::", 1)
            by_prompt.setdefault(pname, []).append(e["media"])
    if len(by_prompt) < 2:
        return
    medias = {p: sum(v) / len(v) for p, v in by_prompt.items()}
    pior = min(medias, key=medias.get)
    melhor = max(medias, key=medias.get)
    if medias[pior] >= medias[melhor] - 0.5:
        return  # diferença pequena, não mexe
    novo = claude_client.generate_text(
        prompt=(f"Este é o MELHOR prompt de narração de manhwa (média {medias[melhor]:.1f}/10):\n"
                f"\"\"\"{prompts.get(melhor,'')}\"\"\"\n\n"
                f"Este é o PIOR (média {medias[pior]:.1f}/10):\n"
                f"\"\"\"{prompts.get(pior,'')}\"\"\"\n\n"
                "Reescreva o PIOR para corrigir o que o faz errar (provavelmente "
                "desalinhar falas entre painéis ou narrar onomatopeias). Mantenha o "
                "objetivo de UMA locução fiel por painel. Responda APENAS o novo prompt."),
        max_tokens=600, temperature=0.6,
        model=claude_client.strong_model())  # Opus só aqui: reescrita de prompt é tarefa "cara"
    if novo and len(novo) > 40:
        prompts[pior] = novo.strip()
        _save_json(PROMPTS_FILE, prompts)
        # zera o histórico do prompt reescrito pra reavaliar do zero
        for combo in list(board["entries"]):
            if combo.endswith("::" + pior):
                board["entries"][combo] = {"n": 0, "soma": 0.0, "media": 5.0}
        print(f"  [ensemble] AUTO-TUNE: prompt '{pior}' reescrito (era {medias[pior]:.1f}, "
              f"melhor '{melhor}' {medias[melhor]:.1f})", flush=True)
