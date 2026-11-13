r"""instagram_criar.py — cria uma conta NOVA do Instagram neste PC, já logada no Chrome do cofre, usando o e-mail de
uma conta Google que já está logada no cofre (D:\logins-google\cofre). Feito em 24/10/2026 pra MS Energy
(@msenergysolar.pa, e-mail msenergypara@gmail.com).

COMO USAR
    $env:IG_SENHA = '<SEGREDO_REMOVIDO>'      # a senha só entra pela variável (nunca em arquivo/log)
    python bin\instagram_criar.py --email msenergypara@gmail.com --nome "MS Energy | Energia Solar" ^
        --arrobas msenergy.solar msenergysolar.pa msenergy.para --cofre ig_msenergy_novo

    --email   conta Google do cofre com "google": "vivo" (lista: cd D:\logins-google; python cofre.py listar)
    --nome    nome que aparece no perfil
    --arrobas @ em ordem de preferência; usa o primeiro livre
    --cofre   nome do perfil do Chrome no cofre onde a conta fica logada (padrão ig_<1º @>)

COMO FUNCIONA (fluxo do Instagram em 24/10 — página única de cadastro)
 1. Abre instagram.com/accounts/emailsignup/ no Chrome do cofre (--cofre), NA TELA.
 2. Preenche e-mail, senha e nome; testa os @ um a um (o Instagram marca "não está disponível").
 3. Data de nascimento: são listas personalizadas (não <select>) — clica em Dia/Mês/Ano e escolhe 15/junho/1995.
 4. Clica "Enviar" -> tela "Insira o código de confirmação ... enviamos para <e-mail inteiro>".
 5. Abre o Gmail desse e-mail (perfil Google do cofre, fica aberto), pega o código de 6 dígitos do e-mail mais novo
    do Instagram e digita (instagram_local._resolver_codigo).
 6. Confere pelo próprio Instagram (API web_form_data) que a sessão é do @ novo e grava em
    config\instagram_local.json (resultado, e-mail, cofre).

ARMADILHAS
 - O código TEM que ser digitado na mesma janela do cadastro: fechou antes = o cadastro não existe (login dá "senha
   incorreta") e é preciso refazer tudo.
 - Captcha/celular/selfie na criação: quem resolve é a dona na janela.
 - Conta nova pra substituir conta SUSPENSA é evasão — não usar pra isso (só conta nova de verdade).
 - Depois de criada, ela NÃO posta sozinha: ligar no reuso_plataformas.json ("instagram" -> "contas") com
   "cofre": "<--cofre>" quando a dona decidir.
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_local as m  # noqa: E402

OCUPADO = r"não está disponível|isn't available|já está em uso|another account is using"


_ORDEM_META = {"emailOrPhone": 0, "password": 1, "fullName": 2}  # posição entre os inputs de texto/senha


def _campo(pg, nome, rotulo):
    """11/11: o cadastro virou "Conta Meta" — inputs SEM name; só o usuário tem aria-label ("Nome de usuário",
    type=search). get_by_label caía em outro elemento e o type() estourava 30 s. Ordem: name (formulário antigo) →
    aria-label → placeholder → posição no formulário novo (e-mail, senha, nome)."""
    c = pg.locator(f"input[name={nome}]")
    if c.count():
        return c.first
    rx = re.compile(rotulo, re.I)
    for loc in (pg.get_by_role("searchbox", name=rx), pg.get_by_role("textbox", name=rx), pg.get_by_placeholder(rx)):
        if loc.count():
            return loc.first
    if nome in _ORDEM_META:
        return pg.locator("input[type=text], input[type=password], input[type=email]").nth(_ORDEM_META[nome])
    return pg.get_by_label(rx).first


def _nascimento(pg):
    for rotulo, valor in (("Dia", "15"), ("Mês", re.compile(r"^\s*junho\s*$", re.I)), ("Ano", "1995")):
        caixa = pg.get_by_role("combobox", name=re.compile(rotulo, re.I))
        if not caixa.count():
            caixa = pg.get_by_text(rotulo, exact=True)
        caixa.first.click()
        pg.wait_for_timeout(1200)
        op = pg.get_by_role("option", name=valor)
        if not op.count():
            op = pg.get_by_text(valor, exact=True) if isinstance(valor, str) else pg.get_by_text(valor)
        op.last.scroll_into_view_if_needed(timeout=10000)
        op.last.click()
        pg.wait_for_timeout(1000)


def criar(email, nome, arrobas, chave):
    import cofre
    from playwright.sync_api import sync_playwright
    senha = os.environ["IG_SENHA"]
    try:
        cofre.conta(chave)
    except KeyError:
        cofre.registrar(chave, usos={"instagram": arrobas[0]}, tipo="instagram")
    # 11/11 (dona: "Instagram usa os proxies grátis"; o Instagram parou de mandar o código do cadastro pela internet de
    # casa — en1653964: Gmail logado, 0 e-mail do Instagram): a conta NASCE no IP fixo grátis dela (mesmo mapa do
    # TikTok, chave ig:<chave>); só os domínios do Instagram/Meta vão pelo proxy, o Gmail segue por casa.
    # IG_CRIAR_PROXY=0 volta a criar pela casa.
    extra = []
    if os.environ.get("IG_CRIAR_PROXY", "1") != "0":
        import proxy_tiktok
        n = proxy_tiktok.ip_da_conta(f"ig:{chave}")
        if proxy_tiktok.garantir() and proxy_tiktok.pronto(n):
            extra = proxy_tiktok.flags(n, "instagram")
            print(f"cadastro pelo IP grátis {n}", flush=True)
        else:
            raise RuntimeError(f"proxy grátis {n} fora — não crio pela internet de casa")
    porta, proc = cofre.abrir(chave, "about:blank", visivel=True, extra=extra)
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        try:
            pg = br.contexts[0].new_page()
            pg.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="domcontentloaded", timeout=90000)
            pg.wait_for_timeout(6000)
            m._clicar(pg, m.COOKIES)
            _campo(pg, "emailOrPhone", r"celular|email").fill(email)
            _campo(pg, "password", r"senha|password").fill(senha)
            _campo(pg, "fullName", r"nome completo|full name").fill(nome)
            escolhido = None
            for a in arrobas:
                try:
                    u = _campo(pg, "username", r"nome de usuário|username")
                    u.wait_for(timeout=30000)
                except Exception:  # 01/11: 3 falhas seguidas aqui sem print — guarda a tela pra ver o que mudou
                    m._print(pg, chave, "erro_sem_campo_usuario")
                    raise
                u.fill("")
                u.type(a, delay=60)
                pg.keyboard.press("Tab")
                pg.wait_for_timeout(4000)
                if not re.search(OCUPADO, m._texto(pg), re.I):
                    escolhido = a
                    break
                print(f"@{a} ocupado", flush=True)
            if not escolhido:
                return None, "todos os @ ocupados"
            print(f"@{escolhido} livre", flush=True)
            _nascimento(pg)
            m._print(pg, chave, "criar_1_preenchido")
            if not m._clicar(pg, ("Enviar", "Submit", "Cadastre-se", "Sign up", "Avançar", "Next")):
                pg.keyboard.press("Enter")
            pg.wait_for_timeout(8000)
            m._print(pg, chave, "criar_2_codigo")
            if m._campo_codigo(pg) and not m._resolver_codigo(p, pg, chave):
                print("código não chegou/no Gmail — a janela fica até 5 min pra dona digitar", flush=True)
                fim = time.time() + 300
                while time.time() < fim and not m._usuario_logado(pg):
                    pg.wait_for_timeout(5000)
            pg.wait_for_timeout(10000)
            m._clicar(pg, m.DEPOIS)
            pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=90000)
            pg.wait_for_timeout(6000)
            m._print(pg, chave, "criar_3_final")
            return escolhido, m._usuario_logado(pg)
        finally:
            m._fechar_gmails()
            cofre.fechar(proc, br, chave)


FILA = m.ROOT / "config" / "instagram_criar_fila.json"
LOG = m.ROOT / "logs" / "instagram_criar.log"


def _log(t):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {t}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _limpo(s):
    return re.sub(r"[^a-z0-9._]", "", s.lower()).strip("._")[:30]


PRODUTOS = m.Path(r"D:\veo\beta\pos_producao\assets\produtos.json")
MARCAS = m.ROOT / "config" / "marcas_instagram.json"


GRUPOS = m.ROOT / "config" / "instagram_produtos.json"


def _produtos_sem_conta():
    """Grupos de produtos (config\\instagram_produtos.json, dona 24/10) que ainda não têm Instagram próprio
    (marcas_instagram.json), na ordem do arquivo."""
    tem = {(v or {}).get("produto") for v in (m._ler(MARCAS).get("contas") or {}).values()}
    feitos = {(v or {}).get("produto") for v in m._ler(FILA).values() if (v or {}).get("logado")}
    return [g for g in (m._ler(GRUPOS).get("grupos") or []) if g["produto"] not in tem | feitos]


def fila():
    """Dona 24/10: PRIMEIRO um Instagram por produto (Hermes Call, Agente IA... de produtos.json) que ainda não tem conta,
    usando o e-mail de um TikTok sem conteúdo próprio ("Veo de reserva"/"a pedido"); depois um por TikTok (mesmo
    e-mail, nome/@ do TikTok). Pula e-mail que já tem Instagram e conta sem Google vivo no cofre."""
    out = _fila_tiktok()
    livres = [c for c in out if re.search(r"Veo de reserva|a pedido", c.pop("_obs", ""), re.I)]
    prod = []
    for p in _produtos_sem_conta():
        if not livres:
            break
        c = livres.pop(0)
        out.remove(c)
        base = _limpo(p["arroba"])
        prod.append(dict(c, produto=p["produto"], nome=p["nome"][:30],
                         arrobas=[f"{base}.ia", f"{base}oficial", f"{base}.br", f"use{base}", f"{base}_inovare"], temas=[]))
    return prod + out


def _fila_tiktok():
    import cofre
    reg = cofre._ler()["contas"]
    usados = {(v or {}).get("email") for v in m._ler(m.ESTADO).values() if isinstance(v, dict)}
    usados |= {"e4487017@gmail.com", "gameoftroneskingsroadbrasil@gmail.com", "msenergypara@gmail.com"}
    feitos = m._ler(FILA)
    out = []
    for conta, r in ((m._ler(m.REUSO).get("tiktok") or {}).get("contas") or {}).items():
        if not r.get("cofre") or (feitos.get(conta) or {}).get("logado"):
            continue
        try:
            email, e = cofre.conta(r["cofre"])
        except KeyError:
            continue
        if e.get("google") != "vivo" or email in usados or email.startswith("ig_"):
            continue
        obs = r.get("_obs") or ""
        h = re.search(r"TikTok @([\w.]+)", obs)
        canal = re.search(r"=\s*([A-Z][\w ]+?)\s*(?:\(|;|->|$)", obs)
        base = h.group(1) if h else conta
        nome = canal.group(1).strip() if canal else re.sub(r"[._]+", " ", base).strip().title()
        arrobas = list(dict.fromkeys(a for a in (_limpo(base), _limpo(base + ".ia"), _limpo(conta),
                                                   _limpo(conta + ".ig"), _limpo(base + "_oficial")) if a))
        out.append({"tiktok": conta, "email": email, "nome": nome, "arrobas": arrobas, "temas": r.get("temas") or [],
                    "_obs": obs})
        usados.add(email)
    return sorted(out, key=lambda c: c["tiktok"] in feitos)  # quem falhou tenta de novo, depois das novas


REGRAS = ("temas", "canais", "postados_em", "parceiro_de", "projetos")


def marcar_produto(arroba, produto_id):
    """Registra a conta de produto no marcas_instagram.json (o comercial_veo passa a anunciar SÓ esse produto)."""
    import politica
    p = next(x for x in m._ler(PRODUTOS)["produtos"] if x["id"] == produto_id)
    g = next((x for x in m._ler(GRUPOS).get("grupos", []) if x["produto"] == produto_id), {})
    d = m._ler(MARCAS)
    d.setdefault("contas", {})[arroba] = {"marca": g.get("nome") or p["nome"], "produto": produto_id,
                                          "itens": g.get("itens", []), "cor": p.get("cor", "#2563EB"),
                                          "apoio": "#111827", "texto": "#FFFFFF"}
    politica.gravar_json(MARCAS, d)
    _log(f"  marca: {arroba} = {p['nome']}")


def ligar(arroba, chave, tiktok=None, regras=None, max_dia=5, sem_veo=True):
    """Põe a conta no postador do Instagram (reuso_plataformas.json) com o MESMO conteúdo do TikTok dela (ou `regras`),
    sem Veo (dona 24/10: "em vez de Veo, os mesmos conteúdos do YouTube e TikTok")."""
    import politica
    dados = m._ler(m.REUSO)
    tt = ((dados.get("tiktok") or {}).get("contas") or {}).get(tiktok) or {}
    novo = {k: list(tt[k]) for k in REGRAS if tt.get(k)}
    novo.update(regras or {})
    if "projetos" in novo:
        novo["projetos"] = [p for p in novo["projetos"] if p != "veo"]
    novo.update({"cofre": chave, "sem_veo": sem_veo, "max_dia": max_dia,
                 "_obs": f"criada {time.strftime('%d/%m')} (instagram_criar.py)" + (f"; mesmo conteúdo do TikTok {tiktok}"
                                                                                   if tiktok else "")})
    contas = dados.setdefault("instagram", {}).setdefault("contas", {})
    contas[arroba] = {**contas.get(arroba, {}), **novo}
    politica.gravar_json(m.REUSO, dados)
    _log(f"  ligada no postador: {arroba} <- {tiktok or regras}")


def proxima():
    """Cria a próxima da fila (o Agendador do Windows chama 5x por dia)."""
    ig = ((m._ler(m.REUSO).get("instagram") or {}).get("contas") or {})
    for tiktok, r in m._ler(FILA).items():  # criada e ainda fora do postador (ex.: rodada antiga): liga agora
        if r.get("logado") and r["logado"] not in ig:
            if r.get("produto"):
                ligar(r["logado"], r["cofre"], regras={"produto": r["produto"]}, sem_veo=False)
                marcar_produto(r["logado"], r["produto"])
            else:
                ligar(r["logado"], r["cofre"], tiktok)
    if not os.environ.get("IG_SENHA"):
        _log("sem IG_SENHA no ambiente — nada feito")
        return
    f = fila()
    if not f:
        _log("fila vazia")
        return
    # 10/11: fabricadeautomacoesia (1ª da fila por ser de produto) falhou 38x desde 04/11 no código do e-mail e travou
    # a fila inteira — 0 contas novas em 7 dias. Quem falhou 3x vai pro fim; as outras passam na frente.
    falhas = {}
    try:
        for linha in LOG.read_text("utf-8", errors="replace").splitlines():
            mm = re.search(r"criando Instagram do TikTok (\S+)", linha)
            if mm:
                falhas[mm.group(1)] = falhas.get(mm.group(1), 0) + 1
    except OSError:
        pass
    f.sort(key=lambda x: falhas.get(x["tiktok"], 0) >= 3)
    # 10/11 (regra 09/11): conta Google do Kaggle não pode abrir outro serviço Google pela casa — o criador abre o
    # Gmail dela pra ler o código. Fora da fila toda conta do kaggle_pool.json.
    try:
        import cofre
        kp = json.loads(m.Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text("utf-8"))
        kg = {str(k.get("cofre") or "").lower() for k in kp["contas"]}
        for k in kp["contas"]:
            try:
                kg.add(cofre.conta(k["cofre"])[0].lower())
            except KeyError:
                pass
    except (OSError, ValueError, KeyError):
        _log("kaggle_pool.json ilegível — sem criar (não dá pra conferir conta do Kaggle)")
        return
    f = [x for x in f if x["tiktok"].lower() not in kg and x["email"].lower() not in kg]
    if not f:
        _log("fila vazia (sem contas do Kaggle)")
        return
    c = f[0]
    _log(f"criando Instagram do TikTok {c['tiktok']} ({c['email']}, nome '{c['nome']}', @ {c['arrobas']})")
    chave = f"ig_{c['arrobas'][0]}"
    try:
        arroba, logado = criar(c["email"], c["nome"], c["arrobas"], chave)
    except Exception as e:  # noqa: BLE001
        arroba, logado = None, None
        _log(f"  erro: {type(e).__name__}: {str(e)[:120]}")
    feitos = m._ler(FILA)
    feitos[c["tiktok"]] = {"t": time.time(), "email": c["email"], "arroba": arroba, "logado": logado,
                           "cofre": chave, "temas": c["temas"], "produto": c.get("produto")}
    FILA.write_text(json.dumps(feitos, ensure_ascii=False, indent=2), encoding="utf-8")
    if logado:
        est = m._ler(m.ESTADO)
        est[logado] = {"resultado": f"logado @{logado}", "t": time.time(), "email": c["email"], "cofre": chave,
                       "tiktok": c["tiktok"], "_obs": f"criada {time.strftime('%d/%m/%Y')} pelo instagram_criar.py"}
        m.ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
        _log(f"  CRIADA @{logado}")
        if c.get("produto"):  # conta de produto: Veo do tema + card do produto (comercial_veo/marcas_instagram)
            ligar(logado, chave, regras={"produto": c["produto"]}, sem_veo=False)
            marcar_produto(logado, c["produto"])
        else:
            ligar(logado, chave, c["tiktok"])
    else:
        _log(f"  não criou (@{arroba}) — ver logs\\instagram_tela\\{chave}_*.png")
        m._avisar(f"Instagram novo do TikTok {c['tiktok']} não foi criado (@{arroba}). Prints em "
                  f"logs\\instagram_tela\\{chave}_*.png")


def main():
    if "--fila" in sys.argv:
        for c in fila():
            print(f"  {c['tiktok']:28} {c['email']:38} {c['nome'][:24]:24} @{c['arrobas'][0]}")
        print(f"Total: {len(fila())}")
        return
    if "--proxima" in sys.argv:
        return proxima()
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--nome", required=True)
    ap.add_argument("--arrobas", nargs="+", required=True)
    ap.add_argument("--cofre")
    a = ap.parse_args()
    chave = (a.cofre or f"ig_{a.arrobas[0]}").lower()
    arroba, logado = criar(a.email.lower(), a.nome, a.arrobas, chave)
    print(f"RESULTADO: @{arroba} logado={logado}", flush=True)
    if logado:
        est = m._ler(m.ESTADO)
        est.pop(chave, None)
        est[logado] = {"resultado": f"logado @{logado}", "t": time.time(), "email": a.email.lower(), "cofre": chave,
                       "_obs": f"criada {time.strftime('%d/%m/%Y')} pelo instagram_criar.py"}
        m.ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
