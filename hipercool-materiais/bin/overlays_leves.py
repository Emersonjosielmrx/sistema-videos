r"""overlays_leves.py — versões DEITADAS e leves (1280x720, qtrle com alfa) dos overlays do hipercool pros vídeos
longos (dona 28/10: partículas e transições no longo sem atrasar). O original é ProRes 4444 12-bit 1080x1920: abrir
ele em cada trecho custava +135 s de CPU por minuto de vídeo (bench_efeitos). Saída:
D:\hipercool-materiais\assets\overlays_leves\<efeito>.mov. Roda 1x (pula o que já existe).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import elemental_transitions as el  # noqa: E402

SAIDA = Path(r"D:\hipercool-materiais\assets\overlays_leves")
FORA = {"blood", "mascot", "mascot_point", "mascot_surprise", "mascot_thumbsup"}  # sangue = risco de monetização


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    feitos = 0
    for nome, arq in el.ASSET_FILE.items():
        if nome in FORA or el.effect_cat(nome) not in (1, 2):
            continue
        src = el.ELEM_DIR / arq
        # VP9 com alfa (yuva420p): fogo 28,5 MB em qtrle -> 0,36 MB, abrir ~0,6 s de CPU (28/10). Quem lê tem que
        # abrir com "-c:v libvpx-vp9" ANTES do -i, senão o alfa some.
        out = SAIDA / f"{nome}.webm"
        if not src.exists() or out.exists():
            continue
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=1280:720,fps=30",
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "34", "-deadline",
                            "good", "-cpu-used", "4", "-an", str(out)], capture_output=True, text=True)
        print(f"{nome}: {'ok' if r.returncode == 0 else r.stderr[-200:]}", flush=True)
        feitos += r.returncode == 0
    print(f"{feitos} novos em {SAIDA}")


if __name__ == "__main__":
    main()
