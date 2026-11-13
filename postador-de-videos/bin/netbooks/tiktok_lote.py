"""tiktok_lote.py — login do TikTok de VÁRIAS contas ao mesmo tempo numa máquina (dona 26/10/2026: "fazer no PC2 os
login do TikTok vários de uma vez"). Cada conta usa o mesmo robô do tiktok_notebooks (Continuar com Google, escolhe a
conta, código do e-mail lido no Gmail), num Chrome próprio numa porta extra (9461…), N de uma vez.

    python bin\\netbooks\\tiktok_lote.py <maquina> [N=4]

- Antes: segura a vez da máquina ("login tiktok lote (dona)": telão fora, Veo/postagem vão pra outro lugar) e limpa a RAM.
- Captcha/código que o robô não resolveu: a janela FICA na tela pra dona; a cada 45 s confere (numa aba nova, sem
  mexer na dela) se já entrou; 10 min sem entrar = fecha e fica pra próxima rodada (o tiktok_notebooks volta em 1 h).
- Fila = a mesma do tiktok_notebooks (Google logado na máquina, TikTok ainda não).
"""
import json
import queue
import sys
import threading
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent.parent), str(Path(__file__).resolve().parent)]
import maquina_remota as mr  # noqa: E402
import tiktok_notebooks as tt  # noqa: E402

VEZ = "login tiktok lote (dona)"
TRAVA = threading.Lock()  # reuso_plataformas.json / netbooks_logins.json / reservas / estado: um por vez


def _ligar(perfil, nome):
    """O mesmo que tt._ligar, com a gravação na trava (vários logando juntos) e a espera dos cookies fora dela."""
    time.sleep(40)  # o Chrome grava os cookies (~30 s) antes de fechar
    with TRAVA:
        for _ in range(10):
            try:
                pol = mr._politica()
                arq = pol.CONFIG_DIR / "reuso_plataformas.json"
                dados = pol.ler_json(arq, {})
                for conta in (mr._mapa_perfis().get(perfil) or {}).get("tiktok", []):
                    c = (dados.get("tiktok") or {}).get("contas", {}).get(conta)
                    if c is not None:
                        c["maquina"] = [m for m in mr._lista(c.get("maquina")) if m != nome] + [nome]
                        c["perfil_remoto"] = perfil
                pol.gravar_json(arq, dados)
                lg = mr._logins()
                lg.setdefault(perfil, {}).setdefault(nome, {})["tiktok"] = True
                pol.gravar_json(mr.LOGINS, lg)
                return
            except PermissionError:
                time.sleep(2)


tt._ligar = _ligar


def _ocupar(nome):
    with TRAVA:
        try:
            mr.ocupar(nome, VEZ, 30)
        except PermissionError:
            pass


def _gravar(perfil, nome, res):
    with TRAVA:
        est = tt._ler()
        est.setdefault(perfil, {})[nome] = {"resultado": res, "t": time.time()}
        tt.ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
    mr.log(f"tiktok lote {perfil} no {nome}: {res}")
    print(f"{time.strftime('%H:%M')} {perfil}: {res}", flush=True)


def _esperar_dona(perfil, nome, porta, minutos=10):
    """A janela de captcha/código está na tela. Confere numa aba NOVA (não mexe na da dona) se o TikTok já entrou."""
    from playwright.sync_api import sync_playwright
    fim = time.time() + minutos * 60
    r = mr.Remoto(nome)
    r.porta = porta
    try:
        while time.time() < fim:
            time.sleep(45)
            _ocupar(nome)
            try:  # chrome_conta reaproveita a janela de login aberta da mesma conta (não abre outra)
                local = r.abrir(perfil, "https://www.tiktok.com/login", sem_espera=True)
                with sync_playwright() as p:
                    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{local}")
                    ctx = br.contexts[0]
                    if tt._sessao(ctx):
                        pg = ctx.new_page()
                        ok = tt._confirmar(ctx, pg, perfil, nome)
                        if ok:
                            tt._ligar(perfil, nome)
                            return f"logado {ok} (dona resolveu)"
                        pg.close()
            except Exception:  # noqa: BLE001
                pass
            finally:
                if r.tunel:
                    r.tunel.terminate()
                    r.tunel = None
        return "codigo_pendente"
    finally:
        r.aberto = True
        r.fechar()


def trabalhador(nome, porta, fila, fim):
    while time.time() < fim:
        try:
            perfil = fila.get_nowait()
        except queue.Empty:
            return
        _ocupar(nome)
        try:
            res = tt.logar(perfil, nome, porta)
        except Exception as e:  # noqa: BLE001
            res = f"erro: {type(e).__name__}: {str(e)[:100]}"
            r = mr.Remoto(nome)
            r.porta = porta
            try:
                r._ssh(f"{r.run} fechar {porta}", timeout=120)
            except Exception:  # noqa: BLE001
                pass
        if res in ("codigo", "captcha"):
            print(f"{time.strftime('%H:%M')} {perfil}: {res} — janela na tela do {nome} pra você resolver", flush=True)
            res = _esperar_dona(perfil, nome, porta)
        _gravar(perfil, nome, res)


def main(nome, n):
    agora = mr.reservado(nome)  # o tiktok_notebooks (vigia) pode estar no meio de uma conta: essa fica com ele
    em_curso = agora.split("login tiktok ", 1)[1].strip() if agora.startswith("login tiktok ") else ""
    contas = [p for p, m in tt.fila() if m == nome and p != em_curso]
    print(f"{len(contas)} contas na fila do TikTok no {nome}; {n} de uma vez", flush=True)
    if not contas:
        return
    mr.ocupar(nome, VEZ, 30)
    r = mr.Remoto(nome)
    for i in range(n):  # janelas que sobraram de um lote interrompido: fecha normal antes
        r._ssh(f"{r.run} fechar {9461 + i}", timeout=120)
    r._ssh(f"{r.run} liberar", timeout=120)  # fecha o que não precisa e limpa a RAM antes (dona 26/10: "sempre")
    if r.win:
        r._ssh(r"echo login > C:\vitrine\login.txt", timeout=30)  # telão fora já (o vitrine.py repete por rodada)
    fila = queue.Queue()
    for p in contas:
        fila.put(p)
    fim = time.time() + 4 * 3600
    ts = []
    for i in range(n):
        t = threading.Thread(target=trabalhador, args=(nome, 9461 + i, fila, fim), daemon=True)
        t.start()
        ts.append(t)
        time.sleep(20)  # não abre todos no mesmo segundo (PC2 lento pra subir Chrome)
    for t in ts:
        t.join()
    if r.win:
        r._ssh(r"del C:\vitrine\login.txt 2>nul", timeout=30)
    mr.liberar(nome, quem=VEZ)
    est = tt._ler()
    res = [(est.get(p) or {}).get(nome, {}).get("resultado", "?") for p in contas]
    ok = sum(1 for x in res if str(x).startswith("logado"))
    print(f"FIM: {ok}/{len(contas)} logadas no TikTok do {nome}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4)
