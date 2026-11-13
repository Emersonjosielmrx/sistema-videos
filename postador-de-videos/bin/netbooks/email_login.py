"""email_login.py — roda no PC1: abre a janela de login do Google no(s) notebook(s) e DIGITA SÓ O E-MAIL (dona, 23/10/2026:
"digite pelo menos o e-mail; se der errado deixamos sem"). A senha e o resto ficam com a dona, na tela do notebook.
A janela fica aberta (com a porta de controle ligada: se o Google recusar o login por isso, a dona entra sem ela
com `maquina_remota.py logar`).

    python bin\\netbooks\\email_login.py <perfil> <email> [x200ma acer]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import maquina_remota as mr  # noqa: E402


def um(nome, perfil, email):
    from playwright.sync_api import sync_playwright
    import json
    import time
    r = mr.Remoto(nome)
    for _ in range(40):  # revisão 23/10: o notebook pode estar POSTANDO — não derruba; espera até ~10 min
        try:
            est = json.loads(r._txt(r._ssh(f"{r.run} estado", timeout=30)).strip().splitlines()[-1])
        except (ValueError, IndexError, Exception):  # noqa: BLE001
            est = {}
        aberto = est.get("aberto") or {}
        if not aberto or aberto.get("login"):
            break
        # 23/10: Flow/Veo segura o notebook até ~33 min por vídeo; login com a dona na frente tem prioridade
        # (o Veo refaz o vídeo noutra rodada). Postagem continua sendo esperada.
        abas = r._txt(r._ssh(f"curl -s localhost:{aberto.get('porta')}/json", timeout=30))
        if "flow.google.com" in abas or "labs.google" in abas:
            print(f"{nome}: Veo/Flow de {aberto.get('perfil')} ocupando — fecho pra abrir o login", flush=True)
            break
        print(f"{nome}: postando agora ({aberto.get('perfil')}); espero terminar…", flush=True)
        time.sleep(15)
    else:
        raise RuntimeError("continua postando há 10 min — tente de novo depois")
    for porta_fechar in (0, r.porta):  # duas chamadas: o ";" não separa comandos no cmd do PC2
        r._ssh(f"{r.run} fechar {porta_fechar}", timeout=60)
    try:
        porta = r.abrir(perfil, "https://accounts.google.com/", sem_espera=True)
    except RuntimeError:  # Chrome que acabou de ser fechado ainda saindo: uma nova tentativa resolve
        time.sleep(10)
        porta = r.abrir(perfil, "https://accounts.google.com/", sem_espera=True)
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = next((x for x in br.contexts[0].pages if "google" in x.url), None) or br.contexts[0].pages[0]
            pg.bring_to_front()
            campo = pg.locator("input[type=email], #identifierId").first
            campo.wait_for(state="visible", timeout=60000)
            campo.click()
            campo.fill("")
            pg.keyboard.type(email, delay=60)
            pg.wait_for_timeout(500)
            pg.keyboard.press("Enter")
            pg.wait_for_timeout(5000)
            print(f"{nome}: e-mail digitado; agora em {pg.url[:80]}")
            # dona 23/10: ela loga só o Google; o TikTok entra sozinho no `maquina_remota.py ativar`
    finally:
        r.aberto = False  # a janela FICA aberta pra dona terminar
        if r.tunel:
            r.tunel.terminate()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    perfil, email, maqs = sys.argv[1].lower(), sys.argv[2], sys.argv[3:] or ["x200ma", "acer"]
    for m in maqs:
        try:
            um(m, perfil, email)
        except Exception as e:  # noqa: BLE001
            print(f"{m}: falhou ({type(e).__name__}: {str(e)[:150]})")
