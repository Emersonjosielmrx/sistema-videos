r"""D:\recapd-ambientes\producao\colab\abrir_colab_teste.py (PC1) — 26/11 dona: "pode fazer nessas 17 (contas Google
sem canal), tem minha permissão" — Colab grátis (GPU T4) como RESERVA do Kaggle, rodando o MESMO trabalhador
(kaggle_trabalhador.py da central da casa) só na fila de TESTE (TRAB_PAPEL=teste: fila_teste primeiro; parada 15 min
= 1 longo da produção).

Regras (INCIDENTE_BANIMENTO_02NOV.md):
  - só contas cujo IP fixo (fish_proxy rnprmtfo-N no cofre) NÃO é de nenhuma conta VIVA do Kaggle (conferido 26/11;
    a lista LIVRES abaixo). As 17 são donas de contas do Kaggle banidas em 02/11.
  - o Chrome da conta sai SEMPRE pelo IP fixo dela (ponte_proxy_fixo.py N -> 127.0.0.1:183NN); nunca pela casa.
  - 1 conta por vez (uma sessão de Colab aberta por este script).

Uso:  python abrir_colab_teste.py <apelido>      (ex.: filmescomia1)
Fica rodando (oculto) mantendo a aba viva: a cada 4 min clica na página e nos avisos ("ainda está aí?", reconectar).
Para: criar D:\recapd-ambientes\producao\colab\colab_teste_PARAR. Prints em colab\prints_colab_teste\.
Log: colab\colab_teste.log
"""
import base64
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

AQUI = Path(__file__).resolve().parent
LOG = AQUI / "colab_teste.log"
PRINTS = AQUI / "prints_colab_teste"
PARAR = AQUI / "colab_teste_PARAR"
RCLONE = r"D:\tools\rclone.exe"
CODIGO = "manhwa-drive:colab_recap/colab_codigo/kaggle_trabalhador.py"
# apelido -> N do rnprmtfo (fish_proxy do cofre); conferido 26/11 que o IP não é de conta viva do Kaggle
LIVRES = {"filmescomia1": 27, "fabricadeautomacoes0": 25, "fabricadeautomacoesia": 26, "inovaremanhwaverseesp": 31,
          "jogoscomia": 34, "jornalcomia": 35, "solarmundo195": 71, "vendeafiliados3": 5, "entrevistacomia": 23}
# 26/11: sem "Continuar"/"OK" soltos — o aviso do Gemini também tem "Continuar" (e a caixa do Gemini roubava o foco)
CLIQUES = ("Executar mesmo assim", "Run anyway", "Reconectar", "Reconnect", "Estou aqui", "I'm here")


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%d/%m %H:%M:%S} {m}\n")


def foto(page, nome):
    PRINTS.mkdir(exist_ok=True)
    try:
        page.screenshot(path=str(PRINTS / f"{datetime.now():%H%M%S}_{nome}.png"))
    except Exception:  # noqa: BLE001
        pass


def ponte(n):
    porta = 18300 + n
    def viva():
        try:
            socket.create_connection(("127.0.0.1", porta), timeout=2).close()
            return True
        except OSError:
            return False
    if not viva():
        subprocess.Popen([sys.executable, str(AQUI / "ponte_proxy_fixo.py"), str(n), str(porta)], creationflags=0x08000000)
        for _ in range(20):
            time.sleep(1)
            if viva():
                break
        else:
            raise RuntimeError(f"ponte do rnprmtfo-{n} não subiu — não abro pela internet de casa")
    return porta


def celula(apelido):
    conf = subprocess.run([RCLONE, "config", "show", "manhwa-drive"], capture_output=True, text=True,
                          check=True).stdout.strip()
    b64 = base64.b64encode((conf + "\n").encode()).decode()
    return "\n".join([
        "# 26/11: trabalhador do recap (mesmo do Kaggle) — fila de TESTE. Não fechar esta aba.",
        "import os, base64, subprocess, urllib.request, zipfile, io, pathlib",
        f"os.environ['TRAB_NOME'] = 'colab_{apelido}'",
        "os.environ['TRAB_PAPEL'] = 'teste'",
        "os.environ['TRAB_SESSAO_MAX_H'] = '5'",
        "os.environ['TRAB_LIMITE_H'] = '4'",
        "pathlib.Path('/tmp/rclone_in.conf').write_bytes(base64.b64decode('" + b64 + "'))",
        "os.environ['RCLONE_CONF'] = '/tmp/rclone_in.conf'",
        "rc = pathlib.Path('/tmp/rclone_bin')",
        "if not rc.exists():",
        "    z = urllib.request.urlopen('https://downloads.rclone.org/rclone-current-linux-amd64.zip', timeout=300).read()",
        "    with zipfile.ZipFile(io.BytesIO(z)) as zf:",
        "        rc.write_bytes(zf.read(next(n for n in zf.namelist() if n.endswith('/rclone'))))",
        "    rc.chmod(0o755)",
        f"subprocess.run([str(rc), '--config', '/tmp/rclone_in.conf', 'copyto', '{CODIGO}', '/content/trab.py'], check=True)",
        "subprocess.run('nvidia-smi -L', shell=True)",
        "!python /content/trab.py 2>&1 | tee -a /content/trab.log",
    ])


def clicar_avisos(pg):
    for txt in CLIQUES:
        try:
            b = pg.get_by_role("button", name=txt, exact=True)
            if b.count() and b.first.is_visible() and b.first.is_enabled():
                b.first.click(timeout=3000)
                log(f"clicou '{txt}'")
                pg.wait_for_timeout(1500)
        except Exception:  # noqa: BLE001
            pass


def gpu(pg):
    """Ambiente de execução -> Alterar o tipo -> GPU T4 -> Salvar (pt ou en)."""
    for menu, item in (("Ambiente de execução", "Alterar o tipo de ambiente de execução"),
                       ("Runtime", "Change runtime type")):
        try:
            m = pg.get_by_text(menu, exact=True)
            if not m.count():
                continue
            m.first.click(timeout=5000)
            pg.wait_for_timeout(1200)
            pg.get_by_text(item, exact=True).first.click(timeout=5000)
            pg.wait_for_timeout(2500)
            for rot in ("GPU T4", "T4 GPU"):
                r = pg.get_by_text(rot, exact=True)
                if r.count():
                    r.first.click(timeout=5000)
                    break
            pg.wait_for_timeout(800)
            for salvar in ("Salvar", "Save"):
                s = pg.get_by_role("button", name=salvar, exact=True)
                if s.count():
                    s.first.click(timeout=5000)
                    log("tipo de ambiente: GPU T4")
                    return True
        except Exception as e:  # noqa: BLE001
            log(f"GPU pelo menu '{menu}' falhou: {type(e).__name__}: {str(e)[:120]}")
            pg.keyboard.press("Escape")
    return False


def main(apelido):
    if apelido not in LIVRES:
        sys.exit(f"{apelido} não está na lista de contas liberadas (IP sem conta viva do Kaggle): {sorted(LIVRES)}")
    PARAR.unlink(missing_ok=True)
    n = LIVRES[apelido]
    email = f"{apelido}@gmail.com"
    _, e = cofre.conta(apelido)
    if cofre._cdp_vivo(e["porta"]):  # aberta por outro caminho (talvez sem o IP fixo): fecha e reabre pelo IP certo
        cofre._fechar_porta(e["porta"])
    pp = ponte(n)
    flags = [f"--proxy-server=http://127.0.0.1:{pp}", "--proxy-bypass-list=<-loopback>",
             "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
    porta, _proc = cofre.abrir(apelido, url="about:blank", visivel=True, extra=flags)
    log(f"{email}: Chrome na porta {porta} pelo rnprmtfo-{n} (ponte {pp})")
    p = sync_playwright().start()
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    pg = ctx.new_page()
    pg.goto("https://colab.research.google.com/#create=true", timeout=120000)
    pg.wait_for_timeout(15000)
    foto(pg, "aberto")
    if "accounts.google.com" in pg.url:
        log(f"{email}: pediu LOGIN do Google — parei (a dona loga e roda de novo)")
        return
    # 26/11: o aviso de privacidade do Gemini abre sozinho e a caixa do Gemini roubava o foco: aceita o aviso (é só
    # da IA, que não usamos), fecha o painel do Gemini e só então clica DENTRO da célula
    for txt in ("Continuar", "Continue"):
        try:
            d = pg.get_by_role("dialog").get_by_role("button", name=txt, exact=True)
            if d.count() and d.first.is_visible():
                d.first.click(timeout=3000)
                pg.wait_for_timeout(1500)
        except Exception:  # noqa: BLE001
            pass
    pg.keyboard.press("Escape")
    gpu(pg)
    pg.wait_for_timeout(3000)
    for sel in ('button[aria-label="Fechar"]', 'button[aria-label="Close"]'):
        try:
            x = pg.locator(f"colab-gemini-panel {sel}, .gemini-panel {sel}")
            if x.count():
                x.first.click(timeout=3000)
        except Exception:  # noqa: BLE001
            pass
    cel = pg.locator(".cell.code").first
    cel.locator(".monaco-editor, .view-lines, .inputarea").first.click(timeout=20000)
    pg.wait_for_timeout(800)
    pg.keyboard.insert_text(celula(apelido))
    pg.wait_for_timeout(1500)
    foto(pg, "codigo")
    texto = cel.inner_text(timeout=10000)
    if "trabalhador do recap" not in texto:
        log(f"{email}: o código NÃO entrou na célula (foco em outro lugar) — não rodo. Ver o print 'codigo'.")
        return
    cel.locator("colab-run-button, .cell-execution").first.click(timeout=10000)
    log(f"{email}: célula rodando (trabalhador colab_{apelido}, fila de teste)")
    t0 = time.time()
    while not PARAR.exists():
        clicar_avisos(pg)
        if time.time() - t0 < 600 or int(time.time() - t0) % 1800 < 240:
            foto(pg, "vivo")
        try:
            pg.mouse.move(400, 300)
            pg.mouse.wheel(0, 1)
        except Exception as e:  # noqa: BLE001
            log(f"aba caiu? {type(e).__name__}: {str(e)[:100]}")
            break
        time.sleep(240)
    log(f"{email}: fim do vigia (PARAR ou aba caiu)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "filmescomia1")
