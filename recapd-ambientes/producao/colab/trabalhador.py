"""Roda DENTRO da Colab (conta emersonjosiel649). Pega os pedidos de recap longo na pasta do Drive, faz com o mesmo
run_anime_task do worker do PC2 e devolve o vídeo pronto no Drive. Plano: producao/COLAB_RECAP_LONGO.md.

Pasta de cada pedido (o PC1 sobe, roteiro já feito lá): <FILA>/<id>/pedido.json + source.mp4 + roteiro.txt (+ json
pequenos da pasta de trabalho, ex. legenda_tempos.json). Aqui roda só o anime-pipeline.py (voz edge, efeitos, render).
Saída: final_anime_deitado.mp4 + pronto.json   |   erro.json (com o fim do log)
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FILA = Path("/content/drive/MyDrive/colab_recap/fila")
VIVO = FILA.parent / "vivo.json"
PRODUCAO = Path("/content/raiz/D/recapd-ambientes/producao")
TRABALHO = Path("/content/trabalho")


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _gravar(arq, dados):
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def _pegar(pasta):
    """Marca o pedido e confere se ficou só pra Colab (25/10: Kaggle e VPS pegaram o mesmo pedido no mesmo segundo).
    Mesmo jeito do kaggle_trabalhador._pegar: marca própria + em_andamento.json; outra marca mais antiga = desiste."""
    eu = {"desde": _agora(), "por": "colab"}
    _gravar(pasta / "em_andamento_colab.json", eu)
    _gravar(pasta / "em_andamento.json", eu)
    time.sleep(15)
    rivais = []
    for m in pasta.glob("em_andamento_*.json"):
        if m.name != "em_andamento_colab.json":
            try:
                d = json.loads(m.read_text(encoding="utf-8"))
                rivais.append((d.get("desde", ""), d.get("por", m.stem)))
            except (OSError, ValueError):
                rivais.append(("", m.stem))
    try:
        por = json.loads((pasta / "em_andamento.json").read_text(encoding="utf-8")).get("por")
    except (OSError, ValueError):
        por = "colab"
    if por and por != "colab" and not rivais:  # trabalhador antigo regravou depois de mim
        rivais.append(("", por))
    if any((d, p) < (eu["desde"], "colab") for d, p in rivais):
        print(f"[{_agora()}] {pasta.name}: já pego por {', '.join(p for _, p in rivais)} — deixo pra ele", flush=True)
        (pasta / "em_andamento_colab.json").unlink(missing_ok=True)
        return False
    return True


def fazer(pasta):
    pedido = json.loads((pasta / "pedido.json").read_text(encoding="utf-8"))
    # código novo do PC (token fresco gravado pelo cliente.enviar)
    subprocess.run([sys.executable, str(FILA.parent / "baixar_drive.py")]
                   + [f"D/recapd-ambientes/producao/{p}" for p in ("bin", "config", "secrets")])
    local = TRABALHO / pasta.name
    shutil.rmtree(local, ignore_errors=True)
    shutil.copytree(pasta, local)
    if not (local / "source.mp4").exists():  # pedidos novos: original no manhwa-drive (Drive da 649 é pequeno)
        sys.path.insert(0, str(FILA.parent))
        import baixar_drive
        baixar_drive.baixar_original(pasta.name, local / "source.mp4")
    print(f"[{_agora()}] pedido {pasta.name}: {pedido.get('titulo', '')[:60]}", flush=True)
    t0 = time.time()
    log = local / "pipeline.log"
    cmd = [sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "anime-pipeline.py"),
           "--video-source", str(local / "source.mp4"), "--script", str(local / "roteiro.txt"),
           "--titulo", pedido["titulo"], "--formato", "deitado"]
    with open(log, "w", encoding="utf-8") as f:
        rc = subprocess.run(cmd, cwd=PRODUCAO, stdout=f, stderr=subprocess.STDOUT,
                            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                                 "GEMINI_TTS_PROXY_ENABLED": "0"}).returncode
    seg = round(time.time() - t0)
    final = local / "final_anime_deitado.mp4"
    fim_log = log.read_text(encoding="utf-8", errors="ignore")[-4000:]
    shutil.copy2(log, pasta / "pipeline.log")
    if rc == 0 and final.exists():
        shutil.copy2(final, pasta / "final_anime_deitado.mp4")
        for extra in ("roteiro.txt", "capitulos.json"):  # 25/10: roteiro feito aqui e capítulos voltam pra ficha do PC
            if (local / extra).exists():
                shutil.copy2(local / extra, pasta / extra)
        (pasta / "source.mp4").unlink(missing_ok=True)  # Drive da 649 tem só 3 GB
        _gravar(pasta / "pronto.json", {"fim": _agora(), "segundos": seg})
        r = {"ok": True, "segundos": seg}
    else:
        r = {"ok": False, "error": f"rc={rc}" if rc else "sem final_anime_deitado.mp4", "segundos": seg, "log": fim_log}
        _gravar(pasta / "erro.json", dict(r, fim=_agora()))
    for marca in ("em_andamento_colab.json", "em_andamento.json"):
        (pasta / marca).unlink(missing_ok=True)
    shutil.rmtree(local, ignore_errors=True)
    print(f"[{_agora()}] {pasta.name}: {'OK' if r.get('ok') else r.get('error')} ({r['segundos']} s)", flush=True)


def loop():
    TRABALHO.mkdir(exist_ok=True)
    for sobra in FILA.glob("*/em_andamento_colab.json"):  # sessão anterior da Colab caiu no meio: refaz
        sobra.unlink()
        velho = sobra.with_name("em_andamento.json")
        try:
            if json.loads(velho.read_text(encoding="utf-8")).get("por") in ("colab", None):
                velho.unlink()
        except (OSError, ValueError):
            pass
    while True:
        _gravar(VIVO, {"em": _agora()})
        for pasta in sorted(p for p in FILA.iterdir() if p.is_dir()):
            if ((pasta / "pedido.json").exists() and not any((pasta / n).exists() for n in ("pronto.json", "erro.json"))
                    and not any(pasta.glob("em_andamento*.json")) and _pegar(pasta)):
                fazer(pasta)
                break
        else:
            time.sleep(30)


if __name__ == "__main__":
    loop()
