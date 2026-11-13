"""claude_client.py — cliente Claude via base URL do settings (proxy kr/).

Usado como AUDITOR de fidelidade da narração às imagens e como gerador alternativo
no ensemble. RESILIENTE: a API key do proxy expira em dias; qualquer falha retorna
None em vez de explodir, pra o pipeline seguir só com Gemini.

Lê credenciais de settings.json (env.ANTHROPIC_*). Não usa SDK — urllib puro pra
não depender de versão de pacote.
"""
import base64
import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

# ─── GATEWAY OmniRoute (substitui o Claude Haiku/Anthropic) ──────────────────
# Endpoint próprio compatível com a API Anthropic (/v1/messages), com fila de
# fallback automática entre modelos. Todo o tráfego de "Haiku" passa por aqui —
# não chamamos mais api.anthropic.com. Override por secrets/omniroute.json
# (base_url/api_key/model) ou pelas envs OMNIROUTE_* / GATEWAY_*.
_GATEWAY_DEFAULT = {
    "base": "http://157.173.207.22:20128",
    "key": "<SEGREDO_REMOVIDO>",
    "model": "antigravity/gemini-2.5-flash",  # substitui haiku (rápido/barato)
    "fast": "antigravity/gemini-2.5-flash",
}
_OMNIROUTE_JSON = Path(__file__).resolve().parent.parent / "secrets" / "omniroute.json"

_cfg = None
_disabled = False  # vira True após falha de auth — para de tentar nesta sessão


def _load_cfg():
    global _cfg
    if _cfg is not None:
        return _cfg
    cfg = dict(_GATEWAY_DEFAULT)
    # 1) override por arquivo secrets/omniroute.json (não versionado)
    try:
        if _OMNIROUTE_JSON.exists():
            j = json.loads(_OMNIROUTE_JSON.read_text(encoding="utf-8"))
            if j.get("base_url"):
                cfg["base"] = j["base_url"].rstrip("/")
            if j.get("api_key"):
                cfg["key"] = j["api_key"]
            if j.get("model"):
                cfg["model"] = cfg["fast"] = j["model"]
    except Exception:
        pass
    # 2) override por env (tem prioridade — facilita trocar sem editar arquivo)
    base = os.environ.get("OMNIROUTE_BASE_URL") or os.environ.get("GATEWAY_BASE_URL")
    key = os.environ.get("OMNIROUTE_API_KEY") or os.environ.get("GATEWAY_API_KEY")
    model = os.environ.get("OMNIROUTE_MODEL") or os.environ.get("GATEWAY_MODEL")
    if base:
        cfg["base"] = base.rstrip("/")
    if key:
        cfg["key"] = key
    if model:
        cfg["model"] = cfg["fast"] = model
    cfg["base"] = cfg["base"].rstrip("/")
    _cfg = cfg if (cfg.get("base") and cfg.get("key")) else {}
    return _cfg


def fast_model():
    cfg = _load_cfg()
    return cfg.get("fast") if cfg else None


def strong_model():
    cfg = _load_cfg()
    return cfg.get("model") if cfg else None


def _extract_json(text):
    """Extrai o primeiro objeto JSON de um texto, mesmo embrulhado em prosa ou
    ```fences```. Retorna o dict ou None."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?\s*", "", text.strip())
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    # acha o trecho entre a primeira { e a última } balanceada
    start = t.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                frag = t[start:i + 1]
                try:
                    return json.loads(frag)
                except Exception:
                    return None
    return None


def is_available():
    """True se há credencial e ainda não falhou auth nesta sessão."""
    return bool(_load_cfg()) and not _disabled


def _post(messages, max_tokens=1024, temperature=0.3, model=None, timeout=90,
          max_retries=3):
    """Chama /v1/messages. Retorna texto ou None em falha. Marca _disabled em 401/403."""
    global _disabled
    cfg = _load_cfg()
    if not cfg or _disabled:
        return None
    body = {
        "model": model or cfg["model"],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "stream": True,
    }
    data = json.dumps(body).encode("utf-8")
    delay = 3.0
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                cfg["base"] + "/v1/messages", data=data,
                headers={"content-type": "application/json",
                         "x-api-key": cfg["key"],
                         "anthropic-version": "2023-06-01"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                # O gateway OmniRoute responde SEMPRE em streaming (SSE):
                # linhas "data: {json}". Ler o corpo inteiro com json.loads
                # quebra ("Expecting value char 0") pois começa com "event:".
                full_text = ""
                for line in r:
                    line = line.decode("utf-8", "ignore").strip()
                    if line.startswith("data:"):
                        part = line[5:].strip()
                        if part == "[DONE]":
                            break
                        try:
                            d = json.loads(part)
                        except Exception:
                            continue
                        if d.get("type") == "content_block_delta":
                            full_text += d.get("delta", {}).get("text", "")
            return full_text.strip() or None
        except urllib.error.HTTPError as e:
            code = e.code
            msg = ""
            try:
                msg = e.read().decode("utf-8", "ignore")[:200]
            except Exception:
                pass
            if code in (401, 403):
                # key expirou/inválida — desliga Claude pra esta sessão
                _disabled = True
                print(f"  [claude] auth falhou ({code}) — Claude DESATIVADO nesta sessão. {msg}", flush=True)
                return None
            if code in (429, 500, 502, 503, 529) and attempt < max_retries - 1:
                print(f"  [claude] {code} (tent {attempt+1}/{max_retries}), aguardando {delay:.0f}s", flush=True)
                time.sleep(delay); delay = min(delay * 1.8, 30)
                continue
            print(f"  [claude] HTTP {code}: {msg}", flush=True)
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay); delay = min(delay * 1.8, 30)
                continue
            print(f"  [claude] erro {type(e).__name__}: {str(e)[:120]}", flush=True)
            return None
    return None


def generate_text(prompt, system=None, max_tokens=2048, temperature=0.4, model=None):
    content = prompt if system is None else f"{system}\n\n{prompt}"
    return _post([{"role": "user", "content": content}],
                 max_tokens=max_tokens, temperature=temperature, model=model)


def _img_block(image_bytes, mime="image/jpeg"):
    return {"type": "image", "source": {"type": "base64", "media_type": mime,
            "data": base64.b64encode(image_bytes).decode("ascii")}}


# Frases de RECUSA/ERRO da IA (pt+en) que NÃO são balões e jamais devem virar
# narração. Quando a leitura de balões devolve isso, descartamos e tentamos de novo.
_REFUSAL_PATTERNS = re.compile(
    r"(não consigo ler|nao consigo ler|não posso (ler|transcrever)|nao posso (ler|transcrever)|"
    r"clareza suficiente|resolução (e|do|não|nao)|resolucao (e|do)|imagem fornecida|"
    r"qualidade (da|de) (imagem|resolução)|poderia fornecer|forneça uma imagem|"
    r"i can see this is|i'?m (unable|having difficulty)|i am unable|i can'?t (read|make out|transcribe)|"
    r"unable to (read|transcribe|make out)|difficulty reading|the resolution (and|makes|is)|"
    r"too (blurry|low|small) to|cannot (read|make out|clearly)|i need to be careful|"
    r"copyrighted material|rather than transcrib|provide a (clearer|higher)|"
    r"hard to (distinguish|read|make out)|not clear enough)",
    re.IGNORECASE)


def is_refusal(text):
    """True se o texto é uma recusa/erro da IA (não conteúdo útil).
    Reusável: qualquer chamada de visão pode validar a resposta com isto."""
    if not text:
        return False
    return bool(_REFUSAL_PATTERNS.search(text))


def read_balloons(image_bytes, mime="image/jpeg", max_attempts=3):
    """Retorna o texto dos balões de fala de UM painel, em ordem, ou '' em falha.
    É o núcleo da auditoria: o que ESTE painel realmente diz.

    Se a IA devolver uma RECUSA/erro ('não consigo ler', 'i'm unable to read'...),
    descarta e tenta de novo (até max_attempts) — esse texto nunca pode virar
    narração. Se todas as tentativas recusarem, retorna '' (painel sem balões)."""
    content = [_img_block(image_bytes, mime),
               {"type": "text", "text":
                "Liste APENAS o texto dentro dos balões de fala deste painel de manhwa, "
                "um por linha, de cima para baixo. Se for narração/legenda solta, marque "
                "com [N]. Se não houver texto, responda exatamente 'SEM TEXTO'. "
                "Não comente, não explique, não justifique, não numere, só o texto. "
                "NUNCA escreva frases como 'não consigo ler' ou 'I can't read' — "
                "se não der pra ler, responda só 'SEM TEXTO'."}]
    for attempt in range(max_attempts):
        out = _post([{"role": "user", "content": content}], max_tokens=400,
                    temperature=0.0 if attempt == 0 else 0.3,
                    model=fast_model()) or ""
        if not is_refusal(out):
            return out
        print(f"  [balloons] recusa da IA (tent {attempt+1}/{max_attempts}), refazendo: {out[:60]}...", flush=True)
    return ""  # todas recusaram → painel tratado como sem balões


def _balloon_lines(text):
    """Quebra a resposta de read_balloons em linhas limpas (sem 'SEM TEXTO'
    nem frases de recusa da IA que tenham escapado)."""
    if not text or text.strip().upper().startswith("SEM TEXTO"):
        return []
    out = []
    for ln in text.splitlines():
        ln = ln.strip()
        ln = re.sub(r"^[\-\*\d\.\)]+\s*", "", ln)
        if ln and ln.upper() != "SEM TEXTO" and not is_refusal(ln):
            out.append(ln)
    return out


def _norm(s):
    """Normaliza p/ comparar balões: minúsculo, sem pontuação/acentos repetidos/espaços."""
    s = re.sub(r"\[n\]", "", s.lower())
    s = re.sub(r"[^\wà-ÿ ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def merge_balloons(readers_outputs):
    """Recebe lista de saídas de leitores (cada uma é o texto bruto de read_balloons
    OU equivalente de outro modelo) para UM painel. UNE os balões: mantém a ordem do
    leitor que viu mais balões e ACRESCENTA balões que outros viram e ele não (dedup
    por similaridade). Assim, se o leitor A viu balões 1,3,5 e B viu 1,2,4, o resultado
    tem 1,2,3,4,5. Retorna lista de strings (balões) na ordem mais completa."""
    import difflib
    lists = [_balloon_lines(o) for o in readers_outputs if o]
    lists = [l for l in lists if l]
    if not lists:
        return []
    # base = leitor que viu mais balões
    base = max(lists, key=len)[:]
    base_norm = [_norm(x) for x in base]
    for lst in lists:
        for item in lst:
            ni = _norm(item)
            if not ni:
                continue
            # já presente (igual ou muito parecido)?
            dup = any(ni == bn or difflib.SequenceMatcher(None, ni, bn).ratio() > 0.8
                      for bn in base_norm)
            if not dup:
                base.append(item)
                base_norm.append(ni)
    return base


def audit_narration(image_bytes_list, candidatos, mime="image/jpeg",
                    max_tokens=4096):
    """Recebe os painéis (imagens) e N roteiros candidatos (cada um é lista de
    strings, uma locução por painel). Retorna dict:
      {"melhor_indice": int, "locucoes_finais": [str,...], "notas": [int,...]}
    onde locucoes_finais é o roteiro editado/escolhido mais fiel às imagens, e
    notas dá uma nota 0-10 de fidelidade pra CADA candidato (pra alimentar o placar).
    Retorna None se Claude indisponível."""
    if not is_available():
        return None
    content = []
    for i, b in enumerate(image_bytes_list):
        content.append({"type": "text", "text": f"--- PAINEL {i+1} ---"})
        content.append(_img_block(b, mime))
    cand_txt = []
    for ci, cand in enumerate(candidatos):
        linhas = "\n".join(f"  P{j+1}: {t}" for j, t in enumerate(cand))
        cand_txt.append(f"### CANDIDATO {ci} ###\n{linhas}")
    instr = (
        "Você é auditor de roteiros de narração de manhwa. Acima estão os PAINÉIS "
        "(imagens, em ordem) e abaixo ROTEIROS CANDIDATOS — cada um tem UMA locução "
        "por painel.\n\n" + "\n\n".join(cand_txt) + "\n\n"
        "Tarefa:\n"
        "1. Para CADA candidato, dê uma nota 0-10 de FIDELIDADE: a locução de cada "
        "painel corresponde ao que aquele painel mostra/diz? Penalize falas trocadas "
        "de painel, balões ignorados, ou texto inventado.\n"
        "2. Produza o ROTEIRO FINAL: uma locução por painel, na ordem, escolhendo "
        "do melhor candidato e CORRIGINDO onde algum errou (a fala deve bater com o "
        "balão/ação DAQUELE painel). Mantenha tom de recap dramático, 8-40 palavras.\n"
        "3. Cada locução começa com 'persona:' (Narrador ou nome do personagem).\n\n"
        "Responda em JSON estrito:\n"
        '{"notas":[n0,n1,...],"melhor_indice":i,"locucoes_finais":'
        '["persona|texto","persona|texto",...]}'
        f"\nO total de locucoes_finais DEVE ser exatamente {len(image_bytes_list)}."
    )
    content.append({"type": "text", "text": instr})
    out = _post([{"role": "user", "content": content}], max_tokens=max_tokens,
                temperature=0.2, model=fast_model())
    if not out:
        return None
    d = _extract_json(out)
    if d is None:
        print("  [claude audit] JSON inválido", flush=True)
    return d


def audit_with_truth(balloons_per_panel, candidatos, max_tokens=8192):
    """Auditoria por TEXTO (não reenvia as 30 imagens — bem mais leve, sem timeout).
    `balloons_per_panel`: lista (por painel) das listas de balões já lidos/merged das
    imagens — é a VERDADE de cada painel. `candidatos`: lista de roteiros (cada um é
    lista de 'persona|texto' por painel). Claude escolhe o melhor, edita e GARANTE que
    cada locução cobre os balões daquele painel. Retorna mesmo formato de audit_narration."""
    if not is_available():
        return None
    n = len(balloons_per_panel)
    verdade = []
    for i, bs in enumerate(balloons_per_panel):
        txt = " / ".join(bs) if bs else "(sem texto — só ação)"
        verdade.append(f"P{i+1}: {txt}")
    cand_txt = []
    for ci, cand in enumerate(candidatos):
        linhas = "\n".join(f"  P{j+1}: {t}" for j, t in enumerate(cand))
        cand_txt.append(f"### CANDIDATO {ci} ###\n{linhas}")
    prompt = (
        "Você é o agente REVISOR de um pipeline de narração de manhwa.\n\n"
        "VERDADE DOS PAINÉIS (texto realmente lido dos balões de cada painel, em ordem):\n"
        + "\n".join(verdade) + "\n\n"
        "ROTEIROS CANDIDATOS (cada um tem uma locução por painel):\n"
        + "\n\n".join(cand_txt) + "\n\n"
        "Tarefa (faça nesta ordem):\n"
        "1. Nota 0-10 de FIDELIDADE de cada candidato: a locução de cada painel bate "
        "com a VERDADE daquele painel? Penalize falas trocadas de painel, balões "
        "ignorados e texto inventado. Penalize TAMBÉM transformar em narração um painel "
        "que tem balão de diálogo (devia ser o PERSONAGEM falando).\n"
        "2. Monte o ROTEIRO FINAL: uma locução por painel. Escolha o melhor candidato "
        "por painel e CORRIJA usando a VERDADE — cada locução DEVE cobrir o que aquele "
        "painel diz (todos os balões relevantes daquele painel), sem puxar fala de "
        "outro painel. Tom de recap dramático BR, 8-40 palavras. Não narre onomatopeias "
        "como fala.\n"
        "REGRA DE VOZ (CRÍTICA — a maioria das locuções deve ser de PERSONAGEM):\n"
        "  - Se a VERDADE do painel tem QUALQUER fala/diálogo (não-onomatopeia), a "
        "locução é do PERSONAGEM que fala, dita em 1ª pessoa com a fala dele. NUNCA "
        "transforme diálogo em narração ('ele disse que...'). Diga a fala direto.\n"
        "  - Use Narrador SÓ quando o painel é puro ação/cenário SEM diálogo, OU num "
        "momento-chave de virada/gancho pra costurar a história. O narrador é a minoria.\n"
        "  - Identifique o personagem por nome quando der; senão use rótulo estável "
        "(ex: 'Rapaz', 'Garota', 'Velho'). NUNCA o rótulo genérico 'Personagem'.\n"
        "3. Cada locução começa com 'persona|' (Narrador, ou o nome/rótulo do personagem).\n\n"
        "Responda em JSON estrito:\n"
        '{"notas":[...],"melhor_indice":i,"locucoes_finais":["persona|texto",...]}'
        f"\nlocucoes_finais DEVE ter exatamente {n} itens."
    )
    out = _post([{"role": "user", "content": prompt}], max_tokens=max_tokens,
                temperature=0.2, model=fast_model())
    if not out:
        return None
    d = _extract_json(out)
    if d is None:
        print("  [claude audit_truth] JSON inválido", flush=True)
    return d
