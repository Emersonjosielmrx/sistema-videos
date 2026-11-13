import json, time, subprocess, random, sys, os
from pathlib import Path
from playwright.sync_api import sync_playwright

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

def kill_by_pid(proc):
    """Mata apenas o Chrome que EU abri, nao todos."""
    if proc and proc.poll() is None:
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True)
        except:
            pass
        try:
            proc.wait(timeout=3)
        except:
            proc.kill()

def engage_with_retry(account, videos):
    port = PORT_MAP.get(account)
    if not port: return []
    profile_dir = get_profile_dir(account)
    if not list(profile_dir.rglob("Cookies")): return []
    
    print(f"\n--- {account} (porta {port}) - {len(videos)} videos ---")
    engaged = []
    
    for i, video_url in enumerate(videos):
        clean_url = video_url.split('&')[0]
        print(f"[{account}] {i+1}/{len(videos)} | {clean_url[-20:]}")
        
        proc = subprocess.Popen([
            CHROME_PATH, f'--user-data-dir={profile_dir}', f'--remote-debugging-port={port}', 
            '--headless=new', '--no-first-run', '--disable-gpu', 
            '--disable-software-rasterizer', '--window-size=1280,1080', 'about:blank'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(7)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{port}')
                ctx = browser.contexts[0]
                ctx.set_default_timeout(10000)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                
                page.goto(clean_url, timeout=30000, wait_until='domcontentloaded')
                time.sleep(5)
                
                acted = False
                
                # LIKE
                try:
                    r = page.evaluate("() => { const btn = document.querySelector('like-button-view-model button'); if(!btn) return 'nf'; if(btn.getAttribute('aria-pressed')==='true') return 'al'; btn.click(); return 'ok'; }")
                    if r == 'ok': 
                        print('  ❤️  Like')
                        acted = True
                    elif r == 'al':
                        print('  🤍  Ja curtiu')
                        acted = True
                except: pass
                
                # COMMENT
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
                        js = """(t) => {
                            const root = document.querySelector('#contenteditable-root');
                            if (root) {
                                root.textContent = t;
                                root.dispatchEvent(new Event('input', { bubbles: true }));
                                setTimeout(() => {
                                    const submit = document.querySelector('ytd-button-renderer#submit-button button, #submit-button');
                                    if (submit) { submit.removeAttribute('disabled'); submit.click(); }
                                }, 500);
                            }
                        }"""
                        page.evaluate(js, comment_text)
                        print(f'  💬 {comment_text[:25]}')
                        acted = True
                        time.sleep(2)
                except: pass
                
                if acted:
                    engaged.append(clean_url)
                
                browser.close()
        except Exception as e:
            print(f'  ⚠️ {str(e)[:40]}')
        
        kill_by_pid(proc)
        time.sleep(2)
    
    return engaged

if __name__ == '__main__':
    all_videos = json.loads(Path('D:/projetos-navegador/target_videos.json').read_text('utf-8'))
    
    needs_retry = [
        'mundosolar1995', 'canalalucinaai', 'seebotsia',
        'gameoftroneskingsroadbrasil', 'inovaremanhwaversethai',
        'inovaremanhwaverseita', 'inovaremanhwaverseesp',
        'inovaremanhwaverseind', 'inovaremanhwaverseing',
        'inovaremanhwaverse', 'mentoriaiapro', 'msenergypara'
    ]
    
    report = Path('D:/projetos-navegador/engajamento_report_batch2.txt')
    lines = ["RELATÓRIO BATCH 2 - Cross-engagement retry\n"]
    
    for acc in needs_retry:
        urls = engage_with_retry(acc, all_videos)
        lines.append(f"Conta {acc}: {len(urls)} engajamentos")
        for u in urls:
            lines.append(f"  - {u}")
        report.write_text("\n".join(lines), encoding='utf-8')
        print(f"\n>>> {acc}: {len(urls)} OK <<<")
    
    lines.append("\n--- FIM ---")
    report.write_text("\n".join(lines), encoding='utf-8')
    print("\nBatch 2 finalizado!")
