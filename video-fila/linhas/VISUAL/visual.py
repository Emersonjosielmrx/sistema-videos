r"""Engenharia reversa VISUAL (dona 01/11): "a ideia não é analisar textos, narrações ou tags, e sim VISUALMENTE os
efeitos, transições, tudo visualmente, cada detalhe" — canais de edit/AMV de anime (canais.json). Vale pra longos e
curtos, e entra NA FRENTE das outras análises.

Por vídeo: baixa em 480p sem áudio (1 por vez, pela fila única ytdlp_vez; para no 1º bloqueio), corta em blocos de
40 s, manda cada bloco em VÍDEO pro Gemini (vê o movimento, não só quadros) e pede a decupagem visual: tempo, tipo
(corte, transição, efeito, câmera, texto, cor, sincronia com a batida), como reproduzir em ffmpeg/Remotion. Depois um
resumo por vídeo e, a cada vídeo novo, a lista única VISUAL_MELHORIAS.md (A FAZER V-xx / JÁ FEITO / DESCARTADO) — o
pedido manda a lista pra IA não repetir o que já está nela. Não mexe em código de produção (só análise).

    python visual.py fila            # vídeos novos dos canais (RSS), mais vistos primeiro; 1 rodada = MAX_RODADA
    python visual.py <url>           # um vídeo
    python visual.py lista           # o que está na fila
Saída: referencias\<id>\VISUAL.md (+ blocos.json, meta.json). Log: visual.log.
"""
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401
import ytdlp_vez  # noqa: E402

sys.path.insert(0, r"D:\hipercool-videos\bin")
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).resolve().parent
CANAIS = AQUI / "canais.json"
REFS = AQUI / "referencias"
FILA = AQUI / "fila.json"
MELHORIAS = AQUI / "VISUAL_MELHORIAS.md"
LOG = AQUI / "visual.log"
TMP = Path(r"D:\hipercool-materiais\engenharia_reversa\visual_tmp")
COOKIES = Path(r"D:\recapd-ambientes\producao\cookies.txt")
BLOCO_S = 40
MAX_MIN = 8          # edits passam de 3 min às vezes; longos de verdade: só os primeiros 8 min (o visual se repete)
MAX_RODADA = 2       # vídeos por rodada (tarefa de 2 em 2 h)
MIN_LIVRE_GB = 5


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                  timeout=30).read().decode("utf-8", "replace")


def feed(cid):
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", _get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"),
                        re.S):
        vid = re.search(r"<yt:videoId>([^<]+)", e)
        v = re.search(r'views="(\d+)"', e)
        t = re.search(r"<title>([^<]*)", e)
        if vid:
            out.append({"id": vid.group(1), "views": int(v.group(1)) if v else 0,
                        "titulo": (t.group(1) if t else "").replace("&amp;", "&").replace("&quot;", '"'),
                        "short": "/shorts/" in e})
    return out


def atualizar_fila():
    """Junta os vídeos dos canais (RSS, sem yt-dlp) na fila; ordem = canal com prioridade, depois mais views."""
    fila = _ler(FILA, {})
    for c in _ler(CANAIS, {}).get("canais", []):
        try:
            itens = feed(c["id"])
        except Exception as e:  # noqa: BLE001
            log(f"feed {c['nome']} falhou: {e}")
            continue
        for i in itens:
            f = fila.setdefault(i["id"], {"situacao": "na fila"})
            f.update(canal=c["nome"], prioridade=c.get("prioridade", 5), views=i["views"], titulo=i["titulo"],
                     short=i["short"])
        time.sleep(2)
    _gravar(FILA, fila)
    return fila


def _livre_gb():
    import shutil
    return shutil.disk_usage("D:\\").free / 1e9


def baixar(vid):
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / f"{vid}.mp4"
    if out.exists() and out.stat().st_size > 50_000:
        return out
    cmd = ["yt-dlp", f"https://www.youtube.com/watch?v={vid}", "-f", "bv*[height<=480][ext=mp4]/bv*[height<=480]",
           "-S", "res,vcodec:h264", "--download-sections", f"*0-{MAX_MIN * 60}", "-o", str(out), "--no-warnings",
           "--no-playlist", "--write-info-json"]
    if COOKIES.exists():
        cmd += ["--cookies", str(COOKIES)]
    with ytdlp_vez.vez("engenharia reversa visual: vídeo"):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if r.returncode != 0 or not out.exists():
        erro = "\n".join(l for l in (r.stderr or r.stdout or "").splitlines() if "ERROR" in l or "not a bot" in l) \
            or (r.stderr or r.stdout or "")[-300:]  # 02/11: o fim do erro era o comando, não o motivo
        if ytdlp_vez.bloqueio(erro) or "not a bot" in erro:
            ytdlp_vez.pausar("engenharia reversa visual: " + erro[-150:])
            raise RuntimeError("BLOQUEIO " + erro[-120:])
        raise RuntimeError(erro[-200:])
    return out


def _dur(mp4):
    try:
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     str(mp4)], capture_output=True, text=True, timeout=60).stdout.strip())
    except ValueError:
        return 0.0


def _ja_temos():
    try:
        t = MELHORIAS.read_text(encoding="utf-8")
    except OSError:
        return ""
    return ("\n\nJÁ CONHECEMOS (não repita como novidade; se este trecho usa um deles, cite o ID, ex. 'usa V-03'):\n"
            + t[t.find("## A FAZER"):][:6000] if "## A FAZER" in t else "")


PEDIDO = """Você é editor de vídeo sênior (After Effects / CapCut / Premiere) fazendo ENGENHARIA REVERSA VISUAL de um edit
de anime que dá muitas views. IGNORE texto falado, letra da música, título e tags: só o que se VÊ.
Trecho: segundos {a:.0f} a {b:.0f} do vídeo "{titulo}" ({views} views).

Para CADA evento visual, uma linha JSON com:
 "t": segundo (no vídeo inteiro, ex. {a:.0f}.4),
 "tipo": corte | transicao | efeito | camera | texto | cor | ritmo | composicao | particula | distorcao,
 "nome": nome curto do efeito (ex. "flash branco", "zoom punch", "shake", "RGB split", "speed ramp", "wipe com máscara",
         "glow", "letterbox", "freeze frame", "chromatic aberration", "motion blur direcional"),
 "como": como aparece (duração em quadros/segundos, direção, intensidade, cor, se bate com a batida),
 "reproduzir": como fazer em ffmpeg ou Remotion/After Effects (filtro/efeito concreto e valores),
 "nota": 1-10 de quanto isso prende o olho.
Seja exaustivo: um edit tem dezenas de eventos por 10 s. Conte também cortes por segundo e se os cortes caem na batida.
Responda SÓ um JSON: {{"eventos": [...], "cortes_por_s": n, "na_batida": "sim/não/parcial", "paleta": "...",
"assinatura": "o que torna o estilo deste trecho reconhecível, em 1 frase"}}"""


def _bloco_ia(mp4, a, b, meta):
    import gemini_llm
    clip = TMP / f"_bloco_{os.getpid()}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", str(mp4), "-an",
                    "-vf", "scale=-2:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", str(clip)],
                   check=True, capture_output=True, timeout=300)
    parts = [{"text": PEDIDO.format(a=a, b=b, titulo=meta.get("titulo", ""), views=meta.get("views", "?"))
              + _ja_temos()},
             {"inline_data": {"mime_type": "video/mp4", "data": base64.b64encode(clip.read_bytes()).decode()}}]
    clip.unlink(missing_ok=True)
    for _ in range(3):
        txt = gemini_llm._call(parts, max_tokens=8000, temperature=0.3, timeout=300) or ""
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
        time.sleep(20)
    return None


def _resumo(meta, blocos):
    # o claude_client do hipercool (que vem antes no sys.path) não tem generate_text: carrega o do recapd pelo caminho
    import importlib.util
    spec = importlib.util.spec_from_file_location("claude_client_recapd",
                                                  r"D:\recapd-ambientes\producao\bin\claude_client.py")
    claude_client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(claude_client)
    eventos = [e for b in blocos for e in (b.get("eventos") or [])]
    pedido = (
        f"Decupagem visual do edit \"{meta.get('titulo')}\" ({meta.get('views')} views, canal {meta.get('canal')}), "
        f"{len(eventos)} eventos:\n{json.dumps(blocos, ensure_ascii=False)[:60000]}\n\n"
        "Escreva em português, markdown: 1) ASSINATURA VISUAL (o que faz esse estilo ser reconhecível); 2) RECEITA: "
        "os 10 efeitos/transições que mais aparecem, com frequência, duração e como reproduzir (ffmpeg/Remotion, "
        "valores concretos); 3) RITMO: cortes/s ao longo do vídeo, relação com a batida, onde acelera; 4) O QUE "
        "COPIAR NOS NOSSOS VÍDEOS (recap de manhwa/anime narrado, longo 16:9 e Shorts 9:16): até 8 itens testáveis, "
        "cada um dizendo em qual momento do nosso vídeo usar (gancho, virada, luta, revelação, troca de cena)."
        + _ja_temos())
    return claude_client.generate_text(pedido, max_tokens=6000, temperature=0.3, timeout=400,
                                       model=os.environ.get("ENG_REVERSA_MODELO", "gemini-fila")) or ""


def analisar(vid, meta):
    pasta = REFS / vid
    pasta.mkdir(parents=True, exist_ok=True)
    mp4 = baixar(vid)
    dur = min(_dur(mp4), MAX_MIN * 60)
    feitos = _ler(pasta / "blocos.json", [])
    a = len(feitos) * BLOCO_S
    while a < dur - 1:
        b = min(dur, a + BLOCO_S)
        r = _bloco_ia(mp4, a, b, meta)
        feitos.append({"de": a, "ate": b, **(r or {"erro": "IA sem resposta"})})
        _gravar(pasta / "blocos.json", feitos)  # retomável: cai no meio = continua do bloco seguinte
        log(f"  {vid} {a:.0f}-{b:.0f}s: {len((r or {}).get('eventos') or [])} eventos")
        a = b
    resumo = _resumo(meta, feitos)
    if len(resumo) < 400:
        raise RuntimeError("IA não devolveu o resumo")
    n = sum(len(b.get("eventos") or []) for b in feitos)
    (pasta / "VISUAL.md").write_text(
        f"# {meta.get('titulo')}\nhttps://youtu.be/{vid} · {meta.get('canal')} · {meta.get('views')} views · "
        f"{dur:.0f} s analisados · {n} eventos visuais\n\n" + resumo.strip() + "\n", encoding="utf-8")
    _gravar(pasta / "meta.json", {**meta, "dur_analisada": dur, "eventos": n})
    mp4.unlink(missing_ok=True)
    for j in TMP.glob(f"{vid}*.json"):
        j.unlink(missing_ok=True)
    log(f"{vid}: VISUAL.md pronto ({n} eventos)")
    return pasta


def fila_rodada():
    if ytdlp_vez.pausado():
        log("yt-dlp em pausa (bloqueio) — rodada não baixa nada")
        return
    if _livre_gb() < MIN_LIVRE_GB:
        log(f"D: com {_livre_gb():.1f} GB — não baixo")
        return
    fila = atualizar_fila()
    pend = sorted((k for k, v in fila.items() if v.get("situacao") == "na fila"),
                  key=lambda k: (fila[k].get("prioridade", 5), -(fila[k].get("views") or 0)))
    for vid in pend[:MAX_RODADA]:
        try:
            analisar(vid, fila[vid])
            fila[vid]["situacao"] = "analisado"
            fila[vid]["em"] = datetime.now().isoformat(timespec="seconds")
        except Exception as e:  # noqa: BLE001
            if str(e).startswith("BLOQUEIO"):
                log(f"{vid}: YouTube barrou — paro a rodada")
                break
            # 02/11: o corte por "--download-sections" às vezes sai truncado e o ffmpeg não abre (erro -138): apaga o
            # arquivo e tenta mais 1 vez numa próxima rodada; na 2ª falha fica "falhou" de vez
            for x in TMP.glob(f"{vid}*"):
                x.unlink(missing_ok=True)
            tent = fila[vid].get("tentativas", 0) + 1
            fila[vid]["tentativas"] = tent
            fila[vid]["situacao"] = "na fila" if tent < 2 else f"falhou: {str(e)[-200:]}"
            log(f"{vid}: falhou ({str(e)[-200:]}) — tentativa {tent}")
        _gravar(FILA, fila)
        time.sleep(120)


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "fila"
    if alvo == "fila":
        fila_rodada()
    elif alvo == "lista":
        f = atualizar_fila()
        for k, v in sorted(f.items(), key=lambda kv: (kv[1].get("prioridade", 5), -(kv[1].get("views") or 0))):
            print(f"{k} {v.get('situacao'):12} {v.get('views', 0):>9} {v.get('canal')} {v.get('titulo', '')[:60]}")
    else:
        vid = re.search(r"([\w-]{11})(?:\?|$|&)", alvo.split("v=")[-1].split("/")[-1])
        vid = vid.group(1) if vid else alvo
        f = _ler(FILA, {})
        analisar(vid, f.get(vid) or {"titulo": vid, "views": None, "canal": None})
