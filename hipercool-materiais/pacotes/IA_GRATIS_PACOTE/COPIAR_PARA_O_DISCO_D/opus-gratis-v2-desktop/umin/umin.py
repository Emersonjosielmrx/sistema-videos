# -*- coding: utf-8 -*-
r"""umin.py — 1min.ai pela API oficial (sem navegador), com o Claude escolhido certo.

Por que API e não a tela: no chat da tela o 1min manda a mesma pergunta para VÁRIOS modelos juntos e vem
com o Qwen marcado; cada modelo extra gasta crédito. Pela API o modelo vai fixo no corpo e não tem isso.
O endpoint compatível com OpenAI (/openai/v1) NÃO tem Claude; o Claude só sai pelo /api/chat-with-ai.

Medido em 30/10/2026 (pergunta curta, conta de teste conta_exemplo):
  Opus 5.5 = 3.973 créditos (8 s; pela TELA saía ~21.600) | Opus 5 = 14.124 (5 s) | Fable 5.1 = 60.357 (9 s)
  Haiku 5.5 = 87 (3 s). Das 13h40 às 14h20 o Opus 5.5 deu "503 Bedrock is unable to process your request"
  (AWS sem capacidade; falha não é cobrada: credit 0) — por isso as novas tentativas e o --reserva.
O bônus de cadastro foi 265.000 créditos; a chave de API NÃO lê o saldo (só a sessão do site), então o
saldo aqui é calculado: base (265.000 + bônus resgatados) − usado (o 1min devolve o "usado" em cada resposta).

Chave: D:\opus-gratis\segredos\1min.key (criada em app.1min.ai > menu da equipe > API > New API Key).
Uso:
  python umin.py "pergunta"                       # Opus 5.5 (tenta 3x se a AWS der 503)
  python umin.py -m fable "pergunta"              # apelidos: python umin.py modelos
  python umin.py --reserva opus5 "pergunta"       # se o Opus 5.5 não responder, usa o Opus 5 (avisa no fim)
  python umin.py --conversa nova "pergunta"       # cria conversa e guarda o id (contexto entre perguntas)
  python umin.py --conversa ultima "e agora?"     # continua a última conversa
  python umin.py saldo                            # saldo calculado e gasto médio por modelo (do umin_uso.jsonl)
  python umin.py calibrar 224173                  # acerta a base com o saldo que a tela mostra agora
Como módulo:  from umin import perguntar;  texto, info = perguntar("oi", modelo="opus", reservas=("opus5",))
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
CHAVE = AQUI.parent / "segredos" / "1min.key"
ESTADO = AQUI / "umin_estado.json"   # última conversa, último "usado" e a base do saldo
LOG = AQUI / "umin_uso.jsonl"        # uma linha por pergunta (ok ou falha): modelo, segundos, créditos gastos
API = "https://api.1min.ai/api"
TIMEOUT = 300
BASE_PADRAO = 265_000                # bônus de cadastro visto na conta de teste
ESPERAS_503 = (8, 20, 45)            # AWS ocupada: tenta de novo depois desses segundos

MODELOS = {
    "opus": "us.anthropic.claude-opus-5-5",
    "opus5": "us.anthropic.claude-opus-5",
    "opus48": "us.anthropic.claude-opus-4-8",
    "opus47": "us.anthropic.claude-opus-4-7",
    "opus46": "us.anthropic.claude-opus-4-6-v1",
    "fable": "us.anthropic.claude-fable-5-1",
    "fable5": "us.anthropic.claude-fable-5",
    "sonnet": "us.anthropic.claude-sonnet-5-5",
    "haiku": "us.anthropic.claude-haiku-5-5",
}


class ErroUmin(RuntimeError):
    pass


class Ocupado(ErroUmin):
    """A AWS (Bedrock) recusou por falta de capacidade: vale tentar de novo; não foi cobrado."""


def _chave():
    try:
        return CHAVE.read_text(encoding="utf-8").strip()
    except OSError:
        raise ErroUmin(f"sem chave em {CHAVE} (criar em app.1min.ai, menu da equipe > API > New API Key)") from None


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_estado(st):
    ESTADO.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


# ─────────────── rodízio multi-conta (31/10): cada conta tem sua chave e saldo próprio ───────────────
CONTAS = AQUI / "umin_contas.json"
CUSTO_MIN = 14_000          # 1 Opus 5.5 ≈ 13.900; conta abaixo disso não aguenta nem 1 msg → fora da fila


# ─────────────── orçamento DIÁRIO (31/10, dona: "só gaste o que vai ter diário") ───────────────
# O único crédito que renova é a visita diária: 15 mil por conta por dia. Então o 1min só pode gastar, por dia,
# 15 mil × (contas com chave). O dia do 1min vira à meia-noite de Los Angeles = 04:10 aqui (com folga).
POR_CONTA_DIA = 15_000
ORCAMENTO = AQUI / "umin_orcamento.json"


def _dia_1min():
    from datetime import timedelta
    return (datetime.now() - timedelta(hours=4, minutes=10)).date().isoformat()


def orcamento():
    """(gasto_hoje, limite_hoje)."""
    try:
        o = json.loads(ORCAMENTO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        o = {}
    gasto = o.get("gasto", 0) if o.get("dia") == _dia_1min() else 0
    limite = POR_CONTA_DIA * sum(1 for c in _contas() if c.get("chave"))
    return gasto, limite


def _gastar(valor):
    if not valor or valor <= 0:
        return
    gasto, _ = orcamento()
    ORCAMENTO.write_text(json.dumps({"dia": _dia_1min(), "gasto": gasto + int(valor)}), encoding="utf-8")


def _contas():
    try:
        return json.loads(CONTAS.read_text(encoding="utf-8")).get("contas", [])
    except (OSError, ValueError):
        # sem o cofre de contas: cai na chave única (compat)
        try:
            return [{"apelido": "unica", "chave": CHAVE.read_text(encoding="utf-8").strip(),
                     "base": BASE_PADRAO, "usado": 0, "sem_cota_ate": None, "stats": {}}]
        except OSError:
            return []


def _gravar_contas(contas):
    CONTAS.write_text(json.dumps({"contas": contas}, ensure_ascii=False, indent=1), encoding="utf-8")


def _saldo(c):
    return c.get("base", BASE_PADRAO) - c.get("usado", 0)


def _pronta(c):
    if not c.get("chave"):
        return False
    sc = c.get("sem_cota_ate")
    if sc and datetime.now().isoformat() < sc:
        return False
    return _saldo(c) >= CUSTO_MIN


def _proxima(ignorar=()):
    """A conta pronta com MAIS saldo (espalha o uso e evita a que está quase no fim)."""
    prontas = [c for c in _contas() if _pronta(c) and c["apelido"] not in ignorar]
    return max(prontas, key=_saldo) if prontas else None


def _marcar_conta(apelido, usado=None, sem_cota=False, ok=None, saldo_real=None):
    contas = _contas()
    for c in contas:
        if c["apelido"] == apelido:
            if usado is not None:
                c["usado"] = usado
                c["visto_em"] = datetime.now().isoformat(timespec="minutes")
            if sem_cota:
                from datetime import timedelta
                amanha = datetime.now().replace(hour=4, minute=10, second=0, microsecond=0)
                if datetime.now().hour >= 4:
                    amanha += timedelta(days=1)  # 31/10: replace(day=day+1) quebrava no fim do mês ("day 32")
                c["sem_cota_ate"] = amanha.isoformat()
            if saldo_real is not None:  # o 1min diz no erro quanto a conta tem: acerta a base
                c["base"] = c.get("usado", 0) + saldo_real
            if ok is not None:
                st = c.setdefault("stats", {"ok": 0, "erros": 0})
                st["ok" if ok else "erros"] = st.get("ok" if ok else "erros", 0) + 1
            break
    _gravar_contas(contas)


def _registrar(**campos):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), **campos}, ensure_ascii=False) + "\n")


def _post(caminho, corpo, chave=None):
    r = requests.post(f"{API}/{caminho}", json=corpo, timeout=TIMEOUT,
                      headers={"API-KEY": chave or _chave(), "Content-Type": "application/json"})
    try:
        dados = r.json()
    except ValueError:
        dados = {"bruto": r.text[:500]}
    if r.status_code >= 400:
        raise ErroUmin(f"HTTP {r.status_code}: {json.dumps(dados, ensure_ascii=False)[:400]}")
    return dados


def nova_conversa(modelo="opus", titulo=None):
    mid = MODELOS.get(modelo, modelo)
    d = _post("conversations", {"type": "UNIFY_CHAT_WITH_AI", "model": mid,
                                "title": titulo or f"opus-gratis {datetime.now():%d/%m %H:%M}"})
    uuid = (d.get("conversation") or d).get("uuid")
    if not uuid:
        raise ErroUmin(f"conversa sem uuid: {json.dumps(d)[:300]}")
    st = _estado()
    st["conversa"] = uuid
    _gravar_estado(st)
    return uuid


def _uma_vez(prompt, mid, conversa, busca_web, chave=None):
    po = {"prompt": prompt, "settings": {"webSearchSettings": {"webSearch": bool(busca_web)}}}
    if conversa:
        po["conversationId"] = conversa
        po["settings"]["historySettings"] = {"isMixed": False, "historyMessageLimit": 10}
    t0 = time.time()
    d = _post("chat-with-ai", {"type": "UNIFY_CHAT_WITH_AI", "model": mid, "promptObject": po}, chave=chave)
    seg = round(time.time() - t0, 1)
    rec = d.get("aiRecord") or {}
    res = (rec.get("aiRecordDetail") or {}).get("resultObject")
    if rec.get("status") not in (None, "SUCCESS"):
        erro = res if isinstance(res, dict) else {}
        detalhe = f"{erro.get('code')}: {erro.get('message') or json.dumps(res, ensure_ascii=False)[:300]}"
        _registrar(modelo_pedido=mid, ok=False, segundos=seg, erro=detalhe[:200],
                   cobrado=(rec.get("metadata") or {}).get("credit"))
        if erro.get("code") == "BEDROCK_CHAT_COMPLETION_ERROR" or "503" in str(erro.get("details")):
            raise Ocupado(detalhe)
        raise ErroUmin(detalhe)
    texto = "".join(res) if isinstance(res, list) else str(res or "")
    if not texto.strip():
        # 31/10: o 1min às vezes devolve SUCCESS com o texto vazio e COBRA (medido: 7.313). Leva o rec junto para o
        # chamador descontar o gasto (antes sumia do saldo e do orçamento).
        e = ErroUmin(f"resposta vazia (cobrada {(rec.get('metadata') or {}).get('credit')})")
        e.rec = rec
        raise e
    return texto, rec, seg


def _uma_conta(prompt, pedido, reservas, conversa, busca_web, conta):
    """Tenta uma conta (chave própria), com os modelos pedido+reservas e as re-tentativas de AWS ocupada.
    Devolve (texto, rec, seg, mid) ou levanta (Ocupado=todas 503; ErroUmin com INSUFFICIENT = conta sem crédito)."""
    chave = conta["chave"]
    falhas = []
    for mid in [pedido] + [MODELOS.get(r, r) for r in reservas]:
        for espera in (0,) + ESPERAS_503:
            if espera:
                time.sleep(espera)
            try:
                texto, rec, seg = _uma_vez(prompt, mid, conversa, busca_web, chave=chave)
            except Ocupado as e:
                falhas.append(str(e))
                continue
            return texto, rec, seg, mid
        # este modelo não respondeu (só 503): tenta a próxima reserva
    raise Ocupado("; ".join(falhas[-3:]) or "sem resposta")


def perguntar(prompt, modelo="opus", conversa=None, busca_web=False, reservas=()):
    """Devolve (texto, info). Roda a FILA de contas do 1min (cada uma com sua chave e saldo): conta sem crédito
    (INSUFFICIENT_CREDITS) sai da fila até o dia virar e a próxima responde. Re-tenta na AWS ocupada (não é cobrado).
    info["aviso"] avisa quando trocou de modelo; info["conta"] diz qual conta respondeu."""
    pedido = MODELOS.get(modelo, modelo)
    gasto_hoje, limite_hoje = orcamento()
    if gasto_hoje >= limite_hoje:
        raise ErroUmin(f"sem cota: orçamento diário do 1min esgotado ({gasto_hoje:,} de {limite_hoje:,}; "
                       f"renova às 04:10)")
    ignorar, erro_final = set(), None
    while True:
        conta = _proxima(ignorar)
        if not conta:
            raise ErroUmin("nenhuma conta do 1min com crédito agora" + (f"; {erro_final}" if erro_final else ""))
        apelido = conta["apelido"]
        try:
            texto, rec, seg, mid = _uma_conta(prompt, pedido, reservas, conversa, busca_web, conta)
        except Ocupado as e:                 # AWS ocupada em tudo nesta conta: tenta a próxima conta
            erro_final = f"{apelido}: ocupado ({e})"
            ignorar.add(apelido)
            continue
        except ErroUmin as e:
            rec_vazio = getattr(e, "rec", None)
            if rec_vazio is not None:  # resposta vazia, mas cobrada: desconta da conta e do orçamento do dia
                usado_v = (rec_vazio.get("teamUser") or {}).get("usedCredit")
                if usado_v is not None:
                    _gastar(usado_v - (conta.get("usado") or 0))
                    _marcar_conta(apelido, usado=usado_v, ok=False)
                _registrar(ok=False, conta=apelido, erro="resposta vazia cobrada", usado=usado_v)
                raise
            if "INSUFFICIENT_CREDITS" in str(e) or "insufficient" in str(e).lower():
                import re as _re
                m = _re.search(r"requires (\d+) credits.*?only has (\d+)", str(e))
                precisa, tem = (int(m.group(1)), int(m.group(2))) if m else (None, None)
                if tem is not None and tem >= CUSTO_MIN and precisa and precisa > tem:
                    # 31/10: o 1min cobra pelo TAMANHO — um turno longo do Claude Code pediu 715.526 créditos, mais
                    # que o saldo inteiro de qualquer conta. A conta NÃO está vazia: não marca; e se nem a conta com
                    # mais saldo aguenta, nenhuma aguenta -> devolve "sem cota" já (a VPS põe o 4.6/5.5).
                    _marcar_conta(apelido, saldo_real=tem)
                    if tem >= max((_saldo(c) for c in _contas() if c.get("chave")), default=0):
                        raise ErroUmin(f"sem cota: pedido grande demais para o 1min (precisa {precisa:,} créditos; "
                                       f"a conta com mais saldo tem {tem:,})") from None
                    ignorar.add(apelido)
                    continue
                _marcar_conta(apelido, sem_cota=True, ok=False, saldo_real=tem)   # sem crédito: fora até amanhã
                erro_final = f"{apelido}: sem crédito"
                ignorar.add(apelido)
                continue
            raise
        break
    tu = rec.get("teamUser") or {}
    usado = tu.get("usedCredit")
    antes = conta.get("usado")
    info = {"modelo_pedido": pedido, "modelo_usado": rec.get("model") or mid, "segundos": seg, "conta": apelido,
            "gasto": (usado - antes) if (antes is not None and usado is not None) else None, "usado": usado}
    if usado is not None:
        info["saldo_calculado"] = conta.get("base", BASE_PADRAO) - usado
        _marcar_conta(apelido, usado=usado, ok=True)
        _gastar(info["gasto"])
    else:
        _marcar_conta(apelido, ok=True)
    if info["modelo_usado"] != pedido:
        info["aviso"] = f"pedi {pedido} e respondeu {info['modelo_usado']}"
    _registrar(ok=True, chars_in=len(prompt), chars_out=len(texto), **info)
    return texto, info


def _resumo_gastos():
    por = {}
    try:
        linhas = LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return por
    for ln in linhas:
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        m = d.get("modelo_usado") or d.get("modelo_pedido")
        p = por.setdefault(m, {"ok": 0, "falhas": 0, "gastos": []})
        if d.get("ok") is False:
            p["falhas"] += 1
        else:
            p["ok"] += 1
            if d.get("gasto"):
                p["gastos"].append(d["gasto"])
    return por


def main(a):
    if not a:
        print(__doc__)
        return
    if a[0] == "modelos":
        for k, v in MODELOS.items():
            print(f"{k:8} {v}")
        return
    if a[0] == "add":  # add <apelido> <chave> [base]  — registra a conta no cofre (base = bônus de cadastro, padrão 265000)
        apelido, chave = a[1], a[2]
        base = int(a[3].replace(",", "").replace(".", "")) if len(a) > 3 else BASE_PADRAO
        contas = [c for c in _contas() if c["apelido"] != apelido]
        contas.append({"apelido": apelido, "email": apelido if "@" in apelido else apelido + "@gmail.com",
                       "chave": chave.strip(), "base": base, "usado": 0, "sem_cota_ate": None, "stats": {"ok": 0, "erros": 0}})
        _gravar_contas(contas)
        print(f"ok: {apelido} adicionada (saldo {base:,}); total {len(contas)} contas")
        return
    if a[0] == "calibrar":  # saldo que a tela mostra agora -> base = saldo + usado
        st = _estado()
        if "usado" not in st:
            raise SystemExit("faça 1 pergunta antes (o 'usado' vem na resposta)")
        st["base"] = int(a[1].replace(",", "").replace(".", "")) + st["usado"]
        _gravar_estado(st)
        print(f"base = {st['base']:,}")
        return
    if a[0] == "saldo":
        contas = _contas()
        total = prontas = 0
        for c in sorted(contas, key=_saldo, reverse=True):
            s = _saldo(c)
            total += max(0, s)
            st = "PRONTA" if _pronta(c) else ("sem cota" if c.get("sem_cota_ate") else "baixa")
            if _pronta(c):
                prontas += 1
            print(f"  {c['apelido']:28} saldo {s:>9,}  {st}  (ok {c.get('stats',{}).get('ok',0)})")
        print(f"\n{len(contas)} contas · {prontas} prontas · saldo total {total:,}")
        g, lim = orcamento()
        print(f"ORÇAMENTO DE HOJE (só o que entra por dia: 15 mil × {lim // POR_CONTA_DIA} contas): gasto {g:,} de "
              f"{lim:,} — {'LIBERADO' if g < lim else 'ESGOTADO até 04:10'}")
        return
    modelo, conversa, reservas = "opus", None, ()
    while a and a[0].startswith("-"):
        if a[0] in ("-m", "--modelo"):
            modelo, a = a[1], a[2:]
        elif a[0] == "--reserva":
            reservas, a = tuple(a[1].split(",")), a[2:]
        elif a[0] == "--conversa":
            conversa = nova_conversa(modelo) if a[1] == "nova" else (_estado().get("conversa") if a[1] == "ultima" else a[1])
            a = a[2:]
        else:
            raise SystemExit(f"opção desconhecida {a[0]}")
    texto, info = perguntar(" ".join(a), modelo=modelo, conversa=conversa, reservas=reservas)
    print(texto)
    print("\n---", json.dumps(info, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        main(sys.argv[1:])
    except ErroUmin as e:
        raise SystemExit(f"ERRO 1min: {e}") from None
