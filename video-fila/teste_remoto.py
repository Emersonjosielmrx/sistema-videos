r"""teste_remoto.py — roda um TESTE fora do PC1 (dona 15/11: "sempre que for possível fazer o teste em outro PC e mandar
pra esse já feito — imagem/vídeo no Flow, treinamento etc.; mas não é impossível usar este PC: analisar a fila antes, ver
se é preciso e avisar").

    python teste_remoto.py --tipo render  -- <comando>          # ffmpeg, render de Short, efeito, montagem
    python teste_remoto.py --tipo python  -- <comando>          # script Python qualquer (sem conta/cofre)
    python teste_remoto.py --tipo pesado  -- <comando>          # treino de voz, whisper, demucs (precisa CPU forte)
    python teste_remoto.py --listar                              # quem está livre agora pra cada tipo
    opções: --arquivos a,b (sobe antes), --trazer x,y (baixa depois), --maquina desktop (força), --pc1 (força aqui)

Escolhe a 1ª máquina OCIOSA (maquinas.medir) na ordem do tipo; nenhuma livre = diz quem está ocupada e por quê e só
roda no PC1 com --pc1 (a decisão fica com quem chamou). 1 ssh por teste (regra: sem rajada). NÃO serve para o que fala
como conta (Chrome do cofre, TikTok, YouTube, Kaggle): isso continua pelo caminho da conta (saída fixa).
Flow/imagem já roda fora do PC1 pela fila do Flow (D:\flow-imagens\cliente.gerar escolhe a máquina).
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
# ordem de preferência por tipo (mais forte primeiro). HP Pavilion sem SSE4.2/AVX: só ffmpeg/python puro.
ORDEM = {
    "render": ["desktop", "sti", "hp", "x200ma", "asus"],
    "python": ["desktop", "sti", "hp", "x200ma", "asus", "acer"],
    "pesado": ["desktop", "sti"],
}
# pasta de trabalho de teste em cada máquina (Windows usa D:\tmp; Linux ~/teste_remoto)
DIR = {"desktop": "D:/tmp/teste_remoto"}


def livres(tipo):
    """Ocupação pela medida de 1 em 1 min do uso_maquinas.py (estado/uso_maquinas.jsonl) — sem abrir ssh em cada
    máquina (regra: sem rajada). Medida com mais de 15 min = desconhecida (não usa)."""
    import json
    from datetime import datetime
    ult = {}
    try:
        with open(AQUI / "estado" / "uso_maquinas.jsonl", encoding="utf-8") as f:
            for linha in f.readlines()[-400:]:
                try:
                    r = json.loads(linha)
                    ult[r["m"]] = r
                except (ValueError, KeyError):
                    pass
    except OSError:
        pass
    out = []
    for h in ORDEM[tipo]:
        r = ult.get(h)
        if not r:
            out.append((h, False, "sem medida"))
            continue
        idade = (datetime.now() - datetime.fromisoformat(r["t"])).total_seconds() / 60
        if idade > 15:
            out.append((h, False, f"medida velha ({idade:.0f} min)"))
        elif r.get("trab") or (r.get("cpu") or 0) > 60:
            out.append((h, False, f"{r.get('fazendo', '?')[:50]} (CPU {r.get('cpu')}%)"))
        else:
            out.append((h, True, f"livre (CPU {r.get('cpu')}%)"))
    return out


def _alvo(h):
    if h == "acer":
        return "emerson-ia@100.98.55.125"
    return h


def rodar(h, cmd, arquivos, trazer):
    pasta = DIR.get(h, "~/teste_remoto")
    alvo = _alvo(h)
    subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", alvo,
                    f"mkdir -p {pasta}" if h != "desktop" else f"New-Item -ItemType Directory -Force {pasta} | Out-Null"],
                   capture_output=True, timeout=60)
    for a in arquivos:
        subprocess.run([SCP, "-q", a, f"{alvo}:{pasta}/"], check=True, timeout=1800)
    t0 = time.time()
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", alvo,
                        f"cd {pasta}; {cmd}"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"[{h}] rc={r.returncode} em {time.time() - t0:.0f} s", flush=True)
    print((r.stdout or "")[-4000:])
    if r.stderr:
        print((r.stderr or "")[-1500:], file=sys.stderr)
    destino = Path(r"D:\tmp\teste_remoto") / h
    for x in trazer:
        destino.mkdir(parents=True, exist_ok=True)
        subprocess.run([SCP, "-q", f"{alvo}:{pasta}/{x}", str(destino)], timeout=1800)
        print(f"trazido: {destino / Path(x).name}")
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", choices=list(ORDEM), default="python")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--maquina")
    ap.add_argument("--pc1", action="store_true")
    ap.add_argument("--arquivos", default="")
    ap.add_argument("--trazer", default="")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    if a.listar:
        for t in ORDEM:
            print(f"{t}: " + " | ".join(f"{h} {'LIVRE' if ok else 'ocupada'} ({mot})" for h, ok, mot in livres(t)))
        return 0
    cmd = " ".join(x for x in a.cmd if x != "--")
    arquivos = [x for x in a.arquivos.split(",") if x]
    trazer = [x for x in a.trazer.split(",") if x]
    if a.pc1:
        print("rodando NO PC1 (--pc1: quem chamou decidiu que precisa)", flush=True)
        return subprocess.run(cmd, shell=True).returncode
    if a.maquina:
        return rodar(a.maquina, cmd, arquivos, trazer)
    st = livres(a.tipo)
    for h, ok, _ in st:
        if ok:
            return rodar(h, cmd, arquivos, trazer)
    print("NENHUMA máquina livre para '" + a.tipo + "': " + "; ".join(f"{h}: {m}" for h, _, m in st))
    print("-> espere, force uma com --maquina <nome>, ou rode aqui com --pc1 se for urgente (e avise a dona).")
    return 3


if __name__ == "__main__":
    sys.exit(main())
