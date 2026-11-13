# -*- coding: utf-8 -*-
r"""Trabalhador da 🌉 Ponte PC ↔ n8n. Só biblioteca padrão do Python (nada para instalar).

O PC pergunta ao n8n se tem pedido (a cada `intervalo_s`), faz com o que já existe no PC e devolve o resultado.
Nenhuma porta aberta no PC; nada é postado daqui (o "guardar_para_postar" só deixa o vídeo na caixa de saída).

    python trabalhador.py               fica rodando (LIGAR_PONTE.bat abre assim, sem janela)
    python trabalhador.py --uma-vez     pega no máximo 1 pedido e sai (teste)
    python trabalhador.py --testa montar_video <job_da_fabrica>   roda a ação aqui, sem o n8n (teste local)

Config em config.json (mesma pasta): n8n, token, maquina, intervalo_s, acoes_liberadas.
"""
import base64
import ctypes
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CFG = json.loads((AQUI / "config.json").read_text(encoding="utf-8"))
TRABALHO = AQUI / "trabalho"
CAIXA = AQUI / "caixa-de-saida"
LOG = AQUI / "logs" / "trabalhador.log"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
PY_VEO = r"D:\veo\venv\Scripts\python.exe"
GERA_IMAGEM = r"D:\flow-imagens\gera_imagem.py"
VERSAO = "1"
SEM_JANELA = 0x08000000  # CREATE_NO_WINDOW: filho de pythonw não abre console na tela
MAX_ARQUIVO = 15 * 1024 * 1024


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    if LOG.exists() and LOG.stat().st_size > 1_000_000:
        LOG.replace(LOG.with_suffix(".log.1"))
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        try:
            print(linha, flush=True)
        except (OSError, ValueError):
            pass


def n8n(caminho, corpo=None, tempo=60):
    req = urllib.request.Request(CFG["n8n"].rstrip("/") + "/webhook/" + caminho,
                                 data=json.dumps(corpo).encode() if corpo is not None else None,
                                 method="POST" if corpo is not None else "GET",
                                 headers={"X-Ponte-Token": CFG["token"], "Content-Type": "application/json",
                                          "User-Agent": "ponte-pc/" + VERSAO})
    with urllib.request.urlopen(req, timeout=tempo) as r:
        return json.loads(r.read() or b"{}")


def baixa(url, destino, tempo=180):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ponte-pc"})
    with urllib.request.urlopen(req, timeout=tempo) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)
    return destino


# ───────── ações ─────────

def saude(dados, pasta):
    class MEM(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MEM()
    m.dwLength = ctypes.sizeof(MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    d = shutil.disk_usage("D:\\")
    info = {"maquina": CFG["maquina"], "hora": datetime.now().isoformat(timespec="seconds"),
            "ram_livre_gb": round(m.ullAvailPhys / 2**30, 1), "ram_total_gb": round(m.ullTotalPhys / 2**30, 1),
            "disco_d_livre_gb": round(d.free / 2**30, 1), "cpus": os.cpu_count(),
            "ffmpeg": os.path.exists(FFMPEG), "flow_imagens": os.path.exists(GERA_IMAGEM)}
    return {"ok": True, "mensagem": f"PC {CFG['maquina']}: {info['ram_livre_gb']} GB de RAM livre, "
                                    f"{info['disco_d_livre_gb']} GB livres no D:", "dados": info}


def imagem_flow(dados, pasta):
    prompt = str(dados.get("prompt") or "").strip()
    if not prompt:
        return {"ok": False, "mensagem": "faltou o prompt"}
    formato = dados.get("formato") if dados.get("formato") in ("16:9", "4:3", "1:1", "3:4", "9:16") else "9:16"
    saida = pasta / "flow.png"
    cmd = [PY_VEO, GERA_IMAGEM, prompt, str(saida), "--formato", formato, "--max-contas", str(int(dados.get("max_contas") or 2))]
    if dados.get("maquinas"):
        cmd += ["--maquinas", str(dados["maquinas"])]
    env = dict(os.environ, PYTHONUTF8="1")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900, env=env,
                       creationflags=SEM_JANELA)
    feitos = sorted(pasta.glob("flow*.png"))
    if not feitos:
        return {"ok": False, "mensagem": "o Flow não entregou imagem: " + (r.stderr or r.stdout or "")[-300:]}
    return {"ok": True, "mensagem": f"imagem do Google Flow ({formato})", "arquivo": feitos[0]}


def _ass_tempo(s):
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def _ass_texto(t):
    return str(t).replace("{", "(").replace("}", ")").replace("\\", " ").replace("\n", " ")


def _legenda_ass(filme, W, H, total):
    """Legenda palavra a palavra (a palavra falada em amarelo) + gancho no topo nos primeiros 2,8 s."""
    px = round(min(W, H) * (0.085 if W < H else 0.075))
    linhas = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
              "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
              "MarginR, MarginV, Encoding",
              f"Style: Fala,Arial Black,{px},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,"
              f"{max(3, round(px * 0.12))},2,2,40,40,{round(H * (0.25 if W < H else 0.14))},1",
              f"Style: Topo,Arial Black,{round(px * 0.72)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,3,"
              f"{round(px * 0.3)},0,8,60,60,{round(H * 0.07)},1", "",
              "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    if filme.get("gancho"):
        linhas.append(f"Dialogue: 1,{_ass_tempo(0)},{_ass_tempo(min(2.8, total))},Topo,,0,0,0,{{\\fad(150,300)}},"
                      f"{_ass_texto(filme['gancho']).upper()}")
    for c in filme["cenas"]:
        palavras = _ass_texto(c["fala"]).upper().split()
        if not palavras:
            continue
        grupos, g = [], []
        for p in palavras:
            if len(g) >= 4 or len(" ".join(g + [p])) > 24:
                grupos.append(g)
                g = []
            g.append(p)
        if g:
            grupos.append(g)
        letras = sum(len(p) for p in palavras)
        t, ini, fim = float(c["ini"]), float(c["ini"]), float(c["fim"])
        for grupo in grupos:
            for j, p in enumerate(grupo):
                dt = (fim - ini) * len(p) / letras
                texto = " ".join(("{\\c&H4DE1FF&}" + q + "{\\c&HFFFFFF&}") if k == j else q for k, q in enumerate(grupo))
                linhas.append(f"Dialogue: 0,{_ass_tempo(t)},{_ass_tempo(t + dt)},Fala,,0,0,0,,{texto}")
                t += dt
    return "\n".join(linhas) + "\n"


def montar_video(dados, pasta):
    filme = dados.get("filme")
    if not filme and dados.get("job"):
        st = json.loads(urllib.request.urlopen(CFG["n8n"].rstrip("/") + "/webhook/gratis-video-status?id=" + str(dados["job"]),
                                               timeout=60).read())
        filme = st.get("filme")
    if not filme or not filme.get("cenas"):
        return {"ok": False, "mensagem": "faltou o filme (dados.filme ou dados.job da fábrica grátis)"}
    W, H = int(filme.get("largura") or 720), int(filme.get("altura") or 1280)
    voz = baixa(filme["voz"], pasta / "voz.mp3")
    imgs = {}
    for k, c in enumerate(filme["cenas"]):
        if c["img"] not in imgs:
            imgs[c["img"]] = baixa(c["img"], pasta / f"img{k}{Path(c['img'].split('?')[-1]).suffix or '.jpg'}")
    cenas = filme["cenas"]
    total = max(float(filme.get("total") or 0), float(cenas[-1]["fim"]) + 0.5)
    X = 0.3  # transição
    SW, SH = (round(W * 1.12) // 2) * 2, (round(H * 1.12) // 2) * 2
    entradas, filtros = [], []
    for i, c in enumerate(cenas):
        d = (float(cenas[i + 1]["ini"]) if i + 1 < len(cenas) else total) - float(c["ini"])
        L = d + (X if i + 1 < len(cenas) else 0)
        entradas += ["-loop", "1", "-framerate", "30", "-t", f"{L:.3f}", "-i", imgs[c["img"]].name]
        mx, my = SW - W, SH - H
        x, y = [(f"{mx}*t/{L:.3f}", f"{my / 2}"), (f"{mx}*(1-t/{L:.3f})", f"{my / 2}"),
                (f"{mx / 2}", f"{my}*t/{L:.3f}"), (f"{mx / 2}", f"{my}*(1-t/{L:.3f})")][i % 4]
        filtros.append(f"[{i}:v]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},"
                       f"crop={W}:{H}:x='{x}':y='{y}',fps=30,format=yuv420p,setsar=1[v{i}]")
    atual = "v0"
    for i in range(1, len(cenas)):
        filtros.append(f"[{atual}][v{i}]xfade=transition=fade:duration={X}:offset={float(cenas[i]['ini']):.3f}[x{i}]")
        atual = f"x{i}"
    (pasta / "legenda.ass").write_text(_legenda_ass(filme, W, H, total), encoding="utf-8")
    fonte = next((f for f in (r"C:\Windows\Fonts\ariblk.ttf", r"C:\Windows\Fonts\arialbd.ttf") if os.path.exists(f)), None)
    if fonte:
        shutil.copy(fonte, pasta / Path(fonte).name)
    filtros.append(f"[{atual}]subtitles=legenda.ass:fontsdir=.[vf]")
    saida = pasta / "video.mp4"
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *entradas, "-i", voz.name,
           "-filter_complex", ";".join(filtros), "-map", "[vf]", "-map", f"{len(cenas)}:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",  # 30/10: sem isto saía yuvj444p (High 4:4:4), que celular e Instagram não tocam
           "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}", "-movflags", "+faststart", saida.name]
    r = subprocess.run(cmd, cwd=pasta, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200,
                       creationflags=SEM_JANELA)
    if r.returncode or not saida.exists() or saida.stat().st_size < 50_000:
        return {"ok": False, "mensagem": "ffmpeg falhou: " + (r.stderr or "")[-400:]}
    return {"ok": True, "mensagem": f"vídeo {W}x{H} montado no ffmpeg do PC ({total:.1f} s)", "arquivo": saida}


def guardar_para_postar(dados, pasta):
    url = str(dados.get("video_url") or "")
    if not url.startswith("http"):
        return {"ok": False, "mensagem": "faltou video_url"}
    dia = CAIXA / datetime.now().strftime("%Y-%m-%d")
    dia.mkdir(parents=True, exist_ok=True)
    nome = pasta.name
    ext = ".webm" if ".webm" in url else ".mp4"
    baixa(url, dia / (nome + ext), tempo=600)
    meta = {k: dados.get(k) for k in ("titulo", "descricao", "hashtags", "plataforma", "canal")}
    meta.update({"origem": url, "baixado_em": datetime.now().isoformat(timespec="seconds"),
                 "aviso": "Só guardado. Nada foi postado: postar pelos postadores do PC, com aprovação."})
    (dia / (nome + ".json")).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "mensagem": f"guardado em {dia / (nome + ext)} para aprovação (nada foi postado)",
            "dados": {"arquivo_no_pc": str(dia / (nome + ext))}}


ACOES = {"saude": saude, "imagem_flow": imagem_flow, "montar_video": montar_video, "guardar_para_postar": guardar_para_postar}


def executa(pedido):
    acao = pedido.get("acao")
    pasta = TRABALHO / str(pedido.get("id") or int(time.time()))
    pasta.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        if acao not in CFG.get("acoes_liberadas", []):
            res = {"ok": False, "mensagem": f"ação '{acao}' não liberada neste PC (config.json → acoes_liberadas)"}
        else:
            res = ACOES[acao](pedido.get("dados") or {}, pasta)
    except Exception as e:  # noqa: BLE001 — o erro volta ao n8n em vez de derrubar o trabalhador
        res = {"ok": False, "mensagem": f"{type(e).__name__}: {e}"[:600]}
        log(traceback.format_exc()[-800:])
    res["segundos"] = round(time.time() - t0, 1)
    return res, pasta


def devolve(pedido, res):
    corpo = {"id": pedido["id"], "acao": pedido.get("acao"), "ok": bool(res.get("ok")), "maquina": CFG["maquina"],
             "mensagem": res.get("mensagem", ""), "dados": {**(res.get("dados") or {}), "segundos": res.get("segundos")}}
    arq = res.get("arquivo")
    if arq and Path(arq).exists():
        if Path(arq).stat().st_size > MAX_ARQUIVO:
            corpo["mensagem"] += f" (arquivo de {Path(arq).stat().st_size // 2**20} MB ficou só no PC: {arq})"
        else:
            corpo["arquivo_b64"] = base64.b64encode(Path(arq).read_bytes()).decode()
            corpo["extensao"] = Path(arq).suffix.lstrip(".")
    n8n("ponte-pc/resultado", corpo, tempo=300)


def uma_rodada():
    p = n8n(f"ponte-pc/proximo?maquina={CFG['maquina']}&versao={VERSAO}")
    if not p or p.get("vazio") or not p.get("id"):
        return False
    log(f"pedido {p['id']} ({p.get('acao')}) de {p.get('origem')}")
    res, pasta = executa(p)
    devolve(p, res)
    log(f"pedido {p['id']}: {'ok' if res.get('ok') else 'ERRO'} em {res.get('segundos')} s — {res.get('mensagem', '')[:200]}")
    if res.get("ok"):
        shutil.rmtree(pasta, ignore_errors=True)
    return True


def main():
    if "--testa" in sys.argv:
        i = sys.argv.index("--testa")
        acao, arg = sys.argv[i + 1], (sys.argv[i + 2] if len(sys.argv) > i + 2 else "")
        dados = {"job": arg} if acao == "montar_video" else {"prompt": arg} if acao == "imagem_flow" else {}
        res, pasta = executa({"id": "teste-" + datetime.now().strftime("%H%M%S"), "acao": acao, "dados": dados})
        print(json.dumps({k: str(v) for k, v in res.items()}, ensure_ascii=False, indent=1))
        return
    trava = open(AQUI / "trabalhador.lock", "w")
    try:
        msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("já tem um trabalhador rodando neste PC")
        return
    log(f"trabalhador ligado ({CFG['maquina']}, ações: {', '.join(CFG.get('acoes_liberadas', []))})")
    falhas = 0
    while True:
        try:
            pegou = uma_rodada()
            falhas = 0
            if "--uma-vez" in sys.argv:
                return
            if pegou:
                continue
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            falhas += 1
            log(f"sem contato com o n8n ({type(e).__name__}: {str(e)[:120]}); tentativa {falhas}")
            if "--uma-vez" in sys.argv:
                return
        time.sleep(min(300, CFG.get("intervalo_s", 20) * (1 + min(falhas, 10))))


if __name__ == "__main__":
    main()
