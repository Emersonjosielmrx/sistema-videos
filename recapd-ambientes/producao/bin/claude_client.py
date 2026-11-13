"""claude_client.py — cliente Claude via base URL do settings (proxy kr/).

Usado como AUDITOR de fidelidade da narração às imagens e como gerador alternativo
no ensemble. RESILIENTE: a API key do proxy expira em dias; qualquer falha retorna
None em vez de explodir, pra o pipeline seguir só com Gemini.

Lê credenciais de settings.json (env.ANTHROPIC_*). Não usa SDK — urllib puro pra
não depender de versão de pacote.
"""
import base64
import json
import logging
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
    "model": "antigravity/gemini-3-flash",  # (2.5-pro saiu do catálogo 16/10) substitui haiku (rápido/barato)
    "fast": "antigravity/gemini-3-flash",
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


_MORTOS = Path(__file__).resolve().parent.parent / "estado" / "modelos_mortos.json"


def _modelo_morto(modelo, marcar=False, minutos=15):
    """09/11: modelo que falhou (timeout/vazio) fica 15 min fora da cadeia, em todos os processos — sem isso cada
    roteiro esperava 3 min (2 Geminis mortos x 30 s + retries) antes de chegar no Sonnet web."""
    import json as _j
    import time as _t
    try:
        d = _j.loads(_MORTOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    if marcar:
        d[modelo] = _t.time() + minutos * 60
        try:
            _MORTOS.parent.mkdir(parents=True, exist_ok=True)
            _MORTOS.write_text(_j.dumps(d), encoding="utf-8")
        except OSError:
            pass
        return True
    return d.get(modelo, 0) > _t.time()


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
        "stream": False,
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
                resp = json.loads(r.read().decode("utf-8"))
            parts = resp.get("content", [])
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            # 07/11: o Antigravity responde 200 com o TEXTO "This version of Antigravity is no longer supported" — virava
            # "roteiro" com 0 frases e o Short morria ("não narra": 29 só hoje, 128 disparos -> 24 Shorts). Troca pelo
            # Gemini 3.5 do AI Studio (mesmo gateway) uma vez; se ele também falhar, volta None como antes.
            if "Antigravity is no longer supported" in text[:200]:
                # 07/11 teste: 2.5 e 3.6 respondem em 3 s; o 3.5 dá timeout (cota disputada)
                for alt in os.environ.get("GEMINI_SEM_ANTIGRAVITY",
                                          "gemini/gemini-2.5-flash,gemini/gemini-3.6-flash,claude-web/claude-sonnet-5-5").split(","):
                    alt = alt.strip()
                    if not alt or alt == body["model"] or _modelo_morto(alt):
                        continue
                    print(f"  [claude] {body['model']}: Antigravity fora — tento {alt}", flush=True)
                    r2 = _post(messages, max_tokens, temperature, alt, min(timeout, 40), 1)
                    if r2 and "Antigravity is no longer supported" not in r2[:200]:
                        return r2
                    _modelo_morto(alt, marcar=True)
                return None
            return text.strip() or None
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


_TEXTO_VIDEO_ARQ = Path(__file__).resolve().parent.parent / "workspace" / "modelo_texto.jsonl"
_ARGON_PAUSA = Path(__file__).resolve().parent.parent / "workspace" / "argon_pausa.txt"


def _texto_video(content, max_tokens, temperature, timeout):
    """27/10 (dona: "mude o gemini pelo Argon para vídeo, não para o melhorador"; depois "Argon curto, se demorar
    troca pro Gemini 3.8"): texto do Short (roteiro, título, gancho) no Argon pelo proxy :20133 com teto
    TEXTO_VIDEO_TIMEOUT (120 s); falhou/demorou = TEXTO_VIDEO_RESERVA (Gemini 3.8) e o Argon descansa 15 min. Cada
    chamada vai pro modelo_texto.jsonl (medir a diferença). TEXTO_VIDEO_MODELO vazio = como antes."""
    modelo = os.environ.get("TEXTO_VIDEO_MODELO", "")
    cfg = _load_cfg()
    if not modelo or not cfg:
        return None, None
    try:
        if time.time() < float(_ARGON_PAUSA.read_text().strip() or 0):
            return None, "pausa"
    except (OSError, ValueError):
        pass
    body = json.dumps({"model": modelo, "max_tokens": max_tokens, "temperature": temperature, "stream": False,
                       "messages": [{"role": "user", "content": content}]}).encode("utf-8")
    t, texto, erro = time.time(), None, None
    try:
        req = urllib.request.Request(os.environ.get("TEXTO_VIDEO_BASE", "http://157.173.207.22:20133") + "/v1/messages",
                                     data=body, headers={"content-type": "application/json", "x-api-key": cfg["key"],
                                                         "anthropic-version": "2023-06-01"})
        # 27/10 (dona: "Argon curto; se começar a demorar troca pro Gemini 3.8"): teto curto (mediana medida 71 s)
        with urllib.request.urlopen(req, timeout=float(os.environ.get("TEXTO_VIDEO_TIMEOUT") or 120)) as r:
            resp = json.loads(r.read().decode("utf-8"))
        texto = "".join(p.get("text", "") for p in resp.get("content", []) if p.get("type") == "text").strip() or None
        if not texto:
            erro = "vazio"
    except Exception as e:  # noqa: BLE001 — qualquer falha = Gemini; nunca desliga o claude_client
        erro = f"{type(e).__name__}: {str(e)[:120]}"
    if erro:
        try:
            _ARGON_PAUSA.write_text(str(time.time() + 900))
        except OSError:
            pass
    try:
        with open(_TEXTO_VIDEO_ARQ, "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": time.strftime("%Y-%m-%dT%H:%M:%S"), "modelo": modelo, "ok": not erro,
                                "s": round(time.time() - t, 1), "erro": erro, "pc": os.environ.get("COMPUTERNAME"),
                                "pedido": content[:80]}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return texto, erro


# 28/10: "[EMPTY RESPONSE]" chegou como TEXTO e foi queimado no topo de 2 Shorts como gancho (sem-obra-5119c9/918e98).
# Resposta que é só um aviso de vazio/erro do gateway = falha (vai pra reserva / volta vazio). "[ERRO: LIXO]" do
# anime_script é recusa de propósito e continua passando.
_PLACEHOLDER = re.compile(r"^\s*[\[(<]?\s*(empty( response)?|no response|null|none|undefined|nan|error|erro)\s*[\])>]?\s*$",
                          re.IGNORECASE)


def _placeholder(texto):
    return bool(texto) and bool(_PLACEHOLDER.match(str(texto)))


def generate_text(prompt, system=None, max_tokens=2048, temperature=0.4, model=None, timeout=90, video=False):
    texto = _generate_text(prompt, system, max_tokens, temperature, model, timeout, video)
    if _placeholder(texto):
        logging.warning(f"[claude_client] resposta-aviso descartada: {str(texto)[:40]!r}")
        return ""
    return texto


def _generate_text(prompt, system=None, max_tokens=2048, temperature=0.4, model=None, timeout=90, video=False):
    # timeout: o anime_script passa 300 s (bloco grande); sem o parâmetro todo roteiro de anime quebrava (16/10)
    content = prompt if system is None else f"{system}\n\n{prompt}"
    if video and model is None:
        texto, _erro = _texto_video(content, max_tokens, temperature, timeout)
        if _placeholder(texto):
            texto, _erro = None, f"aviso {texto[:30]!r}"
        if texto:
            return texto
        model = os.environ.get("TEXTO_VIDEO_RESERVA") or None  # Argon falhou/demorou: reserva (Gemini 3.8)
        if model:
            t = time.time()
            texto = _post([{"role": "user", "content": content}], max_tokens=max_tokens, temperature=temperature,
                          model=model, timeout=timeout)
            try:
                with open(_TEXTO_VIDEO_ARQ, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"em": time.strftime("%Y-%m-%dT%H:%M:%S"), "modelo": model, "ok": bool(texto),
                                        "s": round(time.time() - t, 1), "erro": None if texto else "vazio",
                                        "pc": os.environ.get("COMPUTERNAME"), "pedido": content[:80],
                                        "reserva_de": _erro}, ensure_ascii=False) + "\n")
            except OSError:
                pass
            if texto and not _placeholder(texto):
                return texto
            model = None
    return _post([{"role": "user", "content": content}],
                 max_tokens=max_tokens, temperature=temperature, model=model, timeout=timeout)


_IA_SAUDE = Path(__file__).resolve().parent.parent / "workspace" / "ia_saude.json"
SAUDE_PAUSA_S = 900  # modelo que acabou de falhar/travar descansa 15 min (como o Argon em _texto_video)


def _saude_ler():
    try:
        return json.loads(_IA_SAUDE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _saude_marcar(modelo, ok, segundos, erro=None):
    d = _saude_ler()
    e = d.setdefault(modelo, {})
    e.update({"em": time.strftime("%Y-%m-%dT%H:%M:%S"), "ok": ok, "s": round(segundos, 1), "erro": erro,
              "falhas_seguidas": 0 if ok else int(e.get("falhas_seguidas") or 0) + 1})
    if ok:
        e["ok_em"] = time.time()
    else:
        e["erro_em"] = time.time()
    try:
        _IA_SAUDE.parent.mkdir(parents=True, exist_ok=True)
        _IA_SAUDE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def modelo_descansando(modelo):
    """True se o modelo falhou/travou há menos de SAUDE_PAUSA_S (e não voltou a responder depois)."""
    e = _saude_ler().get(modelo) or {}
    return float(e.get("erro_em") or 0) > float(e.get("ok_em") or 0) and time.time() - float(e.get("erro_em") or 0) < SAUDE_PAUSA_S


def generate_text_vivo(prompt, modelos, system=None, max_tokens=2048, temperature=0.4, timeout=240, rodadas=1,
                       pausa=180):
    """rodadas > 1 (29/10, sessão LONGOS): a cadeia inteira falhou = espera `pausa` s e passa por ela de novo. No Top
    Fighter (29/10 13:51–14:03) a OmniRoute caiu ~12 min (3 timeouts + HTTP 500) e o longo saiu sem resumo e sem
    falas; 1 h depois os 3 modelos respondiam em 5 s com o roteiro inteiro."""
    for r in range(max(1, rodadas)):
        if r:
            logging.warning(f"[claude_client] cadeia inteira falhou — nova rodada em {pausa} s ({r + 1}/{rodadas})")
            time.sleep(pausa)
        texto, modelo, tentativas = _cadeia_uma_vez(prompt, modelos, system, max_tokens, temperature, timeout,
                                                    ignorar_descanso=bool(r))
        if texto:
            return texto, modelo, tentativas
    return texto, modelo, tentativas


def _cadeia_uma_vez(prompt, modelos, system=None, max_tokens=2048, temperature=0.4, timeout=240,
                    ignorar_descanso=False):
    """29/10 (Fable, LONGOS_07 — ver FABLE_DECISOES.md D7): texto por uma CADEIA de modelos. 28/10 o
    'antigravity/gemini-3.8-flash-tiered' parou de responder (120–150 s sem nem um "ok") e o longo saiu SEM resumo e
    SEM falas, sem aviso. Aqui: 1 tentativa por modelo (o _post sozinho repetia 3× o timeout = 12 min por modelo
    travado), pula por 15 min quem acabou de falhar (ia_saude.json), e devolve (texto, modelo_usado, tentativas).
    tentativas = [{modelo, ok, s, erro}] para o chamador registrar o que faltou. Texto vazio em todos = ("", None, …)."""
    content = prompt if system is None else f"{system}\n\n{prompt}"
    modelos = [m for m in modelos if m]
    tentativas = []
    for i, modelo in enumerate(modelos):
        if not ignorar_descanso and modelo_descansando(modelo) and i < len(modelos) - 1:
            tentativas.append({"modelo": modelo, "ok": False, "s": 0, "erro": "descansando (falhou há < 15 min)"})
            continue
        t = time.time()
        texto = _post([{"role": "user", "content": content}], max_tokens=max_tokens, temperature=temperature,
                      model=modelo, timeout=timeout, max_retries=1)
        ok = bool(texto) and not _placeholder(texto)
        _saude_marcar(modelo, ok, time.time() - t, None if ok else ("vazio" if not texto else f"aviso {texto[:30]!r}"))
        tentativas.append({"modelo": modelo, "ok": ok, "s": round(time.time() - t, 1),
                           "erro": None if ok else ("vazio/erro" if not texto else f"aviso {texto[:30]!r}")})
        try:
            with open(_TEXTO_VIDEO_ARQ, "a", encoding="utf-8") as f:
                f.write(json.dumps({"em": time.strftime("%Y-%m-%dT%H:%M:%S"), "modelo": modelo, "ok": ok,
                                    "s": round(time.time() - t, 1), "erro": tentativas[-1]["erro"],
                                    "pc": os.environ.get("COMPUTERNAME"), "pedido": content[:80],
                                    "cadeia": i}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        if ok:
            return texto, modelo, tentativas
        logging.warning(f"[claude_client] {modelo} falhou em {time.time() - t:.0f} s ({tentativas[-1]['erro']}) — próximo da cadeia")
    return "", None, tentativas


CADEIA_TEXTO_LONGO = [os.environ.get("GEMINI_TEXTO_VIDEO") or "antigravity/gemini-3.8-flash-tiered",
                      "agy/gemini-3.8-flash-high", "gemini-fila", "antigravity/gemini-3-flash"]  # nunca Opus/Kiro


def registrar_faltou(pasta, parte, motivo, tentativas=()):
    """O vídeo saiu SEM uma parte (resumo, falas…) porque a IA falhou: grava faltou.json na pasta do vídeo (o painel e
    o publish leem) e avisa no Telegram (avisos.py, importante). Não trava a produção (dona: nenhum canal 1 dia sem
    postar) — só deixa de ser silencioso."""
    pasta = Path(pasta)
    try:
        arq = pasta / "faltou.json"
        d = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
        d[parte] = {"em": time.strftime("%Y-%m-%dT%H:%M:%S"), "motivo": motivo, "tentativas": list(tentativas)}
        arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except (OSError, ValueError):
        pass
    try:
        import sys
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import avisos
        modelos = ", ".join(f"{t.get('modelo')} ({t.get('erro') or 'ok'}, {t.get('s')}s)" for t in tentativas) or "-"
        avisos.enviar(f"⚠️ Longo {pasta.name}: saiu SEM {parte} — {motivo}. IA: {modelos}", origem="longo",
                      importante=True, chave=f"faltou:{pasta.name}:{parte}")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[claude_client] aviso de 'faltou {parte}' não saiu ({type(e).__name__})")


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
        # só marcador de lista ("- ", "1. ", "2) ", "..."): o padrão antigo comia o número do balão ("100 anos" -> "anos")
        ln = re.sub(r"^(?:(?:[-*•]+|\d{1,3}[.)])\s+|[-*•]+(?=\S)|\.{2,}\s*)+", "", ln)
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
