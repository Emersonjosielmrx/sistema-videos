"""amostras_drive.py — sobras de TREINO e TESTE de voz (amostras_voz) vão pro Drive depois de usadas (dona 25/10/2026:
"as amostras de voz também podem ser movidas; deixe os modelos que usamos, o treinamento não vamos repetir; mova
documentando e deixe o script pra mover sempre, só depois de usados").

Os modelos prontos (models\\rvc\\vozes\\<voz>\\<voz>.pth) não são tocados. FICAM no PC, porque a produção ainda lê:
  dataset_narradores (voz.wav/wavs: clone2, reacoes_reais/colheita, importar_kaggle), 2026-10-18_vozes_clonadas
  (STATUS/fila do voz_clonada), amostras_audio, clone2\\comparar_v1_v2/_calib/humano, reacoes_colheita,
  trechos_icones, formatos, kaggle_conversor (fora o teste e as saídas antigas) e todos os .md/.txt/.json/.py.
VÃO pro Drive (só mídia/pesos; textos e scripts ficam), quando a pasta está parada há DIAS dias:
  PASTAS abaixo. Cada arquivo enviado fica anotado no _NO_DRIVE.md da pasta (registro_drive.py).

    python amostras_drive.py subir [--simular]
    python amostras_drive.py trazer <caminho dentro de amostras_voz>   # pasta ou arquivo, volta do Drive
A faxina diária (D:\\video-fila\\faxina_disco.py) chama "subir" junto do vozes_drive e do fontes_drive.
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registro_drive  # noqa: E402

AMOSTRAS = Path(r"D:\hipercool-materiais\amostras_voz")
DRIVE = "manhwa-drive:videos-backup/hipercool-materiais/amostras_voz"
RCLONE = r"D:\tools\rclone.exe"
DIAS = 3
# experimento/treino já encerrado (o resultado que vale foi pro models\rvc\vozes): globs dentro de amostras_voz
PASTAS = ["kaggle_piloto/treino-*", "kaggle/treino-*", "dataset_v3/*", "clone2/fidelidade",
          "kaggle_conversor/teste_e2e", "kaggle_conversor/conversor-rvc-*", "referencias"]
FICA = {".md", ".txt", ".json", ".jsonl", ".py", ".ps1", ".bat", ".ipynb", ".log", ".err", ".csv", ".list"}


def _rclone(*args, timeout=3600):
    return subprocess.run([RCLONE, *args, "--retries", "3"], capture_output=True, text=True, timeout=timeout,
                          creationflags=0x08000000)


def _candidatas():
    for g in PASTAS:
        yield from (p for p in sorted(AMOSTRAS.glob(g)) if p.is_dir())


def subir(simular=False):
    lim, total, n = time.time() - DIAS * 86400, 0, 0
    for pasta in _candidatas():
        arqs = [f for f in pasta.rglob("*") if f.is_file()]
        if not arqs or max(f.stat().st_mtime for f in arqs) > lim:
            continue  # mexida há pouco: ainda em uso
        for f in arqs:
            if (f.suffix.lower() in FICA or f.suffix.lower() == ".pyc" or ".bak" in f.name
                    or f.name == registro_drive.ARQ):
                continue
            tam = f.stat().st_size
            destino = f"{DRIVE}/{f.relative_to(AMOSTRAS).as_posix()}"
            if simular:
                total, n = total + tam, n + 1
                continue
            try:
                r = _rclone("moveto", str(f), destino, timeout=600 + tam / 80e3)
            except subprocess.TimeoutExpired:  # Drive engasgado: fica no PC, a próxima faxina tenta de novo
                print(f"amostras_drive: {f.relative_to(AMOSTRAS)} demorou demais, fica pra próxima", flush=True)
                continue
            if r.returncode == 0 and not f.exists():
                registro_drive.anotar(f, destino, tam, "amostras_drive.py")
                total, n = total + tam, n + 1
            else:
                print(f"amostras_drive: {f.relative_to(AMOSTRAS)} não subiu ({(r.stderr or '')[-120:]})", flush=True)
    print(f"amostras_drive: {n} arquivo(s), {total / 1e9:.2f} GB {'iriam' if simular else 'foram'} pro Drive", flush=True)
    return total


def trazer(rel):
    """Traz de volta do Drive (pasta inteira ou um arquivo) pro mesmo lugar em amostras_voz."""
    rel = rel.replace("\\", "/").strip("/")
    local = AMOSTRAS / rel
    _rclone("copyto" if Path(rel).suffix else "copy", f"{DRIVE}/{rel}", str(local))  # com extensão = arquivo
    print(f"amostras_drive: {rel} {'voltou' if local.exists() else 'não achei no Drive'}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["subir"]:
        subir("--simular" in a)
    elif a[:1] == ["trazer"] and len(a) > 1:
        trazer(a[1])
    else:
        print(__doc__)
