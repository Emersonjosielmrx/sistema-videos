"""Testa se um Chrome profile tem sessao TikTok ativa."""
import json, urllib.request, time, sys, os

profile_path = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv) > 2 else 9270

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
try:
    resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=5)
    ws_url = json.loads(resp.read())['webSocketDebuggerUrl']
except:
    print('CHROME_OFF', flush=True)
    sys.exit(1)

from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
b = pw.chromium.connect_over_cdp(ws_url)
ctx = b.contexts[0]
page = ctx.new_page()

result = 'ERRO'
try:
    page.goto('https://www.tiktok.com/tiktokstudio/upload', timeout=30000)
    time.sleep(15)
    
    url = page.url
    if 'login' in url.lower() or 'signup' in url.lower():
        result = 'NAO_LOGADO'
    elif 'upload' in url.lower() or 'studio' in url.lower():
        try:
            has_input = page.evaluate('() => !!document.querySelector("input[type=file]")')
        except:
            has_input = False
        if has_input:
            result = 'LOGADO'
        else:
            time.sleep(10)
            try:
                url2 = page.url
                if 'login' in url2.lower():
                    result = 'NAO_LOGADO'
                else:
                    has_input = page.evaluate('() => !!document.querySelector("input[type=file]")')
                    result = 'LOGADO' if has_input else 'NAO_LOGADO'
            except:
                result = 'NAO_LOGADO'
    else:
        result = 'NAO_LOGADO'
except Exception as e:
    err = str(e)[:60]
    if 'navigation' in err.lower() or 'destroyed' in err.lower():
        time.sleep(5)
        try:
            url = page.url
            result = 'NAO_LOGADO' if 'login' in url.lower() else 'LOGADO'
        except:
            result = 'NAO_LOGADO'
    else:
        result = f'ERRO:{err}'

print(result, flush=True)
sys.stdout.flush()
try:
    page.close()
except:
    pass
os._exit(0)
