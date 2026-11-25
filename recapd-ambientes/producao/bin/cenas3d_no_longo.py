"""23/11 dona: 3D recortado (aprovado) com sentido na história, em cima do longo pronto.
  python cenas3d_no_longo.py <pid_da_fila> [n_cenas]
PC1 (leve): baixa só o roteiro.txt, a IA escolhe os momentos (cenas3d_historia) e monta os storyboards.
DESKTOP (pesado, regra "PC1 livre"): 2 conexões ssh, sem rajada —
  1ª: renderiza as cenas (kit3d), baixa o final_anime_deitado.mp4 do Drive e devolve a duração;
  2ª: ffmpeg encaixa cada cena recortada (fundo magenta) no canto, ~4,4 s a partir da frase, sobe
      <pid>/final_com_3d.mp4 no Drive e apaga o vídeo local (o desktop tem pouco disco).
Tempo da frase = proporção do texto no vídeo (aproximado; o resumo de abertura conta junto)."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cenas3d_historia  # noqa: E402

R = r"D:\tools\rclone.exe"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
F = "manhwa-drive:colab_recap"
KIT = Path(r"D:\kit3d-producao")
FF = r"D:\ferramentas\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
REM = "D:/tmp/kit3d/prod"
RCL_DESK = r"D:\tools\rclone.exe"


def rc(*a, t=3600):
    return subprocess.run([R, *a], capture_output=True, text=True, timeout=t, encoding="utf-8", errors="replace")


def remoto(ps_texto, nome, t=7200):
    ps = Path(r"D:\tmp") / nome
    ps.write_text(ps_texto, encoding="utf-8")
    subprocess.run([SCP, "-q", str(ps), "desktop:D:/tmp/"], check=True, timeout=600)
    r = subprocess.run([SSH, "desktop", f"powershell -ExecutionPolicy Bypass -File D:/tmp/{nome}"],
                       capture_output=True, text=True, timeout=t, encoding="utf-8", errors="replace")
    return r.stdout or ""


def main(pid, n=None):
    W = Path(r"D:\tmp\cenas3d_longo") / pid
    W.mkdir(parents=True, exist_ok=True)
    rc("copyto", f"{F}/fila/{pid}/roteiro.txt", str(W / "roteiro.txt"), t=600)
    linhas = [l.strip() for l in (W / "roteiro.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    cj = W / "cenas3d.json"
    cenas = json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else cenas3d_historia.gerar(linhas, W, n)
    print(f"{len(cenas)} cenas escolhidas", flush=True)
    for c in cenas:
        d = KIT / "projects" / f"_l3_{c['pasta']}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "storyboard.json").write_text((W / "cenas3d" / c["pasta"] / "storyboard.json").read_text(encoding="utf-8"),
                                           encoding="utf-8")
    tar = Path(r"D:\tmp\k3_l3.tar")
    subprocess.run(["tar", "-cf", str(tar), "-C", str(KIT / "projects")] + [f"_l3_{c['pasta']}" for c in cenas],
                   check=True)
    subprocess.run(["tar", "-rf", str(tar), "-C", str(KIT), "engine/player.js", "engine/player.css"], check=True)
    subprocess.run([SCP, "-q", str(tar), "desktop:D:/tmp/"], check=True, timeout=900)
    nomes = ",".join(f'"_l3_{c["pasta"]}"' for c in cenas)
    # 23/11: o rclone do desktop aponta pra outra conta (lá "manhwa-drive" = outra raiz): o vídeo vem do Drive pro
    # PC1 (só cópia, sem render) e vai pro desktop por scp; a saída faz o caminho de volta
    loc = W / "final.mp4"
    if not loc.exists():
        rc("copyto", f"{F}/fila_src/{pid}/final_anime_deitado.mp4", str(loc), t=7200)
    if not loc.exists():
        print("não baixou o final do Drive"); return
    remoto('New-Item -ItemType Directory -Force D:/tmp/l3 | Out-Null\n"ok"\n', "k3_l3_mk.ps1", t=120)
    try:
        subprocess.run([SCP, "-q", str(loc), "desktop:D:/tmp/l3/final.mp4"], check=True, timeout=7200)
    finally:
        # 24/11 (dona: "vídeo grande não fica no PC, só o link no Drive"): o original está em {F}/fila_src/{pid};
        # a cópia de 5 GB no PC1 só serve de ponte pro desktop -> sai assim que o scp termina (ou falha)
        loc.unlink(missing_ok=True)
    out = remoto(
        f'$env:PATH = "{FF};" + $env:PATH\n'
        f'Set-Location {REM}\n'
        f'New-Item -ItemType Directory -Force D:/tmp/l3 | Out-Null\n'
        f'tar -xf D:/tmp/k3_l3.tar -C projects\n'
        f'Copy-Item -Force projects/engine/player.js engine/player.js\n'
        f'Copy-Item -Force projects/engine/player.css engine/player.css\n'
        f'foreach ($n in {nomes}) {{ cmd /c "node tools/render.mjs projects/$n 2>&1" | Select-Object -Last 1 }}\n'
        f'"DUR=" + (ffprobe -v error -show_entries format=duration -of csv=p=0 D:/tmp/l3/final.mp4)\n'
        f'"ALT=" + (ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 D:/tmp/l3/final.mp4)\n',
        "k3_l3_a.ps1")
    print(out[-1500:], flush=True)
    try:
        total = float(next(l for l in out.splitlines() if l.startswith("DUR=")).split("=", 1)[1])
        alt = int(next(l for l in out.splitlines() if l.startswith("ALT=")).split("=", 1)[1])
    except (StopIteration, ValueError):
        print("desktop não baixou o vídeo / não mediu"); return
    tot = sum(len(l) for l in linhas) or 1
    inicio, acc = [], 0
    for l in linhas:
        inicio.append(total * acc / tot)
        acc += len(l)
    ok = [c for c in cenas if f"_l3_{c['pasta']}" in out or "Pronto" in out]
    entradas = ['-i', 'D:/tmp/l3/final.mp4']
    filtro, ult = [], "0:v"
    for k, c in enumerate(ok):
        entradas += ['-i', f'{REM}/projects/_l3_{c["pasta"]}/render/video.mp4']
        ini = max(0.5, inicio[c["frase_i"]] + 0.3)
        x = "W-w-20" if k % 2 == 0 else "20"
        filtro.append(f"[{k + 1}:v]fps=30,crop=1200:1000:360:0,colorkey=0xff00ff:0.30:0.10,scale=-1:{int(alt * 0.42)},"
                      f"setpts=PTS-STARTPTS+{ini:.2f}/TB[c{k}]")
        filtro.append(f"[{ult}][c{k}]overlay=x={x}:y=H-h-{int(alt * 0.23)}:eof_action=pass:"
                      f"enable='between(t,{ini:.2f},{ini + 4.4:.2f})'[o{k}]")
        ult = f"o{k}"
        c["inicio_s"] = round(ini, 1)
        print(f"  {int(ini // 60)}:{ini % 60:04.1f} {c['tipo']} {c.get('texto')} | {c['frase'][:70]}", flush=True)
    (W / "cenas3d_tempos.json").write_text(json.dumps(ok, ensure_ascii=False, indent=1), encoding="utf-8")
    (W / "filtro.txt").write_text(";".join(filtro), encoding="utf-8")
    subprocess.run([SCP, "-q", str(W / "filtro.txt"), "desktop:D:/tmp/l3/"], check=True, timeout=300)
    args = " ".join(f'"{a}"' if a != "-i" else a for a in entradas)
    out = remoto(
        f'$env:PATH = "{FF};" + $env:PATH\n'
        f'ffmpeg -v error -y {args} -filter_complex_script D:/tmp/l3/filtro.txt -map "[{ult}]" -map "0:a?" '
        f'-c:v libx264 -preset veryfast -crf 21 -c:a copy D:/tmp/l3/final_com_3d.mp4\n'
        f'if (Test-Path D:/tmp/l3/final_com_3d.mp4) {{ "FEITO" }}\n',
        "k3_l3_b.ps1", t=4 * 3600)
    print(out[-800:])
    if "FEITO" in out:
        saida = W / "final_com_3d.mp4"
        subprocess.run([SCP, "-q", "desktop:D:/tmp/l3/final_com_3d.mp4", str(saida)], check=True, timeout=7200)
        r_ = rc("copyto", str(saida), f"{F}/fila_src/{pid}/final_com_3d.mp4", t=7200)
        if r_.returncode == 0:
            print("PRONTO", f"{F}/fila_src/{pid}/final_com_3d.mp4")
            saida.unlink(missing_ok=True)
            loc.unlink(missing_ok=True)
    remoto('Remove-Item -Force D:/tmp/l3/final.mp4, D:/tmp/l3/final_com_3d.mp4 -ErrorAction SilentlyContinue\n"limpo"\n',
           "k3_l3_rm.ps1", t=120)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
