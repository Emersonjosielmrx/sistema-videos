"""Reserva do modelo dos agentes (vigia geral e IA do painel) quando o modelo principal fica sem crédito (22/10).

O principal é o "modelo" do claude_proxy.json (kr/claude-sonnet-4.5, Kiro). O crédito do Kiro é mensal e, no ritmo de
out/2026 (~10 contas por dia), acaba uns 10 dias antes da renovação (dia 1, 00:00 UTC): sem reserva, o vigia e a IA do
painel param. Regra: quem chama pega a ordem em modelos(); se o agente voltar com "API Error" sem ter feito nenhum
passo, chama marcar() (o modelo fica fora por 1 h, pra todos) e repete com o próximo.
Reservas testadas 22/10 com claude.exe -p + ferramenta Read (D:\\tmp\\kiro_reserva\\teste_cli.py): antigravity/gemini-3-flash
11 s e agy/gemini-3.8-flash-high 48 s (gemini-3.8-flash-tiered levou 239 s: fora). Os cc/ ficam de fora: são as contas
do Claude Code do dono.

23/10: com o Kiro zerado (401 "No active credentials for provider: kiro"), cada agente gastava ~4 min nas 10 tentativas
do Claude Code antes de cair na reserva, e de novo a cada hora. Agora modelos() testa o principal DIRETO no gateway
(1 pedido de 5 tokens, ~2 s, no máximo a cada TESTE_S) e, se a resposta for "sem crédito/sem credencial", deixa ele
fora por SEM_CREDITO_S (6 h: o Kiro só volta na virada do mês, mas testa de novo caso alguém religue antes).
"""
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# 23/10 (dona: "adicione o fallback do Antigravity Gemini 3.8"): o 3.8 vai primeiro — testado 23/10 como agente
# (claude.exe -p + Read): 94 s e resposta certa; o 3-flash (mais rápido, mais simples) fica de segunda reserva
RESERVAS = ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash", "gemini/gemini-2.5-flash",
            "openrouter/google/gemini-2.5-flash"]  # 09/11: gemini-3.5 dava resposta vazia; +openrouter fallback
ESTADO = Path(__file__).resolve().parent / "estado" / "ia_reserva.json"
PROXY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")
FORA_S = 3600
SEM_CREDITO_S = 3600  # 26/10: era 6 h; com o conta-gota o Kiro pausa e volta todo dia à meia-noite
TESTE_S = 600
# 26/10 (dono: "o Kiro agora tem créditos mas tem que ser no conta-gota, aguentar até dia 1"): robô não usa Kiro; ele
# fica pro chat do dono. Religar: "robos_podem_usar_kiro": true em config\kiro_conta_gota.json. O limite diário do que
# sobra (chat + produção) é o /opt/omniroute/kiro_conta_gota.py na 157.
CONTA_GOTA = Path(__file__).resolve().parent / "config" / "kiro_conta_gota.json"


def _conta_gota():
    try:
        return json.loads(CONTA_GOTA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def kiro_para_robos():
    return bool(_conta_gota().get("robos_podem_usar_kiro"))


def kiro_para_consertos():
    """26/10 (dono: "Gemini pra coisas menores e o Kiro apenas para as correções"): conserto de verdade (propor/aplicar
    do painel, pedido pelo dono ou pelo vigia) pode usar o Kiro; pergunta, vigia e aprendizado não."""
    return bool(_conta_gota().get("kiro_para_consertos", True))


def eh_kiro(modelo):
    return str(modelo or "").startswith(("kr/", "kiro/"))


SEM_CREDITO = re.compile(r"No active credentials|reached the limit|credits?[_ ]exhausted|insufficient|\b40[12]\b", re.I)

AVISO_RESERVA = ("\n\nMODO RESERVA: o modelo principal está sem crédito e você é um modelo mais simples. Só mexa em "
                 "arquivo se o conserto for óbvio e pequeno (1 a 3 linhas), sempre com backup antes; na dúvida, não "
                 "mexa e responda REVISAR com o diagnóstico (o que achou, onde e o que faria).")


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(d):
    try:
        ESTADO.parent.mkdir(parents=True, exist_ok=True)
        tmp = ESTADO.with_name(ESTADO.name + ".tmp")
        tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
        tmp.replace(ESTADO)
    except OSError:
        pass


def _fora(d, modelo):
    """Falhou na última hora (marcar) ou está sem crédito até a hora gravada em "_ate"."""
    return (time.time() - float(d.get(modelo, 0) or 0) <= FORA_S
            or float((d.get("_ate") or {}).get(modelo, 0) or 0) > time.time())


def testar(modelo):
    """Pergunta ao gateway direto, sem o Claude Code: None = respondeu; senão o erro (ex.: "HTTP 401 ...")."""
    cfg = json.loads(PROXY.read_text(encoding="utf-8"))
    corpo = json.dumps({"model": modelo, "max_tokens": 5,
                        "messages": [{"role": "user", "content": "responda só: ok"}]}).encode("utf-8")
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/v1/messages", corpo, {
        "Content-Type": "application/json", "anthropic-version": "2023-06-01",
        "x-api-key": cfg["auth_token"], "Authorization": "Bearer " + cfg["auth_token"]})
    try:
        corpo_resp = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        # 07/11: o Antigravity responde 200 com o TEXTO "This version of Antigravity is no longer supported" — conta
        # como sem crédito (fora 1 h) pra a cadeia pular pro próximo em vez de usar essa resposta como se fosse real
        if "Antigravity is no longer supported" in corpo_resp:
            return "HTTP 402 Antigravity is no longer supported (versão do cliente no OmniRoute desatualizada)"
        return None
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code} {e.read()[:300].decode('utf-8', 'replace')}"


def modelos(principal, conserto=False):
    """Ordem pra tentar agora: o principal e as reservas, tirando quem está fora. O principal é testado no gateway
    (no máximo a cada TESTE_S); sem crédito/credencial = fora por SEM_CREDITO_S pra todos os agentes.
    conserto=True: é correção de verdade — pode usar o Kiro (conta-gota, 26/10); o resto vai pro Gemini."""
    d = _ler()
    if eh_kiro(principal) and not (kiro_para_robos() or (conserto and kiro_para_consertos())):
        return list(RESERVAS)
    todos = list(dict.fromkeys([principal] + RESERVAS))
    vivos = [m for m in todos if not _fora(d, m)]
    if vivos and vivos[0] == principal and time.time() - float((d.get("_teste") or {}).get(principal, 0)) > TESTE_S:
        try:
            erro = testar(principal)
        except Exception:  # noqa: BLE001 — gateway/rede fora: o agente tenta do jeito antigo
            erro = None
        d = _ler()
        d.setdefault("_teste", {})[principal] = time.time()
        if erro and SEM_CREDITO.search(erro):
            d.setdefault("_ate", {})[principal] = time.time() + SEM_CREDITO_S
            d.setdefault("_motivo", {})[principal] = erro[:200]
            vivos = vivos[1:]
        _gravar(d)
    return vivos or todos


def principal_sem_credito(principal):
    """Até quando (timestamp) o principal está fora por falta de crédito; 0 = está valendo."""
    ate = float((_ler().get("_ate") or {}).get(principal, 0) or 0)
    return ate if ate > time.time() else 0


def falhou_sem_trabalhar(texto, passos=0):
    """O gateway recusou (sem crédito, fora do ar...) antes do agente fazer qualquer coisa."""
    return passos == 0 and "API Error" in (texto or "") and "STATUS" not in (texto or "")


def falha_de_modelo(texto):
    """O agente parou por erro do gateway/modelo (sem crédito, limite, fora do ar), tenha feito passos ou não."""
    return bool(re.search(r"API Error|upstream error|rate.?limit|overloaded|No active credentials", texto or "", re.I))


def marcar(modelo, motivo=""):
    """Tira o modelo da ordem por FORA_S; se o motivo for falta de crédito/credencial, por SEM_CREDITO_S."""
    d = _ler()
    d[modelo] = time.time()
    if SEM_CREDITO.search(motivo or ""):
        d.setdefault("_ate", {})[modelo] = time.time() + SEM_CREDITO_S
        d.setdefault("_motivo", {})[modelo] = str(motivo)[:200]
    _gravar(d)


def eh_reserva(modelo):
    return modelo in RESERVAS
