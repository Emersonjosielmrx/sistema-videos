r"""rodar_seguro.py — subprocess.run que VOLTA no prazo, sempre (13/11/2026).

Por quê: no Windows, subprocess.run(capture_output=True, timeout=N) mata o processo no estouro e depois espera SEM
prazo os canais de saída fecharem. Se o processo travado (rclone, ssh, scp) demora a morrer ou deixou um filho com o
canal aberto, a chamada nunca volta. Visto com py-spy em 13/11 21:43: o alimentador do PC2 parado 14 min dentro de uma
chamada com timeout de 60 s — e o PC2 sem Short por 1 h 25. O mesmo padrão fazia o despacho do PC3 e do STI durarem
40-60 min numa rodada.

Uso (mesma assinatura do que os despachos usam):
    from rodar_seguro import run
    r = run([...], capture_output=True, text=True, timeout=60)   # r.returncode, r.stdout, r.stderr
No estouro levanta subprocess.TimeoutExpired, como o original, depois de matar a ÁRVORE do processo (taskkill /T).
A saída vai pra arquivo temporário (não há canal pra ficar esperando). Sem capture_output/timeout = subprocess.run puro.
RODAR_SEGURO=0 volta ao subprocess.run em tudo.
"""
import os
import subprocess
import tempfile

TimeoutExpired = subprocess.TimeoutExpired
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run(cmd, capture_output=False, text=False, timeout=None, encoding=None, errors=None, check=False, **kw):
    if os.environ.get("RODAR_SEGURO") == "0" or timeout is None or not capture_output \
            or "stdout" in kw or "stderr" in kw or kw.get("input") is not None:
        return subprocess.run(cmd, capture_output=capture_output, text=text, timeout=timeout, encoding=encoding,
                              errors=errors, check=check, **kw)
    kw.setdefault("stdin", subprocess.DEVNULL)
    with tempfile.TemporaryFile() as so, tempfile.TemporaryFile() as se:
        p = subprocess.Popen(cmd, stdout=so, stderr=se, **kw)
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, timeout=30,
                                   creationflags=_SEM_JANELA)
                else:
                    p.kill()
            except Exception:  # noqa: BLE001
                pass
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            raise
        so.seek(0)
        se.seek(0)
        out, err = so.read(), se.read()
    if text or encoding:
        enc = encoding or "utf-8"
        out, err = out.decode(enc, errors or "replace"), err.decode(enc, errors or "replace")
    r = subprocess.CompletedProcess(cmd, p.returncode, out, err)
    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, out, err)
    return r
