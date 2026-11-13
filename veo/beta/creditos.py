# -*- coding: utf-8 -*-
"""
========================================================================
creditos.py  —  Deteccao de "acabou o credito" no Google Flow
========================================================================

Este modulo concentra TODA a logica de detectar, no lado do WORKER
(gera_auto.py), que uma conta do Flow ficou sem creditos. Antes essa
logica vivia solta dentro do gera_auto.py; foi extraida pra ca pra ficar
facil de achar, entender e ajustar.

Como o Flow avisa que acabou o credito (2 formas, checamos as duas):
  1. TEXTO na pagina: aparece uma frase tipo "no credits available",
     "atingiu o limite diario", etc.  ->  creditos_esgotados(page)
  2. SALDO ZERO SEM AVISO: quando o saldo e exatamente 0, o Flow NAO
     mostra banner nenhum — a geracao simplesmente trava e da timeout de
     ~8 min. So o menu de conta mostra o numero real.
                                       ->  ler_saldo_creditos(page)

Contrato entre processos (NAO MUDAR sem mudar o cron junto):
  - O worker (gera_auto.py) levanta CreditosEsgotadosError, imprime no
    stdout a linha  CREDITOS_ESGOTADOS padrao='...'  e sai com exit code 2.
  - O orquestrador (cron_gerar_video_llm.py) le esse exit code / marcador,
    marca a sessao como EXHAUSTED ate a proxima meia-noite e pula pra
    proxima conta.  (Ver marcar_creditos_esgotados() no cron.)

Se voce for menos experiente: pra AJUSTAR quais frases contam como
"sem credito", edite so a lista PATTERNS abaixo.
"""
import re as _re
import datetime as _dt

# Frases que o Flow exibe quando a conta ficou sem creditos (PT-BR e EN).
# CUIDADO: alguns itens sao regex com word boundary (\b) pra nao dar falso
# positivo em "50 creditos" / "100 creditos".
PATTERNS = [
    "no credits available",          # EN (instrutivo)
    "nenhum cr",                     # PT-BR "nenhum credito/credito disponivel"
    r"\b0\s*cr",                     # regex: "0 creditos" mas nao "50 creditos"
    "0 credits left",                # EN
    "atingiu o limite di",           # PT-BR "atingiu o limite diario"
    "reached the daily limit",       # EN
    "atingiu o limite de g",         # PT-BR "atingiu o limite de geracao"
    "hit your generation limit",     # EN
    "seus cr",                       # PT-BR "seus creditos estao acabando"
    "low on credits",                # EN
]

# Alias historico (o codigo antigo importava esse nome). Mantido por compat.
_CREDITS_EXHAUSTED_PATTERNS = PATTERNS


class CreditosEsgotadosError(Exception):
    """Sessao sem creditos - pular pra proxima imediatamente."""


def creditos_esgotados(page):
    """Detecta se a pagina do Flow exibe algum sinal de creditos esgotados.

    Retorna (True, padrao_encontrado) se achar, (False, None) caso contrario.
    """
    try:
        texto = page.evaluate("() => document.body.innerText") or ""
    except Exception:
        return False, None
    if not texto:
        return False, None
    tlow = texto.lower()
    for pat in PATTERNS:
        if pat.startswith("\\b"):
            # Pattern regex com word boundary
            if _re.search(pat, tlow):
                return True, pat
        elif pat in tlow:
            return True, pat
    return False, None


# Menu da conta (UI de 12/10/2026, flow.google.com): painel role=dialog "Configurações da conta" / "Account settings".
# O Esc NAO fecha mais: so o X "Fechar painel da conta" / "Close account panel". Aberto, ele cobre o botao de enviar
# (era o "TIMEOUT" de 12-32 min por tentativa).
MENU_CONTA = ("div[role=dialog][aria-label='Configurações da conta'], "
              "div[role=dialog][aria-label='Account settings']")
_X_MENU_CONTA = ("button[aria-label='Fechar painel da conta'], button[aria-label='Close account panel'], "
                 "button[aria-label*='Fechar' i], button[aria-label*='Close' i]")
# "1.050 créditos do Google Flow" (PT) / "1,050 Google Flow credits" (EN)
_RE_SALDO = _re.compile(r"(\d[\d.,]*)\s*(?:cr[eé]ditos?\s+do\s+google\s+flow|google\s+flow\s+credits?)", _re.I)
_RE_SALDO_SOLTO = _re.compile(r"(\d[\d.,]*)\s*cr[eé]dit", _re.I)


def menu_conta_aberto(page):
    try:
        loc = page.locator(MENU_CONTA)
        return loc.count() > 0 and loc.first.is_visible()
    except Exception:
        return False


def fechar_menu_conta(page, log=print):
    """Fecha o menu da conta pelo X; se nao fechar, recarrega a pagina. True se ficou fechado."""
    if not menu_conta_aberto(page):
        return True
    try:
        page.locator(MENU_CONTA).first.locator(_X_MENU_CONTA).first.click(timeout=5000)
        page.wait_for_timeout(800)
    except Exception as e:
        log(f"[CREDITOS] X do menu da conta falhou: {type(e).__name__}")
    if not menu_conta_aberto(page):
        return True
    log("[CREDITOS] menu da conta nao fechou pelo X — recarregando a pagina")
    try:
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
    except Exception:
        pass
    return not menu_conta_aberto(page)


def ler_saldo_creditos(page, log=print):
    """Le o saldo de creditos abrindo o menu de conta (avatar canto sup direito) e FECHA o menu no fim.

    CRITICO: quando o saldo e 0, o Flow NAO mostra banner na pagina principal —
    a geracao simplesmente trava e da timeout de 480s. So o menu de conta mostra
    o numero real. Por isso checamos aqui ANTES de gerar.

    Retorna o saldo (int) ou None se nao conseguiu ler.
    """
    try:
        # Abre o menu de conta clicando no avatar/botao de conta
        clicked = page.evaluate("""() => {
            const els = [...document.querySelectorAll('button,[role="button"],img,[aria-label]')];
            for (const b of els) {
                const t = (b.getAttribute('aria-label') || b.alt || '');
                if (/conta do google|google account|sua conta|your account|perfil|profile/i.test(t)) {
                    b.click();
                    return t;
                }
            }
            return null;
        }""")
        if not clicked:
            return None
        try:
            page.locator(MENU_CONTA).first.wait_for(state="visible", timeout=6000)
            texto = page.locator(MENU_CONTA).first.inner_text(timeout=3000)
        except Exception:
            page.wait_for_timeout(1500)
            texto = page.evaluate("() => document.body.innerText") or ""
        m = _RE_SALDO.search(texto) or _RE_SALDO_SOLTO.search(texto)
        saldo = int(_re.sub(r"[.,]", "", m.group(1))) if m else None
        if saldo is not None:
            log(f"[CREDITOS] saldo lido no menu de conta: {saldo}")
        return saldo
    except Exception as e:
        log(f"[CREDITOS] nao consegui ler saldo: {str(e)[:60]}")
        return None
    finally:
        fechar_menu_conta(page, log)


def salvar_evidencia(page, log=print):
    """Salva screenshot + texto da pagina pra diagnostico quando creditos
    acabam. Ajuda a confirmar depois qual mensagem o Flow mostrou."""
    try:
        import os as _os
        _logs = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logs")
        _os.makedirs(_logs, exist_ok=True)
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        path_png = _os.path.join(_logs, f"creditos_esgotados_{ts}.png")
        page.screenshot(path=path_png, full_page=False)
        log(f"[CREDITOS] screenshot salvo: {path_png}")
        try:
            txt = page.evaluate("() => document.body.innerText") or ""
            txtpath = _os.path.join(_logs, f"creditos_esgotados_{ts}.txt")
            with open(txtpath, "w", encoding="utf-8") as f:
                f.write(txt[:5000])
            log(f"[CREDITOS] texto salvo: {txtpath}")
        except Exception:
            pass
    except Exception as e:
        log(f"[CREDITOS] nao consegui screenshot: {e}")
