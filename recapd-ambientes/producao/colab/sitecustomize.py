"""Só na Colab (Linux): o código do PC tem caminhos fixos "D:\\..." e "C:\\...". Aqui eles viram /content/raiz/D/...
(RAIZ_WIN). Carregado sozinho pelo Python quando esta pasta está no PYTHONPATH."""
import os
import pathlib
import re

RAIZ = os.environ.get("RAIZ_WIN", "/content/raiz")
_WIN = re.compile(r"^([A-Za-z]):[\\/]+")


def traduzir(a):
    if isinstance(a, str):
        m = _WIN.match(a)
        if m:
            return f"{RAIZ}/{m.group(1).upper()}/" + a[m.end():].replace("\\", "/")
    return a


if os.name != "nt":
    _init = pathlib.PurePath.__init__

    def _init_traduzido(self, *args, **kw):
        _init(self, *[traduzir(a) for a in args], **kw)

    pathlib.PurePath.__init__ = _init_traduzido

    import builtins
    _open = builtins.open

    def _open_traduzido(file, *args, **kw):
        return _open(traduzir(file), *args, **kw)

    builtins.open = _open_traduzido

    for _nome in ("exists", "isfile", "isdir", "getsize"):
        _f = getattr(os.path, _nome)
        setattr(os.path, _nome, (lambda f: lambda p, *a: f(traduzir(p), *a))(_f))

    # 02/11 (dona: "aplique logo o nosso maior problema: a produção dos vídeos"; pesquisa H6): no Kaggle a T4 só
    # trabalhava no Applio — todo encode (~800 clipes + concat + legenda) era libx264 nos 4 vCPUs. Com ENCODER_GPU=1
    # (o kaggle_trabalhador liga depois de testar o NVENC na sessão) todo "ffmpeg ... -c:v libx264 -preset X -crf N"
    # vira h264_nvenc de qualidade equivalente (-cq N, -b:v 0). Deu erro = roda de novo com libx264 (nunca perde vídeo).
    import subprocess as _sp

    _run = _sp.run

    def _nvenc(cmd):
        """Lista do ffmpeg com libx264 -> mesma lista com h264_nvenc; None se não é encode libx264."""
        if not isinstance(cmd, (list, tuple)) or not cmd or "ffmpeg" not in str(cmd[0]) or "libx264" not in cmd:
            return None
        out, i, crf, intermed = [], 0, 20, False
        cmd = [str(c) for c in cmd]
        while i < len(cmd):
            c = cmd[i]
            if c == "libx264":
                out.append("h264_nvenc")
            elif c == "-preset" and i + 1 < len(cmd):
                # só a PASSADA FINAL (a que queima a legenda: subtitles=/ass= no filtro) ganha a qualidade máxima (p6);
                # clipes, concat e mascote são intermediários (regravados depois) -> p2, o mais rápido com boa nota
                final = any("subtitles=" in str(x) or "ass=" in str(x) for x in cmd)
                intermed = not final
                out += ["-preset", "p6" if final else "p2"]
                i += 1
            elif c == "-crf" and i + 1 < len(cmd):
                try:
                    crf = int(float(cmd[i + 1]))
                except ValueError:
                    crf = 20
                i += 1
            elif c in ("-tune", "-x264-params", "-x264opts") and i + 1 < len(cmd):
                i += 1  # opções só do x264
            else:
                out.append(c)
            i += 1
        k = out.index("h264_nvenc") + 1
        # cq do NVENC: IGUAL ao crf (revisão sonnet 02/11: o NVENC precisa de cq <= crf do x264 pra mesma qualidade;
        # a 1ª versão usava crf+1). -b:v 0 OBRIGATÓRIO senão o vbr cai no padrão de 2 Mbps; final com AQ e lookahead
        extra = ["-rc", "vbr", "-cq", str(crf), "-b:v", "0", "-tune", "hq"]
        if not intermed:
            extra += ["-spatial-aq", "1", "-temporal-aq", "1", "-rc-lookahead", "16", "-bf", "2", "-b_ref_mode",
                      "middle"]
            # 04/11 dona aprovou ("faça esse vídeo final no Kaggle"): o final saía ~13 Mbit/s (waaQ 8,9 GB / 87 min) e
            # a internet de casa sobe a ~7,6 Mbit/s — 2,5 h por longo. Teto de 8 Mbit/s só na passada final (o YouTube
            # recodifica tudo; 1080p60 continua). FINAL_MAXRATE=0 tira o teto.
            teto = os.environ.get("FINAL_MAXRATE", "8M")
            if teto and teto != "0":
                extra += ["-maxrate", teto, "-bufsize", f"{int(float(teto.rstrip('Mm')) * 2)}M"]
        return out[:k] + extra + out[k:]

    def _run_gpu(cmd, *a, **kw):
        alt = _nvenc(cmd) if os.environ.get("ENCODER_GPU") == "1" else None
        if alt is None:
            return _run(cmd, *a, **kw)
        try:
            r = _run(alt, *a, **kw)
            if getattr(r, "returncode", 0) == 0:
                return r
        except _sp.CalledProcessError:
            pass
        except _sp.TimeoutExpired:
            raise
        return _run(cmd, *a, **kw)  # NVENC falhou (sessão sem GPU, formato não aceito): libx264 como antes

    _sp.run = _run_gpu
