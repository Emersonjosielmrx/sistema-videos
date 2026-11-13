"""Engenharia reversa de vídeo de referência (28/10, método do playbook reference-video.md do Hypit).

Antes de criar, o editor estuda um vídeo que deu certo: o que ele comunica e POR QUE funciona (ANALISE.md) e cada
sistema visual/sonoro com tempo de entrada, comportamento e saída (LINHA_DO_TEMPO.md). O nosso vídeo copia a
ESTRUTURA (gancho, ritmo dos cortes, como o texto entra e sai, legenda), nunca o texto, a marca ou as imagens.

    python referencia.py adicionar <arquivo.mp4 | link> --tipo anuncio|entretenimento [--nome x] [--nota "por que"]
    python referencia.py analisar [nome]        # transcreve, tira as grades e a IA escreve a análise
    python referencia.py lista

Pasta de cada uma: referencias/<nome>/ — source.mp4, info.json, transcript.json, evidencia/*.jpg, cortes.json,
ANALISE.md, LINHA_DO_TEMPO.md, ESTRUTURA.json. A produção (gerar.etapa_preparar_editor) copia a menos usada do
mesmo tipo para public/referencia/ e o manual do editor manda ler (config "referencias": {"ligado": true}).
"""
import sem_janela  # noqa: F401 — nenhum filho abre janela
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REFS = RAIZ / "referencias"
USOS = REFS / "usos.json"
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
PY_DL = r"D:\veo\venv\Scripts\python.exe"  # tem o yt_dlp
WHISPER = r"D:\hipercool-materiais\models\whisper"
FONTE = r"C:\Windows\Fonts\arialbd.ttf"


def log(m):
    print(f"[{datetime.now():%d/%m %H:%M:%S}] {m}", flush=True)


def _ff():
    return FF if Path(FF).exists() else "ffmpeg", FP if Path(FP).exists() else "ffprobe"


def _slug(s):
    s = re.sub(r"[^\w]+", "_", s.lower()).strip("_")
    return s[:40] or datetime.now().strftime("ref_%Y%m%d_%H%M%S")


# ───────────────────────────── adicionar ─────────────────────────────

def baixar(url, destino):
    """1 download, na vez única do yt-dlp do PC (rajada barra o IP da casa)."""
    sys.path.insert(0, r"D:\hipercool-materiais\comum")
    import ytdlp_vez
    if ytdlp_vez.pausado():
        raise SystemExit("yt-dlp em pausa (YouTube barrou o IP) — tente mais tarde ou baixe o arquivo à mão")
    with ytdlp_vez.vez("claude-code-video: referência"):
        r = subprocess.run([PY_DL, "-m", "yt_dlp", "-f", "bv*[height<=1920][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                            "--merge-output-format", "mp4", "--max-filesize", "150M", "--no-playlist",
                            "--write-info-json", "-o", str(destino / "source.%(ext)s"), url],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if r.returncode or not (destino / "source.mp4").exists():
        if ytdlp_vez.bloqueio(r.stdout + r.stderr):
            ytdlp_vez.pausar("referência do claude-code-video")
        raise SystemExit(f"download falhou: {(r.stderr or r.stdout)[-600:]}")
    meta = {}
    for p in destino.glob("source*.info.json"):
        d = json.loads(p.read_text("utf-8"))
        meta = {k: d.get(k) for k in ("title", "uploader", "view_count", "like_count", "duration", "webpage_url")}
        p.unlink()
    return meta


def adicionar(fonte, tipo, nome=None, nota=""):
    REFS.mkdir(exist_ok=True)
    nome = _slug(nome or (Path(fonte).stem if Path(fonte).exists() else re.sub(r"https?://", "", fonte)))
    pasta = REFS / nome
    pasta.mkdir(exist_ok=True)
    if Path(fonte).exists():
        shutil.copy2(fonte, pasta / "source.mp4")
        meta = {"arquivo": str(fonte)}
    else:
        meta = baixar(fonte, pasta)
    meta.update({"tipo": tipo, "nota_da_dona": nota, "adicionada": datetime.now().isoformat(timespec="minutes"),
                 "fonte": fonte})
    (pasta / "info.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    log(f"referência {nome} adicionada ({tipo})")
    return pasta


# ───────────────────────────── evidência ─────────────────────────────

def sondar(video):
    _, fp = _ff()
    r = subprocess.run([fp, "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
                        "-of", "json", str(video)], capture_output=True, text=True)
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a, b = v["r_frame_rate"].split("/")
    return {"duracao": float(d["format"]["duration"]), "w": v["width"], "h": v["height"],
            "fps": round(float(a) / float(b), 2), "audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def transcrever(video, saida):
    """Palavra por palavra com tempo (faster-whisper; modelos no D:)."""
    import psutil
    from faster_whisper import WhisperModel
    livre = psutil.virtual_memory().available / 2**30
    tamanho = "medium" if livre >= 4 else "small"
    log(f"  whisper {tamanho} (RAM livre {livre:.1f} GB)")
    m = WhisperModel(tamanho, device="cpu", compute_type="int8", download_root=WHISPER)
    segs, info = m.transcribe(str(video), word_timestamps=True, vad_filter=True)
    palavras = [{"p": w.word.strip(), "ini": round(w.start, 2), "fim": round(w.end, 2)}
                for s in segs for w in (s.words or [])]
    d = {"idioma": info.language, "texto": " ".join(w["p"] for w in palavras), "palavras": palavras}
    saida.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    return d


def cortes(video, limiar=0.32):
    """Tempos de mudança brusca de imagem (corte de câmera / troca de cena)."""
    ff, _ = _ff()
    r = subprocess.run([ff, "-hide_banner", "-i", str(video), "-vf", f"select='gt(scene,{limiar})',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def _quadro(video, t, larg):
    ff, _ = _ff()
    from io import BytesIO
    from PIL import Image
    r = subprocess.run([ff, "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={larg}:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    return Image.open(BytesIO(r.stdout)).convert("RGB") if r.stdout else None


def grade(video, tempos, palavras, saida, colunas=4, larg=300, titulo=""):
    """Quadros com o TEMPO e as PALAVRAS faladas perto dele embaixo (a legenda original continua visível)."""
    from PIL import Image, ImageDraw, ImageFont
    fonte = ImageFont.truetype(FONTE, 17) if Path(FONTE).exists() else ImageFont.load_default()
    ims = [(t, _quadro(video, t, larg)) for t in tempos]
    ims = [(t, im) for t, im in ims if im]
    if not ims:
        return None
    h = ims[0][1].height
    faixa = 46
    linhas = (len(ims) + colunas - 1) // colunas
    topo = 30 if titulo else 0
    tela = Image.new("RGB", (colunas * larg, topo + linhas * (h + faixa)), "#111")
    d = ImageDraw.Draw(tela)
    if titulo:
        d.text((8, 6), titulo, fill="#FFD54A", font=fonte)
    for n, (t, im) in enumerate(ims):
        x, y = (n % colunas) * larg, topo + (n // colunas) * (h + faixa)
        tela.paste(im, (x, y))
        perto = " ".join(w["p"] for w in palavras if w["ini"] <= t + 0.35 and w["fim"] >= t - 0.35)
        d.rectangle([x, y + h, x + larg - 1, y + h + faixa - 1], fill="#000")
        d.text((x + 6, y + h + 3), f"{t:5.2f}s", fill="#7CFC00", font=fonte)
        d.text((x + 6, y + h + 23), perto[:34], fill="#FFFFFF", font=fonte)
    tela.save(saida, quality=88)
    return saida


def evidencia(pasta):
    video = pasta / "source.mp4"
    ev = pasta / "evidencia"
    ev.mkdir(exist_ok=True)
    info = sondar(video)
    dur = info["duracao"]
    tr = pasta / "transcript.json"
    falas = json.loads(tr.read_text("utf-8")) if tr.exists() else (transcrever(video, tr) if info["audio"] else
                                                                    {"palavras": [], "texto": ""})
    ps = falas["palavras"]
    cs = cortes(video)
    (pasta / "cortes.json").write_text(json.dumps({"cortes": cs, **info}, indent=1), "utf-8")
    arqs = []
    # 1) visão geral: 1 quadro por segundo (vídeo longo: 32 quadros espalhados), páginas de 16
    passo = max(1.0, dur / 32)
    ts = [round(i * passo, 2) for i in range(int(dur / passo) + 1) if i * passo < dur - 0.05]
    for pg in range(0, len(ts), 16):
        arqs.append(grade(video, ts[pg:pg + 16], ps, ev / f"geral_{pg // 16 + 1}.jpg",
                          titulo=f"visão geral {ts[pg]:.0f}–{ts[min(pg + 15, len(ts) - 1)]:.0f}s"))
    # 2) abertura quadro a quadro (o gancho): 0–3 s a cada 0,25 s
    arqs.append(grade(video, [i * 0.25 for i in range(12) if i * 0.25 < dur], ps, ev / "abertura_0-3s.jpg",
                      titulo="abertura 0–3 s (gancho), a cada 0,25 s"))
    # 3) cortes: antes / no corte / depois (como a troca acontece), até 12 cortes
    tc = [x for c in cs[:12] for x in (c - 0.2, c + 0.04, c + 0.25)]
    if tc:
        arqs.append(grade(video, tc, ps, ev / "cortes.jpg", colunas=6, larg=220,
                          titulo=f"{len(cs)} cortes; 3 quadros por corte (antes / no corte / depois)"))
    # 4) final (a chamada e como termina)
    arqs.append(grade(video, [max(0, dur - 3 + i * 0.5) for i in range(6)], ps, ev / "final.jpg", colunas=6,
                      larg=220, titulo="últimos 3 s"))
    return info, falas, cs, [a for a in arqs if a]


# ───────────────────────────── análise ─────────────────────────────

PROMPT = """Você é um diretor de motion design estudando um vídeo de REFERÊNCIA que deu certo, para que o nosso
próximo vídeo vertical ({tipo}) aprenda com ele. Método (engenharia reversa do Hypit):

1. Entenda o TODO primeiro: o gancho, o argumento ou a história, as viradas de atenção, o fechamento e a reação que o
   vídeo quer do público. Forme uma explicação provisória de POR QUE ele funciona.
2. Leia esse sentido nos DETALHES: cada elemento desenhado (legenda, texto na tela, grafismo/MG, efeito, foto/vídeo,
   som) com conteúdo, aparência, posição, ENTRADA, comportamento enquanto fica, quanto tempo fica e SAÍDA — sempre
   ligado à palavra, pausa ou ação que ele serve, e o que isso faz por quem assiste (apresenta, contrasta, acumula
   prova, amplifica a reação, deixa um processo claro, passa a atenção para a próxima ideia).
3. Um elemento que sobrevive a um corte pertence a um SISTEMA maior que a tomada: descreva o sistema 1 vez e marque
   no tempo o que muda nele. Repetição do mesmo comportamento = 1 explicação com as variações e os tempos.
4. Separe o que é VISÍVEL/AUDÍVEL do que é INTERPRETAÇÃO sua. Dúvida = diga que é dúvida (não invente).

Material nesta pasta (abra as imagens com Read — são a sua visão do vídeo):
- info.json (título, views, nota da dona), cortes.json (duração, tamanho, fps, tempo de cada corte detectado)
- transcript.json (cada palavra falada com tempo, Whisper — pode ter erro de grafia de nome)
- evidencia/*.jpg: grades de quadros com o TEMPO (verde) e as PALAVRAS faladas naquele instante (branco):
{grades}

Escreva 3 arquivos nesta pasta (Write), em português:

ANALISE.md — o modelo do vídeo inteiro: o que ele tenta conseguir; como a história e o RITMO funcionam (cortes por
10 s, duração média de cada tomada, onde acelera e onde respira); o que cada sistema visual/sonoro contribui; o que
persiste ou volta; como momentos distantes se ligam; POR QUE FUNCIONA. Fato da referência e interpretação sua
distinguíveis no texto.

LINHA_DO_TEMPO.md — seções nomeadas por tempo e fase, no formato:
## 0.00–2.10 · Gancho: a pergunta absurda
(o que é falado; objetos ativos com texto exato, cor, posição em px aproximados num 1080x1920, como entram — de
onde, com que movimento, quantos quadros —, o que fazem e como saem; o que isso faz por quem assiste)
Cubra do primeiro ao último segundo, sem buraco.

ESTRUTURA.json — o que o NOSSO editor deve levar, sem texto/marca/imagem dela:
{{"tipo": "{tipo}", "duracao_s": n, "gancho": {{"ate_s": n, "como": "..."}}, "cortes_por_10s": n,
 "blocos": [{{"de": s, "ate": s, "funcao": "gancho|problema|prova|virada|solucao|chamada|...", "visual": "...",
   "texto_tela": "como o texto aparece (não o texto dela)", "movimento": "...", "transicao_saida": "..."}}],
 "legenda": {{"posicao": "...", "palavras_por_bloco": n, "destaque": "como a palavra falada aparece",
   "entrada": "..."}},
 "sistemas": ["sistema que persiste e como muda"], "som": "...",
 "manter": ["relação que deve ficar quando trocar o produto/assunto"], "mudar": ["o que redesenhar para nós"],
 "por_que_funciona": "1 a 3 frases"}}

No fim responda só: FEITO."""


def analisar(pasta, modelo=None):
    sys.path.insert(0, str(RAIZ))
    import motor
    log(f"referência {pasta.name}: evidência")
    info, falas, cs, arqs = evidencia(pasta)
    log(f"  {info['duracao']:.1f}s, {len(cs)} cortes, {len(falas['palavras'])} palavras, {len(arqs)} grades")
    meta = json.loads((pasta / "info.json").read_text("utf-8"))
    grades = "\n".join(f"  - evidencia/{Path(a).name}" for a in arqs)
    for nome in ("ANALISE.md", "LINHA_DO_TEMPO.md", "ESTRUTURA.json"):
        (pasta / nome).unlink(missing_ok=True)
    txt = motor.chamar(PROMPT.format(tipo=meta.get("tipo", "anuncio"), grades=grades), pasta, "claude-code-video",
                       "referencia", timeout=2400, max_turnos=40, ferramentas=motor.EDITOR, modelo=modelo,
                       aceitar_limite=True)
    faltam = [n for n in ("ANALISE.md", "LINHA_DO_TEMPO.md", "ESTRUTURA.json") if not (pasta / n).exists()]
    if faltam:
        raise RuntimeError(f"análise incompleta (faltam {faltam}): {txt[-300:]}")
    est = json.loads(re.sub(r"^```\w*|```$", "", (pasta / "ESTRUTURA.json").read_text("utf-8").strip()).strip())
    (pasta / "ESTRUTURA.json").write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
    meta["analisada"] = datetime.now().isoformat(timespec="minutes")
    (pasta / "info.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    log(f"  análise pronta: {len(est.get('blocos') or [])} blocos — {str(est.get('por_que_funciona'))[:160]}")
    return est


def prontas(tipo=None):
    out = []
    for p in sorted(REFS.glob("*/info.json")) if REFS.exists() else []:
        m = json.loads(p.read_text("utf-8"))
        if m.get("analisada") and (tipo is None or m.get("tipo") == tipo) and (p.parent / "ESTRUTURA.json").exists():
            out.append(p.parent)
    return out


def para_video(tipo, pub, vid):
    """Escolhe a referência analisada menos usada do tipo e copia o estudo para pub/referencia/. None se não há."""
    cands = prontas(tipo)
    if not cands:
        return None
    usos = json.loads(USOS.read_text("utf-8")) if USOS.exists() else {}
    ref = min(cands, key=lambda p: (len(usos.get(p.name, [])), p.name))
    dst = pub / "referencia"
    dst.mkdir(exist_ok=True)
    for n in ("ANALISE.md", "LINHA_DO_TEMPO.md", "ESTRUTURA.json"):
        shutil.copy2(ref / n, dst / n)
    for g in (ref / "evidencia").glob("*.jpg"):
        shutil.copy2(g, dst / g.name)
    usos.setdefault(ref.name, []).append(vid)
    USOS.write_text(json.dumps(usos, ensure_ascii=False, indent=1), "utf-8")
    return {"nome": ref.name, "pasta": "referencia/",
            "arquivos": ["referencia/ANALISE.md", "referencia/LINHA_DO_TEMPO.md", "referencia/ESTRUTURA.json"]}


# ───────────────────────────── busca automática (a cada rodada) ─────────────────────────────
# 28/10 (dona): "vídeo de referência tem que ser buscado pelo próprio melhorador, e você também, a cada rodada".
# Uma rodada = no máximo 1 referência nova (a do tipo com menos), 1 busca no YouTube pela vez única do yt-dlp
# (proxy), só Shorts <= 75 s com muitas views, nunca repetida. Chamado pela tarefa (cron_auto.bat) e pelo melhorador.
BUSCAS = {
    "entretenimento": ["curiosidades que você não sabia #shorts", "história real bizarra #shorts",
                       "mistério não resolvido #shorts", "bastidores de filme curiosidade #shorts",
                       "fato histórico chocante #shorts", "você sabia ciência #shorts"],
    "anuncio": ["anúncio criativo produto #shorts", "propaganda viral criativa #shorts",
                "comercial criativo empresa #shorts", "anúncio whatsapp automação #shorts",
                "propaganda de app que viralizou #shorts", "ugc anúncio produto #shorts"],
}


def _cfg():
    try:
        return json.loads((RAIZ / "config.json").read_text("utf-8")).get("referencias") or {}
    except Exception:  # noqa: BLE001
        return {}


def _ja_temos():
    ids = set()
    for p in REFS.glob("*/info.json") if REFS.exists() else []:
        m = json.loads(p.read_text("utf-8"))
        ids |= set(re.findall(r"(?:v=|shorts/|youtu\.be/)([\w-]{11})", f"{m.get('webpage_url')} {m.get('fonte')}"))
        ids |= set(re.findall(r"[\\/]([\w-]{11})_[^\\/]*[\\/]source\.mp4$", str(m.get("fonte"))))
    return ids


PARCEIROS_LOCAL = Path(r"D:\recapd-ambientes\producao\workspace\anime")


def parceiro_local():
    """28/10 (dona mandou a lista dos parceiros, já no parceiro.json do Cortes): Short de PARCEIRO que o Cortes já
    baixou (workspace\\anime\\<id>_<título>\\source.mp4) — nenhum download novo do YouTube. Vale como referência de
    entretenimento (leva a ESTRUTURA: gancho, ritmo, texto, legenda). None se não há um novo de até 90 s."""
    temos = _ja_temos()
    for mp4 in sorted(PARCEIROS_LOCAL.glob("*/source.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        vid = mp4.parent.name[:11]
        if vid in temos or time.time() - mp4.stat().st_mtime < 120:  # ainda baixando
            continue
        try:
            dur = sondar(mp4)["duracao"]
        except Exception:  # noqa: BLE001
            continue
        if 12 <= dur <= 90:
            return {"arquivo": mp4, "titulo": mp4.parent.name[12:], "dur": dur}
    return None


def buscar(tipo, n=0):
    """Melhor Short (views) da busca n do tipo que ainda não temos. None se nada serve."""
    sys.path.insert(0, r"D:\hipercool-materiais\comum")
    import ytdlp_vez
    if ytdlp_vez.pausado():
        log("  yt-dlp em pausa — sem busca nesta rodada")
        return None
    buscas = (_cfg().get("buscas") or {}).get(tipo) or BUSCAS[tipo]
    q = buscas[n % len(buscas)]
    with ytdlp_vez.vez("claude-code-video: busca de referência"):
        cmd = [PY_DL, "-m", "yt_dlp", "--flat-playlist", "-J", f"ytsearch40:{q}"]
        px = ytdlp_vez.proxy_url()
        if px:
            cmd[3:3] = ["--proxy", px]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    if ytdlp_vez.bloqueio(r.stdout + r.stderr):
        ytdlp_vez.pausar("busca de referência do claude-code-video")
        return None
    try:
        itens = json.loads(r.stdout).get("entries") or []
    except ValueError:
        return None
    temos = _ja_temos()
    bons = [e for e in itens if e.get("id") not in temos and (e.get("duration") or 999) <= 75
            and (e.get("view_count") or 0) >= _cfg().get("views_min", 100000)]
    if not bons:
        log(f"  busca '{q}': nenhum Short novo com views suficientes")
        return None
    e = max(bons, key=lambda e: e.get("view_count") or 0)
    log(f"  busca '{q}': {e.get('view_count')} views, {e.get('duration')} s — {str(e.get('title'))[:80]}")
    return {"url": f"https://www.youtube.com/shorts/{e['id']}", "titulo": e.get("title"), "views": e.get("view_count"),
            "busca": q}


def rodada():
    """1 referência nova por vez, de tempos em tempos (config referencias.intervalo_h, padrão 3 h)."""
    c = _cfg()
    if not c.get("ligado"):
        return None
    REFS.mkdir(exist_ok=True)
    import msvcrt
    trava = open(REFS / ".rodada.lock", "w")
    try:
        msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return None  # outra rodada (tarefa ou melhorador) já está buscando/analisando
    infos = [json.loads(p.read_text("utf-8")) for p in REFS.glob("*/info.json")]
    pend = [p.parent for p in REFS.glob("*/info.json") if not json.loads(p.read_text("utf-8")).get("analisada")]
    if pend:  # uma que caiu no meio: termina antes de buscar outra
        return analisar(pend[0])
    ult = max((m.get("adicionada", "") for m in infos), default="")
    if ult and (datetime.now() - datetime.fromisoformat(ult)).total_seconds() < c.get("intervalo_h", 3) * 3600:
        return None
    conta = {t: sum(1 for m in infos if m.get("tipo") == t) for t in BUSCAS}
    tipo = min(conta, key=conta.get)
    if conta[tipo] >= c.get("max_por_tipo", 30):
        return None
    local = parceiro_local() if tipo == "entretenimento" else None
    if local:
        nome = _slug(f"parc_{local['titulo']}")
        p = adicionar(str(local["arquivo"]), tipo, nome, f"Short de parceiro (lista da dona), {local['dur']:.0f} s")
        return analisar(p)
    achado = buscar(tipo, conta[tipo])
    if not achado:
        return None
    nome = _slug(f"{tipo[:4]}_{achado['titulo'] or achado['url']}")
    p = adicionar(achado["url"], tipo, nome, f"busca automática '{achado['busca']}', {achado['views']} views")
    return analisar(p)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("adicionar")
    a.add_argument("fonte")
    a.add_argument("--tipo", choices=["anuncio", "entretenimento"], required=True)
    a.add_argument("--nome")
    a.add_argument("--nota", default="")
    a.add_argument("--analisar", action="store_true")
    b = sub.add_parser("analisar")
    b.add_argument("nome", nargs="?")
    b.add_argument("--modelo")
    sub.add_parser("lista")
    sub.add_parser("rodada")
    x = ap.parse_args()
    if x.cmd == "rodada":
        try:
            rodada()
        except BaseException as e:  # noqa: BLE001 — rodada de fundo: registra e sai
            log(f"rodada falhou: {type(e).__name__}: {str(e)[:300]}")
        return
    if x.cmd == "adicionar":
        p = adicionar(x.fonte, x.tipo, x.nome, x.nota)
        if x.analisar:
            analisar(p)
    elif x.cmd == "analisar":
        alvos = [REFS / x.nome] if x.nome else [p.parent for p in REFS.glob("*/info.json")
                                                if not json.loads(p.read_text("utf-8")).get("analisada")]
        for p in alvos:
            analisar(p, x.modelo)
    else:
        usos = json.loads(USOS.read_text("utf-8")) if USOS.exists() else {}
        for p in sorted(REFS.glob("*/info.json")) if REFS.exists() else []:
            m = json.loads(p.read_text("utf-8"))
            print(f"{p.parent.name:42} {m.get('tipo'):15} {'analisada' if m.get('analisada') else 'PENDENTE':10} "
                  f"usos={len(usos.get(p.parent.name, []))}  {m.get('title') or m.get('fonte')}")


if __name__ == "__main__":
    main()
