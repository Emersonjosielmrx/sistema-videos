# -*- coding: utf-8 -*-
"""instalar_pc3.py — instala o Cortes (Shorts de parceiro COM voz clonada) no DESKTOP (PC3) (dono 24/10/2026:
"faça a instalação no PC3"; kanban das Máquinas: arrastar Cortes pro PC3).

Mesmo desenho do PC2 (C:\\recapd-e-animes + C:\\hipercool-materiais, o PC1 escolhe o vídeo e baixa a fonte; o PC3
NUNCA usa yt-dlp: mesmo IP da casa), mais o que o PC2 não tem: a voz clonada (Applio/RVC no venv_vozes, modelos-base e
as vozes). O PC3 tem um D: de verdade (do dono), então no lugar do "subst D: C:\\" do PC2 entram 2 junções no D:
(D:\\hipercool-materiais e D:\\recapd-ambientes\\producao -> C:\\...), e os caminhos fixos do código valem iguais.
Nada do dono é apagado; cada passo pode ser repetido (copia por cima).

    python instalar_pc3.py            # tudo
    python instalar_pc3.py <passo>    # só um: pastas, codigo, segredos, voz, vozes, modelos, assets, venv, testar
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transferencias  # noqa: E402  (_ps_remoto)

HOST = "desktop"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
TAR = r"C:\Windows\System32\tar.exe"
LOG = Path(__file__).resolve().parent / "logs" / "instalar_pc3.log"
PROD = Path(r"D:\recapd-ambientes\producao")
MAT = Path(r"D:\hipercool-materiais")
R_PROD = "C:/recapd-e-animes"
R_MAT = "C:/hipercool-materiais"
# o código do Cortes é 3.13 (PC1 e PC2); o PC3 só tinha 3.11 — leva a instalação do PC1 (portátil, sem site-packages)
PY313_LOCAL = Path(r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313")
PY_PC3 = r"C:\hipercool-materiais\python\Python313\python.exe"
PARCEIROS = ["porao", "drezin", "mike", "mattz", "ijax", "momo", "pie", "mangaticos", "guugou", "omelhormanhwa",
             "kkvirjao", "doinsuka", "solem8037", "jubertim", "iki", "solemsun"]
N_PERSONAGENS = 10  # os de melhor nota média no narradores_nichos.json (os 74 passariam de 8 GB)
ASSETS = ["fonts", "generated_batch", "mascote", "mascote_mov", "memes_img", "overlays", "sfx", "sfx_extras", "sfx_foley",
          "sfx_memes", "sfx_prioridade", "trilhas", "_divisorias", "_downloads_vfx"]  # o mesmo conjunto do PC2
SEGREDOS = ["elevenlabs_keys.json", "elevenlabs_keys_hipercool.json", "el_proxies.txt", "gemini_keys.json",
            "gemini_keys_pc2.json", "groq_keys.json", "omniroute.json", "omniroute_key.txt", "proxies.txt",
            "sightengine.json", "cohere_keys.json", "deepinfra_keys.json", "fireworks_keys.json", "novita_keys.json",
            "pollinations.json", "siliconflow.json", "together_keys.json", "zai.json"]  # só chave de API: sem cookie/conta
PACOTES = ["edge-tts", "numpy", "opencv-python-headless", "pillow", "psutil", "tabulate", "aiohttp", "requests", "tzdata"]
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ps(script, timeout=1800):
    rc, txt = transferencias._ps_remoto(HOST, script, timeout=timeout)
    if rc != 0:
        raise RuntimeError(f"PC3 rc={rc}: {txt[-400:]}")
    return txt


def mandar(origem, itens, destino, excluir=()):
    """tar daqui -> ssh -> tar de lá (cmd /c: o PowerShell do PC3 estraga stdin binário)."""
    ini = time.time()
    exc = [f"--exclude={e}" for e in excluir]
    t = subprocess.Popen([TAR, "-cf", "-", *exc, "-C", str(origem), *itens], stdout=subprocess.PIPE,
                         creationflags=_SEM_JANELA)
    # 26/10: o shell do ssh do PC3 alterna entre cmd e PowerShell; aspas aninhadas quebravam nos dois. Destinos sem espaço
    # vão sem aspas internas (vale nos dois shells)
    win = destino.replace("/", "\\")
    cmd = (f'cmd /c "mkdir {win} 2>nul & tar -xf - -C {destino}"' if " " not in destino
           else f'cmd /c "if not exist "{destino}" mkdir "{destino}" & tar -xf - -C "{destino}""')
    r = subprocess.run([SSH, "-o", "BatchMode=yes", HOST, cmd],
                       stdin=t.stdout, capture_output=True, timeout=6 * 3600, creationflags=_SEM_JANELA)
    t.stdout.close()
    ok = t.wait() == 0 and r.returncode == 0
    log(f"  {'ok' if ok else 'FALHOU'} {origem} [{', '.join(itens)[:120]}] -> {destino} ({time.time() - ini:.0f} s)"
        + ("" if ok else f" {(r.stderr or b'').decode('utf-8', 'replace')[-300:]}"))
    if not ok:
        raise RuntimeError(f"cópia falhou: {origem} -> {destino}")


def passo_pastas():
    log("pastas e junções no PC3")
    print(ps(r"""
New-Item -ItemType Directory -Force C:\hipercool-materiais, C:\recapd-e-animes\logs, C:\recapd-e-animes\workspace\anime, 'C:\hipercool-materiais\animes recap\shorts', C:\hipercool-materiais\videos_voz_clonada, C:\hipercool-materiais\anime, D:\recapd-ambientes | Out-Null
foreach ($j in @(@('D:\hipercool-materiais','C:\hipercool-materiais'), @('D:\recapd-ambientes\producao','C:\recapd-e-animes'),
                  @('C:\pc3_shorts','C:\hipercool-materiais\animes recap\shorts'))) {
  if (-not (Test-Path $j[0])) { cmd /c mklink /J $j[0] $j[1] | Out-Null }
  "{0} -> {1}" -f $j[0], (Get-Item $j[0]).Target
}
"""))


def passo_codigo():
    log("código: bin + config do Cortes, bin/comum do hipercool-materiais")
    nomes = [p.name for p in (PROD / "bin").iterdir() if p.is_file()
             and (not p.name.startswith("_") or p.name == "_whisper_sub.py")  # 26/10: o Whisper roda por ele
             and ".bak" not in p.name and ".bkp" not in p.name and p.suffix in (".py", ".json", ".ps1", ".bat")]
    mandar(PROD / "bin", nomes, f"{R_PROD}/bin")
    mandar(PROD, ["config"], R_PROD, excluir=["*.bak*"])
    mandar(MAT, ["bin", "comum"], R_MAT, excluir=["__pycache__", "*.bak*", "*.bkp*"])
    mandar(Path(__file__).resolve().parent, ["pc3_parceiro.ps1"], f"{R_PROD}/bin")


def passo_segredos():
    log("segredos (só chaves de API)")
    mandar(PROD / "secrets", [s for s in SEGREDOS if (PROD / "secrets" / s).exists()], f"{R_PROD}/secrets")


def passo_voz():
    log("voz clonada: runtime 3.11.15 + venv_vozes + Applio (sem a junção rvc) + modelos-base do RVC")
    mandar(MAT / "python", ["runtimes", "venv_vozes"], f"{R_MAT}/python", excluir=["__pycache__"])
    # 26/10: applio\rvc é o CÓDIGO do RVC (lib, infer...); só applio\rvc\models é junção pros modelos. Antes a junção ia
    # na pasta rvc inteira e o RVC não abria ("No module named 'rvc.lib'")
    print(ps(r"""
$j = 'C:\hipercool-materiais\tools\applio\rvc'
if ((Test-Path $j) -and (Get-Item $j).LinkType) { cmd /c rmdir $j }
"""))
    mandar(MAT / "tools", ["applio"], f"{R_MAT}/tools", excluir=["applio/rvc/models", "applio/logs", "__pycache__"])
    mandar(MAT / "models" / "rvc", ["embedders", "formant", "predictors", "pretraineds"], f"{R_MAT}/models/rvc")
    mandar(MAT / "amostras_voz", ["clone2"], f"{R_MAT}/amostras_voz", excluir=["*.wav", "*.mp3", "__pycache__"])
    print(ps(r"""
$j = 'C:\hipercool-materiais\tools\applio\rvc\models'
if (-not (Test-Path $j)) { cmd /c mklink /J $j C:\hipercool-materiais\models\rvc | Out-Null }
New-Item -ItemType Directory -Force C:\hipercool-materiais\python\tmp | Out-Null
"applio\rvc\models -> " + (Get-Item $j).Target
"""))


def personagens_escolhidos():
    enc = json.loads((PROD / "config" / "narradores_nichos.json").read_text(encoding="utf-8"))
    vozes = MAT / "models" / "rvc" / "vozes"
    nota = {}
    for v, d in enc.items():
        if v.startswith("_") or v in PARCEIROS or v in ("lula", "bolsonaro") or not isinstance(d, dict):
            continue
        if (vozes / v / "personagem.json").exists() and (vozes / v / f"{v}.pth").exists():
            ns = [x for x in d.values() if isinstance(x, (int, float))]
            nota[v] = sum(ns) / len(ns) if ns else 0
    return sorted(nota, key=lambda v: -nota[v])[:N_PERSONAGENS]


def passo_vozes():
    escolha = PARCEIROS + personagens_escolhidos()
    log(f"vozes: {len(escolha)} ({', '.join(escolha)})")
    mandar(MAT / "models" / "rvc" / "vozes", [v for v in escolha if (MAT / "models" / "rvc" / "vozes" / v).exists()],
           f"{R_MAT}/models/rvc/vozes", excluir=[".ultimo_uso"])


def passo_modelos():
    log("modelos: kokoro, huggingface, depth-anything")
    mandar(MAT / "models", ["kokoro", "huggingface", "depth-anything-v2-small"], f"{R_MAT}/models")


def passo_assets():
    log("assets (o mesmo conjunto do PC2)")
    for a in ASSETS:
        if (MAT / "assets" / a).exists():
            mandar(MAT / "assets", [a], f"{R_MAT}/assets")


def passo_venv():
    log("venv do Cortes no PC3 (Python 3.13 levado do PC1 + os pacotes do PC2)")
    mandar(PY313_LOCAL.parent, ["Python313"], f"{R_MAT}/python", excluir=["Python313/Lib/site-packages/*", "__pycache__"])
    print(ps(rf"""
if (-not (Test-Path C:\recapd-e-animes\venv\Scripts\python.exe)) {{ & '{PY_PC3}' -m venv C:\recapd-e-animes\venv }}
& C:\recapd-e-animes\venv\Scripts\python.exe -m pip install --disable-pip-version-check -q {' '.join(PACOTES)} 2>&1 | Select-Object -Last 5
& C:\recapd-e-animes\venv\Scripts\python.exe -c "import edge_tts, cv2, numpy, PIL; print('venv ok')"
& D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe -c "import torch; print('venv_vozes ok, torch', torch.__version__)"
""", timeout=3600))


def passo_testar():
    log("teste: imports do pipeline no PC3")
    print(ps(r"""
$env:PATH = 'C:\hipercool-materiais\bin;' + $env:PATH
cd C:\recapd-e-animes\bin
& C:\recapd-e-animes\venv\Scripts\python.exe -X utf8 -c "import anime_auto, anime_tts, anime_voz_clonada as v; print('pipeline importa ok'); print('vozes no PC3:', len(v._ordem()))"
(Get-Command ffmpeg).Source
"livre C: {0:N1} GB" -f ((Get-PSDrive C).Free/1GB)
""", timeout=600))


PASSOS = {"pastas": passo_pastas, "codigo": passo_codigo, "segredos": passo_segredos, "voz": passo_voz,
          "vozes": passo_vozes, "modelos": passo_modelos, "assets": passo_assets, "venv": passo_venv,
          "testar": passo_testar}


FEITOS = Path(__file__).resolve().parent / "estado" / "instalar_pc3.json"


def _feitos():
    try:
        return json.loads(FEITOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ssh_ok():
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST, "hostname"], capture_output=True,
                       timeout=40, creationflags=_SEM_JANELA)
    return r.returncode == 0


def main():
    """--auto (tarefa InstalarPC3, a cada 15 min): faz os passos que faltam quando o ssh do PC3 deixa entrar — desde
    24/10 11:42 ele recusa a chave de vez em quando ("Permission denied"); passo feito não repete."""
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    auto = "--auto" in sys.argv
    pedidos = [a for a in sys.argv[1:] if a != "--auto"] or list(PASSOS)
    feitos = _feitos()
    if auto:
        pedidos = [p for p in PASSOS if p not in feitos]
        if not pedidos:
            return
        if not ssh_ok():
            log(f"auto: ssh do PC3 recusou — fica pra próxima (faltam {', '.join(pedidos)})")
            return
    for p in pedidos:
        try:
            PASSOS[p]()
        except Exception as e:  # noqa: BLE001
            log(f"[!] passo {p} falhou: {type(e).__name__}: {str(e)[:300]}")
            raise
        feitos[p] = datetime.now().isoformat(timespec="seconds")
        FEITOS.parent.mkdir(exist_ok=True)
        FEITOS.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
    log("fim: " + ", ".join(pedidos))


if __name__ == "__main__":
    main()
