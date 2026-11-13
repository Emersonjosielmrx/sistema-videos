# -*- coding: utf-8 -*-
"""Material REAL da MS Energy tirado do Google Fotos das contas do dono (dono 22/10/2026: "material real podemos
implementar uma busca no Google Fotos via navegador mesmo, tem varias contas logadas que tem fotos").

1. D:\\logins-google\\buscar_fotos_google.py busca pelo navegador do cofre (fabricadeautomacoesia, emersongenc,
   emersonjosiel649, emersonjosielmrx1995) e baixa para assets\\fotos_instagram\\google_fotos (videos em \\videos).
2. Cada foto entra no MESMO indice das fotos do Instagram (assets\\fotos_instagram\\indice.json, chave
   "google_fotos/<arquivo>"); print de celular (proporcao de tela de celular) ja sai marcado como ruim sem gastar visao.
3. baixar_fotos_insta.classificar() da o veredito por visao; roteiro_ms.fotos_boas() so usa foto real, sem rosto, sem
   texto/telefone e mostrando energia solar. Retomavel: rodar de novo so baixa/classifica o que falta.

    python fotos_google_ms.py [--sem-videos] [--so-classificar]
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baixar_fotos_insta as insta  # noqa: E402
from buscar_fotos_google import buscar  # noqa: E402

DESTINO = insta.DIR / "google_fotos"
BUSCAS = ["painel solar", "placa solar", "energia solar", "usina solar", "inversor solar", "telhado",
          # 24/10 (dono: "pegar todo o material possivel"): mais termos
          "solar", "fotovoltaico", "módulo solar", "instalação solar", "inversor", "estrutura telhado", "obra",
          # dono 24/10: "casa, predio, azul — tem muitas fotos com clientes"
          "casa", "prédio", "azul"]
DRIVE = "manhwa-drive:ms-energy/material_real"  # copia de tudo no Drive principal (dono 24/10)
RCLONE = r"D:\tools\rclone.exe"


def todas_contas():
    """Todo perfil Google do cofre (sem os de Instagram/TikTok/backup): o Fotos de cada um pode ter obra da MS Energy."""
    pasta = Path(r"D:\logins-google\cofre\perfis")
    return sorted((p.name for p in pasta.iterdir() if p.is_dir() and not p.name.startswith(("ig_", "_"))
                  and "__" not in p.name and ".bkp" not in p.name),
                  key=lambda n: (n != "contapessoal", n not in COM_FOTOS, n in POR_ULTIMO, n))  # pessoal, depois as que o dono disse ter fotos


# dono 24/10: "essas aqui sao as que tem" (busca comeca por elas)
COM_FOTOS = {"e4487017", "emersonjosiel1995", "fabricadeautomacoes0", "fabiovideoseducativos", "inovarecap",
             "emersonjosiel649", "emersonjosielmrx1995", "emersongencshin", "solarmundo195", "mundosolar1995",
             "en1653964", "aulasrevolution", "emersongenc"}
# dono 24/10: "essas deixe por ultimo"
POR_ULTIMO = {"filmescomia00", "jogoscomia", "canalalucinaai", "entrevistacomia", "jornalcomia", "canalhistoriacomia",
              "aulacomia", "comoseriasecomia"}


def subir_drive():
    """Copia fotos + videos + indices pro Drive principal (so o que falta; nunca apaga nada la)."""
    import subprocess
    r = subprocess.run([RCLONE, "copy", str(DESTINO), DRIVE, "--transfers", "4", "--stats-one-line", "--stats", "0"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"Drive {DRIVE}: {'ok' if r.returncode == 0 else 'ERRO ' + r.stderr[-300:]}")


PRAZO_CONTA_S = 45 * 60  # 24/10: a busca travou 2x sem erro numa conta e parou TODAS as outras


def _esperar_memoria(minimo_gb=1.5, espera_max_s=1200):
    """24/10 22:21: o Chrome caiu sem memoria ("RangeError: Failed to allocate memory") com o carrossel rodando junto."""
    try:
        import psutil
    except ImportError:
        return
    import time
    t0 = time.time()
    while psutil.virtual_memory().available / 2 ** 30 < minimo_gb and time.time() - t0 < espera_max_s:
        print(f"  memoria baixa ({psutil.virtual_memory().available / 2 ** 30:.1f} GB) — espero 60 s", flush=True)
        time.sleep(60)


def buscar_por_conta(contas, por_busca, videos, forcar=False):
    """Cada conta num processo proprio com prazo: travou = mata o processo E o Chrome daquela conta e segue."""
    import subprocess
    for conta in contas:
        _esperar_memoria()
        cmd = [sys.executable, "-u", r"D:\logins-google\buscar_fotos_google.py", "--destino", str(DESTINO),
               "--buscas", *BUSCAS, "--contas", conta, "--por-busca", str(por_busca)] + \
              (["--videos"] if videos else []) + (["--forcar"] if forcar else [])
        proc = subprocess.Popen(cmd)
        try:
            proc.wait(timeout=PRAZO_CONTA_S)
        except subprocess.TimeoutExpired:
            print(f"{conta}: passou de {PRAZO_CONTA_S // 60} min — encerro e sigo para a proxima", flush=True)
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { "
                            f"$_.CommandLine -match 'cofre\\\\perfis\\\\{conta}' }} | ForEach-Object {{ "
                            "Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                           capture_output=True, timeout=60)


def registrar():
    """Fotos baixadas -> indice.json das fotos (o que ja estiver la fica como esta)."""
    g = json.loads((DESTINO / "indice_google.json").read_text("utf-8")) if (DESTINO / "indice_google.json").exists() else {}
    ind = insta._carregar()
    novos = prints = 0
    for nome, it in g.items():
        chave = "<SEGREDO_REMOVIDO>" + nome
        if it.get("tipo") != "foto" or chave in ind or not (DESTINO / nome).exists():
            continue
        e = ind[chave] = {"data": it.get("data"), "tipo": "google_fotos", "conta": it.get("conta"), "busca": it.get("busca")}
        w, h = Image.open(DESTINO / nome).size
        if min(w, h) / max(w, h) < 0.5:  # 9:19,5 / 9:20 = print de tela de celular (foto de camera e 3:4 ou 9:16)
            e["visao"] = {"boa_para_video": False, "foto_real": False, "pre_filtro": "print de celular"}
            prints += 1
        novos += 1
    insta._salvar(ind)
    print(f"no indice: {novos} novas do Google Fotos ({prints} prints de celular descartados sem visao)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-videos", action="store_true")
    ap.add_argument("--so-classificar", action="store_true")
    ap.add_argument("--todas", action="store_true", help="todas as contas Google do cofre (padrao: as 4 de antes)")
    ap.add_argument("--por-busca", type=int, default=150)
    ap.add_argument("--depois-de", help="retoma a lista --todas depois desta conta (a busca travou nela)")
    ap.add_argument("--forcar", action="store_true", help="busca de novo termos ja feitos (progresso_busca.json)")
    a = ap.parse_args()
    if not a.so_classificar:
        contas = todas_contas() if a.todas else ["fabricadeautomacoesia", "emersongenc", "emersonjosiel649",
                                                  "emersonjosielmrx1995"]
        if a.depois_de in contas:
            contas = contas[contas.index(a.depois_de) + 1:]
        # 25/10: uma conta por processo, com prazo e espera de memoria (antes: tudo num processo so — travou 2x)
        buscar_por_conta(contas, a.por_busca, not a.sem_videos, forcar=a.forcar)
    # 25/10: classificar ANTES de subir pro Drive (a copia de 4 GB levou a madrugada inteira e segurava a classificacao)
    registrar()
    insta.classificar()
    subir_drive()
    sys.path.insert(0, r"D:\ms-energy\bin")
    import roteiro_ms
    gf = [n for n, _ in roteiro_ms.fotos_boas() if n.startswith("google_fotos/")]
    print(f"fotos do Google Fotos aprovadas para video/carrossel: {len(gf)} (total aprovadas: {len(roteiro_ms.fotos_boas())})")
