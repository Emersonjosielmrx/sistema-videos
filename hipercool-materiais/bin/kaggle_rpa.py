"""kaggle_rpa.py — treina as vozes clonadas na GPU gratis do Kaggle PELO NAVEGADOR (cofre + Playwright, como as postagens).

Conta: emersonjosiel649 (Kaggle "emersonjosiel", telefone verificado em 18/10/2026: libera GPU T4 30 h/semana e
internet). Sem API do Kaggle: tudo pela pagina, como uma pessoa faria. Roda com python\\venv (tem o Playwright).

  kaggle_rpa.py treinar   empacota quem tem material e nao tem modelo, sobe como dataset NOVO, importa o
                          amostras_voz\\kaggle_treino_rvc.ipynb num notebook NOVO, liga GPU T4 x2 e internet e roda
                          Save & Run All (Commit). Um lote por vez: com lote em andamento nao faz nada.
  kaggle_rpa.py baixar    se o lote terminou, baixa o modelos_rvc.zip e roda importar_kaggle.py (poe os modelos em
                          models\\rvc\\vozes e relanca a fila, que gera as amostras).
  kaggle_rpa.py auto      o que o vigia (voz_clonada.py vigiar, 10 em 10 min) chama: com lote, confere a cada 30 min
                          se terminou; sem lote, manda o que estiver esperando treino.
  kaggle_rpa.py status    reescreve e mostra o amostras_voz\\kaggle\\STATUS.txt.

Cada lote tem dataset e notebook com nome datado: evita versao de dataset e entrada presa a versao velha.
Pasta amostras_voz\\kaggle\\: STATUS.txt (para ler), estado.json, erro_*.png, LEIA.txt (o que fazer quando falha).
Ultima linha impressa: "KAGGLE: <ENVIADO|IMPORTADO|RODANDO|FALHOU|NADA> <info>".
"""
import json
import re
import subprocess
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cofre  # noqa: E402
import empacotar_kaggle  # noqa: E402

CONTA = "emersonjosiel649"
USUARIO = "emersonjosiel"
RAIZ = Path(r"D:\hipercool-materiais")
NOTEBOOK = RAIZ / "amostras_voz" / "kaggle_treino_rvc.ipynb"
PASTA = RAIZ / "amostras_voz" / "kaggle"
ESTADO = PASTA / "estado.json"
IMPORTAR = RAIZ / "bin" / "importar_kaggle.py"
CHECAR_MIN = 30
ESPERA_FALHA_H = 2
MAX_TENTATIVAS = 2  # voz que falhou 2 lotes seguidos fica de fora (STATUS.txt mostra)
# os 3 usos da GPU na conta (treino, piloto da fidelidade e conversor dos vídeos grandes): 1 sessão de GPU por vez
ESTADOS_KAGGLE = [RAIZ / "amostras_voz" / p / "estado.json" for p in ("kaggle", "kaggle_piloto", "kaggle_conversor")]
_ultimo = ["", ""]


class Falha(Exception):
    pass


class SemSaida(Falha):
    pass


def _fim(evento, info):
    _ultimo[:] = [evento, info]
    print(f"KAGGLE: {evento} {info}", flush=True)


def _ler():
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}


def _gravar(est):
    PASTA.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def _outro_lote():
    """Nome da pasta de outro uso do Kaggle com lote rodando (o ESTADO de quem chama fica de fora), ou None."""
    for arq in ESTADOS_KAGGLE:
        if arq == ESTADO:
            continue
        try:
            if json.loads(arq.read_text(encoding="utf-8")).get("lote"):
                return arq.parent.name
        except (OSError, ValueError):
            continue
    return None


def _status_txt(est):
    """Resumo em portugues simples para quem so acompanha (vigia, modelo menor, o dono)."""
    agora = datetime.now()
    lin = [f"Atualizado: {agora:%d/%m %H:%M}   (o vigia confere sozinho a cada 30 min; o que fazer se falhar: LEIA.txt)",
           f"Ultimo resultado: {_ultimo[0]} {_ultimo[1]}", ""]
    lote = est.get("lote")
    if lote:
        conf = datetime.fromtimestamp(lote.get("checado", 0))
        lin += ["LOTE TREINANDO NO KAGGLE:",
                f"  notebook: https://www.kaggle.com/code/{USUARIO}/{lote['notebook']}  (aba Logs = andamento ao vivo)",
                f"  vozes: {', '.join(lote['vozes'])}",
                f"  enviado: {lote['enviado']}   ultima conferida: {conf:%d/%m %H:%M}",
                "  normal: ~1 h por voz; acima de 11 h sem terminar = problema (ver LEIA.txt)"]
    else:
        lin.append("Nenhum lote treinando agora.")
    tent = est.get("tentativas", {})
    espera = empacotar_kaggle.esperando_treino()
    fora = [v for v in espera if tent.get(v, 0) >= MAX_TENTATIVAS]
    lin += ["", f"Com material e sem modelo: {', '.join(espera) or 'nenhuma'}",
            f"Cota: {est.get('gpu', 'GPU T4 = 30 h por semana (ainda nao lida)')}"]
    if fora:
        lin.append(f"DESISTIDAS (falharam {MAX_TENTATIVAS} lotes, precisam de gente): {', '.join(fora)}")
    hist = est.get("historico", [])[-5:]
    if hist:
        lin += ["", "Lotes que ja voltaram:"]
        lin += [f"  {h['terminado']}  {h['notebook']}: voltaram {', '.join(h['voltaram']) or 'nenhuma'}"
                + (f"; sem modelo {', '.join(h['faltaram'])}" if h["faltaram"] else "")
                + (f"; ERRO {h['erro']}" if h.get("erro") else "") for h in hist]
    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / "STATUS.txt").write_text("\n".join(lin) + "\n", encoding="utf-8")
    return "\n".join(lin)


def _cdp_arquivo(pg, entrada, arquivo):
    """Arquivo no <input type=file> so pelo CAMINHO (CDP DOM.setFileInputFiles): set_input_files do Playwright
    transfere o conteudo pela conexao CDP e recusa acima de 50 MB (mesmo jeito do youtube_web_poster)."""
    entrada.evaluate("el => { window.__kg_entrada = el; }")
    cdp = pg.context.new_cdp_session(pg)
    try:
        obj = cdp.send("Runtime.evaluate", {"expression": "window.__kg_entrada"})["result"]["objectId"]
        cdp.send("DOM.setFileInputFiles", {"files": [str(Path(arquivo).resolve())], "objectId": obj})
    finally:
        cdp.detach()


def _texto(pg):
    return pg.evaluate("document.body.innerText")


def _checar_login(pg):
    """Deslogado o Kaggle mostra o notebook privado como 'We can't find that page' (ou manda pro login): em 19/10
    00:12 isso virou 'terminou sem saida' e o vigia fechou um lote com as 7 vozes treinadas. Falha comum = o lote
    fica aberto e a proxima conferida tenta de novo."""
    if "/account/login" in pg.url or "can't find that page" in _texto(pg):
        raise Falha("Kaggle deslogado ou pagina fora do ar (o lote continua; ver LEIA.txt: entrar de novo)")


def _esperar(pg, cond, segundos, erro):
    fim = time.time() + segundos
    while time.time() < fim:
        if cond():
            return
        pg.wait_for_timeout(3000)
    raise Falha(erro)


# 22/10: um navegador do Kaggle por vez. O lote normal, o piloto de fidelidade (kaggle_piloto.py) e o conversor dos
# vídeos grandes (kaggle_conversor.py) usam o mesmo Chrome do cofre. Trava com mais de 45 min = processo que morreu.
TRAVA_NAV = RAIZ / "amostras_voz" / "kaggle_navegador.lock"


def _pegar_trava_nav(espera_s=30 * 60):
    fim = time.time() + espera_s
    while True:
        try:
            with open(TRAVA_NAV, "x", encoding="utf-8") as f:
                f.write(f"{os.getpid()} {time.time():.0f}")
            return
        except FileExistsError:
            try:
                idade = time.time() - float(TRAVA_NAV.read_text(encoding="utf-8").split()[1])
            except (OSError, ValueError, IndexError):
                idade = 0
            if idade > 45 * 60:
                TRAVA_NAV.unlink(missing_ok=True)
                continue
            if time.time() > fim:
                raise Falha("navegador do Kaggle ocupado por outro script há 30 min")
            time.sleep(15)


def _soltar_trava_nav():
    try:
        if TRAVA_NAV.read_text(encoding="utf-8").split()[0] == str(os.getpid()):
            TRAVA_NAV.unlink()
    except (OSError, IndexError):
        pass


class Navegador:
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        _pegar_trava_nav()
        try:
            self.porta, self.proc = cofre.abrir(CONTA)
            self.pw = sync_playwright().start()
            self.br = self.pw.chromium.connect_over_cdp(f"http://127.0.0.1:{self.porta}", timeout=120000)
            self.pg = self.br.contexts[0].new_page()
            self.pg.set_default_timeout(30000)
        except BaseException:
            _soltar_trava_nav()
            raise
        return self.pg

    def __exit__(self, tipo, erro, _tb):
        try:
            if erro is not None:
                try:
                    PASTA.mkdir(parents=True, exist_ok=True)
                    self.pg.screenshot(path=str(PASTA / f"erro_{datetime.now():%Y%m%d_%H%M}.png"), timeout=90000)
                except Exception:  # noqa: BLE001
                    pass
            try:
                self.pg.close()
            except Exception:  # noqa: BLE001
                pass
            cofre.fechar(self.proc, self.br, CONTA)
            self.pw.stop()
        finally:
            _soltar_trava_nav()


# ─── etapas na pagina (cada uma conferida no Kaggle real em 18/10/2026) ───────
def criar_dataset(pg, zip_, titulo):
    pg.goto("https://www.kaggle.com/datasets?new=true", wait_until="domcontentloaded", timeout=90000)
    if "/account/login" in pg.url:
        raise Falha("Kaggle deslogado (ver LEIA.txt: entrar de novo)")
    entrada = pg.locator("input[type='file']").first
    entrada.wait_for(state="attached", timeout=60000)
    _cdp_arquivo(pg, entrada, zip_)
    campo = pg.locator("input[placeholder='Enter dataset title']")
    campo.wait_for(state="visible", timeout=60000)
    campo.fill(titulo)
    criar = pg.get_by_role("button", name="Create", exact=True).last
    _esperar(pg, criar.is_enabled, 900, "upload do dataset nao terminou em 15 min")
    criar.click()
    _esperar(pg, lambda: pg.get_by_role("button", name="Go to Dataset").count() > 0, 600,
             "Kaggle nao confirmou a criacao do dataset em 10 min")
    pg.get_by_role("button", name="Go to Dataset").click(timeout=60000)
    _esperar(pg, lambda: re.search(r"/datasets/[^/]+/[^/?]+", pg.url), 120, "nao abriu a pagina do dataset")
    url = pg.url.split("?")[0]
    print("dataset:", url, flush=True)
    return url


def _sumario(pg):
    t = _texto(pg)
    i = t.find("Table of contents")
    return t[i:i + 200] if i >= 0 else ""


def _rascunho_salvo(pg):
    t = _texto(pg)
    return "Draft saved" in t and "Draft saving" not in t


def novo_notebook(pg, ipynb, titulo, marca="Treino RVC"):
    """Lote de 18/10 19:16: importado com o editor ainda em 'Editor Loading', o modelo padrao do Kaggle sobrescreveu
    o nosso e a versao rodaria o notebook vazio. Por isso: espera carregar e confere o titulo no sumario.
    marca = titulo da 1a celula markdown do notebook (aparece no 'Table of contents'); o conversor passa o dele
    (22/10 08:04: com "Treino RVC" fixo aqui o conversor falhava sempre)."""
    try:
        pg.goto("https://www.kaggle.com/code/new", wait_until="domcontentloaded", timeout=90000)
    except Exception as e:  # noqa: BLE001
        if "ERR_ABORTED" not in str(e):  # 19/10 19:12: a pagina do dataset recem-criado ainda navegava e cancelou
            raise
        pg.wait_for_timeout(10000)
        pg.goto("https://www.kaggle.com/code/new", wait_until="domcontentloaded", timeout=90000)
    _esperar(pg, lambda: "/edit" in pg.url and "Draft Session" in _texto(pg) and "Editor Loading" not in _texto(pg),
             420, "editor do notebook nao abriu em 7 min")  # 19/10 09:00: 3 min nao bastaram com o PC carregado
    pg.wait_for_timeout(5000)
    pg.locator("button:has-text('File')").first.click()
    pg.get_by_role("menuitem").filter(has_text="Import Notebook").first.click()
    entrada = pg.locator("input[type='file'][accept*='.ipynb']").first
    entrada.wait_for(state="attached")
    _cdp_arquivo(pg, entrada, ipynb)
    pg.get_by_text(Path(ipynb).name).first.wait_for(state="visible")
    pg.get_by_role("button", name="Import", exact=True).last.click()
    _esperar(pg, lambda: marca in _sumario(pg), 120, "o notebook importado nao apareceu no editor")
    _esperar(pg, lambda: _rascunho_salvo(pg), 120, "rascunho do notebook importado nao salvou")
    pg.wait_for_timeout(3000)
    nome = pg.locator("input[aria-label^='Title']").first
    nome.fill(titulo)
    nome.press("Escape")
    pg.wait_for_timeout(1500)
    nome.press("Escape")
    pg.wait_for_timeout(1500)
    _abrir_barra(pg)
    print("notebook:", pg.url, flush=True)


def _abrir_barra(pg):
    """O sumario (conferido pelo 'Treino RVC') fica na barra da direita, que recolhe sozinha depois dos menus."""
    if not pg.locator("button[aria-label='Collapse Sidebar']").first.is_visible():
        pg.locator("button:has-text('arrow_left')").first.click()
        pg.wait_for_timeout(1500)


def adicionar_dataset(pg, url_dataset):
    """Dataset recem-criado demora minutos para aparecer na busca do Add Input ("0 Results", 19/10 13:25):
    refaz a busca a cada 30 s por ate 15 min."""
    pg.locator("button:has-text('Add Input')").first.click()
    busca = pg.locator("input[placeholder='Search keyword or URL']")
    adicionar = pg.locator("button[aria-label^='Add Dataset']").first
    for _ in range(30):
        busca.fill("")
        busca.fill(url_dataset)
        try:
            _esperar(pg, adicionar.is_visible, 30, "")
            break
        except Falha:
            pass
    else:
        raise Falha("dataset novo nao apareceu na busca do Add Input em 15 min")
    adicionar.click(timeout=60000)
    pg.wait_for_timeout(5000)
    pg.locator("button[aria-label='Close']:visible").first.click()
    _esperar(pg, lambda: "DATASETS" in _texto(pg), 180, "dataset nao entrou como input do notebook")


def _settings(pg, item=None):
    pg.locator("button:has-text('Settings')").first.click()
    pg.wait_for_timeout(1200)
    if item:
        sub = pg.get_by_role("menuitem").filter(has_text=item).first
        sub.hover()
        pg.wait_for_timeout(600)
        sub.click()
        pg.wait_for_timeout(1200)


def _fechar_menus(pg):
    pg.keyboard.press("Escape")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(800)


def acelerador(pg, nome):
    """nome = 'GPU T4 x2' ou 'None'. Confirma o dialogo e confere a marca no menu."""
    pg.locator("button:has-text('Settings')").first.click()
    pg.wait_for_timeout(1200)
    sub = pg.get_by_role("menuitem").filter(has_text="Accelerator").first
    sub.hover()
    pg.wait_for_timeout(600)
    item = pg.get_by_role("menuitem").filter(has_text=nome).first
    item.click()
    aviso = ""
    if nome != "None":
        confirma = pg.locator(f"[role='dialog'] button:has-text('Turn on {nome}')")
        confirma.wait_for(state="visible", timeout=30000)
        aviso = " ".join(pg.locator("[role='dialog']").first.inner_text().split())
        print("GPU:", aviso[:200], flush=True)
        confirma.click()
    else:
        pg.wait_for_timeout(1500)
        if pg.locator("[role='dialog'] button").count():
            pg.locator("[role='dialog'] button").last.click()
    pg.wait_for_timeout(3000)
    pg.keyboard.press("Escape")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(1000)
    pg.locator("button:has-text('Settings')").first.click()
    pg.wait_for_timeout(1200)
    sub = pg.get_by_role("menuitem").filter(has_text="Accelerator").first
    sub.hover()
    pg.wait_for_timeout(600)
    marcado = pg.get_by_role("menuitem").filter(has_text="check").filter(has_text=nome).count() > 0
    pg.keyboard.press("Escape")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(800)
    if not marcado:
        raise Falha(f"acelerador '{nome}' nao ficou marcado (cota de GPU acabou? ver LEIA.txt)")
    return aviso


def internet_ligada(pg):
    _settings(pg)
    ligar = pg.get_by_role("menuitem").filter(has_text="Turn on internet")
    if ligar.count() and ligar.first.is_visible():
        ligar.first.click()
        pg.wait_for_timeout(2000)
        confirma = pg.locator("[role='dialog'] button:has-text('Turn on')")
        if confirma.count():
            confirma.first.click()
            pg.wait_for_timeout(2000)
        _settings(pg)
    ok = pg.get_by_role("menuitem").filter(has_text="Turn off internet").count() > 0
    _fechar_menus(pg)
    if not ok:
        raise Falha("internet do notebook nao ligou (telefone ainda verificado? ver LEIA.txt)")


def rodar_versao(pg):
    """Save Version > Save & Run All (Commit). Devolve o slug do notebook.
    Confere pelo contador ao lado de 'Save Version' (0 -> 1): o texto antigo ('Version #|Committing') deu falso
    positivo em 18/10 e o lote ficou como rascunho sem rodar."""
    _abrir_barra(pg)
    if "Treino RVC" not in _sumario(pg):
        raise Falha("o editor nao esta com o notebook de treino (sumario sem 'Treino RVC')")
    _esperar(pg, lambda: _rascunho_salvo(pg), 120, "rascunho nao salvou antes da versao")

    def versoes():
        v = re.findall(r"Save Version\s+(\d+)", _texto(pg))
        return int(v[0]) if v else -1
    antes = versoes()
    pg.locator("button[aria-label='Save Version']").first.click()
    try:  # a gaveta "Save version" nao tem role=dialog; o tipo padrao ja e o commit
        pg.get_by_text("Save & Run All (Commit)").first.wait_for(state="visible")
    except Exception:  # noqa: BLE001
        raise Falha("gaveta de versao sem 'Save & Run All (Commit)'") from None
    pg.wait_for_timeout(1500)
    pg.get_by_role("button", name="Save", exact=True).last.click()
    _esperar(pg, lambda: versoes() > antes, 180, f"Kaggle nao criou a versao (contador continuou em {antes})")
    pg.wait_for_timeout(10000)  # fechar o navegador logo em seguida ja deixou a versao sem rodar
    return re.search(r"/code/[^/]+/([^/?]+)", pg.url).group(1)


def situacao(pg, nb):
    """'rodando', 'terminou' ou 'sem versao' (a pagina cai no editor: o Save Version nao pegou e nada rodou)."""
    pg.goto(f"https://www.kaggle.com/code/{USUARIO}/{nb}", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)
    _checar_login(pg)
    if "/edit" in pg.url:
        return "sem versao"
    return "rodando" if re.search(r"Running for|Queued|Fetching worker|Committing", _texto(pg)) else "terminou"


def ler_resumo(pg, nb):
    """Linhas do RESUMO.txt da aba Output (aberto por padrao): '<voz>: OK (...)' / '<voz>: FALHOU: <erro>'.
    'Terminou' nao quer dizer que treinou: o lote de 18/10 terminou com as 5 vozes FALHOU so neste arquivo."""
    pg.goto(f"https://www.kaggle.com/code/{USUARIO}/{nb}/output", wait_until="domcontentloaded", timeout=90000)
    padrao = r"^\w+: (?:OK|FALHOU|nao deu tempo).*$"
    try:
        _esperar(pg, lambda: re.search(padrao, _texto(pg), re.M), 60, "")
    except Falha:
        return []
    return re.findall(padrao, _texto(pg), re.M)


def baixar_saida(pg, nb, nome, destino):
    """Aba Output da versao: baixa <nome> pelo Chrome direto na pasta (CDP Browser.setDownloadBehavior)."""
    destino.mkdir(parents=True, exist_ok=True)
    alvo = destino / nome
    alvo.unlink(missing_ok=True)
    cdp = pg.context.browser.new_browser_cdp_session()
    cdp.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(destino)})
    try:
        pg.goto(f"https://www.kaggle.com/code/{USUARIO}/{nb}/output", wait_until="domcontentloaded", timeout=90000)
        arq = pg.get_by_text(nome, exact=True).first
        try:
            arq.wait_for(state="visible", timeout=90000)
        except Exception:  # noqa: BLE001
            _checar_login(pg)
            raise SemSaida(f"a versao terminou sem {nome} na saida (ver a aba Logs no Kaggle)") from None
        arq.click()
        pg.wait_for_timeout(3000)
        # icone 'get_app' do cabecalho do arquivo; o botao 'Download' do topo so abre o menu do Kaggle CLI
        pg.locator("span[role='button'][aria-label='Download']:visible").first.click()
        _esperar(pg, lambda: alvo.exists() and not list(destino.glob("*.crdownload")), 900,
                 f"download do {nome} nao terminou em 15 min")
    finally:
        cdp.send("Browser.setDownloadBehavior", {"behavior": "default"})
        cdp.detach()
    print(f"baixado: {alvo} ({alvo.stat().st_size / 1e6:.1f} MB)", flush=True)
    return alvo


# ─── comandos ────────────────────────────────────────────────────────────────
def treinar(est):
    if est.get("lote"):
        return _fim("RODANDO", f"lote em andamento: {est['lote']['notebook']}")
    tent = est.setdefault("tentativas", {})
    vozes = [v for v in empacotar_kaggle.esperando_treino() if tent.get(v, 0) < MAX_TENTATIVAS]
    if not vozes:
        return _fim("NADA", "nenhuma voz esperando treino")
    outro = _outro_lote()
    if outro:
        return _fim("NADA", f"espera: lote de {outro} rodando no Kaggle (1 sessão de GPU por vez)")
    zip_ = empacotar_kaggle.empacotar(vozes)
    print(f"{zip_.name} ({zip_.stat().st_size / 1e6:.0f} MB): {', '.join(vozes)}", flush=True)
    marca = datetime.now().strftime("%Y%m%d %H%M")
    with Navegador() as pg:
        url_ds = criar_dataset(pg, zip_, f"vozes {marca}")
        novo_notebook(pg, NOTEBOOK, f"treino rvc {marca}")
        adicionar_dataset(pg, url_ds)
        internet_ligada(pg)
        aviso = acelerador(pg, "GPU T4 x2")
        nb = rodar_versao(pg)
    horas = re.search(r"You have ([\d.]+) hours? remaining", aviso)
    if horas:
        est["gpu"] = f"{horas.group(1)} h de GPU restantes na semana (visto em {datetime.now():%d/%m %H:%M}, antes deste lote)"
    for v in vozes:
        tent[v] = tent.get(v, 0) + 1
    est["lote"] = {"notebook": nb, "dataset": url_ds, "vozes": vozes,
                   "enviado": datetime.now().isoformat(timespec="minutes"), "checado": time.time()}
    est.pop("falha_treinar", None)
    _gravar(est)
    _fim("ENVIADO", f"{len(vozes)} vozes ({', '.join(vozes)}) -> kaggle.com/code/{USUARIO}/{nb}")


def _intervalo(lote):
    """Minutos entre conferidas: 30, e 10 perto do fim previsto (~37 min por voz no T4, 2 vozes por vez nas 2 GPUs,
    + preparo), para nao deixar o lote pronto esperando meia hora."""
    previsto = datetime.fromisoformat(lote["enviado"]).timestamp() + (20 + 45 * ((len(lote["vozes"]) + 1) // 2)) * 60
    return 10 if time.time() > previsto - 15 * 60 else CHECAR_MIN


def baixar(est, forcar=False):
    lote = est.get("lote")
    if not lote:
        return _fim("NADA", "nenhum lote em andamento")
    if not forcar and time.time() - lote.get("checado", 0) < _intervalo(lote) * 60:
        return _fim("RODANDO", f"{lote['notebook']} (proxima conferida em ate {_intervalo(lote)} min)")
    nb = lote["notebook"]
    lote["checado"] = time.time()  # falha aqui tambem so tenta de novo na proxima janela
    _gravar(est)
    with Navegador() as pg:
        sit = situacao(pg, nb)
        if sit == "rodando":
            return _fim("RODANDO", f"{nb} ainda rodando")
        resumo = ler_resumo(pg, nb) if sit == "terminou" else []
        print("RESUMO.txt:", *resumo, sep="\n  ", flush=True)
        try:
            if sit == "sem versao":
                raise SemSaida("o notebook ficou sem versao rodando (o Save Version nao pegou)")
            zip_ = baixar_saida(pg, nb, "modelos_rvc.zip", PASTA / nb)
        except SemSaida as e:  # notebook deu erro ou foi cancelado: encerra o lote, as vozes vao no proximo
            est.setdefault("historico", []).append({**lote, "terminado": datetime.now().isoformat(timespec="minutes"),
                                                    "voltaram": [], "faltaram": lote["vozes"], "erro": str(e),
                                                    "resumo": resumo})
            est.pop("lote")
            _gravar(est)
            raise
    r = subprocess.run([sys.executable, str(IMPORTAR), str(zip_)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    print(r.stdout, r.stderr, flush=True)
    if r.returncode:
        raise Falha(f"importar_kaggle.py falhou: {r.stderr.strip()[-300:]}")
    voltaram = [v for v in lote["vozes"] if (empacotar_kaggle.VOZES / v / f"{v}.pth").exists()]
    for v in voltaram:
        est.get("tentativas", {}).pop(v, None)
    faltaram = sorted(set(lote["vozes"]) - set(voltaram))
    est.setdefault("historico", []).append({**lote, "terminado": datetime.now().isoformat(timespec="minutes"),
                                            "voltaram": voltaram, "faltaram": faltaram, "resumo": resumo})
    est.pop("lote")
    _gravar(est)
    motivo = next((linha for linha in resumo if "FALHOU" in linha), "")[:200]
    _fim("IMPORTADO", f"{len(voltaram)} modelos ({', '.join(voltaram)})"
         + (f"; sem modelo: {', '.join(faltaram)} (vai no proximo lote) {motivo}" if faltaram else ""))


def auto(est):
    if est.get("lote"):
        return baixar(est)
    if time.time() - est.get("falha_treinar", 0) < ESPERA_FALHA_H * 3600:
        return _fim("NADA", f"ultimo envio falhou ha menos de {ESPERA_FALHA_H} h")
    try:
        treinar(est)
    except Exception:
        est["falha_treinar"] = time.time()
        _gravar(est)
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    estado = _ler()
    try:
        if cmd == "treinar":
            treinar(estado)
        elif cmd == "baixar":
            baixar(estado, forcar=True)
        elif cmd == "auto":
            auto(estado)
        elif cmd != "status":
            sys.exit(__doc__)
    except Exception as e:  # noqa: BLE001
        _fim("FALHOU", f"{type(e).__name__}: {e}"[:400])
        sys.exit(2)
    finally:
        texto = _status_txt(_ler())
        if cmd == "status":
            print(texto)
