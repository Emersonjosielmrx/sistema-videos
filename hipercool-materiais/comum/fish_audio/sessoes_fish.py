"""sessoes_fish.py — sessão (token Bearer + workspace) de cada conta do Fish, guardada para o que NÃO precisa de Chrome.

Por quê (dona 18/11: "abrir o navegador só pra ver os créditos não é benéfico"): o Bearer do Fish é o
localStorage.token da página logada e vale por si — com ele, saldo (GET /wallet/<ws>/package), conferir login
(GET /user/self) e histórico saem por HTTP puro, cada conta pela ponte do IP fixo dela. O Chrome só é preciso para o
reCAPTCHA da geração (fabrica_fish.py), e é a própria fábrica que grava a sessão aqui toda vez que abre uma conta.

    sessoes.json: {email: {"token", "workspace", "gravado_em", "ok_em", "morta": bool}}

    python sessoes_fish.py                  # lista as sessões guardadas
    python sessoes_fish.py saldo <email>    # saldo de UMA conta, sem Chrome (pela saída dela)
    python sessoes_fish.py logada <email>   # confere o login SEM Chrome (GET /user/self)
    python sessoes_fish.py vida             # quanto cada token durou (sessoes_vida.jsonl)
    python sessoes_fish.py registrar <email>  # depois do login à mão: põe a conta no rodízio (sessão + saldo)

Regra do IP (CLAUDE.md): cada consulta sai pela ponte rnprmtfo-N da PRÓPRIA conta (fish_audio._subir_ponte); nunca
duas contas pelo mesmo IP. Proibido laço "consultar todas": o saldo de cada conta é lido só quando ela vai ser usada
(escolher conta) ou logo depois de gerar com ela — o creditos.json guarda o resto.
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
ARQ = AQUI / "sessoes.json"
API = "https://api.fish.audio"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/156.0.0.0 Safari/537.36")
_trava = threading.Lock()


class SessaoMorta(RuntimeError):
    """Token recusado (401/403): a conta precisa ser aberta de novo pela fábrica (ou relogada)."""


def carregar():
    try:
        return json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _salvar(d):
    tmp = ARQ.with_name(f"sessoes.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    for i in range(20):
        try:
            tmp.replace(ARQ)
            return
        except PermissionError:
            time.sleep(0.05 * (i + 1))


def gravar(email, token, workspace):
    """Guarda a sessão. Mesmo token de antes = só confirma que está viva (não zera a data de nascimento: é ela que
    mede quanto o token do Fish dura). Token novo = nasce agora."""
    agora = time.strftime("%Y-%m-%dT%H:%M")
    with _trava:
        d = carregar()
        velho = d.get(email.lower()) or {}
        nasceu = velho.get("nasceu_em") if velho.get("token") == token else agora
        if velho.get("token") and velho.get("token") != token:  # trocou: registra quanto o anterior durou
            _registrar_vida(email, velho, "trocado pela página")
        d[email.lower()] = {"token": token, "workspace": workspace, "nasceu_em": nasceu or agora,
                            "gravado_em": agora, "ok_em": agora, "morta": False}
        _salvar(d)


VIDA = AQUI / "sessoes_vida.jsonl"  # quanto cada token do Fish durou (para saber de quanto em quanto tempo morre)


def _registrar_vida(email, s_, motivo):
    try:
        from datetime import datetime
        ini = datetime.fromisoformat(s_.get("nasceu_em") or s_.get("gravado_em"))
        horas = round((datetime.now() - ini).total_seconds() / 3600, 1)
        with VIDA.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"email": email.lower(), "nasceu_em": s_.get("nasceu_em"), "fim": time.strftime(
                "%Y-%m-%dT%H:%M"), "ultimo_ok": s_.get("ok_em"), "horas": horas, "motivo": motivo},
                ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — medição, não requisito
        pass


def vida():
    """Resumo das vidas medidas: [(email, horas, motivo)]."""
    try:
        return [json.loads(l) for l in VIDA.read_text("utf-8").splitlines() if l.strip()]
    except OSError:
        return []


def marcar(email, **campos):
    with _trava:
        d = carregar()
        if email.lower() in d:
            d[email.lower()].update(campos)
            _salvar(d)


def sessao_http(email):
    """requests.Session da conta: Bearer guardado + proxy da ponte do IP DELA. None se não há sessão guardada."""
    import fish_audio as fa
    s_ = carregar().get(email.lower())
    if not s_ or s_.get("morta") or not s_.get("token"):
        return None, None
    _, n = fa.checar_conta(email)           # recusa Kaggle / fora do pool
    porta = fa._subir_ponte(n)
    s = requests.Session()
    s.proxies = {"http": f"http://127.0.0.1:{porta}", "https": f"http://127.0.0.1:{porta}"}
    s.headers.update({"Authorization": f"Bearer {s_['token']}", "Origin": "https://fish.audio",
                      "Referer": "https://fish.audio/", "User-Agent": UA})
    return s, s_.get("workspace")


def saldo(email):
    """(restantes, total) por HTTP, sem Chrome; grava no creditos.json. None = sem sessão guardada.
    Token recusado = marca a sessão como morta e levanta SessaoMorta."""
    import creditos
    s, ws = sessao_http(email)
    if s is None or not ws:
        return None
    try:
        r = s.get(f"{API}/wallet/{ws}/package", timeout=30)
    finally:
        s.close()
    if r.status_code in (401, 403):
        morrer(email, f"recusado no saldo ({r.status_code})")
        creditos.marcar(email.lower(), logado=False, erro=f"sessão recusada ({r.status_code})")
        raise SessaoMorta(f"{email}: token do Fish recusado ({r.status_code})")
    if r.status_code != 200:
        return None
    d = r.json()
    rest, tot = d.get("balance"), d.get("total")
    creditos.marcar(email.lower(), restantes=rest, total=tot, logado=True, erro=None, gasto_desde_leitura=0,
                    lido_em=time.strftime("%Y-%m-%dT%H:%M"))
    marcar(email, ok_em=time.strftime("%Y-%m-%dT%H:%M"))
    return rest, tot


def morrer(email, motivo):
    """Token recusado: marca como morto e registra quanto ele viveu (sessoes_vida.jsonl)."""
    s_ = carregar().get(email.lower())
    if s_ and not s_.get("morta"):
        _registrar_vida(email, s_, motivo)
    marcar(email, morta=True, morreu_em=time.strftime("%Y-%m-%dT%H:%M"))


def logada(email):
    """Conferir login SEM Chrome: GET /user/self com o token guardado, pela saída da conta.
    True = logada; False = token recusado (sessão morta); None = sem sessão guardada / não deu para saber."""
    s, _ = sessao_http(email)
    if s is None:
        return None
    try:
        r = s.get(f"{API}/user/self", timeout=30)
    except requests.RequestException:
        return None
    finally:
        s.close()
    if r.status_code in (401, 403):
        morrer(email, f"recusado no user/self ({r.status_code})")
        return False
    if r.status_code == 200 and r.json().get("email", "").lower() == email.lower():
        marcar(email, ok_em=time.strftime("%Y-%m-%dT%H:%M"))
        return True
    return None


def do_historico(email, voz, texto):
    """Fala IGUAL (mesma voz e texto, velocidade normal) que esta conta já gerou no Fish: devolve o link do MP3 (o
    CDN baixa sem login) ou None. Serve para não pagar de novo uma fala que já foi gerada — por exemplo quando o
    cache local foi limpo ou a fala saiu por outra máquina/chat com esta conta. Só a 1ª página (20 últimas)."""
    s, _ = sessao_http(email)
    if s is None:
        return None
    try:
        r = s.get(f"{API}/task", params={"state": "finished", "type": "tts", "page_size": 20, "page_number": 1},
                  timeout=30)
        if r.status_code != 200:
            return None
        for it in r.json().get("items", []):
            p = it.get("parameters") or {}
            if (p.get("text") == texto and p.get("model_id") == voz and not p.get("prosody")
                    and not it.get("generate_error") and str(it.get("result", "")).startswith("https://")):
                return it["result"]
    except (requests.RequestException, ValueError):
        return None
    finally:
        s.close()
    return None


def registrar_conta(email):
    """Depois do login à mão de UMA conta (login_fish.py): abre ela na fábrica (grava o token aqui) e lê o saldo por
    HTTP, para ela entrar no creditos.json e no rodízio. Uma conta por chamada — nunca em laço sobre o pool."""
    import fish_http as fh
    f = fh.FishHTTP(email)          # a fábrica abre a conta pelo IP dela e grava a sessão em sessoes.json
    try:
        r = saldo(email)
    finally:
        f.fechar()
    return r


def saldo_em_fundo(email):
    """Lê o saldo numa linha de fundo (quem chama não espera: a montagem do vídeo segue)."""
    def rodar():
        try:
            saldo(email)
        except Exception:  # noqa: BLE001 — informação, não requisito
            pass
    t = threading.Thread(target=rodar, daemon=True, name=f"saldo-{email}")
    t.start()
    return t


if __name__ == "__main__":
    if sys.argv[1:2] == ["saldo"]:
        print(saldo(sys.argv[2]))
    elif sys.argv[1:2] == ["logada"]:
        print(logada(sys.argv[2]))
    elif sys.argv[1:2] == ["registrar"]:
        print(registrar_conta(sys.argv[2]))
    elif sys.argv[1:2] == ["vida"]:
        vs = vida()
        for v in vs:
            print(f"{v['email']:40s} durou {v['horas']:>6} h  ({v['motivo']}; nasceu {v['nasceu_em']})")
        print(f"{len(vs)} token(s) medidos" + (f"; menor vida {min(v['horas'] for v in vs)} h" if vs else
                                                " — nenhum morreu ainda"))
    else:
        for e, s_ in carregar().items():
            print(f"{e:40s} {'MORTA' if s_.get('morta') else 'ok':6s} nasceu {s_.get('nasceu_em') or s_.get('gravado_em')} "
                  f"último ok {s_.get('ok_em')}")
