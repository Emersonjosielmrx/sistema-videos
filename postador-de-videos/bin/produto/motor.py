"""Motor dos verificadores (cópia adaptada de D:\\claude-code-video\\motor.py, 26/10): Claude Code sem janela
(claude.exe -p) pelo OmniRoute com um modelo Gemini, rodando dentro da pasta dos quadros para OLHAR as imagens
(só ferramenta Read). Config em config\\produto_lapidar.json. Consumo em logs\\produto_motor.jsonl.
"""
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config" / "produto_lapidar.json"
CONSUMO = RAIZ / "logs" / "produto_motor.jsonl"
EXT = Path.home() / ".vscode" / "extensions"
SO_LER = ("Read", "Bash,Edit,Write,WebFetch,WebSearch,Agent")
# editor/corretor: escreve a edição em Remotion, roda o `still` e olha os quadros
EDITOR = ("Read,Write,Edit,Glob,Grep,Bash", "WebFetch,WebSearch,Agent")


class SemCota(Exception):
    pass


class MotorErro(Exception):
    pass


def cfg():
    return json.loads(CONFIG.read_text("utf-8"))


def _exe():
    """claude.exe da extensão mais nova (a pasta muda de nome a cada atualização)."""
    achados = sorted(EXT.glob("anthropic.claude-code-*/resources/native-binary/claude.exe"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    if not achados:
        raise MotorErro("claude.exe não encontrado nas extensões do VS Code")
    return str(achados[0])


_saude = {}


def responde(modelo, prazo=60):
    """Ping curto antes de entregar uma sessão longa ao modelo. 27/10: com as chaves em "cooling down" o OmniRoute
    segura cada pedido 4–5 min antes do 429 — numa edição de 90 turnos isso virava 60 min de timeout. Cache 10 min."""
    import time
    import urllib.request
    agora = time.time()
    if modelo in _saude and agora - _saude[modelo][0] < 600:
        return _saude[modelo][1]
    c = cfg()
    corpo = {"model": modelo, "max_tokens": 30, "messages": [{"role": "user", "content": "Responda só: OK"}]}
    req = urllib.request.Request(c["gateway"].rstrip("/") + "/v1/messages", data=json.dumps(corpo).encode(),
                                 headers={"x-api-key": c["chave"], "Authorization": "Bearer " + c["chave"],
                                          "content-type": "application/json", "anthropic-version": "2023-06-01"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=prazo).read())
        ok = bool("".join(b.get("text", "") for b in d.get("content", [])).strip())
    except Exception:  # noqa: BLE001
        ok = False
    _saude[modelo] = (agora, ok)
    return ok


_SEM_COTA = re.compile(r"429|rate.?limit|quota|exhausted|credit|usage limit|limit reached|overloaded", re.I)


def chamar(prompt, pasta, etapa, timeout=900, max_turnos=20, modelo=None, ferramentas=SO_LER, aceitar_limite=False):
    c = cfg()
    modelo = modelo or c["modelo"]
    env = dict(os.environ, ANTHROPIC_BASE_URL=c["gateway"], ANTHROPIC_AUTH_TOKEN=c["chave"],
               ANTHROPIC_MODEL=modelo, ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
               # 26/10 11:11: o corretor reescreve o Video.tsx inteiro e estourou os 32000 tokens de saída
               CLAUDE_CODE_MAX_OUTPUT_TOKENS="64000")
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = [_exe(), "-p", "--output-format", "json", "--max-turns", str(max_turnos),
           "--setting-sources", "project",          # sem os hooks/prompts do chat do dono
           "--allowedTools", ferramentas[0], "--disallowedTools", ferramentas[1]]
    ini = datetime.now()
    # 29/10: com o PC carregado o Claude Code esperou só 3 s pelo prompt no stdin ("no stdin data received in 3s")
    # e saiu sem resposta (revisor perdido no teste). Prompt num arquivo + stdin dele: já está todo lá quando abre
    arq_prompt = Path(pasta) / f".prompt_{etapa}_{os.getpid()}.txt"
    arq_prompt.write_text(prompt, encoding="utf-8")
    try:
        with arq_prompt.open("rb") as entrada:
            r = subprocess.run(cmd, stdin=entrada, capture_output=True, cwd=str(pasta), env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        _registrar(etapa, ini, None, "timeout")
        raise MotorErro(f"timeout {timeout}s")
    finally:
        arq_prompt.unlink(missing_ok=True)
    saida = r.stdout.decode("utf-8", "replace")
    try:
        # 29/10: o Claude Code passou a imprimir "⚠ claude.ai connectors are disabled..." junto da saída; a última
        # linha deixou de ser o JSON e editor/melhorador caíram todos em "saída inválida" -> pega o último JSON
        res = next(json.loads(ln) for ln in reversed(saida.strip().splitlines()) if ln.lstrip().startswith("{"))
    except (ValueError, StopIteration):
        erro = (saida + r.stderr.decode("utf-8", "replace"))[-400:]
        _registrar(etapa, ini, None, erro)
        if _SEM_COTA.search(erro):
            raise SemCota(erro)
        raise MotorErro(f"saída inválida: {erro}")
    _registrar(etapa, ini, res, None if not res.get("is_error") else str(res.get("result"))[:300])
    if aceitar_limite and res.get("subtype") == "error_max_turns":
        # editor/corretor: o que ele mudou já está no disco; quem chamou renderiza e confere
        return (res.get("result") or "").strip() or "(parou no limite de turnos)"
    if res.get("is_error") or res.get("subtype") != "success":
        txt = f"{res.get('api_error_status')} {res.get('result')}"
        if res.get("api_error_status") == 429 or _SEM_COTA.search(txt):
            raise SemCota(txt[:300])
        raise MotorErro(txt[:300])
    texto = (res.get("result") or "").strip()
    if not texto:
        raise MotorErro("resposta vazia")
    return texto


def chamar_json(prompt, pasta, etapa, **kw):
    """Como chamar(), mas devolve o 1º objeto JSON da resposta (1 nova tentativa se vier quebrado)."""
    txt = ""
    for tentativa in range(2):
        txt = chamar(prompt if not tentativa else prompt + "\n\nIMPORTANTE: responda SÓ o JSON válido, nada mais.",
                     pasta, etapa, **kw)
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
    raise MotorErro(f"JSON inválido: {txt[:200]}")


def _registrar(etapa, ini, res, erro):
    u = (res or {}).get("usage") or {}
    linha = {"em": ini.isoformat(timespec="seconds"), "etapa": etapa,
             "segundos": round((datetime.now() - ini).total_seconds(), 1),
             "entrada": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
             "saida": u.get("output_tokens", 0), "turnos": (res or {}).get("num_turns"), "erro": erro}
    CONSUMO.parent.mkdir(exist_ok=True)
    with CONSUMO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
