#!/usr/bin/env python3
"""postar_tiktok_auto.py — Reaproveita no TikTok (Chrome CDP) video que ja saiu em outra rede.

O que postar vem do catalogo (bin/catalogo.py): ja postado no YouTube/Instagram, ainda nao no TikTok, na conta do tema
(config/reuso_plataformas.json), no maximo max_por_conta_dia por conta. Video que ja foi para o Google Drive e baixado
so para postar e apagado em seguida. Perfil deslogado sai da rodada.
Conta sem video proprio completa com Veo limpo (bin/reserva_veo.py); conta que nao postou no dia = aviso no Telegram.

Uso: python postar_tiktok_auto.py [--simular] [--ate-min N]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogo  # noqa: E402
import comercial_veo  # noqa: E402
import etapas  # noqa: E402
import proxy_tiktok  # noqa: E402
import reserva_veo  # noqa: E402

PY_EXE = Path(r"D:\veo\venv\Scripts\python.exe")
CDP_POSTER = Path(r"D:\postador-de-videos\bin\tiktok_cdp_poster.py")
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
LOG_FILE = Path(r"D:\postador-de-videos\logs\tiktok_auto.log")
POSTED_LOG = catalogo.TIKTOK_AUTO


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_posted():
    if POSTED_LOG.exists():
        try:
            return json.loads(POSTED_LOG.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_posted(data):
    # 22/10 (P05): troca atômica — o arquivo já truncou uma vez (bak_20261015) e truncado o TikTok reposta
    import politica
    politica.gravar_json(POSTED_LOG, data)


def check_chrome(port):
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=5)
        json.loads(resp.read())
        return True
    except Exception:
        return False


def duracao(video):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def post_via_cdp(video_path, port, desc=None):
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    # 01/11: caminho de máquina remota (C:\postador-worker\... do desktop) não existe aqui — o 1080p já foi garantido
    # no arquivo local antes do rem.enviar(); antes dava "invalid literal for int()" e o desktop nunca postava
    if Path(video_path).exists():
        video_path = str(_g1080(video_path))
    cmd = [str(PY_EXE), str(CDP_POSTER), "--video", str(video_path), "--port", str(port), "--max", "1"]
    if desc:
        cmd += ["--desc", desc]
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                           timeout=420, encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        if "Post confirmed" in out:
            return True, out
        if "not logged in" in out.lower():
            return False, "not_logged_in"
        if "Post clicked" in out:  # 23/10: já clicou em Publicar — pode ter saído; NÃO reposta em outra máquina
            return False, "clicou_sem_confirmar: " + out.strip()[-300:]
        return False, out.strip()[-400:]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def falhou_antes_de_publicar(msg):
    """Falha ANTES de chegar no botão Publicar (página sem o campo do arquivo, vídeo que não carregou): tentar de novo
    não arrisca vídeo 2x. Mesmo critério da troca de máquina (revisão 23/10): botão que "não clicou" pode ter clicado."""
    m = str(msg)
    return "Post clicked" not in m and any(x in m for x in ("file input not found", "nao baixou", "envio de"))


def motivo_falha(msg):
    """A linha que explica a falha (antes saía só a 1ª linha da saída: "Chrome disponivel nas portas")."""
    linhas = [l.strip() for l in str(msg).splitlines() if l.strip()]
    uteis = [l for l in linhas if re.search(r"ERRO|ERROR|NAO CONFIRMADO|failed|Error|nao |não ", l)]
    return " | ".join((uteis or linhas)[-2:])[:160]


CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PERFIS = Path(r"D:\logins-google\chrome-profiles")


VIA = {}  # conta -> por onde saiu o último post ("celular", "webshareN", "casa", "remoto:<pc>"); vai para o posted_log (D20)


def abrir_conta(conta, r, proxy_n=None):
    """Abre o Chrome da conta so na hora do post (Chrome aberto o dia todo = ~650 MB cada, 15/10).
    "cofre": pelo cofre de logins; "porta": perfil chrome-profiles/<conta> nessa porta. Devolve (porta, proc);
    proc None = ja estava aberto por outro, nao fechar."""
    extra = []
    VIA[conta] = "casa"
    try:  # 29/10 (Fable, D20): contas de teste saem pelo CELULAR (IP de operadora) enquanto o túnel estiver vivo
        import proxy_celular
        if proxy_celular.vivo(conta):
            extra = proxy_celular.flags()
            VIA[conta] = "celular"
            log(f"  {conta}: posta pelo CELULAR (saida {(proxy_celular._ler().get('estado') or {}).get('ip')})")
    except Exception as ex:  # noqa: BLE001
        log(f"  proxy_celular indisponivel ({type(ex).__name__}) -> caminho normal")
    if proxy_n is not None:  # 12/11: Instagram — o chamador já conferiu o IP da conta no ar
        extra = proxy_tiktok.flags(proxy_n)
        VIA[conta] = f"webshare{proxy_n}"
    elif extra:
        pass
    elif (catalogo._ler(catalogo.REUSO, {}).get("tiktok") or {}).get("proxy_webshare") and not r.get("sem_proxy"):
        n = proxy_tiktok.ip_da_conta(conta)
        if proxy_tiktok.garantir() and proxy_tiktok.pronto(n):
            extra = proxy_tiktok.flags(n)
            VIA[conta] = f"webshare{n}"
        else:
            # 03/11 (regra da dona desde 02/11, vale para TikTok: "cada conta só fala com o serviço pela saída fixa
            # dela"; 14 contas do Kaggle banidas juntas por IP cruzado): antes subia pela internet de casa — 2 contas
            # saíram assim às 09:39 e 09:46. Proxy fora = esta conta fica para a próxima rodada.
            raise RuntimeError(f"PROXY FORA (IP {n} da Webshare nao abriu tunel): {conta} fica para a proxima rodada "
                               "(nunca pela internet de casa)")
    if r.get("cofre"):
        sys.path.insert(0, r"D:\logins-google")
        import cofre
        porta, proc = cofre.abrir(r["cofre"], extra=extra)
        if extra and not proc:
            # aberto por outro projeto SEM o proxy desta conta: usar seria sair por outro IP
            raise RuntimeError(f"{conta}: Chrome ja estava aberto por outro projeto sem o proxy dela — fica para a "
                               "proxima rodada")
        return porta, proc
    porta = r["porta"]
    if check_chrome(porta):
        if extra:  # 12/11: mesma trava do cofre — aberto antes, sem o proxy desta conta
            raise RuntimeError(f"{conta}: Chrome ja estava aberto sem o proxy dela — fica para a proxima rodada")
        return porta, None
    proc = subprocess.Popen([CHROME, f"--remote-debugging-port={porta}", f"--user-data-dir={PERFIS / conta}",
                             "--no-first-run", "--no-default-browser-check", "--remote-allow-origins=*",
                             "--window-size=1280,800", "--window-position=-2000,0", *extra, "about:blank"])
    for _ in range(40):
        if check_chrome(porta):
            return porta, proc
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError(f"Chrome de {conta} nao abriu a porta {porta}")


def fechar_conta(porta, proc, r, conta=None):
    """Fecha pelo CDP (grava os cookies) o Chrome que abrimos; Chrome aberto por outro projeto (proc None) fica."""
    if not proc:
        return
    try:
        import websocket
        ws = websocket.create_connection(json.loads(urllib.request.urlopen(
            f"http://127.0.0.1:{porta}/json/version", timeout=5).read())["webSocketDebuggerUrl"], timeout=15)
        ws.send(json.dumps({"id": 1, "method": "Browser.close"}))
        ws.close()
    except Exception:  # noqa: BLE001
        pass
    if r.get("cofre"):
        import cofre
        cofre.fechar(proc, nome=r["cofre"])  # espera fechar e limpa o cache do perfil se passou do limite
        return
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.terminate()
    # 02/11 23h (dona: 20 GB de cópias de upload nos perfis): o perfil fora do cofre também guarda o mp4 de cada upload
    try:
        if conta:
            sys.path.insert(0, r"D:\logins-google")
            import cofre
            cofre.limpar_uploads(PERFIS / conta)
    except Exception:  # noqa: BLE001 — limpeza nunca derruba a postagem
        pass


RECAPD_PY = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
CORTES_PRODUTO = r"D:\recapd-ambientes\producao\bin\cortes_produto.py"


def produto_meio(v, local, conta, posted, cfg, log):
    """26/10 (dono, linha CORTES): 1 a cada N Shorts de parceiro nesta conta vai com 3-4 s de um produto nosso no
    meio (cortes_produto: trecho de demonstração + frase do narrador + checagem de contato). Teste A/B: o formato
    "produto_meio" vai pro registro pra comparar as views. Qualquer falha = posta o Short normal."""
    pp = cfg.get("parceiro_produto") or {}
    if not pp.get("ligado") or v.get("projeto") != "parceiro":
        return None
    n = max(2, int(pp.get("a_cada", 3)))
    hist = [r for r in posted if r.get("account") == conta and r.get("tipo") == "parceiro"][-(n - 1):]
    if len(hist) < n - 1 or any(r.get("formato") == "produto_meio" for r in hist):
        return None
    catalogo.CACHE.mkdir(parents=True, exist_ok=True)
    saida = catalogo.CACHE / f"produto_{Path(local).stem}_{conta}.mp4"
    try:
        r = subprocess.run([RECAPD_PY, "-X", "utf8", CORTES_PRODUTO, "reuso", str(local), str(saida),
                            catalogo.legenda_reuso(v)[:120], v.get("caminho") or ""], capture_output=True, text=True,
                           encoding="utf-8",
                           errors="replace", timeout=600, cwd=str(Path(CORTES_PRODUTO).parent))
        m = re.search(r"^PRODUTO: (.*)$", r.stdout or "", re.M)
        res = json.loads(m.group(1)) if m else None
    except Exception as e:  # noqa: BLE001
        log(f"  produto no meio: falhou ({type(e).__name__}: {str(e)[:120]}) — vai o normal")
        return None
    if not res or not Path(res.get("arquivo", "")).exists():
        log(f"  produto no meio: não montou ({(r.stderr or '')[-160:].strip()}) — vai o normal")
        return None
    log(f"  produto no meio: {res['produto']} aos {res['em_s']}s «{res['fala']}» (1 a cada {n} nesta conta)")
    return {"arquivo": res["arquivo"], "produto": res["produto"], "formato": "produto_meio"}


def feitos_hoje(posted):
    hoje = datetime.now().date().isoformat()
    return Counter(p.get("account") for p in posted if str(p.get("timestamp", "")).startswith(hoje))


def minutos_desde_ultimo(posted, conta):
    """Minutos desde o último post desta conta (None = nunca). 04/11: com a PostagemContinua de hora em hora, a mesma
    conta poderia postar de novo em minutos — regra da dona: mínimo 90 min entre posts da mesma conta."""
    ts = []
    for p in posted:
        if p.get("account") == conta and p.get("timestamp"):
            try:
                ts.append(datetime.fromisoformat(str(p["timestamp"])[:19]))
            except ValueError:
                pass
    return (datetime.now() - max(ts)).total_seconds() / 60 if ts else None


INTERVALO_CONTA_MIN = 90
# 12/11 (dona escolheu "todas dividindo IP" no TikTok, ~8 contas por IP grátis): 2 contas do MESMO IP nunca postam
# em sequência — a próxima do mesmo IP espera INTERVALO_IP_MIN. Desligar: "intervalo_ip_min": 0 na config tiktok.
INTERVALO_IP_MIN = 30


def minutos_desde_ultimo_ip(posted, conta):
    """Minutos desde o último post de QUALQUER outra conta que sai pelo mesmo IP Webshare desta (None = ninguém)."""
    try:
        mapa = json.loads(proxy_tiktok.MAPA.read_text(encoding="utf-8")).get("contas", {})
    except (OSError, ValueError):
        return None
    ip = mapa.get(conta)
    if ip is None:
        return None
    vizinhas = {c for c, n in mapa.items() if n == ip and c != conta}
    ts = []
    for p in posted:
        if p.get("account") in vizinhas and p.get("timestamp"):
            try:
                ts.append(datetime.fromisoformat(str(p["timestamp"])[:19]))
            except ValueError:
                pass
    return (datetime.now() - max(ts)).total_seconds() / 60 if ts else None


def filas(cfg, posted):
    """conta -> (config da conta, quantos ainda hoje, candidatos: os da conta + reserva de Veo)."""
    feitos = feitos_hoje(posted)
    gap = float(cfg.get("intervalo_conta_min", INTERVALO_CONTA_MIN))
    cat = catalogo.sincronizar()
    dispo = catalogo.disponiveis("tiktok", cat)
    cand = defaultdict(list)
    for v in dispo:
        cand[v["conta_reuso"]].append(v)
    out = {}
    for conta, r in cfg.get("contas", {}).items():
        resta = max(0, cfg.get("max_por_conta_dia", 3) - feitos[conta])
        m = minutos_desde_ultimo(posted, conta)
        if m is not None and m < gap:
            continue  # postou há menos de 90 min: fica pra próxima rodada
        # 11/11 dona ("tiktok pode ir fazendo"): conta com TODOS os vídeos em 0 views fica pausada (campo "pausada" na
        # config, posto por tiktok_pausar_zeradas.py) — só gasta postagem/IP nas que dão view. TIKTOK_PAUSADAS=0 ignora.
        if r.get("pausada") and os.environ.get("TIKTOK_PAUSADAS", "1") != "0":
            continue
        gap_ip = float(cfg.get("intervalo_ip_min", INTERVALO_IP_MIN))
        mi = minutos_desde_ultimo_ip(posted, conta) if gap_ip else None
        if mi is not None and mi < gap_ip:
            continue  # 12/11: outra conta do mesmo IP postou há pouco — esta fica para a próxima rodada
        if (r.get("cofre") or r.get("porta") or r.get("maquina")) and resta:
            out[conta] = (r, resta, cand[conta])
    reserva_veo.completar("tiktok", {c: (resta, lst) for c, (_, resta, lst) in out.items()}, dispo, cat, log)
    return {c: x for c, x in out.items() if x[2]}


def avisar_paradas(rede, postados, paradas, log_fn):
    """Impedimento so avisa (dono 18/10: nenhuma conta para sem o dono saber): contas que nao postaram hoje e por que."""
    if not paradas:
        return
    import _tg_safe
    linhas = "\n".join(f"- {_tg_safe.b(c)}: {_tg_safe.esc(m)}" for c, m in paradas.items())
    ok = _tg_safe.send(f"{_tg_safe.b(rede)}: {postados} postado(s) nesta rodada. Sem postar hoje:\n{linhas}")
    log_fn(f"Aviso no Telegram ({len(paradas)} conta(s) sem postar hoje): {'enviado' if ok else 'FALHOU'}")


def como_logar(r):
    if r.get("cofre"):
        return f"deslogada do TikTok: python D:\\logins-google\\cofre.py logar {r['cofre']} e entrar no tiktok.com"
    return f"deslogada do TikTok: abrir o Chrome do perfil chrome-profiles na porta {r.get('porta')} e entrar no tiktok.com"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true", help="so mostra o que postaria (nao baixa nem posta)")
    ap.add_argument("--ate-min", type=float, default=0,
                    help="nao comeca post novo depois de N min (para dar tempo do resumo/aviso antes do prazo da etapa)")
    args = ap.parse_args()
    inicio = time.time()
    log("=== INICIO TikTok Auto (reuso pelo catalogo) ===")
    cfg = catalogo._ler(catalogo.REUSO, {}).get("tiktok") or {}

    posted_log = load_posted()
    plano = filas(cfg, posted_log)
    log("Na fila hoje: " + (", ".join(f"{c} {min(r, len(v))} de {len(v)} disponiveis" for c, (_, r, v) in plano.items()) or "nada"))
    if args.simular:
        for conta, (_, resta, cand) in plano.items():
            for v in cand[:resta]:
                extra = f" [reserva {v['reserva']}]" if v.get("reserva") else ""
                log(f"  [simulacao] {conta}: {'PC   ' if v['no_pc'] else 'Drive'} {v['caminho']}{extra}")
        return

    import threading
    from concurrent.futures import ThreadPoolExecutor
    total = {"ok": 0, "err": 0}
    dead = set()
    erro = {}
    no_prazo = True
    trava = threading.Lock()  # registro do que saiu, reserva do Veo e etapas do Drive (arquivos em comum)
    trava_pc1 = threading.Lock()  # 1 Chrome de conta por vez neste PC (pouca RAM)

    # 03/11: cota do Drive estourada (403 "Queries per minute" do cliente público do rclone) — cada cópia esperava 2 min
    # e falhava; 15 seguidas, 0 post em 1 h. 3 falhas do Drive na rodada = só vídeo que já está no PC até o fim dela.
    drive_falhas = [0]

    def _ja_no_pc(v):
        return bool(v.get("limpo") and Path(v["limpo"]).exists()) or bool(v["no_pc"] and Path(v["caminho"]).exists())

    def um_post(conta, r, cand):
            while cand:
                v = cand.pop(0)
                if drive_falhas[0] >= 3 and not _ja_no_pc(v):
                    continue
                try:
                    local = catalogo.baixar(v)
                except Exception as e:  # noqa: BLE001
                    log(f"  {v['nome']}: {e}")
                    # 07/11: cópia do Drive sobrescrita (hipercool, mesmo nome em 2_tiktok/_/) ou sumida: o tamanho nunca
                    # bate — pula de vez e NÃO conta como falha do Drive (3 delas cortavam o Drive da rodada inteira)
                    if "nao baixou do Drive" in str(e) and ("directory not found" in str(e) or str(e).rstrip().endswith(":")):
                        catalogo.pular("tiktok", v, "cópia do Drive não existe ou foi sobrescrita (tamanho diferente)")
                        continue
                    if not _ja_no_pc(v):
                        with trava:
                            drive_falhas[0] += 1
                            if drive_falhas[0] == 3:
                                log("  [Drive] 3 cópias falharam (cota/lentidão) — o resto da rodada só com vídeo do PC")
                    continue
                d = duracao(local)
                if not d or d > cfg.get("duracao_max_s", 180):
                    catalogo.pular("tiktok", v, f"duracao {d}")
                    catalogo.liberar(local)
                    log(f"  [{conta}] pulado de vez: {v['nome']} tem {round(d) if d else '?'}s "
                        f"(maximo {cfg.get('duracao_max_s', 180)}s)")
                    continue
                legenda_tt = " ".join(catalogo.legenda_reuso(v).split())  # numa linha: o editor não guarda quebra
                if not legenda_tt:  # 28/10 (dono): nunca postar com legenda "Video"/vazia
                    catalogo.pular("tiktok", v, "sem legenda (título não achado)")
                    catalogo.liberar(local)
                    log(f"  [{conta}] pulado de vez: {v['nome']} ({v.get('caminho')}) sem legenda de verdade")
                    continue
                log(f"[{conta}] {v['nome']} ({d:.0f}s, {'PC' if v['no_pc'] else 'Drive'})"
                    + (f" [reserva {v['reserva']}]" if v.get("reserva") else ""))
                # 16/10 (dono): 1 a cada 3 do Veo nesta conta vai COM propaganda, montada segura na hora (comercial_veo)
                com = comercial_veo.preparar(v, "tiktok", conta, log)
                if not com:  # 26/10 (linha CORTES): Short de parceiro com 3-4 s de produto nosso no meio, teste A/B
                    com = produto_meio(v, local, conta, posted_log, cfg, log)
                ok, msg, porta_post = False, "sem tentativa", None
                # 23/10 (dona): conta logada nos notebooks posta por eles; erro num = o outro; erro de novo (ou conta
                # fora dos notebooks) = este PC. Já clicou em Publicar = para (não reposta).
                # 03/11 dona: as máquinas de casa (desktop/x200ma/acer/PC2) postavam 56 contas pela MESMA internet de casa,
                # sem o proxy da conta. Desligado até o Chrome remoto sair pelo proxy dela (tiktok.remoto_com_proxy).
                remoto_ok = bool((catalogo._ler(catalogo.REUSO, {}).get("tiktok") or {}).get("remoto_com_proxy"))
                n_px = None
                if r.get("maquina") and remoto_ok and not r.get("sem_proxy"):
                    n_px = proxy_tiktok.ip_da_conta(conta)
                    if not (proxy_tiktok.garantir() and proxy_tiktok.pronto(n_px)):
                        log(f"  {conta}: proxy {n_px} fora agora — só pelo PC1 (nunca pela máquina sem proxy)")
                        n_px = None
                if n_px is not None:
                    import maquina_remota
                    ordem = maquina_remota.tentativas(r["maquina"], r.get("perfil_remoto"), log_fn=log, proxy_n=n_px)
                else:
                    ordem = iter([None])
                try:
                    for rem in ordem:
                        proc = None
                        pc1 = False
                        if rem is None and r.get("maquina") and not (r.get("cofre") or r.get("porta")):
                            break  # conta só existe nos notebooks: não há Chrome dela neste PC
                        try:
                            arquivo = com["arquivo"] if com else local
                            if rem:
                                porta_post = rem.porta_local
                                from politica import garantir_1080 as _g1080
                                arquivo = rem.enviar(str(_g1080(arquivo)))  # 1080p feito aqui, antes de mandar
                                VIA[conta] = f"remoto:{rem.nome}:webshare{n_px}"
                                log(f"  pelo Chrome do {rem.nome} (proxy Webshare {n_px} da conta)")
                            else:
                                trava_pc1.acquire()
                                pc1 = True
                                porta_post, proc = abrir_conta(conta, r)
                            # 04/11: confere em QUE conta o Chrome está logado antes de postar (os perfis do desktop
                            # estavam no TikTok do Dorama Noturno e 7 posts de outras contas caíram lá)
                            import tiktok_relogar
                            certo, quem = tiktok_relogar.conferir_conta(conta, porta_post, cfg.get("contas", {}), log)
                            if not certo and "não li o @" in quem:  # deslogado: o relogin abaixo resolve
                                ok, msg = False, "not_logged_in"
                            elif not certo:
                                log(f"  {quem} — NÃO posto")
                                try:
                                    sys.path.insert(0, r"D:\video-fila")
                                    import avisos
                                    avisos.enviar(f"TikTok: {quem} (máquina {rem.nome if rem else 'PC1'}) — post "
                                                  "cancelado", "postagens", importante=True, chave=f"conta_errada:{conta}")
                                except Exception:  # noqa: BLE001
                                    pass
                                raise RuntimeError(f"conta errada no Chrome: {quem}")
                            else:
                                ok, msg = post_via_cdp(arquivo, porta_post, legenda_tt)
                            if not ok and falhou_antes_de_publicar(msg):  # 23/10: ~5 por rodada perdiam o dia assim
                                log(f"  falhou antes de publicar ({motivo_falha(msg)}) — tento de novo 1x")
                                time.sleep(20)
                                ok, msg = post_via_cdp(arquivo, porta_post, legenda_tt)
                            # 04/11 dona: "se ao postar aparecer deslogado, logar (Google já logado) e aí postar; Google
                            # deslogado = aí sim marca com problema". Mesmo Chrome, mesma saída (proxy) da conta.
                            if not ok and "Post clicked" not in str(msg) and (
                                    "not_logged_in" in str(msg)
                                    or re.search(r"Entrar no TikTok|Log in to TikTok|tiktok\.com/login", str(msg))):
                                import tiktok_relogar
                                res = tiktok_relogar.relogar(porta_post, tiktok_relogar.email_da_conta(conta, r), log)
                                log(f"  {conta}: estava deslogado — relogar pelo Google: {res}")
                                if res == "ok":
                                    ok, msg = post_via_cdp(arquivo, porta_post, legenda_tt)
                                elif res == "google_deslogado":
                                    msg = "not_logged_in: o GOOGLE deste perfil também está deslogado (precisa da dona)"
                                else:
                                    msg = f"not_logged_in: relogar pelo Google não deu ({res})"
                        except Exception as e:  # noqa: BLE001
                            ok, msg = False, f"abrir Chrome: {e}"
                        finally:
                            if not rem:
                                try:
                                    fechar_conta(porta_post, proc, r, conta)
                                finally:
                                    if pc1:
                                        trava_pc1.release()
                        # só troca de máquina se a falha foi ANTES de publicar com certeza (revisão 23/10: estouro de
                        # tempo perde o "Post clicked" e a próxima máquina postava de novo = vídeo 2x na conta)
                        antes = ("not_logged_in", "abrir Chrome", "file input not found", "nao baixou", "envio de")
                        if ok or not any(x in str(msg) for x in antes):
                            break
                        if rem:
                            log(f"  falhou no {rem.nome} ({str(msg)[:100]}) — tento na próxima máquina")
                finally:
                    if hasattr(ordem, "close"):
                        ordem.close()
                catalogo.liberar(local)
                if com:
                    catalogo.liberar(com["arquivo"])
                if ok:
                    with trava:
                        total["ok"] += 1
                        log(f"  OK #{total['ok']} ({conta})")
                        posted_log.append({"file": v["nome"], "path": v["caminho"], "port": porta_post, "account": conta,
                                           "tipo": v["projeto"],
                                           "formato": (com.get("formato") or "comercial") if com else "limpo",
                                           "produto": com["produto"] if com else None, "reserva": v.get("reserva"),
                                           "via": VIA.get(conta), "timestamp": datetime.now().isoformat()})
                        save_posted(posted_log)
                        try:
                            reserva_veo.usado(v, "tiktok", conta)
                        except Exception as e:  # noqa: BLE001  (nao para a rodada; o limpo ainda pode subir no YouTube)
                            log(f"  ATENCAO: nao marquei {v['nome']} como usado (rejeitar na mao p/ YouTube): {e}")
                        if v.get("reserva") != "limpo":  # limpo da reserva nao esta no catalogo/Drive
                            try:  # no Drive o video passa para a etapa seguinte e entra no _registro/<pc>.jsonl (bin/etapas.py)
                                etapas.registrar(v, "tiktok", conta)
                            except Exception as e:  # noqa: BLE001  (Drive fora nao para a postagem: o log acima ja guardou)
                                log(f"  etapas: {str(e)[:160]}")
                    time.sleep(cfg.get("intervalo_s", 90))
                else:
                    with trava:
                        total["err"] += 1
                        if str(msg).startswith("clicou_sem_confirmar"):
                            # revisão 23/10: clicou em Publicar e não viu a confirmação — pode ter saído. Anota como
                            # postado (sem confirmação) pra próxima rodada NÃO postar de novo; conferir no app se quiser.
                            posted_log.append({"file": v["nome"], "path": v["caminho"], "port": porta_post,
                                               "account": conta, "tipo": v["projeto"], "confirmado": False,
                                               "timestamp": datetime.now().isoformat()})
                            save_posted(posted_log)
                            log(f"  CLICOU SEM CONFIRMAR: {v['nome']} anotado como postado (não reposta)")
                    if "not_logged_in" in str(msg):
                        dead.add(conta)
                        log(f"  DESLOGADO: {conta} — fora desta rodada ({str(msg)[15:120]})")
                    else:
                        erro[conta] = motivo_falha(msg)
                        log(f"  ERRO ({conta}): {motivo_falha(msg)}")
                break
            else:
                erro.setdefault(conta, "os videos da fila nao baixaram do Drive ou eram longos demais")

    def um_post_seguro(conta, r, cand):
        if args.ate_min and time.time() - inicio > args.ate_min * 60:
            return  # ficou na fila do notebook e passou do prazo: não começa post novo
        try:
            um_post(conta, r, cand)
        except Exception as e:  # noqa: BLE001  (uma conta com defeito não derruba a rodada)
            erro[conta] = f"falha inesperada: {type(e).__name__}: {str(e)[:120]}"
            log(f"  ERRO ({conta}): {erro[conta]}")

    # 26/10 (dono: "temos vários computadores, deveriam ter aumentado"): um post por vez, o notebook (3-4 min) travava
    # o PC1 (1,2 min). Conta logada nos notebooks posta em paralelo (1 por notebook); o PC1 segue com as dele.
    n_notebooks = len({m for _, (r, _, _) in plano.items() for m in (r.get("maquina") or [])
                       if isinstance(r.get("maquina"), list)}) or 2
    with ThreadPoolExecutor(max_workers=n_notebooks) as pool:
        for rodada in range(max((r for _, r, _ in plano.values()), default=0)):
            pendentes = []
            for conta, (r, resta, cand) in plano.items():
                if conta in dead or rodada >= resta:
                    continue
                _m = minutos_desde_ultimo(posted_log, conta)
                if _m is not None and _m < float(cfg.get("intervalo_conta_min", INTERVALO_CONTA_MIN)):
                    continue  # 04/11: 2º post da conta nesta rodada só depois de 90 min do 1º
                if args.ate_min and time.time() - inicio > args.ate_min * 60:
                    log(f"Prazo de {args.ate_min:.0f} min: nao comeco post novo")
                    no_prazo = False
                    break
                if r.get("maquina"):
                    pendentes.append(pool.submit(um_post_seguro, conta, r, cand))
                else:
                    um_post_seguro(conta, r, cand)
            for f in pendentes:  # a mesma conta não posta 2 de uma vez: a rodada seguinte espera esta acabar
                f.result()
            if not no_prazo:
                break
    total_ok, total_err = total["ok"], total["err"]

    log("=== RESUMO TikTok ===")
    log(f"Postados: {total_ok} | Erros: {total_err} | Perfis deslogados: {len(dead)}")
    feitos = feitos_hoje(posted_log)
    paradas = {}
    for conta, r in cfg.get("contas", {}).items():
        if feitos[conta]:
            continue
        if conta in dead:
            paradas[conta] = como_logar(r)
        elif not (r.get("cofre") or r.get("porta") or r.get("maquina")):
            paradas[conta] = "sem Chrome configurado (cofre/porta) em reuso_plataformas.json"
        elif conta not in plano:
            paradas[conta] = "sem video: nem o da conta nem Veo de reserva"
        elif conta in erro:
            paradas[conta] = f"erro ao postar: {erro[conta]}"
        else:
            paradas[conta] = "nao chegou a vez antes do prazo da rodada"
    avisar_paradas("TikTok", total_ok, paradas, log)


if __name__ == "__main__":
    main()
