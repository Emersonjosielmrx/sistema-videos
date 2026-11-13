#!/usr/bin/env python3
"""
Posta videos no TikTok via Chrome CDP (sessao ja logada).
Mais confiavel que tiktok-uploader porque usa a sessao real do Chrome.
Validado 2026-07-06 com contas mundosolar (9222) e seebotsia (9251).

Uso:
  python tiktok_cdp_poster.py                       # posta 1 video na porta 9222
  python tiktok_cdp_poster.py --max 3               # posta ate 3
  python tiktok_cdp_poster.py --port 9251           # usa Chrome na porta 9251
  python tiktok_cdp_poster.py --ports 9222,9251     # alterna entre contas
"""
import json, time, sys, os, random, argparse, glob, re, urllib.request
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
VIDEOS_DIR = r'D:\hipercool-inferior-fix\roteador-veo-api-fake\videos\api_jobs'
POSTED_LOG = r'D:\hipercool-producao\logs\tiktok_posted.json'

# Reserva, so quando ninguem manda --desc. Sem #viral/#fyp (AB-04, 16/10: hashtag generica e padrao de spam).
DESCRIPTIONS = [
    'Curiosidades incriveis #curiosidades #brasil',
    'Voce sabia disso? #curiosidades #fatos',
    'Isso vai te surpreender #brasil #curioso',
    'Fatos que ninguem te contou #curiosidades',
    'Inacreditavel mas real #fatos #brasil',
    'Voce nao vai acreditar #curiosidades',
    'Top fatos insanos #curiosidades #brasil',
    'Mundo maluco #curiosidades #fatos',
]


def load_posted():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, 'r') as f:
            return json.load(f)
    return []


def save_posted(posted):
    # 22/10 (P05): troca atômica + utf-8 (antes era write direto sem encoding; truncado = repostagem)
    os.makedirs(os.path.dirname(POSTED_LOG), exist_ok=True)
    tmp = POSTED_LOG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(posted, f, indent=2, ensure_ascii=False)
    os.replace(tmp, POSTED_LOG)


def get_unposted_videos(videos_dir):
    posted = load_posted()
    posted_files = set(p['file'] for p in posted)
    all_vids = glob.glob(os.path.join(videos_dir, '*.mp4'))
    return [v for v in all_vids if os.path.basename(v) not in posted_files]


def get_ws_url(port):
    resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=5)
    return json.loads(resp.read())['webSocketDebuggerUrl']


def check_chrome(port):
    try:
        get_ws_url(port)
        return True
    except:
        return False


def post_one_cdp(video_path, port, description):
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    import os as _os
    if _os.path.exists(str(video_path)):  # 01/11: caminho do desktop/notebook não existe aqui (1080p feito antes do envio)
        video_path = type(video_path)(_g1080(video_path)) if not isinstance(video_path, str) else str(_g1080(video_path))
    import websocket

    ws_url = get_ws_url(port)
    browser_ws = websocket.create_connection(ws_url, timeout=120)
    msg_id = [0]

    def send(ws, method, params=None, session_id=None):
        msg_id[0] += 1
        msg = {'id': msg_id[0], 'method': method}
        if params:
            msg['params'] = params
        if session_id:
            msg['sessionId'] = session_id
        ws.send(json.dumps(msg))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == msg_id[0]:
                return resp

    def send_no_wait(ws, method, params=None, session_id=None):
        msg_id[0] += 1
        msg = {'id': msg_id[0], 'method': method}
        if params:
            msg['params'] = params
        if session_id:
            msg['sessionId'] = session_id
        ws.send(json.dumps(msg))

    def evaluate(ws, expr, session_id):
        r = send(ws, 'Runtime.evaluate', {
            'expression': expr,
            'returnByValue': True,
            'awaitPromise': True
        }, session_id)
        result = r.get('result', {}).get('result', {})
        return result.get('value')

    try:
        r = send(browser_ws, 'Target.createTarget', {'url': 'about:blank'})
        target_id = r['result']['targetId']
        r = send(browser_ws, 'Target.attachToTarget', {'targetId': target_id, 'flatten': True})
        session_id = r['result']['sessionId']

        send(browser_ws, 'Page.enable', {}, session_id)
        send(browser_ws, 'Runtime.enable', {}, session_id)
        send(browser_ws, 'DOM.enable', {}, session_id)

        send_no_wait(browser_ws, 'Page.navigate', {'url': 'https://www.tiktok.com/tiktokstudio/upload'}, session_id)
        time.sleep(15)

        url = evaluate(browser_ws, 'window.location.href', session_id)
        if url and 'login' in url.lower():
            print(f'  SKIP port {port}: not logged in (url={url})', flush=True)
            send(browser_ws, 'Target.closeTarget', {'targetId': target_id})
            browser_ws.close()
            return False

        # 19/10: com a produção usando a CPU toda o TikTok Studio levava > 45 s pra montar e o post falhava
        for attempt in range(40):
            has_input = evaluate(browser_ws, 'document.querySelector("input[type=file]") ? true : false', session_id)
            if has_input:
                break
            time.sleep(3)
        else:
            print('  ERROR: file input not found after 120s', flush=True)
            print(f"  pagina: {evaluate(browser_ws, 'window.location.href', session_id)} | "
                  f"{evaluate(browser_ws, 'document.body ? document.body.innerText.slice(0, 300) : \"\"', session_id)!r}",
                  flush=True)
            send(browser_ws, 'Target.closeTarget', {'targetId': target_id})
            browser_ws.close()
            return False

        r = send(browser_ws, 'DOM.getDocument', {}, session_id)
        root_node_id = r['result']['root']['nodeId']
        r = send(browser_ws, 'DOM.querySelector', {'nodeId': root_node_id, 'selector': 'input[type=file]'}, session_id)
        file_node_id = r['result']['nodeId']

        video_path_fixed = video_path.replace('\\', '/')
        send(browser_ws, 'DOM.setFileInputFiles', {'nodeId': file_node_id, 'files': [video_path_fixed]}, session_id)
        print(f'  File set, waiting for upload...', flush=True)

        for i in range(40):
            time.sleep(3)
            btns = evaluate(browser_ws, 'Array.from(document.querySelectorAll("button")).map(b => b.innerText.trim())', session_id)
            if btns and any(x in btns for x in ['Replace', 'Substituir', 'Substituir vídeo', 'Carregar']):
                if i > 1:
                    print(f'  Upload confirmed ({(i+1)*3}s)', flush=True)
                    break
        else:
            print('  WARN: upload timeout', flush=True)

        time.sleep(2)
        evaluate(browser_ws, '(() => { let j = document.getElementById("react-joyride-portal"); if(j) j.remove(); document.querySelectorAll("[data-floating-ui-portal]").forEach(e => e.remove()); document.querySelectorAll(".TUXModal-overlay").forEach(e => e.remove()); })()', session_id)
        time.sleep(1)

        # O editor da legenda (Draft.js) ignora textContent/execCommand: espera o TikTok por o nome do arquivo,
        # limpa com Ctrl+A + Backspace de verdade e digita pela CDP; confere o texto no fim.
        ler = '(() => { let e = document.querySelector("[contenteditable=true]"); return e ? e.innerText.trim() : null; })()'
        for _ in range(10):
            if evaluate(browser_ws, ler, session_id):
                break
            time.sleep(1)

        def tecla(key, code, vk, mods=0):
            for tipo in ('keyDown', 'keyUp'):
                send(browser_ws, 'Input.dispatchKeyEvent', {'type': tipo, 'key': key, 'code': code,
                                                            'windowsVirtualKeyCode': vk, 'modifiers': mods}, session_id)

        lido = None
        for _ in range(3):
            evaluate(browser_ws, '(() => { let e = document.querySelector("[contenteditable=true]"); if(e) e.focus(); })()', session_id)
            time.sleep(0.3)
            tecla('a', 'KeyA', 65, 2)
            tecla('Backspace', 'Backspace', 8)
            time.sleep(0.5)
            if evaluate(browser_ws, ler, session_id):
                continue
            send(browser_ws, 'Input.insertText', {'text': description}, session_id)
            time.sleep(1.5)
            lido = evaluate(browser_ws, ler, session_id)
            if lido and re.sub(r'\s', '', lido) == re.sub(r'\s', '', description):
                break
        print(f'  Description set: {lido!r}', flush=True)
        time.sleep(1)

        evaluate(browser_ws, '(() => { let j = document.getElementById("react-joyride-portal"); if(j) j.remove(); document.querySelectorAll("[data-floating-ui-portal]").forEach(e => e.remove()); })()', session_id)
        time.sleep(1)

        # Publicar so habilita quando o envio termina; clicar antes nao faz nada (3o post do dia sumia em 15/10)
        estado_botao = '(() => { let b = document.querySelector("[data-e2e=post_video_button]"); if(!b) return "sem"; return (b.disabled || b.getAttribute("aria-disabled") === "true" || b.getAttribute("data-disabled") === "true") ? "off" : "on"; })()'
        for _ in range(60):
            if evaluate(browser_ws, estado_botao, session_id) != 'off':
                break
            time.sleep(2)
        print(f'  Botao Publicar: {evaluate(browser_ws, estado_botao, session_id)}', flush=True)

        print('  Clicking Post...', flush=True)
        posted = False

        result = evaluate(browser_ws, '(() => { let b = document.querySelector("[data-e2e=post_video_button]"); if(b) { b.scrollIntoView(); b.click(); return true; } return false; })()', session_id)
        if result:
            posted = True
            print('  Post clicked via data-e2e!', flush=True)

        if not posted:
            result = evaluate(browser_ws, '(() => { let bs = document.querySelectorAll(".TUXButton--primary"); if(bs.length) { bs[bs.length-1].click(); return true; } return false; })()', session_id)
            if result:
                posted = True
                print('  Post clicked via TUXButton!', flush=True)

        if not posted:
            print('  All click methods failed', flush=True)

        # So conta como postado quando o TikTok confirma (sai da tela de envio ou mostra a msg de publicado);
        # janela "publicar agora?" (verificacao de conteudo ainda rodando) e confirmada.
        confirmado = False
        ultimo = None
        sonda = r'''(() => {
            const dlg = Array.from(document.querySelectorAll('[role=dialog], .TUXModal, [class*="modal" i]')).filter(d => d.offsetParent);
            const bts = dlg.flatMap(d => Array.from(d.querySelectorAll("button"))).map(b => b.innerText.trim()).filter(x => x);
            const t = document.body.innerText;
            const ok = /foi publicad|v[ií]deo publicad|publicado com sucesso|has been posted|video posted|your video is being uploaded|gerenciar (suas )?publica|manage your posts|carregar outro|upload another/i.test(t);
            return {url: location.href, bts: bts, ok: ok};
        })()'''
        for i in range(30 if posted else 0):
            time.sleep(2)
            st = evaluate(browser_ws, sonda, session_id) or {}
            if (st.get('url'), st.get('bts')) != ultimo:
                print(f"  apos clicar: url={st.get('url', '')[:70]} botoes={st.get('bts')}", flush=True)
                ultimo = (st.get('url'), st.get('bts'))
            if st.get('ok') or '/upload' not in (st.get('url') or '/upload'):
                confirmado = True
                break
            alvo = next((b for b in st.get('bts') or [] if b.lower() in ('publicar agora', 'postar agora', 'post now', 'publicar', 'postar')), None)
            if alvo:
                evaluate(browser_ws, f'''(() => {{ const d = Array.from(document.querySelectorAll('[role=dialog], .TUXModal, [class*="modal" i]')).filter(d => d.offsetParent);
                    const b = d.flatMap(x => Array.from(x.querySelectorAll("button"))).find(b => b.innerText.trim() === {json.dumps(alvo)}); if (b) b.click(); }})()''', session_id)
                print(f'  confirmou janela: {alvo}', flush=True)
        print('  Post confirmed' if confirmado else '  NAO CONFIRMADO: TikTok nao mostrou publicado', flush=True)

        time.sleep(3)
        send(browser_ws, 'Target.closeTarget', {'targetId': target_id})
        browser_ws.close()
        return confirmado

    except Exception as e:
        print(f'  ERROR: {e}', flush=True)
        try:
            send(browser_ws, 'Target.closeTarget', {'targetId': target_id})
        except:
            pass
        browser_ws.close()
        return False


def post_one_subprocess(video_path, port, description):
    """Roda o post em subprocess pra isolamento"""
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    # 04/11: o conserto de 01/11 (linha do post_one_cdp) não chegou AQUI — com o vídeo no disco do desktop/notebook
    # (C:\postador-worker\entrada\...) o ffprobe deste PC voltava vazio, int('') estourava e TODO post pelas máquinas
    # falhava ("invalid literal for int() with base 10: ''": 9 em 01/11, 42 em 02/11, 37 em 03/11). O 1080p desses já
    # foi garantido no arquivo local antes do envio.
    if os.path.exists(str(video_path)):
        video_path = type(video_path)(_g1080(video_path)) if not isinstance(video_path, str) else str(_g1080(video_path))
    import subprocess
    code = f'''
import sys, os
sys.path.insert(0, r'D:\\postador-de-videos\\bin')
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from tiktok_cdp_poster import post_one_cdp
result = post_one_cdp({str(video_path)!r}, {port}, {description!r})
sys.exit(0 if result else 1)
'''
    # 16/10: repr() e nao '...' - a legenda da fala do video tem quebra de linha e apostrofo, que quebravam o codigo
    result = subprocess.run(
        [sys.executable, '-u', '-c', code],
        capture_output=True, text=True, timeout=400,
        env={**os.environ, 'PYTHONUTF8': '1'}
    )
    output = result.stdout + result.stderr
    print(output, end='', flush=True)
    return 'Post confirmed' in output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', help='Video especifico')
    parser.add_argument('--max', type=int, default=1)
    parser.add_argument('--desc', default=None, help='Legenda do video (catalogo.legenda_reuso); sem ela, a lista')
    parser.add_argument('--port', type=int, default=None, help='Single CDP port')
    parser.add_argument('--ports', default='9222,9251,9261', help='Comma-separated CDP ports to alternate')
    parser.add_argument('--videos-dir', default=VIDEOS_DIR)
    parser.add_argument('--delay', type=int, default=90, help='Delay entre posts (seg)')
    args = parser.parse_args()

    if args.port:
        ports = [args.port]
    else:
        ports = [int(p) for p in args.ports.split(',')]

    available_ports = [p for p in ports if check_chrome(p)]
    if not available_ports:
        print('ERRO: nenhum Chrome disponivel nas portas configuradas.', flush=True)
        return

    print(f'Chrome disponivel nas portas: {available_ports}', flush=True)

    if args.video:
        videos = [args.video]
    else:
        videos = get_unposted_videos(args.videos_dir)
        random.shuffle(videos)
        videos = videos[:args.max]

    if not videos:
        print('Nenhum video novo pra postar.', flush=True)
        return

    print(f'Videos pra postar: {len(videos)}', flush=True)
    posted_log = load_posted()
    successes = 0

    for i, vid in enumerate(videos):
        port = available_ports[i % len(available_ports)]
        desc = args.desc or random.choice(DESCRIPTIONS)  # 16/10: o postar_tiktok_auto manda a legenda do video
        print(f'\n[{i+1}/{len(videos)}] {os.path.basename(vid)} -> porta {port}', flush=True)

        try:
            ok = post_one_subprocess(vid, port, desc)
            if ok:
                successes += 1
                posted_log.append({
                    'file': os.path.basename(vid),
                    'description': desc,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'account': f'cdp_{port}',
                    'method': 'cdp',
                })
                save_posted(posted_log)
        except Exception as e:
            print(f'ERRO: {e}', flush=True)

        if i < len(videos) - 1:
            print(f'  Aguardando {args.delay}s...', flush=True)
            time.sleep(args.delay)

    print(f'\nResultado: {successes}/{len(videos)} postados.', flush=True)


if __name__ == '__main__':
    main()
