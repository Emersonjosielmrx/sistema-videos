#!/usr/bin/env python3
"""
Posta videos no TikTok via tiktok-uploader (headless=False + overlay patch).
Validado em 2026-07-06: upload + Post funciona com essa abordagem.

Uso:
  python tiktok_poster.py                          # posta 1 video aleatorio
  python tiktok_poster.py --max 5                  # posta ate 5
  python tiktok_poster.py --video path.mp4         # posta video especifico
  python tiktok_poster.py --cookies outro.json     # usa outro arquivo de cookies
"""
import json, time, sys, os, random, argparse, glob
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
COOKIES_DEFAULT = r'D:\credenciais-canais\tiktok_seebotsia_cookies.json'
VIDEOS_DIR = r'D:\hipercool-inferior-fix\roteador-veo-api-fake\videos\api_jobs'
POSTED_LOG = r'D:\hipercool-producao\logs\tiktok_posted.json'

DESCRIPTIONS = [
    'Curiosidades incriveis #curiosidades #viral #fyp #brasil',
    'Voce sabia disso? #curiosidades #viral #fyp #fatos',
    'Isso vai te surpreender #viral #fyp #brasil #curioso',
    'Fatos que ninguem te contou #curiosidades #fyp #viral',
    'Inacreditavel mas real #fatos #viral #fyp #brasil',
    'Voce nao vai acreditar #curiosidades #viral #fyp',
    'Top fatos insanos #viral #fyp #curiosidades #brasil',
    'Mundo maluco #curiosidades #fatos #viral #fyp',
]


def load_posted():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, 'r') as f:
            return json.load(f)
    return []


def save_posted(posted):
    os.makedirs(os.path.dirname(POSTED_LOG), exist_ok=True)
    with open(POSTED_LOG, 'w') as f:
        json.dump(posted, f, indent=2)


def get_unposted_videos(videos_dir):
    posted = load_posted()
    posted_files = set(p['file'] for p in posted)
    all_vids = glob.glob(os.path.join(videos_dir, '*.mp4'))
    return [v for v in all_vids if os.path.basename(v) not in posted_files]


def _remove_all_overlays(page):
    try:
        page.evaluate('''() => {
            let joyride = document.getElementById('react-joyride-portal');
            if(joyride) joyride.remove();
            document.querySelectorAll('[data-floating-ui-portal], [data-floating-ui-inert]').forEach(e => e.remove());
            document.querySelectorAll('.TUXModal-overlay, .react-joyride__overlay').forEach(e => e.remove());
            document.querySelectorAll('[data-test-id=overlay]').forEach(e => e.remove());
        }''')
        time.sleep(0.5)
    except:
        pass


def patched_complete_upload_form(page, path, description, schedule, skip_split_window,
                                  cover_path=None, product_id=None, visibility='everyone',
                                  num_retries=1, headless=False, *args, **kwargs):
    from tiktok_uploader.upload import (_go_to_upload, _remove_cookies_window,
                                         _set_video, _remove_split_window)
    _go_to_upload(page)
    _remove_cookies_window(page)
    _set_video(page, path=path, num_retries=num_retries, **kwargs)

    if not skip_split_window:
        _remove_split_window(page)

    for i in range(30):
        time.sleep(2)
        btns = page.evaluate('() => Array.from(document.querySelectorAll("button")).map(b => b.innerText.trim())')
        if 'Replace' in btns or 'Substituir' in btns:
            print(f'  Upload confirmed ({(i+1)*2}s)', flush=True)
            break
    else:
        print('  WARN: upload may not have completed', flush=True)

    _remove_all_overlays(page)
    time.sleep(1)

    try:
        page.evaluate('''() => {
            let editor = document.querySelector('[contenteditable=true]');
            if(editor) { editor.focus(); editor.textContent = ''; }
        }''')
        time.sleep(0.3)
        page.keyboard.type(description, delay=10)
        print(f'  Description set', flush=True)
    except Exception as e:
        print(f'  Description failed: {e}', flush=True)

    _remove_all_overlays(page)
    time.sleep(1)
    print('  Clicking Post...', flush=True)
    _remove_all_overlays(page)

    posted = False
    try:
        post_btn = page.locator('[data-e2e=post_video_button]')
        post_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
        post_btn.click(timeout=10000)
        posted = True
        print('  Post clicked via locator!', flush=True)
    except:
        pass

    if not posted:
        try:
            page.evaluate('() => { let b = document.querySelector("[data-e2e=post_video_button]"); if(b) b.click(); }')
            posted = True
            print('  Post clicked via JS!', flush=True)
        except:
            pass

    if not posted:
        try:
            page.evaluate('() => { let bs = document.querySelectorAll(".TUXButton--primary"); bs[bs.length-1].click(); }')
            posted = True
            print('  Post clicked via TUXButton!', flush=True)
        except Exception as e:
            print(f'  All post methods failed: {e}', flush=True)
            raise

    time.sleep(10)


def post_one(video_path, cookies_file, description):
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    video_path = type(video_path)(_g1080(video_path)) if not isinstance(video_path, str) else str(_g1080(video_path))
    import tiktok_uploader.upload as upload_mod
    from tiktok_uploader import upload_video

    upload_mod.complete_upload_form = patched_complete_upload_form

    with open(cookies_file, 'r') as f:
        raw_cookies = json.load(f)
    cookies_list = [{'name': c['name'], 'value': c['value'],
                     'domain': c['domain'], 'path': c['path']} for c in raw_cookies]

    print(f'Posting: {os.path.basename(video_path)}', flush=True)
    print(f'  Desc: {description}', flush=True)

    result = upload_video(
        filename=video_path,
        description=description,
        cookies_list=cookies_list,
        browser='chrome',
        headless=False,
    )

    success = not result
    if success:
        print('OK - Video postado!', flush=True)
    else:
        print(f'FALHOU: {result}', flush=True)
    return success


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', help='Video especifico pra postar')
    parser.add_argument('--max', type=int, default=1, help='Max videos pra postar')
    parser.add_argument('--cookies', default=COOKIES_DEFAULT)
    parser.add_argument('--videos-dir', default=VIDEOS_DIR)
    parser.add_argument('--delay', type=int, default=120, help='Delay entre posts (seg)')
    args = parser.parse_args()

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
    posted = load_posted()
    successes = 0

    for i, vid in enumerate(videos):
        desc = random.choice(DESCRIPTIONS)
        try:
            ok = post_one(vid, args.cookies, desc)
            if ok:
                successes += 1
                posted.append({
                    'file': os.path.basename(vid),
                    'description': desc,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'account': 'seebotsia',
                })
                save_posted(posted)
        except Exception as e:
            print(f'ERRO: {e}', flush=True)

        if i < len(videos) - 1:
            print(f'  Aguardando {args.delay}s antes do proximo...', flush=True)
            time.sleep(args.delay)

    print(f'\nResultado: {successes}/{len(videos)} postados com sucesso.', flush=True)


if __name__ == '__main__':
    main()
