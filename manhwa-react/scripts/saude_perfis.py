"""saude_perfis.py - abre cada perfil do inventario (work/inventario_perfis.json) e testa se o LOGIN esta vivo de
verdade (a data do cookie engana: perfis com cookie 'ate 2027' estavam deslogados). Nao envia nada.
Google: myaccount.google.com (redireciona p/ accounts.google.com = morto). TikTok/Instagram/Facebook: so onde ha
cookie de sessao. Grava work/saude_perfis.json."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, r"D:\postador-de-videos\bin")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import youtube_web_poster as W  # noqa: E402  (esperar_assentar: nao marcar morto durante a renovacao da sessao)

SO_MORTOS = "--so-mortos" in sys.argv  # reteste: so o que deu morto/erro na rodada anterior
WORK = Path(r"D:\manhwa-react\work")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORTA = 9599
TESTES = {
    "google": ("https://myaccount.google.com/", lambda u: "accounts.google.com" not in u and "myaccount" in u),
    "tiktok": ("https://www.tiktok.com/tiktokstudio/upload", lambda u: "login" not in u.lower()),
    "instagram": ("https://www.instagram.com/accounts/edit/", lambda u: "login" not in u.lower()),
    "facebook": ("https://www.facebook.com/settings", lambda u: "login" not in u.lower()),
}


def vivo(porta):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


inv = json.loads((WORK / "inventario_perfis.json").read_text(encoding="utf-8"))
anterior = {(r["pasta"], r["sub"]): r for r in json.loads((WORK / "saude_perfis.json").read_text(encoding="utf-8"))} \
    if SO_MORTOS else {}
res = []
for p in inv:
    for s in p["perfis"]:
        if s["sub"] == "System Profile":
            continue
        ant = anterior.get((p["pasta"], s["sub"]))
        if SO_MORTOS and ant and ant.get("google") == "vivo":
            res.append(ant)
            continue
        ses = s["sessoes"] if isinstance(s["sessoes"], dict) else {}
        sites = ["google"] + [k for k in ("tiktok", "instagram", "facebook") if k in ses]
        r = {"pasta": p["pasta"], "sub": s["sub"], "contas": s["contas"], "mb": p["mb"], "cache_mb": p["cache_mb"]}
        proc = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", f"--user-data-dir={p['pasta']}",
                                 f"--profile-directory={s['sub']}", "--no-first-run", "--no-default-browser-check",
                                 "--remote-allow-origins=*", "--window-position=-2000,0", "--window-size=1100,800",
                                 "about:blank"])
        try:
            for _ in range(40):
                if vivo(PORTA):
                    break
                time.sleep(0.5)
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
                pg = br.contexts[0].new_page()
                for site in sites:
                    url, ok = TESTES[site]
                    try:
                        pg.goto(url, wait_until="domcontentloaded", timeout=45000)
                        if site == "google":
                            r[site] = "vivo" if W.esperar_assentar(pg) == "ok" and ok(pg.url) else "morto"
                        else:
                            pg.wait_for_timeout(6000)
                            r[site] = "vivo" if ok(pg.url) else "morto"
                    except Exception as ex:  # noqa: BLE001
                        r[site] = f"erro {type(ex).__name__}"
                try:
                    br.new_browser_cdp_session().send("Browser.close")  # fecha normal (grava cookies)
                except Exception:  # noqa: BLE001
                    pass
        except Exception as ex:  # noqa: BLE001
            r["google"] = r.get("google") or f"erro {str(ex)[:60]}"
        finally:
            try:
                proc.wait(timeout=15)
            except Exception:  # noqa: BLE001
                proc.terminate()
            for _ in range(20):
                if not vivo(PORTA):
                    break
                time.sleep(0.5)
        res.append(r)
        print(f"{r.get('google', '?'):6} " + " ".join(f"{k}={r[k]}" for k in ("tiktok", "instagram", "facebook") if k in r)
              + f"  {','.join(r['contas']) or '-'}  {p['pasta']} [{s['sub']}]", flush=True)
        (WORK / "saude_perfis.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("FIM", len(res))
