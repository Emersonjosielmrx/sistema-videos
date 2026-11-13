r"""
PC1: sobe o que a Colab precisa pro recap longo (plano: producao/COLAB_RECAP_LONGO.md).

  python montar_pacote.py           # código + config + chaves do render + assets (sync, só o que mudou)
  python montar_pacote.py --codigo  # só código/config/chaves (rápido)

Destino: manhwa-drive:colab_recap/raiz/<D|C>/... espelhando os caminhos do Windows (o sitecustomize.py da Colab
traduz D:\ → /content/raiz/D). A Colab baixa de lá com o baixar_drive.py. No manhwa-drive (manhwa-drive:colab_recap/)
vão o sitecustomize.py, o trabalhador.py, o baixar_drive.py e o notebook.
"""
import subprocess
import sys
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
AQUI = Path(__file__).resolve().parent
PRODUCAO = AQUI.parent
DESTINO = "manhwa-drive:colab_recap/raiz"
COLAB = "manhwa-drive:colab_recap"
FORA = ["_SNAPSHOT*/**", "_BACKUP*/**", "_snapshots/**", "*.bkp*", "*.bak*", "__pycache__/**", "*.pyc", "*.log"]
# 26/10: proxies.txt VAI (o Kaggle permite proxy; a Colab, que proibia, saiu de uso). Sem ele o edge bloqueava o IP do
# Kaggle depois de ~60 frases e o longo saía com 3 min (PFbu: 1334 frases puladas).
CHAVES = ["omniroute.json", "omniroute_key.txt", "gemini_estado.json", "gemini_keys.json", "claude_proxy.json",
          "proxies.txt"]
ASSETS = ["dividers", "emoji", "fonts", "hyperframes", "mascote", "mascote_mov", "mascote_viva", "memes_audio", "memes_img", "memes_series", "overlays_leves",
          "memes_png", "music", "overlays", "overlays_cache", "sfx", "sfx_extras", "sfx_foley", "sfx_memes",
          "sfx_prioridade", "trilhas", "_divisorias", "ai_cache"]
SOLTOS = [r"D:\hipercool-videos\config\repertorio_narrador.json", r"D:\hipercool-materiais\comum\reacoes.json",
          r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\impact.ttf", r"C:\Windows\Fonts\timesbd.ttf",
          r"C:\Windows\Fonts\arial.ttf"]


def _destino(caminho_win):
    p = str(caminho_win)
    return f"{DESTINO}/{p[0].upper()}/" + p[3:].replace("\\", "/")


def rc(*args):
    print(">", "rclone", *args[:3], flush=True)
    subprocess.run([RCLONE, *args, "--transfers", "8", "--checkers", "16", "--fast-list"], check=True)


def _carimbar_versao():
    """31/10 dona ("tem que ir por Telegram qual versão saiu pra eu conferir"): versão = hora deste envio + as mudanças
    de config/mudancas_longo.json; o kaggle_trabalhador copia pro pronto.json de cada longo."""
    import json
    from datetime import datetime
    try:
        m = json.loads((PRODUCAO / "config" / "mudancas_longo.json").read_text(encoding="utf-8")).get("mudancas", [])
    except (OSError, ValueError):
        m = []
    v = {"versao": datetime.now().strftime("%Y-%m-%d %H:%M"), "mudancas": m}
    (PRODUCAO / "config" / "versao_codigo.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    print("versão", v["versao"], f"({len(m)} mudanças)", flush=True)


def codigo():
    _carimbar_versao()
    fora = sum((["--exclude", f] for f in FORA), [])
    rc("sync", str(PRODUCAO / "bin"), _destino(PRODUCAO / "bin"), *fora)
    rc("sync", str(PRODUCAO / "config"), _destino(PRODUCAO / "config"), *fora)
    inc = sum((["--include", f] for f in CHAVES), [])
    rc("sync", str(PRODUCAO / "secrets"), _destino(PRODUCAO / "secrets"), *inc)
    for s in SOLTOS:
        if Path(s).exists():
            rc("copyto", s, _destino(s))
    subprocess.run([RCLONE, "deletefile", f"{COLAB}/rclone.conf"], capture_output=True)  # versão antiga levava o token
    # Na Colab nada de rclone (24/10 o curl|bash dele deu aviso de "código não permitido"): o baixar_drive.py usa a API
    # do Drive com o token de 1 h que o cliente.gravar_token põe no Drive da 649. Compartilhar a pasta não dá: o
    # manhwa-drive tem escopo drive.file (Google responde 403).
    for nome in ("sitecustomize.py", "trabalhador.py", "baixar_drive.py", "colab_recap.ipynb"):
        if (AQUI / nome).exists():
            rc("copyto", str(AQUI / nome), f"{COLAB}/{nome}")


def assets():
    base = Path(r"D:\hipercool-materiais\assets")
    for nome in ASSETS:
        if (base / nome).exists():
            rc("sync", str(base / nome), _destino(base / nome))
    # 02/11: a Maria MUDA no cartão de CURTIR (fx_subtitles.mascote_cta) usa as fotos recortadas — fora de assets\, não
    # subiam e no Kaggle o CTA saía sem ela (19 MB)
    rc("sync", r"D:\hipercool-materiais\mascote_waifu_v2\cosplay_recorte",
       _destino(Path(r"D:\hipercool-materiais\mascote_waifu_v2\cosplay_recorte")))
    # 02/11: transições em shader (realce_visual, outro chat) — os .glsl estavam só no PC: no Kaggle caía no xfade
    rc("sync", r"D:\hipercool-materiais\tools\gl-transitions",
       _destino(Path(r"D:\hipercool-materiais\tools\gl-transitions")))


if __name__ == "__main__":
    codigo()
    if "--codigo" not in sys.argv:
        assets()
    print("pacote ok")
