# -*- coding: utf-8 -*-
"""cadeia_veo.py — ORDEM DE ALTERNATIVAS do Veo (dona, 23/10/2026: "pra ter uma ordem de fallbacks do Veo, justamente
pra nao ter como dar errado em todos, algum vai fazer").

Ordem das maquinas (dona, 23/10: "a ordem e primeiro os notebooks, depois o desktop se nao tiver rodando chamada, nem
chamada, e depois o PC2 ou o 1, dependendo de qual esta mais desocupado"):
  1. notebooks (x200ma, acer): o que estiver livre; o Veo reserva contra o login do TikTok (_reservar_notebooks);
  2. desktop: SO sem chamada/OBS (microfone/camera em uso, medido por D:\\video-fila\\maquinas.py) e sem o botao
     "desktop desligado" do painel;
  3. PC2 ou PC1, o mais desocupado (mais RAM livre pela mesma medicao). PC1 em pausa de CARGA ou sem RAM p/ 1 Chrome =
     ocupado. PC2 so entra com conta do Flow logada la (netbooks_logins.json; hoje nenhuma).
Dentro de cada maquina vale a troca de conta do cron (sem credito/deslogada/castigo -> proxima conta).
Pausa MANUAL da dona e pausa de BLOQUEIO nao passam por aqui (o cron para antes). Nada disto gasta credito do Flow.

Maquina que falhou ao abrir o Chrome fica de castigo (logs\\maquinas_veo.json) — antes o x200ma ("o Chrome nao abriu a
porta de controle") comia ~7 min de CADA ciclo. Nada funcionou por mais de VEO_AVISO_H horas (3) = UM aviso a dona,
com o motivo exato (logs\\veo_sem_alternativa.json; zera no proximo video que sair).
"""
import datetime
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
ARQ_CASTIGO = os.path.join(BASE, "logs", "maquinas_veo.json")
ARQ_SEM = os.path.join(BASE, "logs", "veo_sem_alternativa.json")
# 12/11 (dona: "pode usar o STI ao máximo, i5 e 16 GB"): o STI (chegou 11/11) não estava na lista — o Veo ficou
# horas com "cadeia: NENHUMA" (x200ma no telão/falhando "Algo deu errado" desde 05:34, acer no telão) enquanto o STI,
# com 65 contas Google logadas e o Flow funcionando (imagens do Claude Code Video saem lá), ficava parado.
# Ele vai PRIMEIRO: não exibe telão. VEO_SEM_STI=1 tira.
NOTEBOOKS = (("x200ma", "acer") if os.environ.get("VEO_SEM_STI") == "1" else ("sti", "x200ma", "acer"))
AVISO_H = float(os.environ.get("VEO_AVISO_H", "3"))
# castigo por tipo de falha da maquina (minutos)
CASTIGO_MIN = {"FALHOU": 30, "nao respondeu": 20, "OCUPADO": 5}


def _log(m):
    print(f"[cadeia] {m}", flush=True)


def _mr():
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import maquina_remota
    return maquina_remota


def _ler(p, padrao):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def _gravar(p, d):
    try:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, p)
    except Exception as e:
        _log(f"nao gravei {os.path.basename(p)}: {e}")


# ─── maquinas de cada conta ───────────────────────────────────────────────────
def maquinas_da_conta(perfil):
    """Onde o Flow dessa conta pode rodar: as maquinas do postador (maquina_remota.maquinas_flow) + o PC2 se a conta
    estiver logada la (o postador ainda tira o PC2 do Flow; a dona pediu o PC2 na cadeia em 23/10)."""
    try:
        mr = _mr()
        p = (perfil or "").lower()
        maqs = list(mr.maquinas_flow(p))
        info = (mr._logins().get(p) or {}).get("pc2")
        if p not in mr.FLOW_BLOQUEADAS and isinstance(info, dict) and info.get("youtube") and "pc2" not in maqs:
            maqs.append("pc2")
        return maqs
    except Exception:
        return []


def contas_no_pc2():
    try:
        mr = _mr()
        return [p for p, v in mr._logins().items()
                if not p.startswith("_") and isinstance(v, dict) and isinstance(v.get("pc2"), dict)
                and v["pc2"].get("youtube") and p not in mr.FLOW_BLOQUEADAS]
    except Exception:
        return []


# ─── Flow por HTTP na maquina (29/10, D30) ────────────────────────────────────
def http_remoto_ligado(sessao, tipo="video"):
    """O caminho HTTP esta ligado para esta conta? (config.FLOW_HTTP_REMOTO, FLOW_HTTP=0 do gera_auto, contas.SEM_HTTP)"""
    if os.environ.get("FLOW_HTTP") == "0":
        return False
    # 12/11: disjuntor do HTTP (projeto-navegador-sem-navegador\services\veo_flow\flow_gerar.py) — com o HTTP voltando
    # vazio, nem abre o Chrome-só-pro-token: vai direto pela tela (economiza ~77 s por pedido)
    try:
        nsn = r"D:\projeto-navegador-sem-navegador"
        if nsn not in sys.path:
            sys.path.append(nsn)
        from services.veo_flow import flow_gerar as _fg
        if _fg.disjuntor_aberto():
            return False
    except Exception:  # noqa: BLE001
        pass
    try:
        # 12/11: o config do VEO pelo caminho — com o nsn no sys.path (disjuntor), "import config" pegava o config.py
        # do projeto-navegador-sem-navegador (sem FLOW_HTTP_REMOTO -> padrão True: religava o HTTP de vídeo)
        import importlib.util
        _sp = importlib.util.spec_from_file_location("config_veo", os.path.join(BASE, "config.py"))
        config = sys.modules.get("config_veo")
        if config is None:
            config = importlib.util.module_from_spec(_sp)
            _sp.loader.exec_module(config)
            sys.modules["config_veo"] = config
        # 12/11: imagem tem interruptor próprio — o pedido novo (BELUGA, ogiZ0b) funciona pra imagem; vídeo segue
        # pela tela até o pedido novo de vídeo ser mapeado
        chave = "<SEGREDO_REMOVIDO>" if tipo == "imagem" else "FLOW_HTTP_REMOTO"
        if not getattr(config, chave, True):
            return False
        # 12/11: o VIGIA (vigia_flow.py, tarefa VigiaFlow) desliga a rota HTTP sozinho quando ela quebra e religa
        # quando o teste passa — a produção nunca para (vai pela tela)
        try:
            import vigia_flow
            if not vigia_flow.http_permitido("imagem" if tipo == "imagem" else "video"):
                return False
        except Exception:  # noqa: BLE001
            pass
        import contas
        return not contas.sem_http(sessao)
    except Exception:
        return False


_FLOW_PRONTO = {}


def http_remoto(rem, sessao, perfil, prompt, out_path, image, aspect, modelo, log=_log):
    """Antes de abrir o Flow pelo Playwright no Chrome da maquina `rem` (maquina_remota.Remoto JA aberto no perfil),
    tenta gerar por HTTP LA: o Chrome de la so fabrica o token do reCAPTCHA (Remoto.nsn_flow_video) e e fechado assim
    que o Flow aceita o pedido; o mp4 volta por scp. Ordem (igual ao Reel, D23): HTTP na maquina -> Chrome na maquina.
    Devolve (caminho_ou_None, estado):
      "ok"           caminho preenchido
      "pediu"        o Flow aceitou o pedido (credito gasto) mas o arquivo nao veio: NAO repetir no Chrome
      "sem_credito"  saldo < minimo (nao abriu nada a mais)
      "login"        o Flow pediu login nessa maquina
      "pular"        nao tentou ou falhou ANTES de pedir: segue o Chrome como antes
    O saldo lido vai no log como "[CREDITOS] saldo lido no menu de conta: N" (creditos_contas.anotar_uso le isso)."""
    if not http_remoto_ligado(sessao):
        return None, "pular"
    # o mesmo logs\flow_projetos.json do gera_auto (nao importa o gera_auto: rodando como __main__ ele reexecutaria)
    url = _ler(os.path.join(BASE, "logs", "flow_projetos.json"), {}).get(sessao)
    if not url or "/project/" not in url:
        log(f"[http-remoto] {sessao}: sem projeto salvo (flow_projetos.json) — o Chrome cria e salva; proxima vez e HTTP")
        return None, "pular"
    try:
        if rem.nome not in _FLOW_PRONTO:
            _FLOW_PRONTO[rem.nome] = rem.nsn_flow_pronto()
        if not _FLOW_PRONTO[rem.nome]:
            log(f"[http-remoto] {rem.nome}: worker sem o Flow (rode maquina_remota.py instalar-nsn) — Chrome")
            return None, "pular"
        try:
            import config
            fechar = getattr(config, "FLOW_HTTP_FECHAR_CHROME", True)
            duas = getattr(config, "FLOW_HTTP_2_FASES", True)
        except Exception:
            fechar, duas = True, True
        log(f"[http-remoto] {sessao}: pedindo o video por HTTP no {rem.nome} (Chrome so para o token)")
        if fechar and duas:
            # 29/10 (dona: "deixe as maquinas produzindo ao maximo"): pedido aceito -> solta a VEZ da maquina (o cron a
            # reservou como "veo" para o ciclo todo) e baixa depois sem Chrome: a maquina fica livre durante a renderizacao
            def _soltar():
                _mr().liberar(rem.nome, quem="veo")
                log(f"[http-remoto] {rem.nome}: Chrome fechado e vez liberada; o Flow renderiza e o mp4 vem por HTTP")
            r = rem.nsn_flow_video_2fases(perfil, url, prompt, out_path, formato=aspect, modelo=modelo, imagem=image,
                                          soltar=_soltar, log_fn=log)
        else:
            r = rem.nsn_flow_video(perfil, url, prompt, out_path, formato=aspect, modelo=modelo, imagem=image,
                                   fechar_chrome=fechar, log_fn=log)
    except Exception as e:
        log(f"[http-remoto] {rem.nome}: falhou antes de pedir ({type(e).__name__}: {str(e)[:120]}) — Chrome")
        return None, "pular"
    if r.get("saldo") not in (None, "None"):
        log(f"[CREDITOS] saldo lido no menu de conta: {r['saldo']} (por HTTP no {rem.nome})")
    if r.get("ok"):
        log(f"[http-remoto] {sessao}: video gerado por HTTP no {rem.nome} — Chrome aberto {r.get('chrome_s')} s, "
            f"pedido {r.get('segundos')} s, total {r.get('total_s')} s -> {out_path}")
        return out_path, "ok"
    if r.get("sem_credito"):
        return None, "sem_credito"
    if r.get("login"):
        return None, "login"
    if r.get("pediu"):
        log(f"[http-remoto] {sessao}: o Flow aceitou o pedido mas o arquivo nao veio ({r.get('msg')}) — nao repete")
        return None, "pediu"
    log(f"[http-remoto] {sessao}: {r.get('msg')} — segue o Chrome do {rem.nome}")
    return None, "pular"


# ─── castigo de maquina ───────────────────────────────────────────────────────
def castigo(maq):
    """Motivo do castigo em vigor da maquina, ou None."""
    c = _ler(ARQ_CASTIGO, {}).get(maq) or {}
    return c.get("motivo") if c.get("ate", 0) > time.time() else None


def castigar(maq, minutos, motivo):
    d = _ler(ARQ_CASTIGO, {})
    d[maq] = {"ate": time.time() + minutos * 60, "motivo": motivo[:160],
              "desde": datetime.datetime.now().isoformat(timespec="seconds")}
    _gravar(ARQ_CASTIGO, d)
    _log(f"{maq} fora por {minutos} min ({motivo[:100]})")


# 24/10: "está exibindo vídeo no telão" / "está com a vez de 'X'" (maquina_remota.tentativas) tambem sao MAQUINA ocupada:
# sem isso nada casava, o cron culpava a CONTA (15 min fora) e passava pra proxima conta da MESMA maquina - 18 contas
# fora em 40 s no teste das 15:51
_RE_MAQ = re.compile(r"^\s*(x200ma|acer|desktop|pc2)(?::\s*(FALHOU|OCUPADO)[^\r\n]*| n[aã]o respondeu"
                     r"| (est[aá] exibindo|est[aá] com a vez de)[^\r\n]*)", re.M)


def anotar_maquinas(saida):
    """Le a saida do gera_auto (linhas do maquina_remota.tentativas) e poe de castigo quem falhou/estava ocupado.
    Devolve {maquina: tipo}."""
    vistos = {}
    for m in _RE_MAQ.finditer(saida or ""):
        tipo = m.group(2) or ("OCUPADO" if m.group(3) else "nao respondeu")
        vistos[m.group(1)] = tipo
        castigar(m.group(1), CASTIGO_MIN[tipo], m.group(0).strip())
    return vistos


# ─── a cadeia ─────────────────────────────────────────────────────────────────
def _livre(maq):
    if castigo(maq):
        return False
    try:
        # 23/10 (dona: "um navegador por vez; se está fazendo login, nem exibição nem Veo até terminar"): a VEZ da
        # máquina com outro dono (login manual/TikTok, postagem...) = ocupada; a do próprio Veo não conta
        vez = _mr().reservado(maq, quem="veo")
        # 12/11: máquina com 2ª faixa (STI, 16 GB) segue livre pro Veo durante o login AUTOMÁTICO de TikTok — o
        # maquina_remota.tentativas abre o Chrome do Veo na porta extra
        if vez and (_mr().MAQUINAS.get(maq) or {}).get("faixa_extra") and "tiktok" in vez.lower() \
                and "manual" not in vez.lower() and os.environ.get("MAQUINA_SEM_FAIXA_EXTRA") != "1":
            return True
        if vez:
            return False
        return _mr().maquina_livre(maq)
    except Exception:
        return False


def exibindo(maq):
    """O telao (D:\\video-fila\\vitrine\\player.py) esta TOCANDO video nesse notebook agora? Dona 23/10: "o Veo tambem
    nao pode fazer se tiver exibindo um video". O player abre o navegador com o perfil ~/vitrine/perfil_* e a URL do
    video (youtube.com ou file://) na linha de comando; o painel (painel.html) nao conta. Sem resposta = trata como
    exibindo (nao arrisca)."""
    try:
        r = _mr().Remoto(maq)
        if r.win:
            return False  # desktop/PC2 nao tocam video do telao
        saida = r._txt(r._ssh("pgrep -af '[v]itrine/perfil_' || true", timeout=20))
        return any(("youtube.com" in l or "file://" in l) for l in saida.splitlines())
    except Exception:
        return True


def _medir(host):
    """Medicao oficial dos PCs (D:\\video-fila\\maquinas.py: CPU/RAM/render; desktop: chamada/OBS)."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import maquinas
        return maquinas.medir(host)
    except Exception as e:
        return {"host": host, "ocioso": False, "motivo": f"medicao falhou ({type(e).__name__})"}


def cadeia(pausa_carga, pc1_tem_ram, medir=_medir, livre=_livre, contas_pc2=contas_no_pc2, tocando=exibindo):
    """Etapas em ordem p/ este ciclo: [(nome, [maquinas])] e as que ficaram de fora [(nome, motivo)].
    'pc1' = Chrome deste PC (contas locais de contas.py)."""
    etapas, fora = [], []
    nb, porque = [], []
    for m in NOTEBOOKS:
        c = castigo(m)
        if c:
            porque.append(f"{m} de castigo ({c[:60]})")
        elif not livre(m):
            porque.append(f"{m} ocupado (Chrome de outra acao aberto) ou sem resposta")
        elif tocando(m):
            porque.append(f"{m} exibindo video no telao")
        else:
            nb.append(m)
    if nb:
        etapas.append(("notebooks", nb))
    else:
        fora.append(("notebooks", "; ".join(porque)))
    # 2. desktop: so sem chamada (a medicao ja diz "dono usando: microphone:..." / OBS / desligado no painel)
    c = castigo("desktop")
    if c:
        fora.append(("desktop", f"de castigo ({c[:60]})"))
    else:
        md = medir("desktop")
        if not md.get("ocioso"):
            fora.append(("desktop", md.get("motivo") or "ocupado"))
        elif not livre("desktop"):
            fora.append(("desktop", "Chrome de outra conta aberto la"))
        else:
            # 28/10 (dona): o desktop é a máquina MAIS LIVRE -> vai na frente dos notebooks (câmera fixa ter/qui
            # 10-12 h e sex 16-18 h: maquinas.AGENDA_CAMERA deixa ele "ocupado" nesses horários)
            etapas.insert(0, ("desktop", ["desktop"]))
    # 3. PC2 ou PC1, o mais desocupado
    cands = []
    if not contas_pc2():
        fora.append(("pc2", "nenhuma conta do Flow logada no PC2"))
    elif castigo("pc2"):
        fora.append(("pc2", f"de castigo ({castigo('pc2')[:60]})"))
    else:
        m2 = medir("pc2")
        if m2.get("ocioso") and livre("pc2"):
            cands.append((m2.get("ram_gb") or 0, "pc2"))
        else:
            fora.append(("pc2", m2.get("motivo") or "Chrome ocupado"))
    if pausa_carga:
        fora.append(("pc1", "PC1 em pausa por carga (pouca RAM)"))
    elif not pc1_tem_ram:
        fora.append(("pc1", "PC1 sem RAM p/ 1 Chrome"))
    else:
        m1 = medir("pc1")
        if m1.get("ocioso"):
            cands.append((m1.get("ram_gb") or 0, "pc1"))
        else:
            fora.append(("pc1", m1.get("motivo") or "ocupado"))
    for _ram, h in sorted(cands, reverse=True):
        etapas.append((h, [h]))
    return _fixo_primeiro(etapas, fora, livre)


def _fixo_primeiro(etapas, fora, livre):
    """Dono 24/10 (kanban das Maquinas do painel): Veo arrastado pra uma maquina vai PRIMEIRO pra ela; as outras ficam
    de reserva (nenhum canal sem postagem). Fixo no desktop passa por cima de OBS/chamada (o dono mandou)."""
    try:
        with open(r"D:\video-fila\estado\transferencias.json", "r", encoding="utf-8") as f:
            alvo = (json.load(f).get("fixos") or {}).get("veo")
    except Exception:
        alvo = None
    if not alvo:
        return etapas, fora
    resto = []
    for nome, maqs in etapas:
        if alvo in maqs and len(maqs) > 1:
            resto.append((nome, [m for m in maqs if m != alvo]))
        elif alvo not in maqs:
            resto.append((nome, maqs))
    if alvo in {m for _n, ms in etapas for m in ms} or (alvo == "desktop" and not castigo("desktop") and livre("desktop")):
        _log(f"Veo fixado no {alvo} pelo dono: vai primeiro pra ele")
        return [(alvo, [alvo])] + resto, [x for x in fora if x[0] != alvo]
    return etapas, fora + [(alvo, "fixado pelo dono, mas indisponivel agora")]


def resumo(etapas, fora):
    s = " -> ".join(f"{n}({','.join(m)})" for n, m in etapas) or "NENHUMA"
    if fora:
        s += " | fora: " + "; ".join(f"{n}: {mo}" for n, mo in fora)
    return s


# ─── aviso unico a dona ──────────────────────────────────────────────────────
def _enviar_aviso(texto):
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "veo", importante=True, chave="<SEGREDO_REMOVIDO>")
    except Exception as e:
        _log(f"aviso pelo Telegram falhou ({e})")
    try:
        from notifica import avisar_desktop
        avisar_desktop("Veo parado", texto[:200])
    except Exception:
        pass


def registrar_falha(motivo, agora=None):
    """Ciclo sem video. Passou de AVISO_H horas sem nenhum = avisa a dona UMA vez, com o ultimo motivo."""
    agora = agora or datetime.datetime.now()
    d = _ler(ARQ_SEM, {})
    if not d.get("desde"):
        d["desde"] = agora.isoformat(timespec="seconds")
    d["motivo"] = (motivo or "?")[:400]
    d["ultimo"] = agora.isoformat(timespec="seconds")
    horas = (agora - datetime.datetime.fromisoformat(d["desde"])).total_seconds() / 3600
    if horas >= AVISO_H and not d.get("avisado"):
        _enviar_aviso(f"Veo sem gerar ha {horas:.1f} h (desde {d['desde'][11:16]}). Motivo agora: {d['motivo']}")
        d["avisado"] = agora.isoformat(timespec="seconds")
    _gravar(ARQ_SEM, d)
    return d


def registrar_sucesso():
    if os.path.exists(ARQ_SEM):
        try:
            os.remove(ARQ_SEM)
        except OSError:
            pass
