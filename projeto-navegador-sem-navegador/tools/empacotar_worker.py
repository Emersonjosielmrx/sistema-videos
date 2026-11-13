# -*- coding: utf-8 -*-
r"""tools/empacotar_worker.py — monta dist\nsn_worker\: a parte do nsn que roda NOS NOTEBOOKS / PC2 / desktop com os
cookies DELES (dona 29/10: "cada PC tem seus próprios cookies, cada um faz suas postagens com eles"; regra: nunca copiar
cookies entre máquinas). Vai só código + modelos_ig.json (doc_ids das consultas, SEM fb_dtsg/lsd/jazoest/av/__user) +
colher.py (lê os cookies do Chrome LOCAL da máquina pela porta CDP 9460 do chrome_conta.py, sem Playwright).
Desde 29/10 (D30) vai também o Flow/Veo por HTTP (services/veo_flow): o vídeo do Veo é gerado NA máquina, com o Chrome
dela aberto só para o token do reCAPTCHA.

    python tools\empacotar_worker.py            # gera dist\nsn_worker (D23 em FABLE_DECISOES.md)

Na máquina: ~/postador-worker/nsn/ (Linux) ou C:\postador-worker\nsn (Windows). Precisa: python3 + curl_cffi +
websocket-client. Quem instala/atualiza: python bin\maquina_remota.py instalar-nsn (postador-de-videos).
"""
import json
import shutil
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "nsn_worker"
SEGREDOS = {"fb_dtsg", "lsd", "jazoest", "av", "__user", "__csr", "__hsi", "__spin_r", "__spin_t", "__spin_b", "__s",
            "__hs", "__hsdp", "__req", "__rev", "__dyn", "__sjsp", "__ccg"}
ARQUIVOS = ["core/cofre_cookies.py", "core/arquivo.py", "core/cdp_aba.py", "services/instagram/web.py", "services/instagram/postar.py",
            # 29/10 (D30): Flow/Veo por HTTP nas máquinas — o Chrome de lá só fabrica o token do reCAPTCHA
            "services/veo_flow/flow_http.py", "services/veo_flow/flow_gerar.py", "services/veo_flow/saude_flow.py",
            # 29/10 (D31, dona: "tudo isso tem que rodar em todos os notebooks e PCs"): o resto do nsn também —
            # carrossel/story/perfil/DM/comentários (postar.py), robô QUERO, Google Fotos, leitura do Instagram
            # (30/10: core/auth.py, core/session.py e os client.py antigos foram para legado/ — ninguém usava)
            "config.py", "core/maquinas.py", "services/google_photos/fotos_http.py", "tools/quero.py"]
PACOTES = ("core", "services", "services/instagram", "services/veo_flow", "services/google_photos", "tools")

COLHER = r'''# -*- coding: utf-8 -*-
"""colher.py — grava cookies/cofre_<perfil>.json a partir do Chrome LOCAL desta máquina (porta CDP do chrome_conta.py).
Sem Playwright: só websocket. Uso: python3 colher.py <perfil> [porta=9460] [url=https://www.instagram.com/]
Os cookies não saem desta máquina; o PC1 só manda este comando por ssh."""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from core.cdp_aba import Aba  # noqa: E402


def main():
    perfil = sys.argv[1]
    porta = int(sys.argv[2]) if len(sys.argv) > 2 else 9460
    url = sys.argv[3] if len(sys.argv) > 3 else "https://www.instagram.com/"
    urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=5)  # Chrome aberto?
    aba = Aba.da_porta(porta, nova=url)
    try:
        time.sleep(6)
        ua = aba.chamar("Browser.getVersion")["userAgent"].replace("HeadlessChrome", "Chrome")
        todos = aba.chamar("Network.getAllCookies")["cookies"]
    finally:
        aba.fechar(fechar_aba=True)
    d = {"perfil": perfil, "ua": ua, "quando": time.strftime("%Y-%m-%d %H:%M"), "maquina": "local",
         "cookies": [{k: c[k] for k in ("name", "value", "domain", "path")} for c in todos]}
    (ROOT / "cookies").mkdir(exist_ok=True)
    arq = ROOT / "cookies" / f"cofre_{perfil}.json"
    arq.with_suffix(".tmp").write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    arq.with_suffix(".tmp").replace(arq)
    tem = any(c["name"] == "sessionid" and "instagram" in c["domain"] for c in todos)
    google = any(c["name"] in ("SID", "__Secure-1PSID") and "google.com" in c["domain"] for c in todos)
    print(f"COLHIDO {perfil} cookies={len(todos)} instagram_logado={tem} google_logado={google}")


if __name__ == "__main__":
    main()
'''


def modelos_sem_segredos():
    sys.path.insert(0, str(ROOT))
    from services.instagram.web import _modelos
    out = {}
    for nome, q in _modelos().items():
        out[nome] = {k: v for k, v in q.items() if k not in SEGREDOS}
    return out


def imports_faltando():
    """30/10: módulo do projeto importado por um arquivo do pacote mas fora de ARQUIVOS = worker quebra lá no
    ModuleNotFoundError (só aparece na máquina, por ssh). Confere antes de montar."""
    import re
    faltam = set()
    for rel in ARQUIVOS:
        for m in re.finditer(r"^\s*(?:from|import)\s+((?:core|services|tools|relatorios)(?:\.\w+)+|config)\b",
                             (ROOT / rel).read_text("utf-8"), re.M):
            mod = m.group(1).replace(".", "/") + ".py"
            if mod not in ARQUIVOS and not (ROOT / mod.replace(".py", "")).is_dir():
                faltam.add(f"{rel} -> {mod}")
    return sorted(faltam)


def main():
    falta = imports_faltando()
    if falta:  # import dentro de função (ex.: tiktok, catalogo) também conta: melhor parar do que mandar quebrado
        raise SystemExit("pacote incompleto:\n  " + "\n  ".join(falta))
    if DIST.exists():
        try:
            shutil.rmtree(DIST)
        except PermissionError as ex:  # 30/10: terminal/explorer aberto dentro de dist\ prende a pasta no Windows
            raise SystemExit(f"não consegui apagar {DIST} (pasta aberta em outro programa/terminal?): {ex}")
    for rel in ARQUIVOS:
        dst = DIST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    for pk in PACOTES:
        (DIST / pk / "__init__.py").write_text("", "utf-8")
    (DIST / "saida").mkdir()  # mp4 gerados pelo Flow HTTP até o PC1 buscar (fora de entrada/, que o chrome_conta limpa)
    (DIST / "modelos_ig.json").write_text(json.dumps(modelos_sem_segredos(), ensure_ascii=False, indent=1), "utf-8")
    (DIST / "colher.py").write_text(COLHER, "utf-8")
    (DIST / "cookies").mkdir()
    (DIST / "LEIA.md").write_text(
        "# nsn_worker\n\nParte do projeto-navegador-sem-navegador que roda nesta máquina com os cookies DELA.\n"
        "- `python3 colher.py <perfil> 9460` grava cookies/cofre_<perfil>.json do Chrome local (chrome_conta.py).\n"
        "- `python3 -m services.instagram.postar reel <conta> <video> \"legenda\"` posta o Reel por HTTP.\n"
        "- `python3 -m services.veo_flow.flow_gerar --porta 9460 --projeto <url> --nome <perfil> --fechar-chrome video "
        "@prompt.txt saida.mp4` gera o vídeo do Veo por HTTP (o Chrome aberto pelo PC1 só fabrica o token do reCAPTCHA "
        "e é fechado assim que o Flow aceita o pedido).\n"
        "- `python3 -m services.veo_flow.saude_flow` diz quais perfis estão logados no Flow e no Instagram (por HTTP, sem Chrome).\n"
        "- (D31) Qualquer outro módulo (postar carrossel/story/perfil, tools/quero.py, google_photos/fotos_http.py, "
        "instagram/web.py) roda aqui com os cookies daqui quando o PC1 manda (`maquina_remota.Remoto.nsn_run`).\n"
        "- Nunca copie a pasta cookies/ para outra máquina.\n", "utf-8")
    n = sum(1 for _ in DIST.rglob("*") if _.is_file())
    print(f"dist pronto: {DIST} ({n} arquivos)")
    # sanidade: nenhum segredo no pacote
    txt = "".join(p.read_text("utf-8", errors="ignore") for p in DIST.rglob("*.json"))
    for s in ("fb_dtsg", "sessionid", "csrftoken"):
        assert s not in txt, f"segredo {s} vazou no pacote"
    print("sem segredos: ok")


if __name__ == "__main__":
    main()
