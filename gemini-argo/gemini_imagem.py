#!/usr/bin/env python3
r"""gemini_imagem.py — Gera IMAGEM pelo app gemini.google.com (navegador oculto).

Segunda fonte de imagem, independente do Flow (D:\flow-imagens) e da API paga: usa a
cota de imagem do app web do Gemini, que é SEPARADA da cota de texto do Argon. Por isso
roda de preferência em contas que já esgotaram o Argon (a de texto zerada, a de imagem
não) — assim não gasta crédito de texto do Argon.

Reaproveita do gemini_argon.py: o cofre (abre o Chrome oculto pela saída fixa da conta),
a FILA de contas (proxima_conta/marcar_sem_cota/soltar) e a limpeza de conversa. Cada
conta fala só pela própria saída — não varre contas pelo mesmo IP (regra do CLAUDE.md).

Uso módulo:
    from gemini_imagem import gerar
    ok, detalhe = gerar("a red apple on a wooden table", r"D:\saida\maca.png")

Uso CLI:
    python -X utf8 -I gemini_imagem.py "um gato astronauta, arte digital" D:\saida\gato.png
    python -X utf8 -I gemini_imagem.py --conta murilodoctor192 "prompt" saida.png
    python -X utf8 -I gemini_imagem.py --visivel "prompt" saida.png      (depurar)
"""
import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\gemini-argo")   # -I tira a pasta do script do path
import cofre
import gemini_argon as ga  # fila de contas, cofre, utilidades já testadas

log = logging.getLogger("gemini_imagem")
if not log.handlers:
    logging.basicConfig(
        filename=str(Path(r"D:\gemini-argo") / "imagem.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

TIMEOUT_IMAGEM = 120   # geração de imagem leva segundos; 120 s é folga
RECUSA = ("can't create", "cannot create", "unable to", "não posso", "nao posso",
          "I'm not able", "I am unable", "policy", "violates")


def _enviar_prompt(pg, texto):
    """Digita o prompt no chat e envia (mesmo campo testado no mapeador)."""
    for sel in ('div[contenteditable="true"]', '[aria-label*="Ask Gemini"]',
                '[aria-label*="Gemini"]', 'div[role="textbox"]', ".ql-editor", "textarea"):
        try:
            campo = pg.locator(sel).first
            if campo.is_visible(timeout=3000):
                campo.click()
                time.sleep(0.3)
                pg.keyboard.insert_text(texto)
                time.sleep(0.6)
                if len(campo.inner_text(timeout=4000).strip()) < min(5, len(texto)):
                    continue
                pg.keyboard.press("Enter")
                return True
        except Exception:
            continue
    return False


def _esperar_imagem(pg, timeout_s=TIMEOUT_IMAGEM):
    """Espera aparecer uma imagem grande (>200px) na resposta do modelo.
    Retorna o locator da <img>, 'recusa' se o Gemini recusou em texto, ou None."""
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        # imagem grande na resposta = imagem gerada (ícones são pequenos)
        try:
            imgs = pg.locator('[data-message-author-role="model"] img, img').all()
            for im in imgs:
                try:
                    if not im.is_visible(timeout=200):
                        continue
                    box = im.bounding_box()
                    if box and box["width"] > 200 and box["height"] > 200:
                        # espera estabilizar (a imagem vem de uma vez, mas garante)
                        time.sleep(1.5)
                        return im
                except Exception:
                    continue
        except Exception:
            pass
        # recusa em texto (prompt bloqueado): não adianta esperar
        try:
            corpo = pg.locator('[data-message-author-role="model"]').last.inner_text(timeout=1500)
            if corpo and len(corpo) > 40 and any(r.lower() in corpo.lower() for r in RECUSA) \
                    and not pg.locator('[data-message-author-role="model"] img').count():
                return "recusa"
        except Exception:
            pass
        time.sleep(2)
    return None


def _baixar(pg, img, saida):
    """Clica em 'Download full size image' e salva o arquivo. Fallback: screenshot da <img>."""
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    # tenta o botão oficial de download (apareceu no mapeador)
    try:
        img.hover(timeout=3000)
    except Exception:
        pass
    for sel in ['button[aria-label*="Download full size"]', 'button[aria-label*="Download"]',
                'button[aria-label*="Baixar"]']:
        try:
            btn = pg.locator(sel).first
            if btn.is_visible(timeout=2500):
                with pg.expect_download(timeout=30000) as dl_info:
                    btn.click()
                dl_info.value.save_as(str(saida))
                if Path(saida).exists() and Path(saida).stat().st_size > 1000:
                    return True
        except Exception:
            continue
    # fallback: recorta a própria <img> (perde resolução máxima, mas salva algo)
    try:
        img.screenshot(path=str(saida))
        return Path(saida).exists() and Path(saida).stat().st_size > 1000
    except Exception:
        return False


def gerar(prompt, saida, conta=None, visivel=False, prints=False):
    """Gera uma imagem e salva em `saida`. Percorre a fila de contas: a que não gera por
    cota sai da fila com hora de volta e tenta a próxima. Retorna (ok, detalhe)."""
    from playwright.sync_api import sync_playwright

    tentadas, ultimo = 0, ""
    while tentadas < 6:
        try:
            apelido = conta or ga.proxima_conta()
        except RuntimeError as e:
            return False, f"sem conta pronta ({e})"
        tentadas += 1
        log.info("Gerando imagem com %s: %s", apelido, prompt[:60])
        porta, proc = cofre.abrir(apelido, url="about:blank", visivel=visivel)
        br = None
        pdir = str(Path(r"D:\gemini-argo\_teste_imagem")) if prints else None
        try:
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                pg = br.contexts[0].new_page()
                pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)
                ga._fechar_popup_idade(pg)

                if not _enviar_prompt(pg, prompt):
                    ga.marcar_uso(apelido, sucesso=False, erro_msg="não enviou prompt")
                    ultimo = "não achei o campo de texto"
                    continue

                res = _esperar_imagem(pg)
                if prints and pdir:
                    try: pg.screenshot(path=f"{pdir}/gerar_{apelido}.png")
                    except Exception: pass

                if res == "recusa":
                    # recusa é do prompt, não da conta: não penaliza a conta, não insiste
                    ga.marcar_uso(apelido, sucesso=True)
                    ga._limpar_conversa(pg)
                    return False, "Gemini recusou o prompt (política)"
                if res is None:
                    ga.marcar_uso(apelido, sucesso=False, erro_msg="sem imagem no tempo")
                    ultimo = "não gerou imagem (cota de imagem pode ter acabado)"
                    ga.marcar_sem_cota(apelido)  # provável cota de imagem esgotada
                    ga._limpar_conversa(pg)
                    continue

                if _baixar(pg, res, saida):
                    ga.marcar_uso(apelido, sucesso=True)
                    ga._limpar_conversa(pg)
                    return True, f"Gemini imagem ({apelido})"
                ga.marcar_uso(apelido, sucesso=False, erro_msg="gerou mas não baixou")
                ultimo = "gerou mas não consegui baixar"
                ga._limpar_conversa(pg)
        except Exception as e:
            log.error("erro com %s: %s", apelido, e)
            ga.marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            ultimo = str(e)[:100]
        finally:
            try: cofre.fechar(proc, br, apelido)
            except Exception: pass
            ga.soltar(apelido)
        if conta:   # conta fixa: não varre a fila
            break
    return False, f"falhou após {tentadas} conta(s): {ultimo}"


def main():
    ap = argparse.ArgumentParser(description="Gera imagem pelo app Gemini (navegador oculto)")
    ap.add_argument("prompt", help="descrição da imagem")
    ap.add_argument("saida", help="caminho do arquivo .png/.jpg de saída")
    ap.add_argument("--conta", help="apelido fixo (senão usa a fila do Argon)")
    ap.add_argument("--visivel", action="store_true", help="mostra o Chrome (depurar)")
    ap.add_argument("--prints", action="store_true", help="salva screenshots")
    args = ap.parse_args()
    ok, det = gerar(args.prompt, args.saida, conta=args.conta, visivel=args.visivel, prints=args.prints)
    print(("OK: " if ok else "FALHOU: ") + det)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
