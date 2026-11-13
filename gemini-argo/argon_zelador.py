#!/usr/bin/env python3
r"""argon_zelador.py — cuida das 29 contas do Argon em SEGUNDO PLANO, para o pedido nunca pagar o Chrome (Fable 29/10,
D24 em D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md).

Medido em 29/10: 28 das 29 contas estavam com cookie morto; 106 ressincronizações pelo cofre em 2 dias, DENTRO do
pedido (mediana 78 s, p90 1 h). Agora o gemini_http tira a conta morta da fila na hora e este zelador conserta aqui.

A cada passada (tarefa ArgonZelador, 5 min):
  1. Cookies: conta não conferida há 30 min -> GET gemini.google.com/app por HTTP (1-2 s). Sem SNlM0e -> cookies mortos.
  2. Mortas: ressincroniza pelo cofre (Chrome escondido, 1 por vez, só com RAM livre >= 3 GB), até MAX_RESYNC por passada.
  3. Regra da dona (29/10): "toda vez que uma conta voltar, mandar um 'oi' individual nela, para saber exatamente quando
     volta o limite, e isso sempre tem que acontecer" -> conta com `sem_cota_ate` vencido e `confirmar_volta` recebe um
     "oi" (gemini_http.perguntar na conta fixa): Argon respondeu = voltou (hora gravada em `voltou_em`, visível no chat da
     conta); Flash-Lite = ainda sem cota, a hora exata que o Google manda entra na fila.
  4. Grava argon_zelador.json (o painel e o monitor leem) e avisa no Telegram quando uma conta volta.

    python argon_zelador.py            # uma passada
    python argon_zelador.py --status   # resumo
    python argon_zelador.py --todas    # confere os cookies de todas agora (ignora os 30 min)
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: E402,F401
except ImportError:
    pass
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\gemini-argo")
import gemini_http as gh  # noqa: E402
from gemini_argon import _ler_contas, marcar_cookies, marcar_sem_cota, _gravar_contas, _TRAVA_CONTAS, log  # noqa: E402

AQUI = Path(__file__).resolve().parent
ESTADO = AQUI / "argon_zelador.json"
MAX_RESYNC = 6          # Chromes por passada (~60-120 s cada)
CONFERIR_MIN = 30       # conferir cookies de cada conta a cada 30 min
RAM_MIN_GB = 3.0


def ram_livre_gb():
    try:
        import ctypes
        class M(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = M(); m.dwLength = ctypes.sizeof(M)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPhys / 2**30
    except Exception:  # noqa: BLE001
        return 99.0


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, origem="argon", importante=False, chave="<SEGREDO_REMOVIDO>" + texto[:50])
    except Exception:  # noqa: BLE001
        pass


def cookies_vivos(apelido):
    """True/False por HTTP (sem Chrome); None = sem arquivo."""
    try:
        s = gh._carregar_sessao(apelido)
    except gh.SemCookies:
        return None
    gh._cache_tokens.pop(apelido, None)
    try:
        gh._tokens(apelido, s)
        gh._salvar_sessao(apelido, s)
        return True
    except gh.AuthFalhou:
        return False
    except Exception as e:  # noqa: BLE001
        log.warning("zelador: %s não conferida (%s)", apelido, str(e)[:80])
        return None


def passo_cookies(todas=False):
    agora = datetime.now()
    conferidas, mortas = [], []
    for c in _ler_contas()["contas"]:
        visto = c.get("cookies_vistos_em")
        morta = c.get("cookies_mortos_ate") and agora.isoformat() < c["cookies_mortos_ate"]
        if morta and not todas:
            # 30/10: já sabida morta vai direto para a renovação; cookie preso ao Chrome não revive sozinho (antes
            # reconferia as 28 mortas por HTTP, 1 a 1, antes de renovar a 1ª)
            mortas.append(c["apelido"])
            continue
        if not todas and visto and agora - datetime.fromisoformat(visto) < timedelta(minutes=CONFERIR_MIN):
            continue
        v = cookies_vivos(c["apelido"])
        conferidas.append(c["apelido"])
        if v is True:
            marcar_cookies(c["apelido"], True)
        elif v is False:
            mortas.append(c["apelido"])
            if not morta:
                marcar_cookies(c["apelido"], False)
        time.sleep(0.5)
    return conferidas, mortas


VIDA_COOKIE_H = 1.6     # 30/10: cookie do Chrome morre ~2 h depois (290 casos: mín 1,9 h, mediana 2,1 h) -> renovar antes
VOLTA_PERTO_MIN = 30    # conta sem cota só vale renovar se a cota volta em até 30 min
URGENTE_PRONTAS = 4     # menos que isso pronta = fila quase vazia
RAM_MIN_URGENTE_GB = 1.5
ALVO_PRONTAS = int(__import__("os").environ.get("ARGON_ALVO_PRONTAS", "10"))


def _com_cota_logo(c, agora):
    ate = c.get("sem_cota_ate")
    return not ate or ate <= (agora + timedelta(minutes=VOLTA_PERTO_MIN)).isoformat()


def a_renovar(mortas):
    """30/10: ordem de renovação. 1) cookie morto em conta com cota (ou cota voltando em 30 min); 2) PREVENTIVA: conta
    com cota cujo cookie tem mais de 1,6 h (morre com ~2 h). Conta sem cota fica para perto da volta (antes renovava
    qualquer morta, inclusive sem cota, e só DEPOIS de morrer: a fila esvaziava a cada ~2 h)."""
    agora = datetime.now()
    contas = {c["apelido"]: c for c in _ler_contas()["contas"]}
    mortas_com_cota = [a for a in mortas if a in contas and _com_cota_logo(contas[a], agora)]
    # 30/10: manter ALVO_PRONTAS vivas basta (a fila usa a 1ª pronta); com a fila cheia só a preventiva das que estão
    # para morrer. Manter as 29 vivas = ~18 Chromes/h (~100 s cada) num PC já carregado; com 10 = ~6/h
    prontas = sum(1 for c in contas.values() if gh.pronta(c, agora.isoformat()))
    if prontas >= ALVO_PRONTAS:
        mortas_com_cota = []
    velhas = []
    for a, c in contas.items():
        novos = c.get("cookies_novos_em")
        if a in mortas or c.get("bloqueada") or not novos or not _com_cota_logo(c, agora):
            continue
        idade_h = (agora - datetime.fromisoformat(novos)).total_seconds() / 3600
        if idade_h >= VIDA_COOKIE_H:
            velhas.append((idade_h, a))
    velhas = [a for _, a in sorted(velhas, reverse=True)]
    if prontas >= ALVO_PRONTAS:  # só as que faltam para continuar com ALVO_PRONTAS de cookie novo
        velhas = velhas[:max(0, ALVO_PRONTAS - (prontas - len(velhas)))]
    return mortas_com_cota + velhas


def _ram_ok(urgente):
    """RAM para abrir 1 Chrome. Abaixo de 3 GB: primeiro libera (mesma limpeza que os outros projetos fazem antes de abrir
    navegador: fecha OneDrive/Teams/widgets e devolve memória parada) e confere de novo; com a fila quase vazia aceita
    1,5 GB (30/10: com 2,1 GB livres o zelador não renovava NADA e a fila caiu a 1 conta)."""
    if ram_livre_gb() >= RAM_MIN_GB:
        return True
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
        import chrome_conta
        chrome_conta._liberar_ram()
    except Exception as e:  # noqa: BLE001
        log.warning("zelador: limpeza de RAM falhou (%s)", str(e)[:80])
    livre = ram_livre_gb()
    return livre >= (RAM_MIN_URGENTE_GB if urgente else RAM_MIN_GB)


def passo_resync(mortas):
    feitas, falhas = [], []
    agora = datetime.now().isoformat()
    urgente = sum(1 for c in _ler_contas()["contas"] if gh.pronta(c, agora)) < URGENTE_PRONTAS
    for apelido in a_renovar(mortas)[:MAX_RESYNC]:
        if not _ram_ok(urgente):
            log.warning("zelador: RAM livre %.1f GB (mínimo %.1f%s) — ressincronização adiada", ram_livre_gb(),
                        RAM_MIN_URGENTE_GB if urgente else RAM_MIN_GB, ", fila quase vazia" if urgente else "")
            break
        t = time.time()
        try:
            ok = gh.ressincronizar(apelido)
        except Exception as e:  # noqa: BLE001
            ok = False
            log.warning("zelador: %s ressincronização falhou (%s)", apelido, str(e)[:100])
        (feitas if ok else falhas).append(apelido)
        log.info("zelador: %s cookies %s em %.0f s", apelido, "renovados" if ok else "NÃO renovados (deslogada no cofre?)", time.time() - t)
        time.sleep(2)
    return feitas, falhas


OI_PARALELO = 4  # 30/10: os "oi" eram 1 por vez; com 15 contas aguardando e o Argon no Alto a passada passou de 26 min


def passo_oi():
    """Conta com a cota 'de volta' recebe um 'oi' individual; só então entra na fila como confirmada."""
    from concurrent.futures import ThreadPoolExecutor
    agora = datetime.now().isoformat()
    alvos = [c["apelido"] for c in _ler_contas()["contas"] if c.get("confirmar_volta")
             and not (c.get("sem_cota_ate") and agora < c["sem_cota_ate"])
             and not (c.get("cookies_mortos_ate") and agora < c["cookies_mortos_ate"])]
    voltaram, ainda_nao = [], []
    with ThreadPoolExecutor(max_workers=OI_PARALELO) as ex:
        for apelido, ok in zip(alvos, ex.map(_oi, alvos)):
            (voltaram if ok else ainda_nao).append(apelido)
    return voltaram, ainda_nao


def _oi(apelido):
    """True = o Argon respondeu (cota voltou, gravado em voltou_em); False = ainda sem cota ou erro."""
    t = time.time()
    try:
        r = gh.perguntar("oi", conta=apelido, modelo="argon", tentativas=1)
    except Exception as e:  # noqa: BLE001
        r = None
        log.warning("zelador: oi em %s falhou (%s)", apelido, str(e)[:100])
    if not r:
        return False  # perguntar já marcou sem_cota com a hora exata (SemCota) ou o erro
    with _TRAVA_CONTAS:
        d = _ler_contas()
        for x in d["contas"]:
            if x["apelido"] == apelido:
                x.pop("confirmar_volta", None)
                x["voltou_em"] = datetime.now().isoformat(timespec="minutes")
        _gravar_contas(d)
    log.info("zelador: conta %s VOLTOU às %s (confirmado com 'oi', %.0f s)", apelido, datetime.now().strftime("%H:%M"), time.time() - t)
    return True


def resumo():
    agora = datetime.now().isoformat()
    cs = _ler_contas()["contas"]
    return {"contas": len(cs), "prontas": sum(1 for c in cs if gh.pronta(c, agora)),
            "cookies_mortos": sum(1 for c in cs if c.get("cookies_mortos_ate") and agora < c["cookies_mortos_ate"]),
            "sem_cota": sum(1 for c in cs if c.get("sem_cota_ate") and agora < c["sem_cota_ate"]),
            "bloqueadas": sum(1 for c in cs if c.get("bloqueada")),
            "aguardando_oi": sum(1 for c in cs if c.get("confirmar_volta")),
            "proxima_volta": min((c["sem_cota_ate"] for c in cs if c.get("sem_cota_ate") and c["sem_cota_ate"] > agora), default=None),
            "ultimas_voltas": sorted(((c.get("voltou_em"), c["apelido"]) for c in cs if c.get("voltou_em")), reverse=True)[:8]}


_TRAVA_ARQ = None


def _um_so():
    """30/10: 1 zelador por vez no PC. O "não iniciar outra" do Agendador só vale para as instâncias dele: um zelador
    rodado à mão e o agendado chegaram a renovar as mesmas contas ao mesmo tempo (2 Chromes no mesmo perfil)."""
    global _TRAVA_ARQ
    import msvcrt
    _TRAVA_ARQ = open(AQUI / "argon_zelador.lock", "a+")
    try:
        msvcrt.locking(_TRAVA_ARQ.fileno(), msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False


def main(a):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--status" in a:
        print(json.dumps(resumo(), ensure_ascii=False, indent=1))
        return 0
    if not _um_so():
        print("outro zelador já está rodando; saio")
        return 0
    t0 = time.time()
    conferidas, mortas = passo_cookies(todas="--todas" in a)
    feitas, falhas = passo_resync(mortas)
    voltaram, ainda_nao = passo_oi()
    r = resumo()
    r.update({"em": datetime.now().isoformat(timespec="seconds"), "duracao_s": round(time.time() - t0),
              "conferidas": len(conferidas), "mortas_vistas": mortas, "renovadas": feitas, "falhas_renovar": falhas,
              "voltaram": voltaram, "oi_sem_cota": ainda_nao})
    ESTADO.write_text(json.dumps(r, ensure_ascii=False, indent=1), "utf-8")
    print(json.dumps({k: r[k] for k in ("prontas", "cookies_mortos", "sem_cota", "renovadas", "falhas_renovar", "voltaram", "duracao_s")}, ensure_ascii=False))
    for ap in voltaram:
        _avisar(f"🟢 Argon: a conta {ap} voltou às {datetime.now():%H:%M} (confirmado com 'oi')")
    if falhas:
        _avisar("🔴 Argon: contas deslogadas no cofre (cookies não renovam): " + ", ".join(falhas))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
