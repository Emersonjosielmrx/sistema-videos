# -*- coding: utf-8 -*-
"""refazer_caps.py — renderiza de novo, em ordem, capítulos já feitos (16/10/2026).

Por quê: depois da advertência do canal pt antigo, o canal novo (Manhwa Noturno) não pode receber nada que saiu lá:
caps 1-7 têm as vozes antigas do Gemini (o elenco novo do edge vale desde o cap 8) e caps 1-11 têm a censura
antiga (nudez sem censura). Usa fila.renderizar(), a mesma função da produção: roteiro, censura e cache 2.5D vêm do
cache (zero LLM), as vozes saem do elenco fixo (config/fila.json tts_motor) e, no fim de cada capítulo, roda a
análise do vídeo pronto (fila.revisar_pronto: reprovou -> fosco forçado e renderiza de novo uma vez).
Um render por vez; não posta nada (a postagem é separada).

  python bin/refazer_caps.py 1-11 [--longo 1]   (log em logs/refazer_caps.log)
  --longo N[,M]: logo depois do vertical desses capítulos, o 16:9 deles (hiper-longo --refazer --compilar só com
  ele) e a análise do vídeo pronto do capNN.mp4 — o lançamento do canal novo posta o 16:9 do cap 1 em 2º lugar.
  --so-longo N[,M]: ANTES da lista, só o 16:9 desses capítulos (o vertical deles já está pronto/aprovado).
"""
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fila  # noqa: E402

LOG = fila.PROJECT / "logs" / "refazer_caps.log"


def diz(msg):
    linha = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(linha + "\n")
    # Capítulo que acaba ou quebra avisa no Telegram da postagem E no canto da tela do PC (pedido do
    # dono, 16/10): a leva leva horas e ele não vai ficar olhando o terminal.
    if any(m in msg for m in ("pronto em", "FALHOU", "ERRO", "sem pasta")):
        try:
            import notificar
            nivel = "erro" if any(m in msg for m in ("FALHOU", "ERRO")) else (
                "aviso" if "reprovado" in msg or "invalido" in msg else "ok")
            titulo, _, resto = msg.partition(":")
            notificar.aviso(titulo.strip().capitalize(), resto.strip(), nivel=nivel)
        except Exception:  # noqa: BLE001 — avisar nunca derruba a leva
            pass


def longo(n):
    """16:9 só deste capítulo (vozes/censura do cache, refeito) + compilação dele + análise do capNN.mp4."""
    import subprocess
    import revisao_video
    logf = fila.PROJECT / "logs" / f"longo_cap{n:02d}_refazer.log"
    t0 = time.time()
    diz(f"cap {n}: 16:9 começando")
    with open(logf, "w", encoding="utf-8") as fh:
        rc = subprocess.run([fila.PY, str(fila.PROJECT / "bin" / "hiper-longo.py"), "--obra", "the-inheritor",
                             "--caps", f"{n}-{n}", "--refazer", "--compilar"], cwd=fila.PROJECT,
                            env=fila._env_render(), stdout=fh, stderr=subprocess.STDOUT).returncode
    seg = fila.PROJECT / "workspace" / "videos" / "longo" / "the-inheritor" / f"cap{n:02d}.mp4"
    if rc != 0 or not seg.exists():
        diz(f"cap {n}: 16:9 FALHOU (rc={rc}, log {logf.name})")
        return
    v = revisao_video.revisar(seg)
    diz(f"cap {n}: 16:9 pronto em {(time.time() - t0) / 60:.0f} min | análise={v['status']} "
        f"{[p['t'] for p in v['problemas']][:20]}")


def main():
    os.environ.update(fila.ENV)  # lançado fora de um terminal (WMI/tarefa): a análise roda aqui e precisa do ffmpeg
    a, b = (int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else "1-11").split("-"))
    alvos = list(range(a, b + 1))
    com_longo = {int(x) for x in sys.argv[sys.argv.index("--longo") + 1].split(",")} if "--longo" in sys.argv else set()
    so_longo = [int(x) for x in sys.argv[sys.argv.index("--so-longo") + 1].split(",")] if "--so-longo" in sys.argv else []
    for n in so_longo:
        while fila._renders_vivos():
            diz(f"cap {n}: 16:9 esperando render já rodando (pid {fila._renders_vivos()})")
            time.sleep(120)
        try:
            longo(n)
        except Exception:  # noqa: BLE001
            diz(f"cap {n}: 16:9 ERRO\n{traceback.format_exc()[:1200]}")
    if "--assumir" in sys.argv:
        # outro lote (pid) já está renderizando o 1º capítulo da lista: espera ele terminar ESSE capítulo (o log
        # dele diz "cap N: pronto|FALHOU"), encerra aquele lote e segue daqui — sem perder o render em andamento
        import re
        import subprocess
        pid, primeiro = int(sys.argv[sys.argv.index("--assumir") + 1]), alvos[0]
        diz(f"assumindo o lote pid {pid} depois do cap {primeiro}")
        while not re.search(rf"\] cap {primeiro}: (pronto|FALHOU)", LOG.read_text(encoding="utf-8", errors="replace")):
            time.sleep(30)
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        diz(f"lote pid {pid} encerrado depois do cap {primeiro}")
        texto = LOG.read_text(encoding="utf-8", errors="replace")
        if re.search(rf"\] cap {primeiro}: pronto", texto) and primeiro in com_longo:
            longo(primeiro)
        alvos = alvos[1:]
    caps = {n: (chave, obra, pasta) for chave, obra, n, pasta in fila.capitulos()
            if obra["slug"] == "the-inheritor" and n in alvos}
    diz(f"refazer: {alvos}")
    for n in alvos:
        if n not in caps:
            diz(f"cap {n}: sem pasta de painéis — pulando")
            continue
        vivos = fila._renders_vivos()
        while vivos:  # outro render (fila/outra sessão) rodando: espera, nunca dois ao mesmo tempo
            diz(f"cap {n}: esperando render já rodando (pid {vivos})")
            time.sleep(120)
            vivos = fila._renders_vivos()
        chave, obra, pasta = caps[n]
        est = fila.ler_estado()
        for k in ("revisao", "revisao_refeito", "revisao_antigo"):  # análise nova pro vídeo novo
            est.setdefault(chave, {}).pop(k, None)
        t0 = time.time()
        diz(f"cap {n}: começando")
        try:
            ok = fila.renderizar(chave, obra, n, pasta, est)
        except Exception:  # noqa: BLE001
            diz(f"cap {n}: ERRO\n{traceback.format_exc()[:1200]}")
            ok = False
        e = fila.ler_estado().get(chave, {})
        diz(f"cap {n}: {'pronto' if ok else 'FALHOU'} em {(time.time() - t0) / 60:.0f} min | situacao={e.get('situacao')} "
            f"| análise={(e.get('revisao') or {}).get('status')}")
        if ok and n in com_longo:
            try:
                longo(n)
            except Exception:  # noqa: BLE001
                diz(f"cap {n}: 16:9 ERRO\n{traceback.format_exc()[:1200]}")
    diz("FIM")


if __name__ == "__main__":
    main()
