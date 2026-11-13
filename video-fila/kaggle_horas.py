# -*- coding: utf-8 -*-
"""kaggle_horas.py — horas de GPU do Kaggle de TODAS as contas do cofre (dono 24/10/2026: "Kaggle deve contar as
horas de todas as contas"; respondeu "Sim, 1 vez por dia").

Abre o Chrome do cofre de cada conta que já entrou no kaggle.com (pasta IndexedDB do kaggle no perfil) e pede ao
próprio site a cota da semana (POST /api/i/kernels.KernelsService/GetAcceleratorQuotaStatistics, o mesmo que o
editor de notebook chama — achado na sonda de 24/10). Só LÊ: não abre notebook nem liga GPU. Uma conta por vez, com a
mesma trava de navegador do kaggle_rpa (não briga com a fila de voz).

Saída: estado/kaggle_horas.json = {"em", "contas": [{conta, horas, usadas, total, renova, visto, erro}]}; o medidor
do Kaggle (maquinas._medir_kaggle) soma no cartão do painel.

    python kaggle_horas.py              # todas (pula se a última leitura tem menos de 20 h)
    python kaggle_horas.py --forcar
    python kaggle_horas.py --conta emersonjosiel649
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
SAIDA = BASE / "estado" / "kaggle_horas.json"
LOG = BASE / "logs" / "kaggle_horas.log"
PERFIS = Path(r"D:\logins-google\cofre\perfis")
INTERVALO_H = 20
sys.path.append(r"D:\logins-google")  # append: nunca na frente dos módulos daqui
sys.path.append(r"D:\hipercool-materiais\bin")

JS_COTA = """async () => {
  const m = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
  const h = {'content-type': 'application/json'};
  if (m) h['x-xsrf-token'] = decodeURIComponent(m[1]);
  const r = await fetch('/api/i/kernels.KernelsService/GetAcceleratorQuotaStatistics', {method: 'POST', headers: h, body: '{}'});
  return {status: r.status, corpo: await r.text()};
}"""


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def contas_com_kaggle():
    """Perfis do cofre que já abriram o kaggle.com (o login do Google serve pro Kaggle quando a conta existe)."""
    return sorted(p.name for p in PERFIS.iterdir()
                  if (p / "Default" / "IndexedDB" / "https_www.kaggle.com_0.indexeddb.leveldb").exists())


def _seg(x):
    try:
        return float(str(x or "0").rstrip("s"))
    except ValueError:
        return 0.0


def ler_conta(nome, pw):
    import cofre
    porta, proc = cofre.abrir(nome)
    br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=120000)
    pg = br.contexts[0].new_page()
    try:
        pg.goto("https://www.kaggle.com/code", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(3000)
        if "/account/login" in pg.url:
            return {"conta": nome, "erro": "deslogada no Kaggle"}
        r = pg.evaluate(JS_COTA)
        if r["status"] != 200:
            return {"conta": nome, "erro": f"Kaggle respondeu {r['status']} (sem conta Kaggle ou deslogada)"}
        g = (json.loads(r["corpo"]).get("gpuQuota") or {})
        total, usadas = _seg(g.get("totalTimeAllowed")) / 3600, _seg(g.get("timeUsed")) / 3600
        return {"conta": nome, "horas": round(total - usadas, 1), "usadas": round(usadas, 1), "total": round(total, 1),
                "renova": json.loads(r["corpo"]).get("quotaRefreshTime", "")[:10],
                "visto": datetime.now().strftime("%d/%m %H:%M")}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass
        cofre.fechar(proc, br, nome)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    try:
        antes = json.loads(SAIDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        antes = {}
    if "--forcar" not in a and "--conta" not in a and antes.get("em"):
        idade_h = (datetime.now() - datetime.fromisoformat(antes["em"])).total_seconds() / 3600
        if idade_h < INTERVALO_H:
            log(f"última leitura há {idade_h:.0f} h — pula")
            return
    nomes = [a[a.index("--conta") + 1]] if "--conta" in a else contas_com_kaggle()
    import kaggle_rpa as kr
    from playwright.sync_api import sync_playwright
    por_conta = {c["conta"]: c for c in antes.get("contas", [])}
    kr._pegar_trava_nav()  # mesma trava do kaggle_rpa/kaggle_conversor: um Chrome do Kaggle por vez
    try:
        with sync_playwright() as pw:
            for nome in nomes:
                try:
                    c = ler_conta(nome, pw)
                except Exception as e:  # noqa: BLE001
                    c = {"conta": nome, "erro": f"{type(e).__name__}: {str(e)[:120]}"}
                por_conta[nome] = c
                log(f"{nome}: " + (f"{c['horas']} h livres de {c['total']} (renova {c['renova']})" if "horas" in c else c["erro"]))
                time.sleep(2)
    finally:
        kr._soltar_trava_nav()
    contas = sorted(por_conta.values(), key=lambda c: -(c.get("horas") or -1))
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "contas": contas},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    ok = [c for c in contas if "horas" in c]
    log(f"fim: {len(ok)} conta(s) com Kaggle, {sum(c['horas'] for c in ok):.1f} h de GPU livres na semana; "
        f"{len(contas) - len(ok)} sem Kaggle/deslogada")


if __name__ == "__main__":
    main()
