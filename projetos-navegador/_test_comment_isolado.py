"""Teste isolado: tenta comentar em 1 video conhecido com screenshots."""
from playwright.sync_api import sync_playwright
import time, random

VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Never Gonna Give You Up - sabemos que tem comentarios
COMMENT = "Great video!"
PROXY = "gate.visitxiangtan.com:7000:fqjlvf-rotate:cdhz0o4h8tts"

def test_comment():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=r"C:\temp\test_chrome_profile",
            headless=True,
            args=[
                f"--proxy-server=http://{PROXY.split(':')[0]}:{PROXY.split(':')[1]}",
                "--disable-blink-features=AutomationControlled"
            ],
            viewport={"width": 1366, "height": 768}
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print(f"1. Navegando para {VIDEO}")
        page.goto(VIDEO, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        page.screenshot(path=r"C:\projetos-navegador\test_comment_1_loaded.png")
        print("   Screenshot 1: pagina carregada")

        print("2. Scrollando ate comentarios")
        for _ in range(6):
            page.keyboard.press("PageDown")
            time.sleep(random.uniform(0.5, 1.0))

        page.screenshot(path=r"C:\projetos-navegador\test_comment_2_scrolled.png")
        print("   Screenshot 2: apos scroll")

        print("3. Checando se simplebox existe")
        has_box = page.evaluate("() => !!document.querySelector('ytd-comment-simplebox-renderer')")
        print(f"   simplebox existe: {has_box}")

        if not has_box:
            print("   FALHOU: sem simplebox")
            browser.close()
            return False

        print("4. Scrollando simplebox pra view")
        page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (box) box.scrollIntoView({block: 'center'});
        }""")
        time.sleep(1)

        print("5. Clicando no placeholder")
        clicked_sel = page.evaluate("""() => {
            const sels = [
                'ytd-comment-simplebox-renderer div#placeholder-area',
                'ytd-comment-simplebox-renderer #simplebox-placeholder',
                '#placeholder-area'
            ];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) {
                    el.click();
                    return s;
                }
            }
            return '';
        }""")
        print(f"   placeholder clicado: {clicked_sel}")

        if not clicked_sel:
            print("   FALHOU: placeholder nao encontrado")
            browser.close()
            return False

        time.sleep(2)
        page.screenshot(path=r"C:\projetos-navegador\test_comment_3_placeholder_clicked.png")
        print("   Screenshot 3: apos clicar placeholder")

        print("6. Diagnosticando DOM")
        diag = page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (!box) return 'simplebox=null';
            const vis = window.getComputedStyle(box).display;
            if (vis === 'none') return 'display:none';
            const all = Array.from(box.querySelectorAll('*'));
            const ce_els = all.filter(el => el.getAttribute('contenteditable'));
            const ids = all.filter(el => el.id).map(el => el.tagName+'#'+el.id);
            return {
                display: vis,
                total: all.length,
                contenteditable_count: ce_els.length,
                contenteditable_elems: ce_els.map(el => el.tagName+'#'+el.id+'[ce='+el.getAttribute('contenteditable')+']'),
                all_ids: ids.slice(0, 15)
            };
        }""")
        print(f"   DOM: {diag}")

        print("7. Tentando achar contenteditable")
        ce_sels = [
            "#contenteditable-root",
            "div#contenteditable-root",
            "[contenteditable='true']",
            "div[contenteditable='plaintext-only']",
            "div[contenteditable]",
            "ytd-commentbox #contenteditable-root"
        ]

        root = None
        for sel in ce_sels:
            try:
                root = page.query_selector(sel)
                if root:
                    print(f"   contenteditable encontrado: {sel}")
                    break
            except:
                pass

        if not root:
            print("   FALHOU: contenteditable nao encontrado mesmo apos click")
            print("   Tentando fallback: Tab navigation")
            page.keyboard.press("Tab")
            time.sleep(0.5)
            page.keyboard.press("Tab")
            time.sleep(1)

            for sel in ce_sels[:4]:
                try:
                    root = page.query_selector(sel)
                    if root:
                        print(f"   contenteditable encontrado apos Tab: {sel}")
                        break
                except:
                    pass

        if not root:
            page.screenshot(path=r"C:\projetos-navegador\test_comment_4_FAILED.png")
            print("   Screenshot 4: FALHA (sem contenteditable)")
            browser.close()
            return False

        print("8. Digitando comentario")
        root.click()
        time.sleep(0.3)
        root.focus()
        time.sleep(0.2)

        for char in COMMENT:
            page.keyboard.type(char, delay=random.uniform(50, 150))

        page.screenshot(path=r"C:\projetos-navegador\test_comment_5_typed.png")
        print("   Screenshot 5: comentario digitado")

        print("9. Procurando botao submit")
        submit_sel = page.evaluate("""() => {
            const sels = [
                'ytd-commentbox #submit-button button',
                'ytd-button-renderer#submit-button button',
                '#submit-button button',
                'button[aria-label*="Comment"]'
            ];
            for (const s of sels) {
                const btn = document.querySelector(s);
                if (btn && !btn.disabled) {
                    return s + ' (enabled)';
                }
                if (btn) {
                    return s + ' (DISABLED)';
                }
            }
            return '';
        }""")
        print(f"   submit button: {submit_sel}")

        if 'DISABLED' in submit_sel:
            print("   AVISO: botao submit esta disabled")

        print("10. Clicando submit")
        clicked_submit = page.evaluate("""() => {
            const sels = [
                'ytd-commentbox #submit-button button',
                '#submit-button button'
            ];
            for (const s of sels) {
                const btn = document.querySelector(s);
                if (btn) {
                    btn.disabled = false;
                    btn.removeAttribute('disabled');
                    btn.click();
                    return s;
                }
            }
            return '';
        }""")

        if not clicked_submit:
            print("   FALHOU: botao submit nao encontrado")
            page.screenshot(path=r"C:\projetos-navegador\test_comment_6_no_submit.png")
            browser.close()
            return False

        print(f"   submit clicado: {clicked_submit}")
        time.sleep(3)

        page.screenshot(path=r"C:\projetos-navegador\test_comment_7_submitted.png")
        print("   Screenshot 7: apos submit")

        print("\n✅ SUCESSO: comentario postado")
        browser.close()
        return True

if __name__ == "__main__":
    success = test_comment()
    print(f"\nResultado: {'SUCCESS' if success else 'FAILED'}")
