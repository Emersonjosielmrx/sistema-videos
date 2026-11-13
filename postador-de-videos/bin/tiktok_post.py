#!/usr/bin/env python3
"""
Posta video no TikTok via Chrome CDP (seebotsia/fabricadeautomacoesia).
STATUS: NÃO FUNCIONA - TikTok Web Studio tem anti-bot no botão Post.
Upload funciona mas click no Post é bloqueado por proteção JS.
Alternativa: TikTok Content Posting API (precisa app review) ou manual.
Chrome deve estar rodando na porta TIKTOK_CDP_PORT (default 9251).
"""
import time, json, sys, os, urllib.request
from playwright.sync_api import sync_playwright

VIDEO = sys.argv[1] if len(sys.argv) > 1 else r'D:\hipercool-inferior-fix\roteador-veo-api-fake\videos\api_jobs\1d5c2c36cfe340f8a0ce44190f8d2969.mp4'
CAPTION = sys.argv[2] if len(sys.argv) > 2 else '#curiosidades #viral #fyp #brasil'
PORT = int(os.environ.get('TIKTOK_CDP_PORT', '9251'))

def get_ws_url():
    resp = urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version')
    return json.loads(resp.read())['webSocketDebuggerUrl']

def main():
    ws_url = get_ws_url()
    pw = sync_playwright().start()
    b = pw.chromium.connect_over_cdp(ws_url)
    ctx = b.contexts[0]
    
    if not ctx.pages:
        page = ctx.new_page()
    else:
        page = ctx.pages[0]
    
    page.set_viewport_size({'width': 1280, 'height': 1200})
    
    body = page.evaluate('() => document.body.innerText')
    if 'Select video' not in body:
        page.goto('https://www.tiktok.com/creator#/upload?scene=creator_center', 
                  wait_until='domcontentloaded', timeout=20000)
        time.sleep(6)
    
    body = page.evaluate('() => document.body.innerText')
    if 'Select video' not in body:
        print(f'ERRO: pagina nao carregou upload. Body: {body[:200]}')
        os._exit(1)
    
    # Upload
    print(f'Uploading: {VIDEO}')
    file_input = page.locator('input[type=file]').first
    file_input.set_input_files(VIDEO)
    
    for i in range(30):
        time.sleep(2)
        txt = page.evaluate('() => document.body.innerText')
        if 'Uploaded' in txt:
            print(f'Upload OK ({(i+1)*2}s)')
            break
    else:
        print('ERRO: timeout upload')
        os._exit(1)
    
    time.sleep(3)
    
    # Remover modais
    page.evaluate('() => document.querySelectorAll("[data-floating-ui-portal]").forEach(e => e.remove())')
    time.sleep(1)
    
    # Scroll pro Post
    page.evaluate('() => { let b = document.querySelector("[data-e2e=post_video_button]"); if(b) b.scrollIntoView({block:"center"}); }')
    time.sleep(1)
    
    # Click Post
    print('Clicking Post...')
    try:
        page.locator('[data-e2e=post_video_button]').click(timeout=8000)
        print('Click OK via locator')
    except:
        box = page.locator('[data-e2e=post_video_button]').bounding_box()
        if box:
            page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            print('Click via mouse coords')
        else:
            print('ERRO: botao Post nao encontrado')
            os._exit(1)
    
    time.sleep(15)
    
    final = page.evaluate('() => document.body.innerText')
    if 'Manage your posts' in final or 'Your videos' in final:
        print('SUCESSO! Video postado!')
        os._exit(0)
    elif 'Select video' in final:
        print('PROVAVEL SUCESSO (voltou pro inicio)')
        os._exit(0)
    else:
        lines = [l.strip() for l in final.split('\n') if l.strip()][:8]
        print('Estado final:')
        for l in lines:
            print(f'  {l}')
        # Pode ser que ainda esta processando
        print('Video pode nao ter postado (TikTok anti-bot)')
        os._exit(2)

if __name__ == '__main__':
    main()
