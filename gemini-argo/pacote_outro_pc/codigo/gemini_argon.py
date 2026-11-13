#!/usr/bin/env python3
r"""gemini_argon.py — Automação do Gemini Argon (4 Argon) via navegador.

Abre o Chrome com uma conta Pro do cofre, seleciona o modelo 4 Argon com raciocínio alto,
envia a pergunta e coleta a resposta completa.

Uso como módulo:
    from gemini_argon import perguntar
    resposta = perguntar("Explique quantum computing", conta="emersonjosiel2029")

Uso CLI:
    python gemini_argon.py "Explique quantum computing"
    python gemini_argon.py --conta emersonjosiel2029 "Explique quantum computing"

O cofre (D:\logins-google\cofre.py) gerencia perfis e portas CDP.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre

LOG_DIR = Path(r"D:\gemini-argo")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "argon.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("argon")

CONTAS_ARQUIVO = LOG_DIR / "contas_argon.json"
TIMEOUT_RESPOSTA = 540  # abaixo dos 600 s do antigravity-cc-proxy na VPS
DESBLOQUEIO_MIN = 30


# ─────────────────────── gerenciamento de contas ───────────────────────────
def _ler_contas():
    if CONTAS_ARQUIVO.exists():
        return json.loads(CONTAS_ARQUIVO.read_text(encoding="utf-8"))
    return {"contas": [], "indice": 0}


def _gravar_contas(dados):
    """27/10: proxy (várias threads) e classificar_pro gravam ao mesmo tempo; o .tmp único e o os.replace com o
    arquivo aberto noutro processo davam "[WinError 5] Acesso negado" e derrubavam o pedido do Argon."""
    import threading
    tmp = CONTAS_ARQUIVO.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    for tentativa in range(20):
        try:
            os.replace(tmp, CONTAS_ARQUIVO)
            return
        except PermissionError:
            time.sleep(0.05 * (tentativa + 1))
    tmp.unlink(missing_ok=True)
    log.warning("contas_argon.json preso por outro processo: estado da rotação desta chamada não gravado")


def adicionar_conta(email):
    """Adiciona uma conta Pro à lista de rotação."""
    dados = _ler_contas()
    email = email.strip().lower()
    if not email.endswith("@gmail.com"):
        email += "@gmail.com"
    apelido = email.split("@")[0]
    if any(c["email"] == email for c in dados["contas"]):
        print(f"Conta {email} já está na lista")
        return
    dados["contas"].append({
        "email": email,
        "apelido": apelido,
        "bloqueada": False,
        "ultimo_uso": None,
        "erros_seguidos": 0,
    })
    _gravar_contas(dados)
    print(f"Conta {email} adicionada ({len(dados['contas'])} total)")


# 27/10 (dona: "como o OmniRoute: fila, saber quando cada conta volta, não testar todas"): FILA em vez de rodízio.
# Usa a primeira conta com cota até ela acabar; a que acaba sai com hora de volta (espera que começa em 15 min, dobra
# se na volta ainda não tem cota, até 3 h, e zera quando responde); sem nenhuma pronta = erro na hora.
# _EM_USO: pedidos em andamento neste processo; conta ocupada vai pro fim da fila (pedidos em paralelo usam outras).
ESPERA_INICIAL_MIN, ESPERA_MAX_MIN = 15, 180
_EM_USO = {}


def proxima_conta():
    """Apelido da primeira conta pronta na fila (com cota, não bloqueada); a menos ocupada se todas estão em uso."""
    dados = _ler_contas()
    if not dados["contas"]:
        raise RuntimeError("Nenhuma conta cadastrada em contas_argon.json. Use: adicionar_conta('email')")
    from datetime import datetime, timedelta
    agora = datetime.now()
    prontas = []
    for c in dados["contas"]:
        if c.get("bloqueada") and c.get("ultimo_uso") and \
                agora - datetime.fromisoformat(c["ultimo_uso"]) > timedelta(minutes=DESBLOQUEIO_MIN):
            c["bloqueada"] = False
            c["erros_seguidos"] = 0
            log.info("Conta %s desbloqueada após %d min", c["apelido"], DESBLOQUEIO_MIN)
        if c.get("bloqueada") or (c.get("sem_cota_ate") and agora.isoformat() < c["sem_cota_ate"]):
            continue
        prontas.append(c["apelido"])
    if not prontas:
        volta = min((c["sem_cota_ate"] for c in dados["contas"] if c.get("sem_cota_ate")), default=None)
        raise RuntimeError("Nenhuma conta com cota do Argon agora" + (f" (a 1ª volta {volta[11:16]})" if volta else ""))
    escolhida = min(prontas, key=lambda a: _EM_USO.get(a, 0))  # min é estável: a 1ª da fila entre as menos ocupadas
    _EM_USO[escolhida] = _EM_USO.get(escolhida, 0) + 1
    return escolhida


def soltar(apelido):
    """Fim do pedido nesta conta (par do proxima_conta)."""
    if _EM_USO.get(apelido, 0) > 0:
        _EM_USO[apelido] -= 1


def marcar_sem_cota(apelido, horas="auto", volta=None):
    """A cota do Argon da conta acabou (o Gemini passou a responder com o Flash-Lite): sai da fila até a hora de volta.
    volta = epoch EXATO que o Gemini informa na resposta (o mesmo do navegador); sem ele, horas="auto" = espera que
    se ajusta (15 min, dobra a cada vez seguida, até 3 h); número = horas fixas; horas=None = libera (a cota voltou)."""
    from datetime import datetime, timedelta
    dados = _ler_contas()
    for c in dados["contas"]:
        if c["apelido"] == apelido:
            if horas is None:
                c.pop("sem_cota_ate", None)
                c.pop("espera_min", None)
                c.pop("volta_exata", None)
                continue
            if volta:
                c["sem_cota_ate"] = datetime.fromtimestamp(volta + 60).isoformat(timespec="minutes")
                c["volta_exata"] = True
                log.warning("Conta %s sem cota do Argon: volta %s (hora do Google)", apelido, c["sem_cota_ate"][11:16])
                continue
            c["volta_exata"] = False
            if horas == "auto":
                espera = min(ESPERA_MAX_MIN, c.get("espera_min", ESPERA_INICIAL_MIN // 2) * 2)
                c["espera_min"] = espera
            else:
                espera = horas * 60
            c["sem_cota_ate"] = (datetime.now() + timedelta(minutes=espera)).isoformat(timespec="minutes")
            log.warning("Conta %s sem cota do Argon: volta %s (espera %d min)", apelido, c["sem_cota_ate"][11:16], espera)
    _gravar_contas(dados)


def marcar_uso(apelido, sucesso=True, erro_msg=None):
    """Registra uso de uma conta (sucesso ou erro)."""
    dados = _ler_contas()
    from datetime import datetime
    for c in dados["contas"]:
        if c["apelido"] == apelido:
            c["ultimo_uso"] = datetime.now().isoformat(timespec="minutes")
            if sucesso:
                c["erros_seguidos"] = 0
                c.pop("espera_min", None)  # respondeu com o Argon: a próxima falta de cota começa a espera do zero
                c.pop("sem_cota_ate", None)
            else:
                c["erros_seguidos"] = c.get("erros_seguidos", 0) + 1
                if c["erros_seguidos"] >= 3:
                    c["bloqueada"] = True
                    log.warning("Conta %s bloqueada após 3 erros seguidos: %s", apelido, erro_msg)
            break
    _gravar_contas(dados)


# ─────────────────────── automação do navegador ────────────────────────────
def _fechar_popup_idade(pg):
    """Fecha o popup 'Confirme sua idade' clicando em Continuar. Espera a página estabilizar depois."""
    fechou = False
    for texto_btn in ["Continuar", "Continue"]:
        try:
            btn = pg.locator(f'button:has-text("{texto_btn}")').first
            if btn.is_visible(timeout=3000):
                btn.click()
                log.info("Popup de idade fechado (%s)", texto_btn)
                fechou = True
                break
        except Exception:
            pass

    if fechou:
        # Depois de confirmar a idade, o Gemini pode recarregar ou redirecionar
        time.sleep(5)
        # Se saiu da página do Gemini, voltar
        if "gemini.google.com" not in pg.url:
            pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
        # Esperar o botão de modelo ficar visível
        for _ in range(10):
            try:
                btn = pg.locator('button[aria-label*="seletor de modo"]').first
                if btn.is_visible(timeout=2000):
                    return True
            except Exception:
                pass
            time.sleep(1)

    return fechou


def _abrir_dropdown_modelo(pg):
    """Abre o dropdown de seleção de modelo clicando no botão (Flash, Pro, Argon...).
    O aria-label do botão é 'Abrir seletor de modo. No momento: <modelo>'."""
    # Seletor mais confiável: aria-label
    for sel in ['button[aria-label*="seletor de modo"]', 'button[aria-label*="model selector"]',
                'button:has-text("Flash")', 'button:has-text("Argon")',
                'button:has-text("Pro")', 'button:has-text("Flash Lite")']:
        try:
            btn = pg.locator(sel).first
            if btn.is_visible(timeout=3000):
                btn.click()
                time.sleep(1.5)
                return True
        except Exception:
            continue
    log.warning("Não achei o botão do seletor de modelo")
    return False


def _selecionar_argon(pg):
    """Seleciona o modelo 4 Argon no seletor de modelo."""
    if not _abrir_dropdown_modelo(pg):
        return False

    # Clicar em "Argon" — pode ser "4 Argon" com texto em elementos separados
    for sel in ['text=Argon', 'text=4 Argon',
                '[role="option"]:has-text("Argon")', '[role="menuitem"]:has-text("Argon")',
                'div:has-text("Argon"):has-text("Tarefas")',
                'div:has-text("Argon"):has-text("complex")']:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                log.info("Modelo Argon selecionado via: %s", sel)
                time.sleep(2)
                return True
        except Exception:
            continue

    log.warning("Não consegui selecionar o modelo 4 Argon")
    return False


def _configurar_raciocinio_alto(pg):
    """Configura nível de raciocínio para Alto.

    O fluxo é: abrir dropdown de modelo → clicar "Nível de raciocínio >" → sub-menu aparece
    à esquerda com Baixo/Médio/Alto → clicar "Alto".
    """
    if not _abrir_dropdown_modelo(pg):
        return False

    # Clicar em "Nível de raciocínio" (botão com seta)
    for sel in ['text=Nível de raciocínio', 'text=Reasoning level',
                'button:has-text("raciocínio")', 'button:has-text("Reasoning")']:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                log.info("Sub-menu de raciocínio aberto")
                time.sleep(1.5)
                break
        except Exception:
            continue
    else:
        log.warning("Não achei 'Nível de raciocínio'")
        pg.keyboard.press("Escape")
        return False

    # Clicar em "Alto" (Muito detalhado)
    for sel in ['text=Alto', 'text=High',
                'div:has-text("Alto"):has-text("detalhado")',
                'div:has-text("High"):has-text("detailed")']:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                log.info("Raciocínio configurado para Alto")
                time.sleep(1)
                # Fechar menus clicando fora
                pg.keyboard.press("Escape")
                time.sleep(0.5)
                return True
        except Exception:
            continue

    log.warning("Não achei opção 'Alto'")
    pg.keyboard.press("Escape")
    return False


def _enviar_pergunta(pg, texto):
    """Digita a pergunta no campo e envia."""
    seletores_campo = [
        'div[contenteditable="true"]',
        '[aria-label*="Peça ao Gemini"]',
        '[aria-label*="Ask Gemini"]',
        'div[role="textbox"]',
        '.ql-editor',
        'textarea',
    ]
    for sel in seletores_campo:
        try:
            campo = pg.locator(sel).first
            if campo.is_visible(timeout=3000):
                campo.click()
                time.sleep(0.3)
                # insertText do CDP: texto longo de uma vez, sem mexer na área de transferência do PC
                pg.keyboard.insert_text(texto)
                time.sleep(0.5 + len(texto) / 200000)
                if len(campo.inner_text(timeout=5000).strip()) < min(5, len(texto)):
                    log.error("Texto não entrou no campo")
                    return False
                pg.keyboard.press("Enter")
                log.info("Pergunta enviada (%d chars)", len(texto))
                return True
        except Exception:
            continue

    log.error("Não achei o campo de texto")
    return False


def _coletar_resposta(pg, timeout_s=TIMEOUT_RESPOSTA):
    """Espera o Gemini terminar de responder e coleta o texto completo."""
    log.info("Aguardando resposta (timeout %ds)...", timeout_s)
    inicio = time.time()

    # Esperar a resposta começar a aparecer (o Argon com raciocínio alto pode demorar)
    time.sleep(5)

    ultimo_texto = ""
    estavel_desde = None
    sem_texto_count = 0

    while time.time() - inicio < timeout_s:
        try:
            # O Gemini usa message-content para as respostas do modelo
            # Tentar vários seletores do mais específico ao mais genérico
            texto_atual = ""
            for sel in [
                '[data-message-author-role="model"] .markdown-content',
                '[data-message-author-role="model"]',
                '.model-response-text',
                '.response-content',
                'message-content',
                # Fallback: pegar o último bloco grande que não seja o input
                'div.response-container',
            ]:
                try:
                    els = pg.locator(sel).all()
                    for el in els:
                        t = el.inner_text(timeout=2000).strip()
                        if len(t) > len(texto_atual):
                            texto_atual = t
                except Exception:
                    continue
                if texto_atual:
                    break

            if not texto_atual:
                sem_texto_count += 1
                if sem_texto_count > 30:
                    # Fallback: pegar todo o texto visível e filtrar
                    try:
                        body = pg.inner_text("main", timeout=5000)
                        # Remover o texto do input e menus
                        linhas = body.split("\n")
                        # As primeiras linhas são menus, as últimas podem ser o input
                        meio = "\n".join(linhas[5:-3]).strip()
                        if len(meio) > 20:
                            texto_atual = meio
                    except Exception:
                        pass
                if not texto_atual:
                    time.sleep(2)
                    continue

            sem_texto_count = 0
            if texto_atual != ultimo_texto:
                ultimo_texto = texto_atual
                estavel_desde = time.time()
            elif estavel_desde and time.time() - estavel_desde > 8:
                # Texto estável por 8 segundos — verificar se terminou
                gerando = False
                for stop_sel in ['button[aria-label*="Stop"]', 'button[aria-label*="Parar"]',
                                 'button[aria-label*="stop"]', '[class*="loading-indicator"]',
                                 'mat-spinner', '[role="progressbar"]']:
                    try:
                        if pg.locator(stop_sel).first.is_visible(timeout=500):
                            gerando = True
                            break
                    except Exception:
                        pass

                if not gerando:
                    log.info("Resposta completa (%d chars, %.1fs)", len(texto_atual), time.time() - inicio)
                    return texto_atual

        except Exception as e:
            log.debug("Erro ao coletar: %s", e)

        time.sleep(2)

    if ultimo_texto:
        log.warning("Timeout, retornando resposta parcial (%d chars)", len(ultimo_texto))
        return ultimo_texto

    log.error("Timeout sem nenhuma resposta")
    return None


def _limpar_conversa(pg):
    """Clica em 'Nova conversa' pra limpar o histórico."""
    try:
        btn = pg.locator('text=Nova conversa').first
        if not btn.is_visible(timeout=2000):
            btn = pg.locator('text=New chat').first
        if btn.is_visible(timeout=2000):
            btn.click()
            time.sleep(2)
            return True
    except Exception:
        pass
    # Alternativa: navegar de volta
    try:
        pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        return True
    except Exception:
        return False


# ─────────────────────── função principal ──────────────────────────────────
def perguntar(texto, conta=None, raciocinio_alto=True, visivel=False, print_dir=None):
    """Envia uma pergunta ao Gemini Argon e retorna a resposta.

    Args:
        texto: A pergunta/prompt.
        conta: Apelido ou email da conta (None = próxima da rotação).
        raciocinio_alto: Se True, configura o nível de raciocínio para Alto.
        visivel: Se True, mostra o Chrome na tela.
        print_dir: Se informado, salva screenshots do processo nesse diretório.

    Returns:
        str com a resposta, ou None se falhou.
    """
    from playwright.sync_api import sync_playwright

    apelido = conta or proxima_conta()
    log.info("Perguntando com conta %s (%d chars)", apelido, len(texto))

    # Limpar RAM antes de abrir navegador
    try:
        cofre._liberar_ram if hasattr(cofre, '_liberar_ram') else None
    except Exception:
        pass

    porta, proc = cofre.abrir(apelido, url="about:blank", visivel=visivel)
    br = None
    resposta = None

    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0]
            pg = ctx.new_page()

            # 1. Navegar pro Gemini
            pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)

            # 2. Fechar popup de idade se aparecer
            _fechar_popup_idade(pg)
            if print_dir:
                pg.screenshot(path=f"{print_dir}/01_pagina.png")

            # 3. Selecionar modelo 4 Argon
            if not _selecionar_argon(pg):
                marcar_uso(apelido, sucesso=False, erro_msg="Argon não disponível")
                return None
            if print_dir:
                pg.screenshot(path=f"{print_dir}/02_argon.png")

            # 4. Configurar raciocínio alto
            if raciocinio_alto:
                _configurar_raciocinio_alto(pg)
                if print_dir:
                    pg.screenshot(path=f"{print_dir}/03_raciocinio.png")

            # 5. Enviar pergunta
            if not _enviar_pergunta(pg, texto):
                marcar_uso(apelido, sucesso=False, erro_msg="Não conseguiu enviar")
                return None
            if print_dir:
                time.sleep(2)
                pg.screenshot(path=f"{print_dir}/04_enviado.png")

            # 6. Coletar resposta
            resposta = _coletar_resposta(pg)
            if print_dir:
                pg.screenshot(path=f"{print_dir}/05_resposta.png")

            if resposta:
                marcar_uso(apelido, sucesso=True)
                log.info("Resposta recebida (%d chars)", len(resposta))
            else:
                marcar_uso(apelido, sucesso=False, erro_msg="Sem resposta")

            # 7. Limpar conversa
            _limpar_conversa(pg)

    except Exception as e:
        log.error("Erro ao perguntar com %s: %s", apelido, e)
        marcar_uso(apelido, sucesso=False, erro_msg=str(e))
        raise
    finally:
        cofre.fechar(proc, br, apelido)

    return resposta


# ─────────────────────── CLI ───────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Perguntar ao Gemini Argon via navegador")
    parser.add_argument("pergunta", nargs="?", help="Texto da pergunta")
    parser.add_argument("--conta", help="Apelido ou email da conta")
    parser.add_argument("--adicionar", help="Adicionar uma conta Pro à rotação")
    parser.add_argument("--listar", action="store_true", help="Listar contas cadastradas")
    parser.add_argument("--visivel", action="store_true", help="Mostrar o Chrome")
    parser.add_argument("--prints", action="store_true", help="Salvar screenshots")
    parser.add_argument("--sem-raciocinio", action="store_true", help="Não configurar raciocínio alto")
    args = parser.parse_args()

    if args.adicionar:
        adicionar_conta(args.adicionar)
        return

    if args.listar:
        dados = _ler_contas()
        for c in dados["contas"]:
            status = "BLOQUEADA" if c.get("bloqueada") else "ok"
            print(f"  {c['apelido']:35} {status:10} erros={c.get('erros_seguidos', 0)} ultimo={c.get('ultimo_uso', '-')}")
        print(f"Total: {len(dados['contas'])}, próxima: índice {dados.get('indice', 0)}")
        return

    if not args.pergunta:
        parser.print_help()
        return

    print_dir = str(LOG_DIR) if args.prints else None
    r = perguntar(args.pergunta, conta=args.conta, raciocinio_alto=not args.sem_raciocinio,
                  visivel=args.visivel, print_dir=print_dir)
    if r:
        print(r)
    else:
        print("ERRO: Sem resposta", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
