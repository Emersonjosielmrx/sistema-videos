"""
Test script: verifica se comentários funcionam localmente no PC1
"""
import sys
import time
import random
import subprocess
from pathlib import Path

# Add paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "engage_modules"))
sys.path.insert(0, str(BASE_DIR / "shared"))

from playwright.sync_api import sync_playwright
from google_session import get_profile_dir, PORT_MAP

# Config
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEST_ACCOUNT = "aulacomia"
TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print(f"[TEST] Launching Chrome for {TEST_ACCOUNT}...")

# Get profile and port
profile_dir = get_profile_dir(TEST_ACCOUNT)
port = PORT_MAP.get(TEST_ACCOUNT, 9222)

# Launch Chrome
proc = subprocess.Popen([
    CHROME_PATH,
    f"--user-data-dir={profile_dir}",
    f"--remote-debugging-port={port}",
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--mute-audio",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(5)
print(f"[TEST] Chrome PID={proc.pid}, port={port}")

try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print(f"[TEST] Navigating to {TEST_VIDEO}...")
        page.goto(TEST_VIDEO, timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        # Scroll to load comments
        print("[TEST] Scrolling to comments...")
        for _ in range(5):
            page.keyboard.press("PageDown")
            time.sleep(random.uniform(0.4, 1.0))

        # Check comment box
        has_box = page.evaluate(
            "() => !!document.querySelector('ytd-comment-simplebox-renderer')"
        )
        print(f"[TEST] Comment box found: {has_box}")

        if has_box:
            # Click placeholder
            print("[TEST] Clicking comment placeholder...")
            clicked = page.evaluate("""() => {
                const ph = document.querySelector('#simplebox-placeholder, #placeholder-area');
                if (ph) {
                    ph.click();
                    return true;
                }
                return false;
            }""")
            print(f"[TEST] Placeholder clicked: {clicked}")
            time.sleep(2.5)

            # Check for contenteditable
            ce_selectors = [
                "#contenteditable-root",
                "[contenteditable='true']",
                "div[contenteditable='plaintext-only']",
                "[contenteditable]"
            ]

            root = None
            for sel in ce_selectors:
                try:
                    root = page.query_selector(sel)
                    if root:
                        print(f"[TEST] ✓ contenteditable FOUND: {sel}")
                        break
                except:
                    continue

            if root:
                print("[TEST] SUCCESS - COMMENTS WORK ON PC1")
                root.type("Test from PC1 bot", delay=100)
                time.sleep(1)
                print("[TEST] Typed test comment (not submitting)")
            else:
                # Debug
                diag = page.evaluate("""() => {
                    const box = document.querySelector('ytd-comment-simplebox-renderer');
                    if (!box) return 'simplebox=null';
                    const vis = window.getComputedStyle(box).display;
                    const all = box.querySelectorAll('*');
                    const tags = [];
                    for (const el of all) {
                        if (el.id || el.getAttribute('contenteditable')) {
                            tags.push(el.tagName + '#' + el.id + '[ce=' + (el.getAttribute('contenteditable')||'') + ']');
                        }
                    }
                    return 'N=' + all.length + ' vis=' + vis + ' ids=' + tags.slice(0,8).join(',');
                }""")
                print("[TEST] FAIL - COMMENTS BROKEN ON PC1 TOO")
                print(f"[TEST] DOM state: {diag}")

        browser.close()

finally:
    print("[TEST] Killing Chrome...")
    proc.terminate()
    time.sleep(2)
    if proc.poll() is None:
        proc.kill()

print("[TEST] Test complete")
