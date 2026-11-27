"""Vigia do Facebook (dona 20/11/2026: "deve rodar continuamente e acompanhar cada ação feita, para garantir as
Páginas o mais rápido possível e as postagens, e os ajustes em tempo real, resolver problemas").

Tarefa FacebookVigia a cada 15 min. Não posta nada sozinho fora das regras; só destrava e completa:
  1. rodada de postagem (postar_facebook_paginas) ou criação (fb_criar_fila) rodando há > 50 min = travada -> mata
     (o processo e o Chrome que ele abriu na porta da conta) e registra;
  2. Chrome de conta do Facebook (porta 9798/9401) aberto sem nenhuma rodada/criação/medição viva há > 10 min ->
     fecha (sobrou de rodada que caiu; o próximo abrir() reabriria preso no perfil);
  3. Página atrasada: Página ativa com menos Reels do que o relógio pede (deve_postar_agora) há 2 rodadas seguidas e
     sem rodada viva -> roda 1 post só dela (--pagina X --um);
  4. Página pela metade na fila (etapa criada/foto/capa/config) e a conta livre -> roda o fb_criar_fila (retoma);
  5. Página com o mesmo erro 3x hoje -> Telegram (avisos.py, só erro não consertado).
Log: logs/fb_vigia.log (1 linha por ação). Estado: logs/fb_vigia.json.

    python fb_vigia.py          # 1 volta
    python fb_vigia.py --simular
"""
import json, os, subprocess, sys, time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
LOG = BIN.parent / "logs" / "fb_vigia.log"
EST = BIN.parent / "logs" / "fb_vigia.json"
PY = r"D:\veo\venv\Scripts\python.exe"
TRAVADA_MIN = 45  # 21/11: rodada com várias Páginas leva 25+ min postando de verdade; 18 matava rodada viva
SIMULAR = "--simular" in sys.argv


def log(msg):
    linha = f"{datetime.now():%Y-%m-%d %H:%M} {'[sim] ' if SIMULAR else ''}{msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha, flush=True)


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return padrao


def processos():
    """[(pid, criado_em(datetime), linha_de_comando)] de python/chrome que interessam."""
    ps = ("Get-CimInstance Win32_Process | ? { ($_.Name -match 'python') -and $_.CommandLine -match "
          "'postar_facebook_paginas|fb_criar_fila|fb_medir|services.facebook|postar_ms_energy|fb_token_assistido|fb_login_janela' -or ($_.Name -eq 'chrome.exe' "
          "-and $_.CommandLine -match 'remote-debugging-port=(9798|9401|9746|9711)' -and $_.CommandLine -notmatch '--type=') } | "
          "% { \"$($_.ProcessId)|$($_.CreationDate.ToString('yyyy-MM-ddTHH:mm:ss'))|$($_.ParentProcessId)|$($_.CommandLine)\" }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, encoding="utf-8",
                         errors="replace").stdout
    res = []
    for l in out.splitlines():
        partes = l.split("|", 3)
        if len(partes) == 4 and partes[0].isdigit():
            res.append((int(partes[0]), datetime.fromisoformat(partes[1]), int(partes[2] or 0), partes[3]))
    return res


def matar(pid):
    if not SIMULAR:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def rodar_bg(args):
    if SIMULAR:
        return
    flags = 0x08000000 | 0x00000008  # sem janela, desligado do vigia
    subprocess.Popen([PY, "-u", *args], cwd=str(BIN), creationflags=flags,
                     stdout=open(BIN.parent / "logs" / "fb_vigia_acoes.log", "a", encoding="utf-8"), stderr=subprocess.STDOUT,
                     env=dict(os.environ, PYTHONUTF8="1"))


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    agora = datetime.now()
    est = _ler(EST, {})
    procs = processos()
    py = [p for p in procs if "chrome.exe" not in p[3].lower()]
    chromes = [p for p in procs if "chrome.exe" in p[3].lower()]
    acoes = 0

    # 0. (23/11) saúde: ponte de proxy caída é religada e trava de processo morto é apagada (fb_saude.py). Foi o que
    # parou o Facebook das 12h às 15h de 23/11 sem ninguém ver. Não posta nada; só conserta o caminho.
    if not SIMULAR:
        try:
            import fb_saude
            for conta, c in fb_saude.contas_ativas().items():
                fb_saude.ponte(conta, c.get("saida"))
                fb_saude.trava(conta)
        except Exception as e:  # noqa: BLE001
            print(f"[saude] falhou: {e}", flush=True)

    # 1. travadas
    for pid, criado, pai, cmd in py:
        if any(pid == q[2] for q in py):
            continue  # é o lançador do venv (o filho é quem trabalha); mata pela árvore do filho
        if (agora - criado) > timedelta(minutes=TRAVADA_MIN) and ("postar_facebook_paginas" in cmd or "fb_criar_fila" in cmd
                                                                  or "postar_ms_energy" in cmd or "fb_rodada_todas" in cmd):
            log(f"TRAVADA há {int((agora - criado).total_seconds() // 60)} min: pid {pid} {cmd[-80:]} -> mato")
            matar(pai if any(pai == q[0] for q in py) else pid)
            acoes += 1
    # 1b. (24/11) criação PARADA: o log fb_criar_<conta>.log sem escrever há > 15 min e o processo vivo há > 15 min =
    # presa esperando o Facebook (24/11 22:47-23:12 segurou as 2 contas e nada postou). Só a criação: a postagem fica
    # muito tempo sem imprimir durante o upload, então segue com o limite de 45 min acima.
    import re as _re
    for pid, criado, pai, cmd in py:
        if "fb_criar_fila" not in cmd or any(pid == q[2] for q in py):
            continue
        m = _re.search(r"--conta\s+(\S+)", cmd)
        lg = BIN.parent / "logs" / f"fb_criar_{m.group(1)}.log" if m else None
        try:
            parado = lg and lg.exists() and (time.time() - lg.stat().st_mtime) > 15 * 60
        except OSError:
            parado = False
        if parado and (agora - criado) > timedelta(minutes=15):
            log(f"CRIAÇÃO PARADA (log sem mexer há 15 min): pid {pid} {cmd[-60:]} -> mato e libero a conta")
            matar(pai if any(pai == q[0] for q in py) else pid)
            acoes += 1
    procs = processos() if acoes and not SIMULAR else procs
    py = [p for p in procs if "chrome.exe" not in p[3].lower()]

    # 2. Chrome esquecido (sem nenhum python do Facebook vivo)
    if not py:
        for pid, criado, _, cmd in chromes:
            if (agora - criado) > timedelta(minutes=10):
                log(f"Chrome do Facebook esquecido aberto (pid {pid}, {cmd.split('remote-debugging-port=')[1][:4]}) -> fecho")
                matar(pid); acoes += 1

    # 3/4/5 só com nada rodando (não briga com a rodada/criação)
    vivo = [p for p in py if "postar_facebook_paginas" in p[3] or "fb_criar_fila" in p[3]]
    import postar_facebook_paginas as P, fb_escada as E
    cfg, reg = P._ler(P.CFG, {}), P._ler(P.REG, {})
    hoje = agora.strftime("%Y-%m-%d")
    atrasadas = []
    for k, pag in cfg.get("paginas", {}).items():
        if pag.get("pausada"):
            continue
        feitos, lim = P.hoje_na_pagina(reg, k), E.teto(k, pag)
        # atrasada = o relógio já pedia o post da hora ANTERIOR (a rodada de :20 já devia ter feito)
        if feitos < lim and P.deve_postar_agora(feitos, lim, agora - timedelta(hours=1)) and agora.minute >= 35:
            atrasadas.append(k)
        erros = [m for q, m in (reg.get("erros", {}).get(k) or {}).items() if q.startswith(hoje)]
        for m, n in Counter(m[:80] for m in erros).items():
            chave = f"{k}:{hoje}:{m}"
            if n >= 3 and chave not in est.get("avisados", []):
                est.setdefault("avisados", []).append(chave)
                log(f"{pag['nome']}: mesmo erro {n}x hoje -> Telegram: {m}")
                try:
                    sys.path.insert(0, r"D:\video-fila")
                    import avisos
                    if not SIMULAR:
                        avisos.enviar(f"Facebook {pag['nome']}: mesmo erro {n}x hoje — {m}", "facebook_paginas", importante=True)
                except Exception:
                    pass
    seguidas = est.get("atrasadas_antes", [])
    if not vivo:
        for k in atrasadas:
            if k in seguidas:
                log(f"{cfg['paginas'][k]['nome']}: atrasada 2 voltas seguidas -> posto 1 agora")
                rodar_bg(["postar_facebook_paginas.py", "--pagina", k, "--um"]); acoes += 1
                break  # 1 por volta (não abre 2 Chromes da mesma conta)
        fila = _ler(BIN.parent / "logs" / "fb_fila_estado.json", {})
        meio = [k for k, v in fila.get("paginas", {}).items() if v.get("etapa") not in (None, "pronta")]
        if meio and not acoes:
            log(f"Página pela metade na fila ({meio[0]}, etapa {fila['paginas'][meio[0]]['etapa']}) -> retomo")
            rodar_bg(["fb_criar_fila.py"]); acoes += 1
    est["atrasadas_antes"] = atrasadas
    est["ultima_volta"] = agora.isoformat(timespec="seconds")
    est["avisados"] = [a for a in est.get("avisados", []) if hoje in a]
    if not SIMULAR:
        tmp = EST.with_suffix(".tmp"); tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, EST)
    if not acoes:
        print(f"{agora:%H:%M} ok — {len(vivo)} rodada(s) viva(s), atrasadas: {atrasadas or 'nenhuma'}")


if __name__ == "__main__":
    main()
