r"""tiktok_relogar_desktop.py — conserta os perfis do DESKTOP logados no TikTok ERRADO (todos no @user6824946137963 do
Dorama Noturno desde 04/11; 21 contas paradas com "CONTA ERRADA"). Dona 11/11: "perfis de TikTok no desktop você mesmo
pode logar, automático, vários por vez".

Para cada conta: abre o Chrome dela NO DESKTOP pelo IP Webshare da conta (mesma saída do postador remoto, proxy_tiktok),
apaga SÓ os cookies do tiktok.com (sai da conta errada), entra com "Continuar com o Google" (tiktok_relogar.relogar —
o Google do perfil já está logado) e confere o @: se voltar o do Dorama ou outro já registrado, para (o Google do perfil
é que está errado = dona). Contas Google VIVAS do Kaggle ficam de fora (regra 09/11). 1 conta por vez, sem rajada.

    python bin\tiktok_relogar_desktop.py conta1 conta2 ...     # ou --todas (as que deram CONTA ERRADA no log)
Log: logs\tiktok_relogar_desktop.log
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
sys.path.insert(1, str(BIN / "netbooks"))
import maquina_remota as mr  # noqa: E402
import proxy_tiktok  # noqa: E402
import tiktok_relogar as tr  # noqa: E402

LOG = BIN.parent / "logs" / "tiktok_relogar_desktop.log"
DORAMA = "@user6824946137963"


def log(t):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {t}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _vivas_kaggle():
    p = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text("utf-8"))
    return {str(c.get("cofre") or "").split("@")[0].lower() for c in p["contas"] if not c.get("banida")}


def _limpar_tiktok(porta):
    """Apaga só os cookies do tiktok.com no Chrome desta porta (sai da conta errada; Google fica)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        antes = [c for c in ctx.cookies() if "tiktok" in c.get("domain", "")]
        cdp = ctx.new_page().context.new_cdp_session(ctx.pages[0])
        for c in antes:
            cdp.send("Network.deleteCookies", {"name": c["name"], "domain": c["domain"], "path": c.get("path", "/")})
        br.close()
        return len(antes)


def uma(conta, cfg, vivas):
    r = cfg.get(conta) or {}
    perfil = r.get("perfil_remoto") or r.get("cofre") or conta
    if perfil.lower() in vivas or conta.lower() in vivas:
        log(f"{conta}: conta Google VIVA do Kaggle — não mexo no TikTok dela pela casa (regra 09/11)")
        return "kaggle"
    if "desktop" not in (r.get("maquina") or []):
        log(f"{conta}: não roda no desktop — pulo")
        return "fora"
    n = proxy_tiktok.ip_da_conta(conta)
    if not (proxy_tiktok.garantir() and proxy_tiktok.pronto(n)):
        log(f"{conta}: proxy Webshare {n} fora — não abro pela internet de casa")
        return "sem_proxy"
    email = tr.email_da_conta(conta, r)
    rem = mr.Remoto("desktop")
    try:
        porta = rem.abrir(perfil, "about:blank", proxy_n=n)
        apagados = _limpar_tiktok(porta)
        log(f"{conta}: {apagados} cookies do TikTok apagados (saiu de {DORAMA}); entrando com o Google {email}")
        res = tr.relogar(porta, email, log=log)
        a = tr.arroba(porta) if res == "ok" else None
        if res != "ok":
            log(f"{conta}: relogar = {res} — fica pra dona")
            return res
        if not a or a.lower() == DORAMA:
            log(f"{conta}: voltou {a} — o Google DESTE perfil é o do Dorama (perfil trocado) — fica pra dona")
            return "google_errado"
        ok, msg = tr.conferir_conta(conta, porta, cfg, log=log)
        log(f"{conta}: {'OK' if ok else 'ERRADA'} — {msg}")
        return "ok" if ok else "errada"
    finally:
        rem.fechar()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cfg = json.loads((BIN.parent / "config" / "reuso_plataformas.json").read_text("utf-8"))["tiktok"]["contas"]
    contas = sys.argv[1:]
    if "--todas" in contas:
        txt = "".join(p.read_text("utf-8", errors="replace") for p in sorted((BIN.parent / "logs").glob("tiktok_2026111*.log"))[-2:])
        contas = sorted({m.group(1) for m in re.finditer(r"CONTA ERRADA: o Chrome de ([\w.]+) está logado em " + DORAMA, txt)})
    vivas = _vivas_kaggle()
    res = {}
    for c in contas:
        try:
            res[c] = uma(c, cfg, vivas)
        except Exception as e:  # noqa: BLE001
            res[c] = f"erro {type(e).__name__}"
            log(f"{c}: erro {type(e).__name__}: {str(e)[:160]}")
        time.sleep(20)  # sem rajada
    log(f"fim: {json.dumps(res, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
