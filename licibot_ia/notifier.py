"""
LiciBot-IA · notifier.py
Avisos no Telegram (configurados no painel: bot, chat, o que avisar e filtros) e webhook (n8n/WhatsApp).
Texto simples, sem Markdown: título de licitação tem "_" e "*" que quebram o parse_mode.

Tipos de aviso: oportunidade nova, lembrete de prazo ("vou participar" fechando em 24 h), erro na varredura,
IA sem crédito e resumo diário. Fora do horário silencioso; o que cair no silêncio sai depois.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

import httpx

from config import BASE, GAVETA_TIPO, WEBHOOK_URL, avisos

log = logging.getLogger("licibot.aviso")
EMOJI = {"MEI": "🟢", "CPF": "🔵", "AMIGO_SOLAR": "🟡", "DESCARTADO": "🔴"}
ESTADO_ARQ = BASE / "avisos_estado.json"   # quando cada tipo saiu por último (evita repetir)


def _brl(v: float | None) -> str:
    if v is None:
        return "—"
    return f"R$ {v:,.0f}".replace(",", ".")


def _prazo(e: dict[str, Any]) -> str:
    d = (e.get("data_encerramento") or "")[:16]
    return f"{d[8:10]}/{d[5:7]} {d[11:16]}" if len(d) >= 16 else d


def _erro(err: Exception) -> str:
    """Nunca registra a URL (tem o token do bot / segredo do webhook)."""
    resp = getattr(err, "response", None)
    return f"HTTP {resp.status_code}" if resp is not None else type(err).__name__


# ═════════════════════════════════════════════════════════════════════════════
# filtros (os mesmos que o painel mostra)
# ═════════════════════════════════════════════════════════════════════════════

def passa_filtros(e: dict[str, Any], cfg: dict | None = None) -> bool:
    cfg = cfg or avisos()
    if e.get("carteira") not in (cfg["carteiras"] or []):
        return False
    if GAVETA_TIPO.get(e.get("gaveta"), "servico") not in (cfg["tipos"] or []):
        return False
    if cfg["ufs"] and e.get("uf") not in cfg["ufs"]:
        return False
    if (e.get("nota_final") or 0) < cfg["nota_min"]:
        return False
    if (e.get("margem_estimada") or 0) < (cfg["liquido_min"] or 0):
        return False
    inv = e.get("custo_estimado") or 0
    if cfg["invest_min"] and inv < cfg["invest_min"]:
        return False
    if cfg["invest_max"] and inv > cfg["invest_max"]:
        return False
    val = e.get("valor_estimado") or 0
    if cfg["valor_min"] and val < cfg["valor_min"]:
        return False
    if cfg["valor_max"] and val > cfg["valor_max"]:
        return False
    return True


def em_silencio(cfg: dict | None = None, agora: datetime | None = None) -> bool:
    cfg = cfg or avisos()
    h = (agora or datetime.now()).hour
    de, ate = int(cfg["silencio_de"]), int(cfg["silencio_ate"])
    if de == ate:
        return False
    return (de <= h < ate) if de < ate else (h >= de or h < ate)


# ═════════════════════════════════════════════════════════════════════════════
# envio
# ═════════════════════════════════════════════════════════════════════════════

def enviar_telegram(texto: str, cfg: dict | None = None) -> bool | None:
    """None = Telegram não configurado. Quebra em mensagens de até ~3.900 caracteres."""
    cfg = cfg or avisos()
    if not cfg["tg_token"] or not cfg["tg_chat"]:
        return None
    partes, atual = [], ""
    for bloco in texto.split("\n\n"):
        if len(atual) + len(bloco) + 2 > 3900:
            partes.append(atual)
            atual = ""
        atual += ("\n\n" if atual else "") + bloco
    partes.append(atual)
    ok = True
    for p in partes:
        try:
            r = httpx.post(f"https://api.telegram.org/bot{cfg['tg_token']}/sendMessage", timeout=30,
                           data={"chat_id": cfg["tg_chat"], "text": p[:4096], "disable_web_page_preview": "true"})
            r.raise_for_status()
        except httpx.HTTPError as err:
            log.error("telegram falhou: %s", _erro(err))
            ok = False
    return ok


def enviar_webhook(evento: str, dados: Any) -> bool | None:
    if not WEBHOOK_URL:
        return None
    try:
        r = httpx.post(WEBHOOK_URL, timeout=30, json={"fonte": "LiciBot-IA", "evento": evento, "dados": dados})
        r.raise_for_status()
        return True
    except httpx.HTTPError as err:
        log.error("webhook falhou: %s", _erro(err))
        return False


def _algum_ok(*resultados) -> bool:
    """True só se algum canal configurado recebeu. Sem canal nenhum = False: nada é marcado como avisado,
    então tudo chega quando a dona configurar o Telegram."""
    return any(r for r in resultados if r is not None)


def _estado() -> dict:
    try:
        return json.loads(ESTADO_ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _marcar(tipo: str) -> None:
    est = _estado()
    est[tipo] = time.time()
    ESTADO_ARQ.write_text(json.dumps(est), encoding="utf-8")


def _faz_tempo(tipo: str, horas: float) -> bool:
    return time.time() - _estado().get(tipo, 0) >= horas * 3600


# ═════════════════════════════════════════════════════════════════════════════
# os avisos
# ═════════════════════════════════════════════════════════════════════════════

def formatar(e: dict[str, Any]) -> str:
    tipo = {"produto": "📦 produto", "servico": "🛠 serviço", "obra": "⚡ obra"}.get(
        GAVETA_TIPO.get(e.get("gaveta"), ""), "")
    linhas = [
        f"{EMOJI.get(e['carteira'], '⚪')} {e['carteira']} · nota {e['nota_final']:.0f} · {tipo} · fecha {_prazo(e)}",
        f"{(e['objeto_compra'] or '')[:220]}",
        f"🏛 {e['razao_social']} ({e['municipio']}/{e['uf']})",
        f"💰 estimado {_brl(e['valor_estimado'])} · investe {_brl(e.get('custo_estimado'))} · "
        f"sobra {_brl(e['margem_estimada'])}",
    ]
    if e.get("resumo_ia"):
        linhas.append(f"🤖 {e['resumo_ia'][:350]}")
    if e.get("riscos"):
        linhas.append("⚠️ " + "; ".join(e["riscos"].splitlines()[:2])[:220])
    linhas.append(f"🔗 {e['link_pncp']}")
    return "\n".join(linhas)


def terminal(editais: list[dict[str, Any]]) -> None:
    if not editais:
        print("\nNenhuma oportunidade nova nos filtros.")
        return
    print(f"\n{'═' * 72}\n  {len(editais)} OPORTUNIDADE(S)\n{'═' * 72}")
    for e in editais:
        print(f"\n{formatar(e)}\n{'─' * 72}")


def notificar(editais: list[dict[str, Any]], a_mais: int = 0) -> bool:
    """Oportunidades novas (já filtradas, melhores primeiro). True = pode marcar como avisadas."""
    terminal(editais)
    cfg = avisos()
    if not cfg["oportunidade"]:
        return True
    cab = f"📑 LiciBot: {len(editais)} licitação(ões) nova(s) que valem olhar"
    if a_mais:
        cab = (f"📑 LiciBot: {len(editais) + a_mais} licitações nos seus filtros. Aqui vão as {len(editais)} "
               f"melhores; as outras {a_mais} estão no painel.")
    texto = cab + "\n\n" + "\n\n".join(formatar(e) for e in editais)
    return _algum_ok(enviar_webhook("oportunidades", editais), enviar_telegram(texto, cfg))


def aviso_lembretes(editais: list[dict[str, Any]]) -> bool:
    cfg = avisos()
    if not cfg["lembrete_prazo"] or not editais:
        return True
    texto = "⏰ Fecham em menos de 24 h e você marcou ⭐ vou participar:\n\n" + "\n\n".join(
        f"• {_prazo(e)} — {(e['objeto_compra'] or '')[:140]}\n  {e['razao_social']} ({e['uf']})\n  {e['link_pncp']}"
        for e in editais)
    return _algum_ok(enviar_webhook("lembrete_prazo", editais), enviar_telegram(texto, cfg))


def aviso_erro(msg: str) -> None:
    cfg = avisos()
    if not cfg["erro"] or not _faz_tempo("erro", 6):
        return
    if _algum_ok(enviar_telegram(f"❌ LiciBot: a varredura quebrou.\n{msg[:600]}\n\nVeja a aba Log do painel.", cfg)):
        _marcar("erro")


def aviso_sem_credito(motivo: str, na_fila: int) -> None:
    cfg = avisos()
    if not cfg["sem_credito"] or not _faz_tempo("sem_credito", 12):
        return
    if _algum_ok(enviar_telegram(f"🪫 LiciBot: o modelo de IA está sem crédito ({motivo}). {na_fila} licitação(ões) "
                                 "esperando análise; seguem quando o crédito voltar.", cfg)):
        _marcar("sem_credito")


def aviso_resumo(r: dict[str, Any]) -> None:
    """Resumo diário, no horário escolhido (a varredura mais perto do horário manda)."""
    cfg = avisos()
    if not cfg["resumo_diario"] or not _faz_tempo("resumo", 20):
        return
    linhas = [f"📊 LiciBot — resumo de {datetime.now():%d/%m}",
              f"Abertas nos seus filtros: {r['abertas']} (fecham em 48 h: {r['fecha_48h']})",
              f"⭐ vou participar: {r['participar']}",
              f"Fila da IA: {r['fila']}",
              f"Melhores agora:"]
    for e in r["top"][:5]:
        linhas.append(f"• nota {e['nota_final']:.0f} · sobra {_brl(e['margem_estimada'])} · fecha {_prazo(e)} — "
                      f"{(e['objeto_compra'] or '')[:90]}")
    if _algum_ok(enviar_telegram("\n".join(linhas), cfg)):
        _marcar("resumo")


def testar() -> str:
    cfg = avisos()
    if not cfg["tg_token"] or not cfg["tg_chat"]:
        return "falta o token do bot ou o chat"
    ok = enviar_telegram("✅ LiciBot: teste do painel. Os avisos de licitação vão chegar aqui.", cfg)
    return "mensagem de teste enviada" if ok else "o Telegram recusou (confira o token e o chat; veja o log)"
