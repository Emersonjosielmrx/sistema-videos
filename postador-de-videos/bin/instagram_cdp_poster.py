#!/usr/bin/env python3
"""Posta Reels no Instagram via Chrome CDP (sessao ja logada).

Mesma tecnica do tiktok_cdp_poster.py: controla Chrome real via WebSocket.
Nao precisa de token/API — usa a sessao do navegador.

Uso:
  python instagram_cdp_poster.py --video "D:/path/video.mp4" --caption "texto #hash"
  python instagram_cdp_poster.py --video "D:/path/video.mp4" --port 9401
  python instagram_cdp_poster.py --video "D:/path/video.mp4" --caption "texto" --port 9401
"""
import json
import sys
import time
import argparse
import urllib.request
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEFAULT_PORT = 9401
NOVO_POST = r"/novo reel|criar novo|new reel|create new/i"  # janela do post sendo criado
DEFAULT_CAPTION = "Energia solar que transforma #energiasolar #solar #fyp #viral"


def get_ws_url(port):
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=5)
    return json.loads(resp.read())["webSocketDebuggerUrl"]


def check_chrome(port):
    try:
        get_ws_url(port)
        return True
    except Exception:
        return False


def post_reel_cdp(video_path, port, caption):
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    import os as _os
    # 04/11: vídeo no disco da máquina remota (--remoto) não existe aqui — o 1080p já foi feito antes do envio; medir
    # aqui estourava int('') (mesmo defeito do TikTok, que derrubou todo post pelas máquinas desde 01/11)
    if _os.path.exists(str(video_path)):
        video_path = type(video_path)(_g1080(video_path)) if not isinstance(video_path, str) else str(_g1080(video_path))
    import websocket

    ws_url = get_ws_url(port)
    browser_ws = websocket.create_connection(ws_url, timeout=30)
    msg_id = [0]

    def send(method, params=None, session_id=None):
        msg_id[0] += 1
        msg = {"id": msg_id[0], "method": method}
        if params:
            msg["params"] = params
        if session_id:
            msg["sessionId"] = session_id
        browser_ws.send(json.dumps(msg))
        deadline = time.time() + 60
        while time.time() < deadline:
            resp = json.loads(browser_ws.recv())
            if resp.get("id") == msg_id[0]:
                return resp
        raise TimeoutError(f"Timeout waiting for response to {method}")

    def evaluate(expr, session_id):
        r = send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True,
        }, session_id)
        result = r.get("result", {}).get("result", {})
        return result.get("value")

    target_id = None
    session_id = None

    try:
        r = send("Target.createTarget", {"url": "about:blank"})
        target_id = r["result"]["targetId"]
        r = send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        session_id = r["result"]["sessionId"]

        send("Page.enable", {}, session_id)
        send("Runtime.enable", {}, session_id)
        send("DOM.enable", {}, session_id)

        # Navegar pro Instagram
        print("  Navegando pro Instagram...", flush=True)
        send("Page.navigate", {"url": "https://www.instagram.com/"}, session_id)
        time.sleep(10)

        # Checar se esta logado (aguarda pagina carregar)
        for _w in range(3):
            url = evaluate("window.location.href", session_id)
            if url and ("login" in url.lower() or "accounts" in url.lower()):
                print(f"  NAO LOGADO no Instagram (URL: {url})", flush=True)
                print(f"  >>> Abra a janela do Chrome (porta {port}) e faca login manual <<<", flush=True)
                return False
            time.sleep(2)

        # Checar se tem elementos de usuario logado
        logged = evaluate(
            '(() => {'
            '  let sels = ['
            '    "[aria-label=\'New post\']", "svg[aria-label=\'New post\']",'
            '    "[aria-label=\'Nova publicacao\']", "svg[aria-label=\'Nova publicacao\']",'
            '    "[aria-label=\'Criar\']", "svg[aria-label=\'Criar\']",'
            '    "[role=\'img\'][data-testid=\'user-avatar\']",'
            '    "img[data-testid=\'user-avatar\']",'
            '    "a[href*=\'direct\']", "nav a[href*=\'/direct/\']",'
            '    "[aria-label=\'Home\']", "[aria-label=\'Pagina inicial\']",'
            '  ];'
            '  for (let s of sels) {'
            '    if (document.querySelector(s)) return s;'
            '  }'
            '  return false;'
            '})()', session_id)
        print(f"  Logado: {logged}", flush=True)
        if not logged:
            cur_url = evaluate("window.location.href", session_id)
            print(f"  URL atual: {cur_url}", flush=True)
            print(f"  >>> Faca login manual na janela do Chrome (porta {port}) <<<", flush=True)
            return False

        # Clicar no botao "New post" / "Criar" (icone +)
        print("  Procurando botao de nova publicacao...", flush=True)

        clicked_new = False
        for attempt in range(15):
            clicked_new = evaluate(
                '(() => {'
                '  let labels = ["New post", "Nova publica\\u00e7\\u00e3o", "Criar", "Create"];'
                '  for (let lbl of labels) {'
                '    let el = document.querySelector("[aria-label=\\"" + lbl + "\\"]");'
                '    if (el) {'
                '      let link = el.closest("a") || el.closest("[role=link]") || el;'
                '      link.click();'
                '      return "aria:" + lbl;'
                '    }'
                '    let svg = document.querySelector("svg[aria-label=\\"" + lbl + "\\"]");'
                '    if (svg) {'
                '      let link = svg.closest("a") || svg.closest("[role=link]") || svg.parentElement;'
                '      link.click();'
                '      return "svg:" + lbl;'
                '    }'
                '  }'
                '  let links = document.querySelectorAll("a[href=\'#\'], a[role=\'link\'], div[role=\'button\']");'
                '  for (let l of links) {'
                '    let txt = (l.textContent || "").trim().toLowerCase();'
                '    if (txt === "criar" || txt === "create" || txt === "new post") {'
                '      l.click();'
                '      return "text:" + txt;'
                '    }'
                '  }'
                '  let spans = document.querySelectorAll("span");'
                '  for (let s of spans) {'
                '    let txt = (s.textContent || "").trim().toLowerCase();'
                '    if (txt === "criar" || txt === "create") {'
                '      let clickable = s.closest("a") || s.closest("div[role=button]") || s.closest("[tabindex]") || s.parentElement;'
                '      if (clickable) { clickable.click(); return "span:" + txt; }'
                '    }'
                '  }'
                '  return false;'
                '})()', session_id)

            if clicked_new:
                print(f"  Botao clicado: {clicked_new}", flush=True)
                break
            time.sleep(2)
        else:
            print("  ERRO: nao encontrou botao de criar post apos 30s", flush=True)
            return False

        # Esperar submenu e clicar em "Postar" / "Post" (Instagram mostra submenu apos Criar)
        time.sleep(2)
        for _sub in range(8):
            clicked_post = evaluate(
                '(() => {'
                '  let items = document.querySelectorAll("a, div[role=button], button, span");'
                '  for (let el of items) {'
                '    let txt = (el.textContent || "").trim().toLowerCase();'
                '    if (txt === "postar" || txt === "post") {'
                '      let clickable = el.closest("a") || el.closest("div[role=button]") || el;'
                '      clickable.click();'
                '      return "sub:" + txt;'
                '    }'
                '  }'
                '  return false;'
                '})()', session_id)
            if clicked_post:
                print(f"  Submenu clicado: {clicked_post}", flush=True)
                break
            time.sleep(1)

        # Esperar o dialog de upload aparecer
        time.sleep(3)

        # Procurar input[type=file]
        print("  Procurando input de arquivo...", flush=True)

        file_input_ready = False
        for attempt in range(20):
            has_input = evaluate(
                'document.querySelector("input[type=file]") ? true : false',
                session_id
            )
            if has_input:
                file_input_ready = True
                break

            # Tentar clicar em "Selecionar do computador" / "Select from computer"
            evaluate(
                '(() => {'
                '  let btns = document.querySelectorAll("button");'
                '  for (let b of btns) {'
                '    let txt = (b.textContent || "").trim().toLowerCase();'
                '    if (txt.includes("selecionar") || txt.includes("select from") || txt.includes("computador") || txt.includes("computer")) {'
                '      b.click();'
                '      return true;'
                '    }'
                '  }'
                '  return false;'
                '})()', session_id)
            time.sleep(2)

        if not file_input_ready:
            print("  ERRO: input[type=file] nao encontrado apos 40s", flush=True)
            return False

        # Injetar arquivo via DOM.setFileInputFiles
        r = send("DOM.getDocument", {}, session_id)
        root_node_id = r["result"]["root"]["nodeId"]
        r = send("DOM.querySelector", {
            "nodeId": root_node_id,
            "selector": "input[type=file]"
        }, session_id)
        file_node_id = r["result"]["nodeId"]

        # 06/11: vários arquivos separados por "|" = CARROSSEL (o "Criar" do Instagram aceita várias fotos de uma vez)
        arquivos = [x.replace("\\", "/") for x in str(video_path).split("|") if x]
        send("DOM.setFileInputFiles", {
            "nodeId": file_node_id,
            "files": arquivos
        }, session_id)
        print(f"  Arquivo injetado: {Path(video_path).name}", flush=True)

        # Esperar processamento do video
        print("  Aguardando processamento do video...", flush=True)
        for i in range(60):
            time.sleep(3)
            has_next = evaluate(
                '(() => {'
                '  let btns = document.querySelectorAll("button, div[role=button]");'
                '  for (let b of btns) {'
                '    let txt = (b.textContent || "").trim().toLowerCase();'
                '    if (txt === "avan\\u00e7ar" || txt === "next" || txt === "pr\\u00f3ximo" || txt === "proximo") {'
                '      return true;'
                '    }'
                '  }'
                '  return false;'
                '})()', session_id)
            if has_next:
                print(f"  Video processado ({(i+1)*3}s)", flush=True)
                break
        else:
            print("  WARN: timeout esperando processamento (180s) — tentando continuar", flush=True)

        # Clicar "Avançar" / "Next" (2-3 vezes — crop, filtros, caption)
        for step_name in ["crop/ajuste", "filtros", "caption"]:
            time.sleep(2)
            clicked = evaluate(
                '(() => {'
                '  let btns = document.querySelectorAll("button, div[role=button]");'
                '  for (let b of btns) {'
                '    let txt = (b.textContent || "").trim().toLowerCase();'
                '    if (txt === "avan\\u00e7ar" || txt === "next" || txt === "pr\\u00f3ximo" || txt === "proximo") {'
                '      b.click();'
                '      return true;'
                '    }'
                '  }'
                '  return false;'
                '})()', session_id)
            if clicked:
                print(f"  Avançar ({step_name}) clicado", flush=True)
            else:
                print(f"  Avançar ({step_name}) nao encontrado — pode ja estar adiante", flush=True)
            time.sleep(2)

        # Preencher caption
        time.sleep(2)
        print("  Preenchendo caption...", flush=True)

        # 19/10: o editor (Lexical) ignora textContent/execCommand e a legenda saía vazia: foca o campo DENTRO da
        # janela do novo post e digita pela CDP
        foco = evaluate(
            '(() => { const d = [...document.querySelectorAll("[role=dialog]")].find(x => ' + NOVO_POST + '.test(x.innerText));'
            ' const e = d && d.querySelector("[contenteditable=true], textarea"); if (!e) return false; e.focus();'
            ' return e.getAttribute("aria-label") || e.tagName; })()', session_id)
        if foco:
            send("Input.insertText", {"text": caption}, session_id)
            time.sleep(1)
            lido = evaluate('(() => { const e = document.activeElement; return e ? (e.innerText || e.value || "") : ""; })()',
                            session_id)
            print(f"  Caption digitada em {foco!r}: {str(lido)[:60]!r}", flush=True)
        safe_caption = caption.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
        wrote_caption = foco or evaluate(
            '(() => {'
            '  let ta = document.querySelector("textarea[aria-label]");'
            '  if (ta) {'
            '    ta.focus();'
            '    ta.value = "";'
            "    let setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;"
            '    setter.call(ta, "' + safe_caption + '");'
            "    ta.dispatchEvent(new Event('input', { bubbles: true }));"
            "    ta.dispatchEvent(new Event('change', { bubbles: true }));"
            '    return "textarea";'
            '  }'
            '  let editors = document.querySelectorAll("[contenteditable=true], [role=textbox]");'
            '  for (let e of editors) {'
            '    let ph = (e.getAttribute("aria-label") || e.getAttribute("placeholder") || e.dataset.placeholder || "").toLowerCase();'
            '    if (ph.includes("legen") || ph.includes("caption") || ph.includes("escrev") || ph.includes("write")) {'
            '      e.focus();'
            '      e.textContent = "";'
            '      document.execCommand("insertText", false, "' + safe_caption + '");'
            '      return "contenteditable:" + ph;'
            '    }'
            '  }'
            '  if (editors.length > 0) {'
            '    editors[0].focus();'
            '    editors[0].textContent = "";'
            '    document.execCommand("insertText", false, "' + safe_caption + '");'
            '    return "contenteditable:fallback";'
            '  }'
            '  return false;'
            '})()', session_id)

        if wrote_caption:
            print(f"  Caption preenchida via {wrote_caption}", flush=True)
        else:
            print("  WARN: nao encontrou campo de caption — continuando sem", flush=True)

        # Clicar "Compartilhar" / "Share"
        time.sleep(2)
        print("  Clicando Compartilhar...", flush=True)
        shared = False

        # 19/10: so dentro da janela do novo post - na pagina inteira o 1o "Compartilhar" era o de um post do feed
        # atras da janela (abria o envio por mensagem e o Reel nunca saia)
        for attempt in range(10):
            result = evaluate(
                '(() => { const d = [...document.querySelectorAll("[role=dialog]")].find(x => ' + NOVO_POST + '.test(x.innerText));'
                '  if (!d) return false;'
                '  const b = [...d.querySelectorAll("button, div[role=button]")].find(b =>'
                '    /^(compartilhar|share|publicar|publish)$/i.test((b.textContent || "").trim()));'
                '  if (!b) return false; b.click(); return b.textContent.trim(); })()', session_id)
            if result:
                shared = True
                print(f"  Compartilhar clicado: '{result}'", flush=True)
                break
            time.sleep(2)

        if not shared:
            print("  ERRO: nao encontrou botao Compartilhar/Share", flush=True)
            return False

        # Esperar confirmacao de postagem. 19/10: com 90 s o Reel de 84 s ainda subia e fechar a aba cortava o envio;
        # o Instagram de hoje diz "Seu reel foi compartilhado"
        print("  Aguardando confirmacao...", flush=True)
        for i in range(100):
            time.sleep(3)
            done = evaluate(
                '(() => /(reel|publica\\u00e7\\u00e3o|post)( foi)? (foi )?compartilhad|has been shared|was shared/i'
                '.test(document.body.innerText))()', session_id)
            if done:
                print(f"  POSTADO com sucesso! ({(i+1)*3}s)", flush=True)
                return True

        try:
            import base64
            shot = send("Page.captureScreenshot", {"format": "png"}, session_id)["result"]["data"]
            dest = Path(r"C:\Users\Haylla\AppData\Local\Temp\q_veo") / f"ig_sem_confirmacao_{port}.png"
            dest.write_bytes(base64.b64decode(shot))
            print(f"  print: {dest}", flush=True)
        except Exception:
            pass
        print("  Share clicado mas confirmacao textual nao detectada — provavel sucesso", flush=True)
        return True

    except Exception as e:
        print(f"  ERRO: {e}", flush=True)
        return False
    finally:
        if target_id:
            try:
                send("Target.closeTarget", {"targetId": target_id})
            except Exception:
                pass
        try:
            browser_ws.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Posta Reel no Instagram via Chrome CDP")
    parser.add_argument("--video", required=True, help="Caminho do video MP4")
    parser.add_argument("--caption", default=DEFAULT_CAPTION, help="Texto + hashtags")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta CDP do Chrome")
    parser.add_argument("--remoto", action="store_true",
                        help="Chrome de outra máquina (notebook): --video é o caminho LÁ, já enviado (maquina_remota.py)")
    args = parser.parse_args()

    if not args.remoto and not all(Path(x).exists() for x in args.video.split("|")):
        print(f"ERRO: video nao encontrado: {args.video}", flush=True)
        sys.exit(1)

    if not check_chrome(args.port):
        print(f"ERRO: Chrome nao disponivel na porta {args.port}", flush=True)
        print("Inicie com: start_cdp_instagram.bat", flush=True)
        sys.exit(1)

    print(f"Chrome CDP na porta {args.port} OK", flush=True)
    print(f"Video: {args.video}", flush=True)
    print(f"Caption: {args.caption[:80]}...", flush=True)

    ok = post_reel_cdp(args.video, args.port, args.caption)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
