# -*- coding: utf-8 -*-
r"""criar_contas.py — cria as contas do 1min.ai para o pool de contas Google do cofre e guarda a API key de cada uma.

Cada conta nova do 1min ganha ~265.000 créditos de cadastro (+15.000/dia de visita). O 1min loga com Google, e o
"Log in with Google" CRIA a conta automaticamente (auto-signup) na 1ª vez. Depois de logado, a chave é criada e lida
100% pela API do próprio app (header X-Auth-Token: Bearer <JWT>), sem depender de cliques frágeis — só o login do
Google usa clique. Validado ponta a ponta em 31/10/2026 (conta conta_exemplo: logou, 265k, chave criada e lida).

Fluxo por conta: cofre.abrir -> app.1min.ai -> (se não logado) Log In > Log in with Google > escolhe a conta >
Continuar (consentimento, só na 1ª vez) -> js/apikey.js garante 1 chave ACTIVE (criada/lida pela API do app) ->
visita /free-credits (15k/dia) -> registra a chave no cofre do rodízio via `umin.py add <email> <chave>`
(umin_contas.json, base 265.000) -> fecha o Chrome (grava cookies). O rodízio e o seletor "1min-opus-5-5" herdam.

Resumível e idempotente: pula conta que já tem chave salva (use --refazer para forçar) e pula conta com login do
Google morto no cofre. Uma conta por vez (fecha cada Chrome). Login do Google pode falhar (Google recusa clique
automatizado às vezes): a conta fica marcada "falha_login" e o lote segue; essas você faz pela fila de login.

  python criar_contas.py                 # todas as contas do pool (contas_genspark.json) que ainda faltam
  python criar_contas.py a@x.com b@y.com # só essas contas
  python criar_contas.py --refazer [...] # refaz mesmo as que já têm chave
  python criar_contas.py status          # mostra o progresso (quantas feitas, faltam, falharam)
"""
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

AQUI = Path(__file__).resolve().parent
CONTAS_UMIN = AQUI / "umin_contas.json"                   # cofre do rodízio (umin.py); é AQUI que a chave é guardada
FALHAS = AQUI / "criar_contas_estado.json"                # contas que falharam (ex.: login manual) p/ o status
GENSPARK = AQUI.parent / "contas_genspark.json"           # fonte dos e-mails do pool
LOG = AQUI / "criar_contas.jsonl"                          # uma linha por tentativa
URL = "https://app.1min.ai"
URL_CREDITOS = "https://app.1min.ai/free-credits"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
SEM_JANELA = 0x08000000 if os.name == "nt" else 0
PAUSA_ENTRE = 6          # segundos entre contas
USAR_PROXY = False       # --proxy: manda SÓ o 1min por um IP da Webshare (contorna o IP_LOCKED); Google sai de casa
# coordenadas na janela do cofre (1280x900, viewport ~1280x721): botão "Log In" do topo e "Log in with Google" do modal
XY_LOGIN = ("1127", "32")
XY_GOOGLE = ("639", "224")


def cdp(porta, *args, timeout=200):
    r = subprocess.run([NODE, str(AQUI / "cdp.mjs"), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, cwd=AQUI, creationflags=SEM_JANELA,
                       env={**os.environ, "CDP_PORTA": str(porta)})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _ultima_linha_json(saida):
    for ln in reversed(saida.strip().splitlines()):
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                return json.loads(ln)
            except ValueError:
                continue
    return None


def estado_login(porta):
    _, out = cdp(porta, "jsf", str(AQUI / "js" / "login.js"))
    return _ultima_linha_json(out) or {"logado": False, "erro": out[-200:]}


def logar(porta, email):
    """Garante login no 1min. Faz Log In > Log in with Google > escolhe a conta > Continuar (consentimento).
    Devolve True se logou. Não quebra se um passo falhar (ex.: sem consentimento em login repetido)."""
    cdp(porta, "ir", URL, "9")
    if estado_login(porta).get("logado"):
        return True
    cdp(porta, "clicarxy", "552", "27", "2")               # fecha o tour "Workspace Management" (backdrop bloqueia o modal); se não houver, clica área vazia
    cdp(porta, "clicarxy", *XY_LOGIN, "4")                 # abre o modal de login (botão do topo)
    _, out = cdp(porta, "clicar", "Log in with Google", "6")
    if "ERRO" in out:                                      # o texto pode não pegar enquanto o modal anima: usa a posição
        cdp(porta, "clicarxy", *XY_GOOGLE, "6")
    cod, _ = cdp(porta, "usar", "accounts.google.com")     # passa a comandar o popup do Google
    if cod != 0:
        return False                                       # o popup nem abriu (Google recusou): login manual
    cdp(porta, "clicar", email, "6")                       # escolhe a conta no chooser
    cdp(porta, "clicar", "Continuar", "6")                 # consentimento (só na 1ª vez; se não houver, erra e segue)
    cdp(porta, "voltar")                                   # volta à nossa janela (o popup já fechou)
    cdp(porta, "ir", URL, "9")
    return bool(estado_login(porta).get("logado"))


def garantir_chave(porta):
    cdp(porta, "ir", URL, "8")   # garante o contexto app.1min.ai antes de ler o indexedDB (senão "IDB denied")
    _, out = cdp(porta, "jsf", str(AQUI / "js" / "apikey.js"), timeout=120)
    return _ultima_linha_json(out) or {"ok": False, "erro": out[-200:]}


def _ler(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"contas": {}}


def _gravar(p, dados):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def _registrar_log(**campos):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), **campos}, ensure_ascii=False) + "\n")


def chaves_salvas():
    """E-mails que já têm chave no cofre do rodízio (umin_contas.json)."""
    d = _ler(CONTAS_UMIN)
    return {c.get("email") or c.get("apelido"): c for c in d.get("contas", []) if c.get("chave")}


def salvar(email, info):
    """Registra a conta no cofre do rodízio do umin.py (umin.py add <email> <chave>). O umin.py é a fonte única
    da chave e do saldo; o rodízio e o seletor '1min-opus-5-5' herdam de graça. base = 265.000 (default do add)."""
    r = subprocess.run([sys.executable, str(AQUI / "umin.py"), "add", email, info["key"]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=AQUI, timeout=60)
    ok = r.returncode == 0
    # tira a conta da lista de falhas, se estava lá
    f = _ler(FALHAS)
    if email in f.get("contas", {}):
        f["contas"].pop(email, None)
        _gravar(FALHAS, f)
    return ok, (r.stdout or "") + (r.stderr or "")


def marcar_falha(email, motivo):
    f = _ler(FALHAS)
    f.setdefault("_leia", "Contas do pool que ainda NÃO viraram chave no 1min (login manual etc.). umin/criar_contas.py.")
    f.setdefault("contas", {})
    f["contas"][email] = {"status": motivo, "em": datetime.now().isoformat(timespec="seconds")}
    _gravar(FALHAS, f)


def emails_do_pool():
    d = _ler(GENSPARK)
    contas = d.get("contas", [])
    return [c["email"] for c in contas if c.get("email")]


def estado_cofre(email):
    """Devolve ('vivo'|'morto'|'?'|'nao-cofre')."""
    try:
        _, e = cofre.conta(email)
    except KeyError:
        return "nao-cofre"
    return (e.get("google") or (e.get("servicos") or {}).get("google") or "?")


def uma_conta(email, refazer=False):
    if not refazer and email in chaves_salvas():
        return {"email": email, "pulou": "ja-tem-chave"}
    ec = estado_cofre(email)
    if ec in ("morto", "nao-cofre"):
        marcar_falha(email, f"login-google-{ec}")
        return {"email": email, "pulou": f"cofre-{ec}"}
    res = {"email": email}
    extra = ()
    if USAR_PROXY:
        import proxy_umin
        n = proxy_umin.escolher_ip(email)
        if n is None:
            res["erro"] = "proxy Webshare sem túnel até o 1min agora (não abro pelo IP de casa bloqueado)"
            return res
        extra = proxy_umin.flags(n)
        res["proxy_ip"] = n
    porta, proc = cofre.abrir(email, extra=extra)
    res["chrome"] = "aberto" if proc else "ja-estava-aberto"
    if USAR_PROXY and not proc:
        res["erro"] = "Chrome do cofre já estava aberto SEM o proxy (sairia pelo IP bloqueado); feche e refaça"
        return res
    try:
        if not logar(porta, email):
            marcar_falha(email, "falha_login")
            res["erro"] = "nao-logou (login manual)"
            return res
        info = garantir_chave(porta)
        if not info.get("ok"):
            marcar_falha(email, "falha_chave")
            res["erro"] = "chave: " + str(info.get("erro"))[:150]
            return res
        cdp(porta, "ir", URL_CREDITOS, "9")                # resgata a visita diária (15k)
        ok_add, saida_add = salvar(email, info)
        res.update(ok=True, criou=info.get("criou"), add_ok=ok_add, add=saida_add.strip()[-120:],
                   key_prefixo=info["key"][:6] + "…" + info["key"][-3:])
        return res
    finally:
        cdp(porta, "fechar")
        if proc:                                           # fomos nós que abrimos: fecha gravando cookies
            cdp(porta, "encerrar")
            try:
                cofre.fechar(proc, nome=email)
            except Exception:  # noqa: BLE001
                pass


def mostrar_status():
    salvas = chaves_salvas()
    falhas = _ler(FALHAS).get("contas", {})
    pool = emails_do_pool()
    com_chave = [e for e in pool if e in salvas]
    # contas com chave que não estão no pool do genspark (ex.: só no 1min) também contam
    extra = [e for e in salvas if e not in pool]
    print(f"pool: {len(pool)} contas | com chave: {len(com_chave)} (+{len(extra)} fora do pool) | faltam: {len(pool) - len(com_chave)}")
    for e in com_chave + extra:
        print(f"  ok    {e}  saldo={salvas[e].get('base', 0) - salvas[e].get('usado', 0):,}")
    for e in pool:
        if e not in salvas and e in falhas:
            print(f"  FALHA {e}  ({falhas[e].get('status')})")
    for e in pool:
        if e not in salvas and e not in falhas:
            print(f"  -     {e}  (ainda não processada)")


GUARDA_THROTTLE = 5   # se as primeiras N contas falharem no login SEM nenhum sucesso, o Google está barrando: para o run


def _uma_passada(alvos, refazer, etiqueta):
    """Processa a lista uma vez. Devolve (feitas, falhas, puladas, ainda_faltam, throttle)."""
    feitas = falhas = puladas = 0
    seguidas_falha = 0
    throttle = False
    for i, email in enumerate(alvos, 1):
        try:
            r = uma_conta(email, refazer=refazer)
        except Exception as e:  # noqa: BLE001
            r = {"email": email, "erro": f"{type(e).__name__}: {e}", "trace": traceback.format_exc().splitlines()[-2:]}
            marcar_falha(email, "excecao")
        _registrar_log(rodada=etiqueta, **r)
        if r.get("ok"):
            feitas += 1
            seguidas_falha = 0
            print(f"{etiqueta} [{i}/{len(alvos)}] OK    {email}  chave={r.get('key_prefixo')} criou={r.get('criou')} add_ok={r.get('add_ok')}")
        elif r.get("pulou"):
            puladas += 1
            print(f"{etiqueta} [{i}/{len(alvos)}] pulou {email}  ({r['pulou']})")
        else:
            falhas += 1
            if "login" in str(r.get("erro", "")):
                seguidas_falha += 1
            print(f"{etiqueta} [{i}/{len(alvos)}] FALHA {email}  {r.get('erro')}")
        # throttle: muitas falhas de login seguidas e ninguém entrou ainda → Google barrando, para (sem ficar martelando)
        if feitas == 0 and seguidas_falha >= GUARDA_THROTTLE:
            print(f"   ⚠ {seguidas_falha} falhas de login seguidas sem nenhum sucesso: Google barrando. Paro este run.")
            throttle = True
            break
        time.sleep(PAUSA_ENTRE)
    faltam = [e for e in alvos if e not in chaves_salvas()]
    return feitas, falhas, puladas, faltam, throttle


def main(a):
    global USAR_PROXY
    refazer = "--refazer" in a
    a = [x for x in a if x != "--refazer"]
    if "--proxy" in a:
        USAR_PROXY = True
        a = [x for x in a if x != "--proxy"]
        print("PROXY LIGADO: o tráfego do 1min sai por um IP da Webshare (Google continua saindo de casa).")
    rodadas = 6
    if "--rodadas" in a:
        j = a.index("--rodadas")
        rodadas = int(a[j + 1]); del a[j:j + 2]
    if a and a[0] == "status":
        mostrar_status()
        return
    alvos = a or emails_do_pool()
    # 1ª passada em todas; depois repete só as que ainda faltam, parando quando uma rodada não cria nenhuma nova
    print(f"{len(alvos)} conta(s) · até {rodadas} rodadas (repete as que falharem no fim) · refazer={refazer}")
    total_feitas = 0
    pendentes = alvos
    for rodada in range(1, rodadas + 1):
        if not pendentes:
            break
        print(f"\n=== RODADA {rodada} · {len(pendentes)} conta(s) ===")
        feitas, falhas, puladas, pendentes, throttle = _uma_passada(pendentes, refazer, f"R{rodada}")
        total_feitas += feitas
        print(f"--- rodada {rodada}: {feitas} criadas, {falhas} falharam, {puladas} puladas; faltam {len(pendentes)}")
        if throttle:
            print("   Google barrando agora. Rode de novo mais tarde: python criar_contas.py (pula as prontas).")
            break
        if feitas == 0:   # ninguém novo entrou nesta rodada: não adianta insistir mais agora
            print("   (nenhuma nova nesta rodada — paro as repetições)")
            break
    print(f"\nFIM: {total_feitas} criadas no total; faltam {len(pendentes)}. "
          f"Repetir depois: python criar_contas.py (pula as prontas). Status: python criar_contas.py status")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
