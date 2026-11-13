#!/usr/bin/env python3
"""postar_insta_auto.py — Reaproveita como Reel no Instagram video que ja saiu em outra rede.

Mesmo modelo do postar_tiktok_auto.py: candidatos do catalogo (bin/catalogo.py), conta pelo tema em
config/reuso_plataformas.json, no maximo max_por_conta_dia por conta, baixa do Google Drive se preciso e apaga depois.
Envio pelo instagram_poster.py (link publico temporario + Graph API). Conta com login vencido e pulada (o dono precisa
entrar no Instagram e renovar a credencial no n8n).
Conta sem video proprio completa com Veo limpo (bin/reserva_veo.py); conta que nao postou no dia = aviso no Telegram.

Uso: python postar_insta_auto.py [--simular]
"""
import argparse
import json
import os
import re
import subprocess
import urllib.request
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogo  # noqa: E402
import comercial_veo  # noqa: E402
import etapas  # noqa: E402
import instagram_poster as ig  # noqa: E402
import pastas_empresas  # noqa: E402  (24/10: pasta publica de cada Instagram no Drive)
from produto import fila as produto_fila  # noqa: E402  (25/10: vídeos profissionais de produto)
import politica  # noqa: E402  (22/10 P05: gravar_json atômico)
import proxy_tiktok  # noqa: E402  (12/11: postagem do Instagram pelo IP grátis da conta)
import reserva_veo  # noqa: E402
from postar_tiktok_auto import avisar_paradas, duracao, feitos_hoje  # noqa: E402

LOG_FILE = Path(r"D:\postador-de-videos\logs\instagram_auto.log")
POSTED_LOG = catalogo.INSTA_AUTO


def log(msg):
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def conta_ok(conta):
    tok = (conta.get("data") or {}).get("accessToken") or ""
    r = ig.graph_get("me" if tok.startswith("IGAA") else str(conta["data"].get("instagramBusinessAccountId")),
                     {"fields": "username", "access_token": tok})
    return isinstance(r, dict) and bool(r.get("username"))


def cofre_logado(nome):
    """26/10: token da API venceu (inovarecom.ia, videocassetadascom.ia desde 24/10) mas o perfil ig_<conta> do cofre
    está logado neste PC (instagram_local.py --conferir) -> devolve a chave do cofre para postar pelo navegador."""
    est = catalogo._ler(Path(__file__).resolve().parents[1] / "config" / "instagram_local.json", {})
    return f"ig_{nome}" if str((est.get(nome) or {}).get("resultado", "")).startswith("logado") else None


NSN = Path(r"D:\projeto-navegador-sem-navegador")
PY_NSN = Path(r"D:\veo\venv\Scripts\python.exe")  # tem curl_cffi (o mesmo das tarefas NSN_*)

# 30/10 (dona: "sim, faça"): em 29/10 11 contas postaram 5 a 8 Reels em menos de 30 min (a rodada postava todo o
# teto do dia de uma vez, 60 s entre eles) e no dia seguinte landingpageia.ia e jornalcomia viraram "This user is
# inactive so they cannot upload". Agora: no máximo `max_por_rodada_conta` Reels por conta em cada rodada e
# `intervalo_conta_min` minutos entre dois Reels da mesma conta (reuso_plataformas.json -> instagram); sinal de
# bloqueio do Instagram = conta em pausa (config\instagram_pausas.json), sem tentar de novo pelo Chrome.
PAUSAS = Path(__file__).resolve().parents[1] / "config" / "instagram_pausas.json"
BLOQUEIOS = (  # (trecho da resposta, motivo, horas de pausa)
    ("user is inactive", "conta inativa no Instagram (This user is inactive)", 24 * 7),
    ("cannot upload", "Instagram não deixa a conta enviar", 24 * 7),
    ("feedback_required", "Instagram limitou a conta (feedback_required)", 48),
    ("checkpoint", "Instagram pediu verificação (checkpoint)", 48),
    ("challenge_required", "Instagram pediu verificação (challenge)", 48),
    ("Limitamos a frequ", "Instagram limitou a frequência", 48),
    ("accounts/suspended", "conta suspensa pelo Instagram (tela de suspensão)", 24 * 7),  # 01/11: msenergysolar.pa
)


def bloqueio(msg):
    """(motivo, horas) se a mensagem de erro é bloqueio da CONTA (não adianta outro caminho), senão None."""
    t = str(msg or "")
    return next(((m, h) for x, m, h in BLOQUEIOS if x.lower() in t.lower()), None)


def pausas():
    """{conta: {ate, motivo}} só das pausas ainda valendo."""
    agora = time.time()
    return {c: p for c, p in politica.ler_json(PAUSAS, {}).items()
            if isinstance(p, dict) and float(p.get("ate", 0)) > agora}


def pausar(nome, motivo, horas):
    d = politica.ler_json(PAUSAS, {})
    ate = time.time() + horas * 3600
    d[nome] = {"ate": ate, "ate_txt": datetime.fromtimestamp(ate).strftime("%d/%m %H:%M"), "motivo": motivo,
               "desde": datetime.now().strftime("%d/%m %H:%M"),
               "_leia": "apague esta linha para a conta voltar a postar antes do prazo"}
    politica.gravar_json(PAUSAS, d)
    log(f"  [{nome}] PAUSADA até {d[nome]['ate_txt']}: {motivo}")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"Instagram {nome}: {motivo}. Pausei a conta até {d[nome]['ate_txt']} "
                      f"(config\\instagram_pausas.json).", "instagram auto", importante=True)
    except Exception:  # noqa: BLE001 — aviso é ajuda, não requisito
        pass


def ultimo_post(posted, nome):
    """Hora (datetime) do Reel mais recente desta conta no log de postados, ou None."""
    ts = []
    for p in posted:
        if p.get("account") == nome and p.get("timestamp"):
            try:
                ts.append(datetime.fromisoformat(str(p["timestamp"])[:19]))
            except ValueError:
                pass
    return max(ts) if ts else None


PROXY_FORA = "PROXY FORA: fica para a próxima rodada (postagem nunca pela internet de casa)"


def _ip_insta(nome):
    """12/11 dona: "as postagens têm que ser pelo proxy" (login pode ser por casa). IP grátis da conta no ar = n; fora
    = None, e a conta espera a próxima rodada — antes seguia "como antes" (= internet de casa)."""
    try:
        n = proxy_tiktok.ip_da_conta(nome)
        if proxy_tiktok.garantir() and proxy_tiktok.pronto(n):
            return n
        log(f"  {nome}: IP grátis {n} fora do ar agora — não posto por casa, fica para a próxima rodada")
    except Exception as e:  # noqa: BLE001
        log(f"  {nome}: proxy indisponível ({type(e).__name__}) — não posto por casa, fica para a próxima rodada")
    return None


def postar_http(nome, r, arquivo, texto):
    """29/10 (Fable, D21 — dona: "implantar o navegador sem navegador na produção"): o Reel sai por HTTP com a sessão do
    Chrome do cofre deste PC (services\\instagram\\postar.py, provado em recenas.ia 29/10), sem abrir janela. Só quando
    há cookie colhido (cookies\\cofre_ig_<conta>.json com sessionid) e a conta não tem "sem_http". Devolve (ok, msg) ou
    None = não tentou (aí segue o Chrome). Falhou = também segue o Chrome (regra: nunca sem postagem)."""
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    arquivo = type(arquivo)(_g1080(arquivo)) if not isinstance(arquivo, str) else str(_g1080(arquivo))
    ig = catalogo._ler(catalogo.REUSO, {}).get("instagram") or {}
    if not ig.get("postar_http", True) or r.get("sem_http"):
        return None
    arq = NSN / "cookies" / f"cofre_ig_{nome}.json"
    try:
        ck = json.loads(arq.read_text(encoding="utf-8")).get("cookies") or []
    except (OSError, ValueError):
        return None
    if not any(c.get("name") == "sessionid" for c in ck):
        return None
    # 12/11 (dona: "use os 10 IPs grátis, melhor que todos pelo mesmo IP como é hoje"): o Reel por HTTP sai pelo IP
    # fixo Webshare da conta (o mesmo mapa do TikTok: proxy_tiktok.ip_da_conta — mesma pessoa, mesmo IP nas 2 redes).
    # INSTA_PROXY=0 desliga.
    env = dict(os.environ)
    if os.environ.get("INSTA_PROXY", "1") != "0" and not r.get("sem_proxy"):
        n_px = _ip_insta(nome)
        if n_px is None:
            return False, PROXY_FORA
        env["IG_PROXY"] = f"http://127.0.0.1:{proxy_tiktok.porta(n_px)}"
        log(f"  {nome}: Reel por HTTP pelo IP grátis {n_px}")
    try:
        p = subprocess.run([str(PY_NSN if PY_NSN.exists() else sys.executable), "-X", "utf8", "-m", "services.instagram.postar",
                            "reel", nome, str(arquivo), texto], cwd=str(NSN), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1200, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        saida = (p.stdout + p.stderr).strip()
        m = re.search(r"reel ok: (\S+)", saida)
        if m:
            log(f"  {nome}: Reel por HTTP (sem Chrome) -> {m.group(1)}")
            return True, "http"
        log(f"  {nome}: HTTP nao confirmou ({' | '.join(l.strip() for l in saida.splitlines()[-3:])[:300]}) -> Chrome")
        return False, "http: " + saida[-200:]
    except subprocess.TimeoutExpired:
        log(f"  {nome}: HTTP estourou o tempo -> Chrome")
        return False, "http: tempo"
    except Exception as e:  # noqa: BLE001
        log(f"  {nome}: HTTP falhou ({type(e).__name__}: {str(e)[:120]}) -> Chrome")
        return False, f"http: {type(e).__name__}"


def postar_http_remoto(nome, r, arquivo, texto):
    """29/10 (Fable, D23 — dona: "cada PC tem seus próprios cookies"): conta logada nos notebooks posta por HTTP LÁ, com
    os cookies colhidos LÁ (maquina_remota.Remoto.nsn_reel). Não abre Chrome nem ocupa a vez da máquina (vale com o
    telão passando vídeo). Sem cookie colhido ainda = None (o Chrome de lá posta e colhe no fim; da próxima vez é HTTP)."""
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    arquivo = type(arquivo)(_g1080(arquivo)) if not isinstance(arquivo, str) else str(_g1080(arquivo))
    if not r.get("maquina") or r.get("sem_http"):
        return None
    # 12/11 dona: o HTTP de lá sai pela internet de casa (o worker de lá não tem o proxy) — só para quem tem sem_proxy
    if os.environ.get("INSTA_PROXY", "1") != "0" and not r.get("sem_proxy"):
        return None
    import maquina_remota as mr
    perfil = (r.get("cofre") or f"ig_{nome}").lower()
    res = None
    for m in sorted(mr._lista(r["maquina"]), key=lambda x: mr.ORDEM_NAVEGADOR.get(x, 9)):
        rem = mr.Remoto(m)
        try:
            if not rem.vivo() or not rem.nsn_tem_cookie(perfil):
                continue
            ok, msg = rem.nsn_reel(nome, arquivo, texto)
            log(f"  {nome}: HTTP no {m}: {'ok' if ok else msg[:160]}")
            if ok:
                return True, msg
            res = (False, msg)
            if "não reconheceu o login" in msg or "cookie vencido" in msg:
                continue  # cookie de lá venceu: o Chrome de lá recolhe no caminho normal
            return res  # erro do Instagram (ex.: feedback_required): não insiste em outra máquina
        except Exception as e:  # noqa: BLE001
            res = (False, f"nsn {m}: {type(e).__name__}: {str(e)[:100]}")
    return res


def _colher_local(nome, r, porta):
    """10/11: os cookies do HTTP (NSN/cookies/cofre_ig_<conta>.json) eram de 28-29/10 e SEM sessionid — o postar_http
    desistia em toda conta e tudo ia pelo Chrome (lento; 0 Reels por HTTP desde 06/11). Depois de postar pelo Chrome
    deste PC (mesma conta, mesmo IP, Chrome já aberto), grava os cookies frescos: a próxima vai por HTTP e as
    métricas (postar._medir_conta) passam a sair. Falha aqui nunca afeta a postagem. Desligar: IG_COLHER=0."""
    if os.environ.get("IG_COLHER", "1") == "0" or not porta:
        return
    try:
        import websocket
        info = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=10).read())
        ws = websocket.create_connection(info["webSocketDebuggerUrl"], timeout=20)
        ws.send(json.dumps({"id": 1, "method": "Storage.getCookies"}))
        ck = []
        for _ in range(20):
            m = json.loads(ws.recv())
            if m.get("id") == 1:
                ck = (m.get("result") or {}).get("cookies") or []
                break
        ws.close()
        ck = [c for c in ck if "instagram.com" in c.get("domain", "")]
        if not any(c.get("name") == "sessionid" for c in ck):
            log(f"  {nome}: colher cookies — sem sessionid, não gravei")
            return
        chave = (r.get("cofre") or f"ig_{nome}").lower()
        dados = {"perfil": chave, "ua": info.get("User-Agent", "").replace("HeadlessChrome", "Chrome"),
                 "quando": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "cookies": [{k: c[k] for k in ("name", "value", "domain", "path")} for c in ck]}
        for arq in {f"cofre_{chave}.json", f"cofre_ig_{nome}.json"}:
            (NSN / "cookies" / arq).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"  {nome}: cookies frescos gravados ({len(ck)}, com sessionid) — próxima por HTTP")
    except Exception as e:  # noqa: BLE001
        log(f"  {nome}: colher cookies falhou ({type(e).__name__}: {str(e)[:80]})")


def postar_navegador(nome, r, arquivo, texto):
    """19/10 (dono: "todas as contas de insta postando"): conta sem token posta pelo Chrome do cofre
    (bin/instagram_login.py) com o instagram_cdp_poster. Só conta quando o Instagram mostra que compartilhou.
    29/10 (D21): antes do Chrome tenta o HTTP (postar_http); o Chrome virou a reserva.
    29/10 noite (D31, dona: "tudo isso tem que rodar em todos os notebooks e PCs"): conta ativada numa máquina posta
    por HTTP LÁ primeiro (os cookies de lá; mesma ordem do Chrome: máquinas antes do PC1). Até então o HTTP do PC1
    vencia sempre e o caminho das máquinas nunca rodou (log sem nenhum "HTTP no"). Ordem: HTTP na máquina -> HTTP PC1
    -> Chrome na máquina -> Chrome PC1."""
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    arquivo = type(arquivo)(_g1080(arquivo)) if not isinstance(arquivo, str) else str(_g1080(arquivo))
    h = postar_http_remoto(nome, r, arquivo, texto)
    if h and h[0]:
        return h
    if h and bloqueio(h[1]):  # 30/10: conta bloqueada não melhora em outro caminho (Chrome só piora)
        return h
    h = postar_http(nome, r, arquivo, texto)
    if h and h[0]:
        return h
    if h and (bloqueio(h[1]) or h[1] == PROXY_FORA):
        return h
    from postar_tiktok_auto import abrir_conta, fechar_conta
    # 12/11 (dona): o Chrome (notebook ou PC1) também sai pelo IP grátis da conta; máquina sem o Chrome pelo proxy
    # (PC2) é pulada pelo próprio tentativas. INSTA_PROXY=0 = como antes.
    n_px = None
    if os.environ.get("INSTA_PROXY", "1") != "0" and not r.get("sem_proxy"):
        n_px = _ip_insta(nome)
        if n_px is None:
            return False, PROXY_FORA
    # 23/10 (dona): conta logada nos notebooks posta por eles; erro num = o outro; erro de novo (ou conta fora dos
    # notebooks) = este PC. Já clicou em Compartilhar = para (não reposta).
    if r.get("maquina"):
        import maquina_remota
        ordem = maquina_remota.tentativas(r["maquina"], r.get("perfil_remoto"), log_fn=log, proxy_n=n_px)
    else:
        ordem = iter([None])
    res = (False, "navegador: sem tentativa")
    try:
        for rem in ordem:
            porta, proc, extra, envio = None, None, [], arquivo
            if rem is None and r.get("maquina") and not (r.get("cofre") or r.get("porta")):
                break  # conta só existe nos notebooks
            try:
                if rem:
                    porta, envio, extra = rem.porta_local, rem.enviar(arquivo), ["--remoto"]
                    log(f"  {nome}: pelo Chrome do {rem.nome}")
                else:
                    porta, proc = abrir_conta(nome, r, proxy_n=n_px)
                p = subprocess.run([sys.executable, "-u", str(Path(__file__).with_name("instagram_cdp_poster.py")),
                                    "--video", str(envio), "--caption", texto, "--port", str(porta), *extra],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
                saida = p.stdout + p.stderr
                # "Share clicado mas confirmação não detectada — provável sucesso" (o poster sai com 0): antes contava
                # como falha e a próxima rodada repostava (revisão 23/10)
                if rem and "not_logged_in" not in saida:  # D23: Chrome de lá está logado -> colhe o cookie de lá p/ HTTP
                    try:
                        rem.nsn_colher((r.get("cofre") or f"ig_{nome}").lower())
                    except Exception as e:  # noqa: BLE001
                        log(f"  {nome}: colher no {rem.nome} falhou ({type(e).__name__})")
                if "POSTADO com sucesso" in saida or (p.returncode == 0 and "provavel sucesso" in saida):
                    if not rem:
                        _colher_local(nome, r, porta)
                    return True, "navegador"
                res = (False, "navegador: " + " | ".join(l.strip() for l in saida.splitlines()[-4:]))
                if "Compartilhar clicado" in saida or "Share clicado" in saida:
                    return res  # pode ter saído: não reposta em outra máquina
            except subprocess.TimeoutExpired:
                return False, "navegador: estourou o tempo (pode ter compartilhado) — não reposto em outra máquina"
            except Exception as e:  # noqa: BLE001
                res = (False, f"navegador: {type(e).__name__}: {e}")
            finally:
                if not rem:
                    fechar_conta(porta, proc, r)
            if rem:
                log(f"  {nome}: falhou no {rem.nome} ({res[1][:100]}) — tento na próxima máquina")
    finally:
        if hasattr(ordem, "close"):
            ordem.close()
    return res


def legenda(v):
    """16/10 (AB-04): a fala do video / o titulo da rede, sem #viral/#reels (catalogo.legenda_reuso)."""
    return catalogo.legenda_reuso(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true", help="so mostra o que postaria (nao baixa nem posta)")
    ap.add_argument("--contas", nargs="*", help="roda so para estas contas")
    args = ap.parse_args()
    log("=== INICIO Instagram Auto (reuso pelo catalogo) ===")
    cfg = catalogo._ler(catalogo.REUSO, {}).get("instagram") or {}
    creds = {c.get("name", "").lower().replace("instagram", "").strip(): c for c in ig.carregar_contas()}
    posted = catalogo._ler(POSTED_LOG, [])
    feitos = feitos_hoje(posted)
    cat = catalogo.sincronizar()
    dispo = catalogo.disponiveis("instagram", cat)
    cand = defaultdict(list)
    for v in dispo:
        cand[v["conta_reuso"]].append(v)
    # 29/10 (D33, dona: "pode subir, com monitor de banimento"): o teto do dia vem da rampa em config\tetos.json
    # (tetos.py); sem linha lá, vale o max_dia da conta / max_por_conta_dia como antes
    import tetos
    plano = {nome: (max(0, tetos.teto("instagram", nome, padrao=r.get("max_dia") or cfg.get("max_por_conta_dia", 2))
                        - feitos[nome]), cand[nome])
             for nome, r in cfg.get("contas", {}).items()}
    for nome, (resta, _f) in plano.items():
        if tetos.linha("instagram", nome).get("nivel"):
            log(f"  [{nome}] teto da rampa: {tetos.teto('instagram', nome)}/dia (base {tetos.linha('instagram', nome).get('base')}), restam {resta}")
    plano = {nome: x for nome, x in plano.items() if x[0]}
    # 01/11: quem postou menos hoje vai primeiro (a rodada cortada pelo prazo deixava sempre as mesmas do fim da lista)
    plano = dict(sorted(plano.items(), key=lambda x: feitos[x[0]]))
    if args.contas:
        plano = {nome: x for nome, x in plano.items() if nome in args.contas}
    # 30/10: contas em pausa (bloqueio do Instagram) e ritmo por conta — ver BLOQUEIOS acima
    pz = pausas()
    for nome in [n for n in plano if n in pz]:
        log(f"  [{nome}] em pausa até {pz[nome].get('ate_txt')}: {pz[nome].get('motivo')} — pulada")
        plano.pop(nome)
    por_rodada = int(cfg.get("max_por_rodada_conta", 1))
    gap_min = float(cfg.get("intervalo_conta_min", 60))
    agora = datetime.now()
    for nome in list(plano):
        ult = ultimo_post(posted, nome)
        if ult and (agora - ult).total_seconds() < gap_min * 60:
            log(f"  [{nome}] último Reel às {ult:%H:%M}: espera {gap_min:.0f} min entre Reels da conta — fica para a próxima rodada")
            plano.pop(nome)
        elif por_rodada > 0:
            resta, fila = plano[nome]
            plano[nome] = (min(resta, por_rodada), fila)
    # 24/10 (dono): o que a empresa colocou na pasta publica dela vem primeiro (ate metade das vagas do dia, cor da
    # marca, checado por visao); o resto e video da conta / Veo de reserva (bin/pastas_empresas.py)
    # 03/11: as 2 rodadas do dia (10:22 e 13:02) morreram no prazo de 150 min com 0 posts — a preparação das ~33
    # contas (pasta da empresa no Drive lento/403 + vídeo de produto) levou 1h40+ antes do 1º Reel. Orçamento: passou
    # de PREP_MAX_S, as contas seguintes vão sem a pasta da empresa (o resto da fila completa) e a postagem começa.
    prep_ini, prep_max = time.time(), float(cfg.get("prep_max_s", 1200))
    for nome, (resta, fila) in plano.items():
        t_conta = time.time()
        if time.time() - prep_ini < prep_max:
            try:
                fila[:0] = pastas_empresas.itens(nome, (resta + 1) // 2, log)
            except Exception as e:  # noqa: BLE001  (pasta fora nao para a postagem)
                log(f"  [{nome}] pasta da empresa: {type(e).__name__}: {str(e)[:160]}")
        elif not getattr(main, "_avisou_prep", False):
            main._avisou_prep = True
            log(f"  preparação passou de {prep_max / 60:.0f} min — próximas contas sem a pasta da empresa nesta rodada")
        # 25/10 (dono: "focados nos produtos, de maneira profissional"): depois da pasta da empresa vem o vídeo
        # profissional do produto (bin/produto); o Veo de reserva só completa o que ainda sobrar
        try:
            n_emp = sum(1 for v in fila if v.get("projeto") == "empresa")
            fila[n_emp:n_emp] = produto_fila.itens(nome, resta - n_emp, log)
        except Exception as e:  # noqa: BLE001
            log(f"  [{nome}] fila de produto: {type(e).__name__}: {str(e)[:160]}")
        if time.time() - t_conta > 60:
            log(f"  [{nome}] preparação lenta: {time.time() - t_conta:.0f} s")
    log(f"preparação das contas: {time.time() - prep_ini:.0f} s")
    reserva_veo.completar("instagram", plano, dispo, cat, log)
    log("fila pronta — começando a postar")

    total_ok = total_err = 0
    paradas = {}
    for nome, (resta, fila) in plano.items():
        if not fila:
            paradas[nome] = "sem video: nem o da conta nem Veo de reserva"
            continue
        if args.simular:
            for v in fila[:resta]:
                extra = f" [reserva {v['reserva']}]" if v.get("reserva") else ""
                log(f"  [simulacao] {nome}: {'PC   ' if v['no_pc'] else 'Drive'} {v['caminho']}{extra}")
            continue
        r = cfg["contas"][nome]
        conta = creds.get(nome)
        # 23/10 (revisão): conta logada só nos notebooks ("maquina") também posta pelo navegador
        navegador = bool(r.get("cofre") or r.get("maquina"))
        if not navegador and (not conta or not conta_ok(conta)) and cofre_logado(nome):
            log(f"{nome}: token da API vencido — posto pelo navegador (perfil {cofre_logado(nome)} logado)")
            r = {**r, "cofre": cofre_logado(nome)}
            navegador = True
        if not navegador and (not conta or not conta_ok(conta)):
            log(f"{nome}: login do Instagram vencido ou credencial ausente - pulada")
            paradas[nome] = "login do Instagram vencido ou credencial ausente (renovar a credencial no n8n)"
            continue
        while resta and fila:
            v = fila.pop(0)
            try:
                local = catalogo.baixar(v)
            except Exception as e:  # noqa: BLE001
                log(f"  {v['nome']}: {e}")
                # 07/11: hipercool pt/en/id... tem o MESMO nome no mesmo caminho do Drive (2_tiktok/_/) e um sobrescreveu
                # o outro: o tamanho nunca bate e o vídeo era escolhido 5–8x por dia. Sumiu/tamanho errado = pula de vez
                if "nao baixou do Drive" in str(e) and ("directory not found" in str(e) or str(e).rstrip().endswith(":")):
                    catalogo.pular("instagram", v, "cópia do Drive não existe ou foi sobrescrita (tamanho diferente)")
                continue
            d = duracao(local)
            if not d or d > cfg.get("duracao_max_s", 90):
                catalogo.pular("instagram", v, f"duracao {d}")
                catalogo.liberar(local)
                log(f"  [{nome}] pulado de vez: {v['nome']} tem {round(d) if d else '?'}s "
                    f"(maximo {cfg.get('duracao_max_s', 90)}s)")
                continue
            texto = v.get("legenda") or legenda(v)  # pasta da empresa traz a legenda da marca
            if not texto.strip():  # 28/10 (dono): nunca postar com legenda "Video"/vazia
                catalogo.pular("instagram", v, "sem legenda (título não achado)")
                catalogo.liberar(local)
                log(f"  [{nome}] pulado de vez: {v['nome']} ({v.get('caminho')}) sem legenda de verdade")
                continue
            log(f"[{nome}] {v['nome']} ({d:.0f}s, {'PC' if v['no_pc'] else 'Drive'})"
                + (f" [reserva {v['reserva']}]" if v.get("reserva") else ""))
            # 16/10 (dono): 1 a cada 3 do Veo nesta conta vai COM propaganda, montada segura na hora (comercial_veo)
            com = comercial_veo.preparar(v, "instagram", nome, log)
            if navegador:
                ok, msg = postar_navegador(nome, r, com["arquivo"] if com else local, " ".join(texto.split()))
            else:
                url = ig.upload_video_publico(str(com["arquivo"] if com else local))
                ok, msg = ig.postar_reel(conta, url, texto) if url else (False, "nao subiu para link publico")
            catalogo.liberar(local)
            if com:
                catalogo.liberar(com["arquivo"])
            if ok:
                total_ok += 1
                resta -= 1
                log(f"  OK {msg}")
                posted.append({"file": v["nome"], "path": v["caminho"], "account": nome, "media_id": msg.split("=")[-1],
                               "tipo": v["projeto"], "formato": "comercial" if com else "limpo",
                               "produto": com["produto"] if com else None, "reserva": v.get("reserva"),
                               "timestamp": datetime.now().isoformat()})
                politica.gravar_json(POSTED_LOG, posted)  # 22/10 (P05): troca atômica (truncado = repostagem)
                if v.get("projeto") == "empresa":  # originais vao para usados/ no Drive; nada de catalogo/etapas
                    pastas_empresas.usado(v, log)
                    time.sleep(cfg.get("intervalo_s", 60))
                    continue
                if v.get("projeto") == "produto":  # vídeo profissional: vai para _postados/ da fila
                    produto_fila.usado(v, log)
                    time.sleep(cfg.get("intervalo_s", 60))
                    continue
                try:
                    reserva_veo.usado(v, "instagram", nome)
                except Exception as e:  # noqa: BLE001  (nao para a rodada; o limpo ainda pode subir no YouTube)
                    log(f"  ATENCAO: nao marquei {v['nome']} como usado (rejeitar na mao p/ YouTube): {e}")
                if v.get("reserva") != "limpo":  # limpo da reserva nao esta no catalogo/Drive
                    try:  # no Drive o video passa para a etapa seguinte e entra no _registro/<pc>.jsonl (bin/etapas.py)
                        etapas.registrar(v, "instagram", nome)
                    except Exception as e:  # noqa: BLE001  (Drive fora nao para a postagem: o log acima ja guardou)
                        log(f"  etapas: {str(e)[:160]}")
                time.sleep(cfg.get("intervalo_s", 60))
            else:
                total_err += 1
                log(f"  ERRO: {str(msg)[:160]}")
                paradas.setdefault(nome, f"erro ao postar: {' '.join(str(msg).split())[-120:]}")
                b = bloqueio(msg)
                if not b and "nao encontrou botao de criar post" in str(msg):
                    # 10/11: emerson20308.ia logada mas sem o botão de criar post — repetia a cada 30 min o dia todo
                    # (rodadas com 0 posts). 2ª vez no dia = pausa 12 h (a dona confere a conta no navegador).
                    arq_sb = Path(__file__).resolve().parents[1] / "config" / "instagram_sem_botao.json"
                    sb = politica.ler_json(arq_sb, {})
                    chave_sb = f"{nome}|{datetime.now():%Y-%m-%d}"
                    sb[chave_sb] = sb.get(chave_sb, 0) + 1
                    politica.gravar_json(arq_sb, {k: v for k, v in sb.items()
                                                  if k.endswith(datetime.now().strftime("%Y-%m-%d"))})
                    if sb[chave_sb] >= 2:
                        b = ("sem o botão de criar post no Instagram (2x hoje) — conferir a conta no navegador", 12)
                if b:  # 30/10: bloqueio da conta -> pausa (a próxima rodada não insiste)
                    pausar(nome, *b)
                break  # erro de conta/API: nao insiste nesta conta hoje
        else:
            if not feitos_hoje(posted)[nome]:
                paradas.setdefault(nome, "os videos da fila nao baixaram do Drive ou eram longos demais")
    log(f"=== RESUMO Instagram: postados {total_ok} | erros {total_err} ===")
    if not args.simular:
        hoje = feitos_hoje(posted)
        avisar_paradas("Instagram", total_ok, {c: m for c, m in paradas.items() if not hoje[c]}, log)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:  # 23/10: em 21/10 quebrou às 09:00 e ninguém soube (o aviso de conta parada fica no fim)
        log(f"RODADA QUEBROU: {type(ex).__name__}: {ex}")
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"A rodada do Instagram quebrou antes de terminar ({type(ex).__name__}: {str(ex)[:200]}). "
                          "As contas que não postaram tentam de novo na rodada extra (14:05 e 19:35, depois do TikTok).",
                          "postador", importante=True, html_ok=False)
        except Exception:  # noqa: BLE001
            pass
        raise
