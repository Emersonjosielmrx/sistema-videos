# -*- coding: utf-8 -*-
r"""zelador_sonnet.py — renova sozinho o cookie (sessionKey) das contas Sonnet web, no molde do argon_zelador.
Tarefa ZeladorSonnet 1x por dia (oculta). Para cada conta do claude-web:
  - cookie vence em menos de 14 dias, OU o OmniRoute marcou a conta com cookie ruim (expired/error/invalid):
    lê o cookie no PC2; se for a MESMA sessão já salva, apaga o sessionKey no Chrome do perfil e entra de novo pelo
    Google (claude_criar) = sessão nova; ATUALIZA a conta existente no OmniRoute (cadastrar_claude_web.py faz PUT,
    não duplica) e deixa ela ativa e sem o health check falso (Cloudflare).
  - no máximo 5 por rodada (o Google trava depois de muitos logins seguidos — visto 29/10).
Falha só avisa no Telegram (portão avisos.py). Log: D:\sonnet web\zelador_sonnet.log
    python "D:\sonnet web\zelador_sonnet.py"            # rodada normal
    python "D:\sonnet web\zelador_sonnet.py" --simular  # só mostra quem renovaria
    python "D:\sonnet web\zelador_sonnet.py" --so conta_exemplo   # força uma conta só (teste)
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass
sys.path.insert(0, r"D:\postador-de-videos\bin")
sys.path.insert(0, r"D:\sonnet web")
sys.path.insert(0, r"D:\video-fila")

import pegar_cookies as pc  # noqa: E402
import monitor_sonnet as mon  # noqa: E402

BASE = Path(r"D:\sonnet web")
LOG = BASE / "zelador_sonnet.log"
BARRADAS = BASE / "contas_barradas.json"  # barradas no claude.ai (403 com sessão nova): desligadas, não renovar
MAX_RODADA = 5
# 30/10: 45 das 48 sessões vencem no MESMO dia (26/11). Com 5 por dia e janela de 7 dias só daria 35; com 14 dias a
# renovação começa em 12/11 e espalha os vencimentos (cada renovada passa a vencer num dia diferente).
DIAS_ANTES = 14


def log(m):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def cadastrar(email, info):
    nome = f"claude-web {email.split('@')[0]}"
    cmd = ('S=$(docker exec omniroute printenv INITIAL_PASSWORD); python3 /opt/omniroute/cadastrar_claude_web.py "$S"; '
           "sqlite3 /opt/omniroute/data/storage.sqlite \"UPDATE provider_connections SET health_check_interval=0, "
           f"test_status='active', last_error=NULL, error_code=NULL WHERE provider='claude-web' AND name='{nome}'\"")
    return mon.ssh(cmd, entrada=json.dumps({email: info}).encode(), timeout=180).strip()


def _nova(info, exp_antes):
    """Sessão diferente da salva: a mesma sessão relida vem com o vencimento idêntico; a nova vence depois (30/10:
    sessão de ontem renovada hoje = só ~19 h a mais, por isso 10 min de folga e não 1 dia)."""
    return bool(info) and (info.get("expira") or 0) > exp_antes + 600


def renovar(email, exp_antes=0):
    """30/10: reler o cookie devolve a MESMA sessão (mesmo vencimento) — a renovação antiga era de mentira. Agora:
    se o Chrome do perfil não tem sessão mais nova que a salva, apaga o sessionKey lá (só no Chrome; o servidor
    segue aceitando o velho), entra de novo pelo Google (sessão nova, ~4 semanas) e só então grava e faz o PUT."""
    perfil = email.split("@")[0]
    info = pc.pegar(perfil, "pc2")
    if not _nova(info, exp_antes):
        if info:
            log(f"{perfil}: Chrome tem a mesma sessão (vence {time.strftime('%d/%m', time.localtime(exp_antes))}); "
                f"apagando o sessionKey lá para entrar de novo ({pc.esquecer_sessao(perfil, 'pc2')} apagado)")
        import claude_criar as cc
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            r = cc.criar(p, email, None, maq_forcada="pc2")
        log(f"{perfil}: relogin -> {r}")
        info = pc.pegar(perfil, "pc2")
    if not info:
        return False, "sem sessionKey mesmo após relogin"
    if not _nova(info, exp_antes):
        return False, "o login não abriu sessão nova (mesmo vencimento); cookie velho segue no OmniRoute"
    pc.salvar(email, info)
    saida = cadastrar(email, info)
    ok = "atualizada" in saida or "1 criadas" in saida
    if ok:
        teste = oi_na_conta(f"claude-web {perfil}")
        if "permission_denied" in teste or teste.startswith("403"):
            # 30/10 (conta_exemplo): sessão NOVA e ainda 403 = a conta está barrada no claude.ai, não é cookie.
            # Sai do rodízio (cada 403 custava uma volta do combo) e não volta a ser renovada todo dia.
            desligar(f"claude-web {perfil}", "403 com sessão nova")
            return False, "BARRADA no claude.ai (403 permission_denied com sessão nova) — desligada no OmniRoute"
        saida = f"oi: {teste[:60]}; " + saida
    return ok, (f"sessão até {time.strftime('%d/%m', time.localtime(info['expira']))}; " if ok else "") + saida[-200:]


def oi_na_conta(nome):
    """'responda so: oi' só nessa conta (cabeçalho x-omniroute-connection). Devolve 'ok' ou '<status> <erro>'."""
    cmd = ("cd /opt/omniroute; ID=$(sqlite3 data/storage.sqlite \"select id from provider_connections where "
           f"provider='claude-web' and name='{nome}'\"); K=$(sqlite3 data/storage.sqlite \"SELECT key FROM api_keys "
           "WHERE revoked_at IS NULL AND is_active=1 LIMIT 1\"); curl -s -m 90 -o /tmp/zs_oi.json -w '%{http_code}' "
           "http://127.0.0.1:20128/v1/chat/completions -H \"Authorization: Bearer $K\" -H 'Content-Type: application/json' "
           "-H \"x-omniroute-connection: $ID\" -d '{\"model\":\"cw/claude-sonnet-5-5\",\"stream\":false,\"messages\":"
           "[{\"role\":\"user\",\"content\":\"responda so: oi\"}]}'; echo; head -c 200 /tmp/zs_oi.json")
    linhas = mon.ssh(cmd, timeout=150).strip().splitlines()
    if not linhas:
        return "sem resposta"
    return "ok" if linhas[0] == "200" and "chatcmpl-" in " ".join(linhas[1:]) else " ".join(linhas)[:200]


def desligar(nome, motivo):
    mon.ssh("sqlite3 /opt/omniroute/data/storage.sqlite \"UPDATE provider_connections SET is_active=0 "
            f"WHERE provider='claude-web' AND name='{nome}'\"")
    dados = json.loads(BARRADAS.read_text(encoding="utf-8")) if BARRADAS.exists() else {}
    dados[nome.replace("claude-web ", "")] = {"em": time.strftime("%Y-%m-%d %H:%M"), "motivo": motivo}
    BARRADAS.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"  {nome}: DESLIGADA no OmniRoute ({motivo}); religar: UPDATE provider_connections SET is_active=1 ...")


def main(a):
    simular = "--simular" in a
    maximo = int(a[a.index("--max") + 1]) if "--max" in a else MAX_RODADA
    so = a[a.index("--so") + 1].split("@")[0] if "--so" in a else None  # testar numa conta só
    seg = json.loads(pc.SEGREDOS.read_text(encoding="utf-8")) if pc.SEGREDOS.exists() else {}
    vps = {c["nome"].replace("claude-web ", ""): c for c in mon.estado_vps()["contas"] if c["ativa"]}
    limite = time.time() + DIAS_ANTES * 86400
    alvos = []
    for perfil, c in vps.items():
        email = f"{perfil}@gmail.com"
        exp = (seg.get(email) or {}).get("expira") or 0
        ruim = (c["status"] or "") in mon.RUINS
        if so and perfil != so:
            continue
        if so or ruim or (exp and exp < limite) or email not in seg:
            motivo = "cookie ruim no OmniRoute" if ruim else ("sem cookie salvo" if email not in seg else
                                                               f"vence {time.strftime('%d/%m', time.localtime(exp))}")
            alvos.append((0 if ruim else 1, exp, email, motivo))
    alvos.sort()  # cookie ruim primeiro, depois quem vence antes
    log(f"zelador: {len(alvos)} conta(s) pra renovar (máx {maximo} por rodada)")
    falhas, barradas = [], []
    for _, exp, email, motivo in alvos[:maximo]:
        if simular:
            log(f"  simular: {email} ({motivo})")
            continue
        try:
            ok, det = renovar(email, exp)
        except Exception as e:  # noqa: BLE001
            ok, det = False, f"{type(e).__name__}: {str(e)[:150]}"
        log(f"  {email} ({motivo}): {'renovada' if ok else 'FALHOU'} — {det}")
        if not ok:
            (barradas if det.startswith("BARRADA") else falhas).append((email.split("@")[0], det))
    # 30/10: chave por conta/assunto — com a chave só do dia, a 2ª rodada (ou a barrada depois de uma falha de ssh)
    # caía como "repetido" no portão e não saía
    if barradas:
        nomes = ", ".join(p for p, _ in barradas)
        mon.enviar(f"<b>Zelador Sonnet</b>: conta(s) BARRADA(S) no claude.ai — {nomes}. Mesmo com sessão nova o "
                   "claude.ai responde 403 permission_denied; desliguei no OmniRoute (saíram do rodízio). Lista em "
                   "D:\\sonnet web\\contas_barradas.json.", "sonnet-barrada:" + nomes)
    if falhas:
        nomes = ", ".join(p for p, _ in falhas)
        mon.enviar("<b>Zelador Sonnet</b>: não renovei o cookie de "
                   + ", ".join(f"{p} ({d[:60]})" for p, d in falhas)
                   + ". O cookie velho segue no OmniRoute; tento de novo amanhã. Ver D:\\sonnet web\\zelador_sonnet.log.",
                   f"sonnet-zelador:{time.strftime('%Y-%m-%d')}:{nomes}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
