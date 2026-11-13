import json
import time
import subprocess
import random
from pathlib import Path
from playwright.sync_api import sync_playwright

import sys
sys.path.append('D:/projetos-navegador/shared')
from google_session import ACCOUNTS, PORT_MAP, get_profile_dir

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

COMMENTS = [
    "Awesome video!", "Great content!", "I really enjoyed this, thanks!", 
    "Very helpful video.", "Nice explanation!", "Good job!", 
    "Keep up the great work!", "Interesting perspective.", 
    "Loved it!", "Brilliant video!", "This is exactly what I was looking for.",
    "Very informative, thanks!", "Amazing details here.", "Top tier!",
    "Fantastic!", "Thanks for sharing this.", "Loved the edit!",
    "This channel deserves more subs.", "Really well put together.",
    "Such a good video.", "Thanks for the content!", "Outstanding work!"
]

def kill_chrome():
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
    time.sleep(2)

def engage_with_account(account, videos):
    port = PORT_MAP.get(account)
    if not port: return []
        
    profile_dir = get_profile_dir(account)
    if not list(profile_dir.rglob("Cookies")):
        return []
        
    print(f"\n--- Iniciando {account} (porta {port}) ---")
    kill_chrome()
    
    proc = subprocess.Popen([
        CHROME_PATH, f'--user-data-dir={profile_dir}', f'--remote-debugging-port={port}', 
        '--headless=new', '--no-first-run', '--disable-gpu', 
        '--disable-software-rasterizer', '--window-size=1280,1080', 'about:blank'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)
    
    engaged_links = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{port}')
            ctx = browser.contexts[0]
            ctx.set_default_timeout(10000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            
            for i, video_url in enumerate(videos):
                print(f"[{account}] {i+1}/{len(videos)} | {video_url[-15:]}")
                try:
                    clean_url = video_url.split('&')[0]
                    page.goto(clean_url, timeout=30000, wait_until='domcontentloaded')
                    time.sleep(5)
                    
                    acted = False
                    
                    # LIKE
                    try:
                        is_liked = page.evaluate("() => { const btn = document.querySelector('like-button-view-model button'); if(!btn) return 'not_found'; if(btn.getAttribute('aria-pressed')==='true') return 'already'; btn.click(); return 'liked'; }")
                        if is_liked == 'liked': 
                            print('  ❤️  Like dado')
                            acted = True
                        elif is_liked == 'already': 
                            print('  🤍  Ja tinha like')
                    except Exception as e:
                        pass
                        
                    # COMMENTS
                    try:
                        for _ in range(5):
                            page.keyboard.press("PageDown")
                            time.sleep(1)
                            
                        has_box = False
                        for _ in range(6):
                            has_box = page.evaluate("() => !!document.querySelector('ytd-comment-simplebox-renderer')")
                            if has_box: break
                            time.sleep(1)
                            
                        if has_box:
                            page.evaluate("document.querySelector('ytd-comment-simplebox-renderer div#placeholder-area')?.click()")
                            time.sleep(1)
                            
                            comment_text = random.choice(COMMENTS)
                            jseval = f"""(t) => {{
                                const root = document.querySelector('#contenteditable-root');
                                if (root) {{
                                    root.textContent = t;
                                    root.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    setTimeout(() => {{
                                        const submit = document.querySelector('ytd-button-renderer#submit-button button, #submit-button');
                                        if (submit) {{
                                            submit.removeAttribute('disabled');
                                            submit.click();
                                        }}
                                    }}, 500);
                                }}
                            }}"""
                            page.evaluate(jseval, comment_text)
                            
                            print(f'  💬 Comentou: {comment_text}')
                            acted = True
                            time.sleep(2)
                        else:
                            print(f'  ⚠️ Comentarios nao carregaram')
                            
                    except Exception as e:
                        print(f'  ⚠️ Erro comment')
                    
                    if acted:
                        engaged_links.append(clean_url)
                        
                except Exception as e:
                    pass
                time.sleep(3)
                
            browser.close()
    except Exception as e:
        print(f"[{account}] Erro CDP: {str(e)[:60]}")

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
        
    return engaged_links

if __name__ == '__main__':
    all_videos = json.loads(Path('D:/projetos-navegador/target_videos.json').read_text('utf-8'))
    valid_accs = [acc for acc in PORT_MAP.keys() if list(get_profile_dir(acc).rglob("Cookies"))]
    print(f"Temos {len(valid_accs)} perfis com cookies")
    
    report_file = Path('D:/projetos-navegador/engajamento_report.txt')
    lines = ["RELATÓRIO DE ENGAJAMENTOS NAS CONTAS - VÍDEOS ALVO\n"]
    lines.append(f"Qtd Videos: {len(all_videos)}\n")
    
    total_actions = 0
    results = {}
    
    # IMPORTANTE: Desativando a interatividade e varrendo todos
    for i, acc in enumerate(valid_accs):
        print(f"\n[{i+1}/{len(valid_accs)}] Executando cross-engagement para a conta: {acc}")
        
        # Engajar em TODOS os vídeos da lista (foram selecionados 15 videos aleatórios dos canais)
        engaged_urls = engage_with_account(acc, all_videos)
        
        total_actions += len(engaged_urls)
        results[acc] = len(engaged_urls)
        
        lines.append(f"\nConta: {acc} engajou em {len(engaged_urls)} vídeos:")
        for url in engaged_urls:
            lines.append(f"  - {url}")
            
        # Salva o relatório parcialmente para garantir que não se perca num crash
        report_file.write_text("\n".join(lines), encoding='utf-8')
    
    # Wrap-up
    lines.append("\n\n========== RESUMO ==========")
    for acc, count in results.items():
        lines.append(f'{acc}: {count} vídeos engajados')
    lines.append(f"TOTAL DE ENGAJAMENTOS: {total_actions}")
    
    report_file.write_text("\n".join(lines), encoding='utf-8')
    print(f"\n\nPronto! Relatório salvo em {report_file}")
