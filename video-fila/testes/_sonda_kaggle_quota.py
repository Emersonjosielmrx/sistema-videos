# Sonda (24/10): onde o Kaggle mostra as horas de GPU da semana sem ligar sessão. Só LÊ (abre páginas, não roda nada).
import json
import sys

sys.path.insert(0, r"D:\hipercool-materiais\bin")
import kaggle_rpa as kr  # noqa: E402

achados = []
with kr.Navegador() as pg:
    def resp(r):
        u = r.url
        if "kaggle.com/api/" in u and any(k in u.lower() for k in ("quota", "accelerator", "usage", "gpu")):
            try:
                achados.append((u, r.text()[:1500]))
            except Exception as e:  # noqa: BLE001
                achados.append((u, f"(sem corpo: {e})"))
    pg.on("response", resp)
    pg.goto("https://www.kaggle.com/code", wait_until="domcontentloaded", timeout=90000)
    print("url:", pg.url)
    pg.wait_for_timeout(4000)
    links = pg.eval_on_selector_all(f"a[href*='/code/{kr.USUARIO}/']", "els => els.map(e => e.href)")
    print("notebooks:", links[:5])
    alvo = (links[0].split("?")[0].rstrip("/") + "/edit") if links else "https://www.kaggle.com/code"
    pg.goto(alvo, wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_timeout(20000)
    txt = pg.inner_text("body")
    for linha in txt.splitlines():
        if any(k in linha.lower() for k in ("quota", "hrs", "hours", "gpu")):
            print("TEXTO:", linha[:200])
for u, t in achados:
    print("API:", u, "\n   ", t.replace("\n", " ")[:800])
print(json.dumps({"n_api": len(achados)}))
