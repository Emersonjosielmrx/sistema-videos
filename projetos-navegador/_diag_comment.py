"""Diagnóstico: abre um browser com perfil e testa a caixa de comentário."""
import sys, os, time, json, io, subprocess, socket

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, "D:/projetos-navegador")
sys.path.insert(0, "D:/projetos-navegador/shared")
os.chdir("D:/projetos-navegador")

from shared.google_session import PORT_MAP, get_profile_dir

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ACCOUNT = "inovaremanhwaverse"
PORT = PORT_MAP[ACCOUNT]
PROFILE = str(get_profile_dir(ACCOUNT))
VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Kill any chrome on this port
subprocess.run(["taskkill", "/F", "/FI", f"WINDOWTITLE eq *{PORT}*"], capture_output=True)
time.sleep(1)

print(f"Account: {ACCOUNT}")
print(f"Profile: {PROFILE}")
print(f"Port: {PORT}")

# Launch chrome WITHOUT headless for diagnosis
args = [
    CHROME,
    f"--user-data-dir={PROFILE}",
    f"--remote-debugging-port={PORT}",
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--mute-audio",
    "--disable-software-rasterizer",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-background-networking",
    "--no-sandbox",
    "--window-size=1366,768",
    "about:blank",
]
proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Wait for chrome
for i in range(12):
    time.sleep(2)
    try:
        s = socket.create_connection(("127.0.0.1", PORT), timeout=2)
        s.close()
        print(f"Chrome ready after {(i+1)*2}s")
        break
    except:
        continue
else:
    print("Chrome failed to start")
    proc.kill()
    sys.exit(1)

# Connect via Playwright CDP
from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
ctx = browser.contexts[0] if browser.contexts else browser.new_context()
page = ctx.new_page()

print(f"\nGoing to {VIDEO}...")
page.goto(VIDEO, timeout=30000, wait_until="domcontentloaded")
time.sleep(5)

# Check login status
login_status = page.evaluate("""() => {
    const avatar = document.querySelector('#avatar-btn, yt-img-shadow.ytd-topbar-menu-button-renderer img');
    const signin = document.querySelector('a[href*="accounts.google.com"], ytd-button-renderer.style-suggestive a[href*="ServiceLogin"]');
    if (signin) return 'NOT_LOGGED_IN: signin button found';
    if (avatar) return 'LOGGED_IN: avatar found';
    return 'UNKNOWN';
}""")
print(f"Login status: {login_status}")

# Scroll to comments
print("\nScrolling to comments...")
for i in range(6):
    page.keyboard.press("PageDown")
    time.sleep(1)

time.sleep(3)

# Check simplebox
print("\n=== SIMPLEBOX ANALYSIS ===")
analysis = page.evaluate("""() => {
    const result = {};

    // Check if comments section loaded
    const header = document.querySelector('ytd-comments-header-renderer');
    result.header_exists = !!header;
    if (header) {
        result.header_text = header.textContent.substring(0, 100).trim();
    }

    // Check simplebox
    const sb = document.querySelector('ytd-comment-simplebox-renderer');
    result.simplebox_exists = !!sb;
    if (sb) {
        result.simplebox_display = window.getComputedStyle(sb).display;
        result.simplebox_visibility = window.getComputedStyle(sb).visibility;
        result.simplebox_html = sb.innerHTML.substring(0, 2000);

        // Check all children
        const all = sb.querySelectorAll('*');
        result.child_count = all.length;
        const tags = [];
        for (const el of all) {
            const tag = el.tagName.toLowerCase();
            const id = el.id ? `#${el.id}` : '';
            const ce = el.getAttribute('contenteditable');
            const cls = el.className ? `.${String(el.className).split(' ')[0].substring(0,20)}` : '';
            const vis = window.getComputedStyle(el).display;
            tags.push(`${tag}${id}${cls}[ce=${ce||''}][d=${vis}]`);
        }
        result.children = tags;

        // Check #placeholder-area specifically
        const ph = sb.querySelector('#placeholder-area');
        if (ph) {
            const rect = ph.getBoundingClientRect();
            result.placeholder_rect = {
                x: rect.x, y: rect.y,
                width: rect.width, height: rect.height
            };
            result.placeholder_visible = rect.width > 0 && rect.height > 0;
        }

        // Check #comment-dialog
        const cd = sb.querySelector('#comment-dialog');
        if (cd) {
            result.comment_dialog_display = window.getComputedStyle(cd).display;
            result.comment_dialog_html = cd.innerHTML.substring(0, 500);
        }
    }

    // Check if there's a ytd-commentbox anywhere
    const cb = document.querySelector('ytd-commentbox');
    result.commentbox_exists = !!cb;
    if (cb) {
        result.commentbox_display = window.getComputedStyle(cb).display;
    }

    return result;
}""")

for k, v in analysis.items():
    if k == 'simplebox_html':
        print(f"\n{k}:\n{v[:500]}")
    elif k == 'children':
        print(f"\n{k} ({len(v)} elements):")
        for c in v:
            print(f"  {c}")
    else:
        print(f"{k}: {v}")

# Take screenshot
ss_path = "D:/projetos-navegador/_diag_comment_screenshot.png"
page.screenshot(path=ss_path, full_page=False)
print(f"\nScreenshot saved: {ss_path}")

# Now try clicking the placeholder and see what happens
print("\n=== TRYING TO CLICK placeholder-area ===")
try:
    page.click('#placeholder-area', timeout=5000)
    print("page.click('#placeholder-area') succeeded")
except Exception as e:
    print(f"page.click('#placeholder-area') FAILED: {e}")

time.sleep(3)

# Check again after click
after = page.evaluate("""() => {
    const result = {};
    const sb = document.querySelector('ytd-comment-simplebox-renderer');
    if (sb) {
        const all = sb.querySelectorAll('*');
        result.child_count = all.length;
        const tags = [];
        for (const el of all) {
            const tag = el.tagName.toLowerCase();
            const id = el.id ? `#${el.id}` : '';
            const ce = el.getAttribute('contenteditable');
            tags.push(`${tag}${id}[ce=${ce||''}]`);
        }
        result.children = tags;
    }

    // Check commentbox anywhere in page
    const cb = document.querySelector('ytd-commentbox');
    result.commentbox_exists = !!cb;
    if (cb) {
        result.commentbox_display = window.getComputedStyle(cb).display;
        result.commentbox_html = cb.innerHTML.substring(0, 500);
    }

    const ce = document.querySelector('#contenteditable-root, [contenteditable]');
    result.contenteditable_found = !!ce;
    if (ce) {
        result.ce_tag = ce.tagName;
        result.ce_id = ce.id;
    }

    return result;
}""")

print("\n=== AFTER CLICK ===")
for k, v in after.items():
    if isinstance(v, list):
        print(f"{k} ({len(v)} elements):")
        for c in v:
            print(f"  {c}")
    else:
        print(f"{k}: {v}")

# Screenshot after click
ss_path2 = "D:/projetos-navegador/_diag_comment_after_click.png"
page.screenshot(path=ss_path2, full_page=False)
print(f"\nScreenshot after click: {ss_path2}")

# Cleanup
page.close()
browser.close()
pw.stop()
proc.kill()
print("\nDone.")
