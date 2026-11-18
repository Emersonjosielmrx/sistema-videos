"""Gera a narração de um vídeo INTEIRO no Fish Audio (online) — chamado pelo anime_tts.preparar_clone nos Shorts.
Dona 18/11: "quando for Shorts, priorizar gerar o áudio online e aí monta; controle de créditos de cada conta usando
uma por vez; se não houver créditos usa o mesmo p3 com técnicas".

    from fish_lote import gerar
    feitos = gerar([(i, texto, "D:/.../audio_i.wav"), ...], log=print)   # -> {i: wav} das frases que saíram

- Escolhe a conta pelo creditos.json (sem abrir as outras); só lê a página de cobrança da conta escolhida se a
  estimativa estiver velha (renovou/nunca leu).
- Uma conta por vez, cada uma pela saída fixa dela (IP rnprmtfo próprio, nunca a casa).
- Acabou o crédito no meio = troca de conta e continua; nenhuma conta serve = devolve o que fez (o resto vai pro p3).
- Nunca levanta exceção: falha = devolve {} e a produção segue no p3.
FISH_ONLINE=0 desliga tudo.
"""
import os, re, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\logins-google")
import creditos  # noqa: E402

VOZ = os.environ.get("FISH_VOZ", "4b215a58407c4def88e0892def6421b2")  # NARRADOR DO TODO MUNDO ODEIA O CHRIS
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
MAX_CHARS = 480
TRAVA = AQUI / "_em_uso.lock"  # uma geração por vez neste PC (uma conta por vez)


def _travar():
    for _ in range(600):  # espera até 10 min outra geração terminar
        try:
            fd = os.open(str(TRAVA), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:  # trava velha (processo morto) > 30 min = solta
                if time.time() - TRAVA.stat().st_mtime > 1800:
                    TRAVA.unlink()
                    continue
            except OSError:
                pass
            time.sleep(1)
    return False


def _soltar():
    try:
        TRAVA.unlink()
    except OSError:
        pass


def _uma_conta(email, frases, log):
    """Gera as frases nessa conta. Devolve (feitos {i: wav}, motivo_parada|None)."""
    import cofre
    import fish_audio as fa
    feitos = {}
    _, ip_n = fa.checar_conta(email)
    pp = fa._subir_ponte(ip_n)
    porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{pp}",))
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})
            reg = creditos.carregar().get(email, {})
            if creditos.estimado(reg) is None:  # renovou/nunca leu: confere a cota antes
                lido = creditos.ler_na_pagina(pg)
                creditos.gravar_leitura(email, lido)
                if lido is None:
                    return feitos, "deslogada"
                log(f"[fish] {email}: {lido[0]} créditos")
            pg.goto(f"https://fish.audio/pt/app/text-to-speech/?modelId={VOZ}", wait_until="domcontentloaded",
                    timeout=90000)
            time.sleep(8)
            if "/auth" in pg.url or "Iniciar sessão" in pg.inner_text("body")[:3000]:
                creditos.marcar(email, logado=False, erro="deslogada")
                return feitos, "deslogada"

            def fechar_avisos():
                for _ in range(2):
                    pg.keyboard.press("Escape")
                    time.sleep(0.3)
                for sel in ("button[aria-label*='lose' i]", "button:has(svg.lucide-x)"):
                    try:
                        loc = pg.locator(sel)
                        for k in range(loc.count()):
                            if loc.nth(k).is_visible():
                                loc.nth(k).click(timeout=1500)
                                time.sleep(0.4)
                    except Exception:  # noqa: BLE001
                        pass

            for i, texto, destino in frases:
                est = creditos.estimado(creditos.carregar().get(email, {}))
                if est is not None and est < len(texto) + 20:
                    return feitos, "sem crédito"
                fechar_avisos()
                # 18/11: o sinal certo de "pronto" é a resposta audio/mpeg do armazenamento deles
                # (r2.cloudflarestorage.com/fish-platform-data/task/...) — contar botões falha: o site troca os takes
                chegou = []

                def _ouvir(r):
                    try:
                        if "fish-platform-data/task" in r.url and "audio" in r.headers.get("content-type", ""):
                            chegou.append(r.url)
                    except Exception:  # noqa: BLE001
                        pass
                pg.on("response", _ouvir)
                ed = pg.locator("[contenteditable='true'], textarea").first
                ed.click()
                pg.keyboard.press("Control+A")
                pg.keyboard.press("Delete")
                pg.keyboard.insert_text(texto)
                t0 = time.time()
                pg.get_by_text("Gerar fala", exact=False).first.click(timeout=15000)
                for _ in range(360):
                    time.sleep(0.5)
                    if chegou:
                        break
                    if int(time.time() - t0) % 5 == 0:
                        corpo = pg.inner_text("body").lower()
                        if "créditos insuficientes" in corpo or "insufficient credit" in corpo:
                            pg.remove_listener("response", _ouvir)
                            creditos.marcar(email, restantes=0, gasto_desde_leitura=0)
                            return feitos, "sem crédito"
                pg.remove_listener("response", _ouvir)
                if not chegou:
                    return feitos, "não gerou (tempo esgotado)"
                mp3 = Path(destino).with_suffix(".fish.mp3")
                resp = ctx.request.get(chegou[0], timeout=60000)  # mesma sessão e mesmo IP da conta
                if not resp.ok:
                    return feitos, f"download falhou ({resp.status})"
                mp3.write_bytes(resp.body())
                # wav mono 44,1 kHz igual às outras bases (a montagem e a legenda leem wav)
                r = subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100",
                                    str(destino)], capture_output=True)
                mp3.unlink(missing_ok=True)
                if r.returncode or not Path(destino).exists():
                    return feitos, "conversão falhou"
                creditos.gastar(email, len(texto))
                feitos[i] = destino
                log(f"[fish] frase {i} ok em {time.time() - t0:.1f}s ({email})")
    finally:
        try:
            cofre.fechar(proc, nome=email)
        except Exception:  # noqa: BLE001
            pass
    return feitos, None


def gerar(frases, log=print):
    """frases = [(i, texto, destino_wav)]. Devolve {i: destino} das que saíram no Fish."""
    if os.environ.get("FISH_ONLINE", "1") == "0":
        return {}
    frases = [(i, t.strip(), d) for i, t, d in frases if t and t.strip() and len(t.strip()) <= MAX_CHARS]
    if not frases:
        return {}
    if not _travar():
        log("[fish] outra geração ocupando há 10 min — sigo no p3")
        return {}
    feitos, tentadas = {}, set()
    try:
        while True:
            faltam = [f for f in frases if f[0] not in feitos]
            if not faltam:
                break
            precisa = sum(len(t) for _, t, _ in faltam)
            esc = creditos.escolher(min(precisa, 450), excluir=tentadas)
            if not esc:
                log(f"[fish] nenhuma conta com crédito — {len(faltam)} frase(s) vão pro p3")
                break
            email, _est = esc
            tentadas.add(email)
            try:
                f2, motivo = _uma_conta(email, faltam, log)
            except SystemExit as e:  # checar_conta recusou (Kaggle / fora do pool)
                creditos.marcar(email, logado=False, erro=str(e)[:120])
                continue
            except Exception as e:  # noqa: BLE001
                log(f"[fish] {email}: {type(e).__name__}: {str(e)[:150]}")
                continue
            feitos.update(f2)
            if motivo:
                log(f"[fish] {email}: {motivo} — próxima conta")
    finally:
        _soltar()
    log(f"[fish] {len(feitos)}/{len(frases)} frases online")
    return feitos


if __name__ == "__main__":  # teste: python fish_lote.py "frase 1" "frase 2"
    out = Path(r"D:\tmp\fish_lote_teste")
    out.mkdir(parents=True, exist_ok=True)
    r = gerar([(k, t, str(out / f"audio_{k}.wav")) for k, t in enumerate(sys.argv[1:])])
    print(r)
