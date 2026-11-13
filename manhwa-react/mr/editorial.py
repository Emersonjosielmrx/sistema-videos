"""Decisoes editoriais via LLM (proxy Opus/Sonnet ou Claude Code CLI): qualidade, canal, janela, remocoes, gancho, titulo, tags."""
from .common import log, fmt_t
from .llm import ask_json

MOODS = ("tense_dramatic", "sad_emotional", "romantic_sexy", "funny_lighthearted", "neutral_chill", "calm_chill")


def claude_json(cfg, instructions, payload, timeout=None):
    return ask_json(cfg, instructions, payload, timeout=timeout)


def transcript_text(segments):
    lines = []
    for i, s in enumerate(segments):
        who = {"creator": "CRIADOR", "content": "CONTEUDO", "unknown": "?"}.get(s.get("speaker", "unknown"), "?")
        lines.append(f"#{i} [{fmt_t(s['start'])}-{fmt_t(s['end'])}] {who}: {s['text']}")
    return "\n".join(lines)


ANALYSIS_INSTRUCTIONS = """Voce e o editor-chefe de uma rede de canais de Shorts de react em portugues do Brasil. Voce recebera a transcricao de uma
gravacao (webcam do criador + video reagido). Linhas CRIADOR = fala do criador (vai virar legenda); linhas CONTEUDO = audio do video
reagido (so contexto). Duracao total: {dur:.1f}s. Duracao maxima de um Short: {maxdur:.0f}s.
Silencios longos (candidatos a divisao entre reacts diferentes): {gaps}.
{base}
Canais disponiveis (slug - nicho):
{channels}

Responda SOMENTE com um JSON valido, sem comentarios, neste formato:
{{
 "usable": true,
 "score": 7,
 "reason": "por que o video funciona ou nao (1 frase)",
 "topic": "assunto em poucas palavras",
 "channel": "slug do canal mais adequado",
 "work": "nome curto da obra/fonte reagida para mostrar na tela (ex: RE:ZERO, MALCOLM, MOTORHOME SOLAR) ou null",
 "parts": [
   {{"start": 0.0, "end": {dur:.1f},
     "hook": "GANCHO EM CAIXA ALTA, 3 a 7 palavras, curioso/impactante",
     "title": "titulo viral ate 70 caracteres, emoji, terminando com 2 hashtags (#shorts + tema)",
     "description": "3 a 5 linhas: o que acontece, pergunta pro publico, chamada pra seguir; depois uma linha com 10 a 15 hashtags",
     "hashtags": ["#shorts", "#react", "#tema"],
     "tags": ["react", "tema", "obra", "personagem", "..."],
     "keywords": [{{"t": 12.3, "text": "ABSURDO", "emoji": "😱"}}],
     "reactions": [{{"t": 20.1, "type": "laugh|shock|love|angry|question|hype|cringe"}}],
     "memes": [{{"t": 33.0, "id": 12}}],
     "cta": "frase curta de chamada final (ate 5 palavras)",
     "pinned_comment": "comentario para fixar: pergunta curta que gera resposta (1 frase)",
     "title_alternatives": ["titulo alternativo 1", "titulo alternativo 2"],
     "mood": "tense_dramatic|sad_emotional|romantic_sexy|funny_lighthearted|neutral_chill|calm_chill",
     "music": true}}
 ],
 "remove": [{{"start": 0.0, "end": 0.0, "why": "motivo"}}],
 "speakers": {{"12": "content"}}
}}
Regras:
- "channel": escolha pelo tema do video reagido; o nicho do canal tem que combinar de verdade (anime nunca vai para canal de financas,
  games ou forja). Se encaixar bem em mais de um canal, prefira o de fila menor (a rede precisa de 1 video bom por dia em cada canal).
  Na duvida, o canal de curiosidades/inventos.
{regra_partes}
- "remove": trechos do CRIADOR que atrapalham: frases repetidas (retake), erros, "deixa eu ver aqui", testes de gravacao, comentarios sem sentido. Nunca remova CONTEUDO. Pode ser vazio.
- "keywords": 1 a 4 palavras de impacto ditas pelo criador (tempo exato do inicio da palavra) para aparecerem grandes na tela, cada uma com 1 emoji que combine. Pode ser vazio.
- "memes": 0 a 2 memes do CATALOGO DE MEMES (pelo id) que combinem com um momento exato da fala do CRIADOR. So quando encaixar de verdade; senao [].
- "reactions": 0 a 3 momentos de reacao forte do CRIADOR (risada, choque, amor/fofura, raiva, duvida, hype, vergonha alheia) com o tempo exato; so quando evidente na transcricao.
- "pinned_comment": pergunta curta para fixar nos comentarios (gera engajamento).
- "title_alternatives": 2 titulos alternativos no mesmo padrao (para teste A/B).
- Seguranca de monetizacao: no titulo, descricao e tags evite palavras que derrubam anuncios (matar, morte, morrer, sexo, nu, droga, arma, suicidio, sangue);
  use eufemismos (ex.: "elimina", "se vai", "+18").
- "tags": 12 a 20 tags do YouTube (palavras ou frases curtas, SEM #): obra, personagens, genero, "react", termos de busca em portugues.
- "mood": clima da trilha de fundo. "music": false se o video reagido ja tem musica/narracao continua que brigaria com a trilha; true se e mais fala do criador.
- "speakers": a etiqueta CRIADOR/CONTEUDO vem da leitura labial e pode errar (ex.: criador rindo). Pelo TEXTO, corrija os segmentos
  errados: narracao da historia em 3a pessoa / dialogo de personagens / texto que continua a linha CONTEUDO anterior = "content";
  opiniao, comentario, "eu acho", "vamos ver", reacao pessoal = "creator". Liste SO os indices (#) que precisam mudar; se nenhum, {{}}.
- "usable"=false e score<5 se o video nao presta: teste de gravacao ("testando", "mano mano mano"), sem reacao, inaudivel, sem sentido.
- Nao invente fatos; use o que esta na transcricao."""


REGRA_PARTES_CURTA = """- "parts": se a gravacao tiver reacts de videos DIFERENTES separados por silencio longo, crie uma parte por react (use os silencios como fronteira).
  Se a gravacao (ou uma parte) passar de {maxdur:.0f}s, escolha start/end como a MELHOR janela continua de ate {maxdur:.0f}s: comece logo antes de uma fala
  do criador e termine logo depois de uma reacao forte. Nunca comece no meio de uma frase do criador."""

REGRA_PARTES_DESTAQUES = """- "parts": esta e uma gravacao LONGA ({dur_min:.0f} min, react de um video inteiro). Escolha de {nmin} a {nmax} DESTAQUES que virem Shorts
  INDEPENDENTES: os melhores momentos do CRIADOR (reacao forte, risada, choque, revolta, hype, opiniao engracada ou polemica, previsao que gera
  comentario). Cada destaque: 25 a {maxdur:.0f}s, sem sobreposicao entre eles; comece 2 a 6s antes, na frase do CONTEUDO que da o contexto, e termine
  logo depois da reacao. Precisa se entender sozinho, sem ter visto o resto. Ordene do melhor para o pior. Cada destaque tem hook, titulo, descricao
  e tags proprios (nunca repita titulo nem hook). Se houver poucos momentos bons, entregue menos (minimo 1)."""


def _fila_por_canal(cfg):
    """Quantos Shorts prontos (nao postados) cada canal tem em shorts/ e cortes/."""
    from pathlib import Path
    out = {}
    for k in ("ready", "ready_cortes"):
        pasta = cfg["paths"].get(k)
        if pasta and Path(pasta).exists():
            for pj in Path(pasta).glob("*/*.postar.json"):
                out[pj.parent.name] = out.get(pj.parent.name, 0) + 1
    return out


def analyze(cfg, segments, duration, gaps, base=None):
    chans = cfg.get("channels") or [{"slug": "default", "name": cfg["channel"]["name"], "niche": cfg["channel"]["niche"]}]
    fila = _fila_por_canal(cfg)
    ch_txt = "\n".join(f"- {c['slug']} - {c.get('niche', '')} (fila: {fila.get(c['slug'], 0)} prontos)" for c in chans)
    gaps_txt = ", ".join(f"{fmt_t(a)}-{fmt_t(b)}" for a, b in gaps) or "nenhum"
    E = cfg["editorial"]
    maxdur = float(cfg["output"].get("max_duration", 90))
    destaques = duration > float(E.get("long_threshold", 240))
    if destaques:
        regra = REGRA_PARTES_DESTAQUES.format(dur_min=duration / 60, nmin=int(E.get("highlights_min", 3)),
                                              nmax=int(E.get("highlights_max", 8)), maxdur=maxdur)
    else:
        regra = REGRA_PARTES_CURTA.format(maxdur=maxdur)
    base_txt = ""
    if base:
        base_txt = (f"Video reagido (identificado pela narracao): \"{base.get('titulo')}\" do canal {base.get('canal')}. "
                    "Use para \"work\" (nome curto da obra) e para as tags. As etiquetas CONTEUDO ja vem da comparacao com a "
                    "narracao original (confiaveis).\n")
    if (cfg.get("forcar") or {}).get("contexto"):  # ex.: aula do dono (mr/temas.py)
        base_txt += cfg["forcar"]["contexto"] + "\n"
    instr = ANALYSIS_INSTRUCTIONS.format(dur=duration, maxdur=maxdur, gaps=gaps_txt, channels=ch_txt, regra_partes=regra, base=base_txt)
    payload = "TRANSCRICAO:\n" + transcript_text(segments)
    meme_text = ""
    try:
        from .memes import catalog_for_prompt
        if cfg["overlays"].get("memes"):
            _, meme_text = catalog_for_prompt(cfg)
    except Exception:  # noqa: BLE001
        meme_text = ""
    if meme_text:
        payload += "\n\nCATALOGO DE MEMES (id: descricao):\n" + meme_text
    data = claude_json(cfg, instr, payload)
    if not data or "parts" not in data:
        return None
    slugs = {c["slug"] for c in chans}
    if data.get("channel") not in slugs:
        data["channel"] = cfg.get("default_channel") or chans[0]["slug"]
    w = data.get("work")
    data["work"] = (str(w).strip()[:28] if w else None)
    parts = []
    for p in data.get("parts", []):
        try:
            a, b = float(p.get("start", 0)), float(p.get("end", duration))
        except Exception:
            continue
        a, b = max(0.0, a), min(duration, b)
        if b - a < 3:
            continue
        p["start"], p["end"] = a, b
        p["keywords"] = [k for k in p.get("keywords", []) if isinstance(k, dict) and "t" in k and k.get("text")]
        rx = []
        for r in p.get("reactions", []) or []:
            try:
                tt = float(r.get("t"))
            except Exception:
                continue
            ty = str(r.get("type", "")).lower()
            if ty in ("laugh", "shock", "love", "angry", "question", "hype", "cringe") and 0 <= tt <= duration:
                rx.append({"t": tt, "type": ty})
        p["reactions"] = rx[:3]
        mm = []
        for m in p.get("memes", []) or []:
            try:
                mm.append({"t": float(m["t"]), "id": int(m["id"])})
            except Exception:
                continue
        p["memes"] = mm[:3]
        p["pinned_comment"] = str(p.get("pinned_comment") or "").strip()[:200]
        p["title_alternatives"] = [str(x).strip()[:100] for x in (p.get("title_alternatives") or []) if str(x).strip()][:3]
        p["hashtags"] = [h if str(h).startswith("#") else "#" + str(h) for h in (p.get("hashtags") or []) if str(h).strip()]
        p["tags"] = [str(t).strip().lstrip("#") for t in (p.get("tags") or []) if str(t).strip()]
        if not p["tags"]:
            p["tags"] = [h.lstrip("#") for h in p["hashtags"]]
        if p.get("mood") not in MOODS:
            p["mood"] = "neutral_chill"
        p["music"] = bool(p.get("music", True))
        parts.append(p)
    if not parts:
        parts = [{"start": 0.0, "end": duration, "hook": "", "title": "", "description": "", "hashtags": [], "tags": [], "keywords": [], "cta": "",
                  "mood": "neutral_chill", "music": True}]
    data["parts"] = parts
    rem = []
    for r in data.get("remove", []) or []:
        try:
            a, b = float(r["start"]), float(r["end"])
            if 0 <= a < b <= duration and b - a <= 25:
                rem.append({"start": a, "end": b, "why": r.get("why", "")})
        except Exception:
            pass
    data["remove"] = rem
    spk = {}
    for k, v in (data.get("speakers") or {}).items():
        try:
            i = int(str(k).lstrip("#"))
        except Exception:
            continue
        if v in ("creator", "content") and 0 <= i < len(segments):
            spk[str(i)] = v
    data["speakers"] = spk
    data["highlights"] = destaques
    return data


def apply_speakers(ed, segments, words):
    """Aplica as correcoes de quem fala vindas do editorial aos segmentos e suas palavras."""
    n = 0
    for k, v in (ed.get("speakers") or {}).items():
        s = segments[int(k)]
        if s.get("speaker") == v:
            continue
        s["speaker"] = v
        for w in words:
            if s["start"] - 0.01 <= w["s"] <= s["end"] + 0.01:
                w["speaker"] = v
        n += 1
    if n:
        log(f"editorial: {n} segmento(s) com falante corrigido")
    return n


FIX_INSTRUCTIONS = """Voce corrige erros de transcricao automatica (Whisper) em portugues do Brasil. Contexto: criador reagindo a "{topic}".
Receba uma lista numerada de palavras faladas pelo criador. Devolva SOMENTE um JSON: {{"fixes": {{"indice": "palavra corrigida", ...}}}}
contendo apenas os indices que precisam de correcao (palavras erradas, nomes, termos tecnicos). Mantenha uma palavra por indice (pode usar hifen se precisar juntar).
Nao mude palavras corretas, nao adicione nem remova indices. Se nada precisar de correcao devolva {{"fixes": {{}}}}."""


def fix_words(cfg, words, topic=""):
    idx = [i for i, w in enumerate(words) if w.get("speaker") != "content"]
    if not idx:
        return 0
    payload = "\n".join(f"{i}: {words[i]['w']}" for i in idx)
    data = claude_json(cfg, FIX_INSTRUCTIONS.format(topic=topic or "video"), payload, timeout=180)
    if not data or not isinstance(data.get("fixes"), dict):
        return 0
    n = 0
    for k, v in data["fixes"].items():
        try:
            i = int(k)
        except Exception:
            continue
        if 0 <= i < len(words) and isinstance(v, str) and v.strip() and words[i].get("speaker") != "content":
            words[i]["w_orig"] = words[i]["w"]
            words[i]["w"] = v.strip()
            n += 1
    log(f"transcricao: {n} palavras corrigidas pelo editorial")
    return n


def fallback_meta(cfg, segments, part):
    creator = [s["text"] for s in segments if s.get("speaker") != "content" and part["start"] <= s["start"] <= part["end"]]
    txt = " ".join(creator).strip()
    first = " ".join(txt.split()[:6]).upper() if txt else "OLHA ISSO"
    name = cfg["channel"]["name"]
    return {"hook": first, "title": f"React: {first.title()} #shorts #react", "description": f"{txt[:200]}\n\n#shorts #react #{name.lower()}",
            "hashtags": ["#shorts", "#react", f"#{name.lower()}"], "tags": ["react", "shorts", name.lower(), "manhwa", "anime"],
            "keywords": [], "cta": cfg["overlays"].get("cta_text", ""), "mood": "neutral_chill", "music": True}
