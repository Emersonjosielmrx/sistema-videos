r"""Engenharia reversa de vídeo que estourou (dona 28/10; método Hypit: ANÁLISE + LINHA DO TEMPO).

Também atende a fila do campo "Viu um vídeo bom? Mande aqui" do painel :8790 (estado\videos_referencia.jsonl).
Pouco volume pelo IP de casa: legenda automática do vídeo INTEIRO (texto, pelo proxy) + só os primeiros 20 min em 240p
pros cortes de cena. A IA (Gemini 3.8) escreve ANALISE.md e LINHA_DO_TEMPO.md em referencias\<id>\.

    python engenharia_reversa.py <url>          # um vídeo
    python engenharia_reversa.py fila           # os "na fila" do painel
    python engenharia_reversa.py porao          # o mais visto do Porão Manhwa (@oporaodacidadela)
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BIN = Path(r"D:\recapd-ambientes\producao\bin")
sys.path.insert(0, str(BIN))
os.chdir(BIN.parent)
import anime_fetch  # noqa: E402
import anime_segments  # noqa: E402
import ytdlp_vez  # noqa: E402

AQUI = Path(__file__).resolve().parent
REFS = Path(r"D:\video-fila\estado\videos_referencia.jsonl")
COOKIES = BIN.parent / "cookies.txt"
MIN_VIDEO = int(os.environ.get("ENG_REVERSA_MIN", "20"))  # 30/10: lote grande = 12 min + whisper tiny (2 h/vídeo -> ~20 min)


def _info(url, flat=False):
    import yt_dlp
    # 30/10 (Fable): o rótulo tem "metad" -> o ytdlp_vez manda pelo proxy Webshare (antes "info" saía pelo IP de casa e
    # 13 consultas seguidas levaram "Sign in to confirm you're not a bot")
    with ytdlp_vez.vez("engenharia reversa: metadado"):
        return yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "extract_flat": flat,
                                 "cookiefile": str(COOKIES) if COOKIES.exists() else None}).extract_info(url, download=False)


def _mais_visto_porao():
    lista = _info("https://www.youtube.com/@oporaodacidadela/videos", flat=True).get("entries") or []
    melhor = max(lista, key=lambda e: e.get("view_count") or 0)
    return f"https://www.youtube.com/watch?v={melhor['id']}"


def _baixar_inicio(url, pasta):
    feito = next(pasta.glob("inicio.*"), None)
    if feito:
        return feito
    # 30/10 (Fable): a fila da dona (fila_dona/alimentador) já baixou o original em workspace\anime\<id>_*\source.mp4 —
    # corta o começo dele aqui em vez de baixar do YouTube de novo (IP de casa barrado)
    vid = url.rstrip("/").split("=")[-1].split("/")[-1][:11]
    local = next((p for p in sorted((BIN.parent / "workspace" / "anime").glob(f"{vid}*/source*.mp4"))), None)
    if local:
        out = pasta / "inicio.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(local), "-t", str(MIN_VIDEO * 60), "-vf", "scale=-2:240",
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-c:a", "aac", "-b:a", "64k", str(out)],
                       check=True, capture_output=True, timeout=1800)
        return out
    cmd = ["yt-dlp", url, "-f", "bv*[height<=240]+ba/b[height<=360]", "-S", "res,vcodec:h264",
           "--download-sections", f"*0-{MIN_VIDEO * 60}", "--merge-output-format", "mp4",
           "-o", str(pasta / "inicio.%(ext)s"), "--no-warnings", "--no-playlist"]
    if COOKIES.exists():
        cmd += ["--cookies", str(COOKIES)]
    with ytdlp_vez.vez("engenharia reversa: início do vídeo"):
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
    return next(pasta.glob("inicio.*"))


def _whisper(video, pasta):
    """[[início_s, texto]] dos primeiros MIN_VIDEO min (28/10: a legenda pelo proxy cai em "confirme que não é robô")."""
    cache = pasta / "whisper_tempos.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    # 30/10 (Fable): no PC1 a 100% o whisper local em prioridade baixa ficava HORAS sem CPU (bXe7: 2 h parado). Primeiro
    # o Whisper do Groq pelo proxy (hipercool groq_api, áudio opus leve); falhou = o local de sempre.
    try:
        sys.path.append(r"D:\hipercool-videos\bin")
        import groq_api
        opus = pasta / "inicio_audio.ogg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a",
                        "libopus", "-b:a", "24k", str(opus)], check=True, capture_output=True, timeout=600)
        j = groq_api.transcrever(str(opus), idioma="pt", palavras=False)
        segs = (j or {}).get("segments") or []
        if segs:
            cues = [[round(float(s["start"]), 1), str(s.get("text", "")).strip()] for s in segs]
            cache.write_text(json.dumps(cues, ensure_ascii=False), encoding="utf-8")
            opus.unlink(missing_ok=True)
            return cues
    except Exception as e:  # noqa: BLE001
        print(f"groq falhou ({type(e).__name__}: {str(e)[:120]}) — whisper local", flush=True)
    os.environ.setdefault("HF_HOME", r"D:\hipercool-materiais\modelos\hf")
    from faster_whisper import WhisperModel
    # "small" estourou a memória do PC1 (mkl_malloc, 28/10); "base" basta pra achar gancho/ritmo
    segs, _ = WhisperModel(os.environ.get("ENG_REVERSA_WHISPER", "base"), device="cpu", compute_type="int8",
                           cpu_threads=4).transcribe(str(video), language="pt", vad_filter=True)
    cues = [[round(s.start, 1), s.text.strip()] for s in segs]
    cache.write_text(json.dumps(cues, ensure_ascii=False), encoding="utf-8")
    return cues


MELHORIAS = AQUI / "LONGOS_MELHORIAS.md"


def _ja_temos():
    """01/11 (dona: "o analisador não repetir as mesmas coisas"): as listas JÁ FEITO / A FAZER / DESCARTADO do
    LONGOS_MELHORIAS.md entram no pedido pra IA só trazer o que é NOVO."""
    try:
        t = MELHORIAS.read_text(encoding="utf-8")
    except OSError:
        return ""
    t = t[t.find("## A FAZER"):] if "## A FAZER" in t else t
    return ("\n\nJÁ CONHECEMOS (não repita isto como sugestão; se este vídeo confirma um item, cite o ID, ex. 'confirma "
            "L-06'):\n" + t[:7000])


def _por_minuto(cues, trocas, dur):
    linhas = []
    for m in range(int(dur // 60) + 1):
        falas = [t for s, t in cues if m * 60 <= s < (m + 1) * 60]
        cortes = sum(1 for t in trocas if m * 60 <= t < (m + 1) * 60) if m < MIN_VIDEO else None
        linhas.append(f"{m:3d} min | {len(' '.join(falas).split()):3d} palavras | "
                      f"{'' if cortes is None else f'{cortes:3d} cortes | '}{' '.join(falas)[:220]}")
    return "\n".join(linhas)


def _local(url):
    vid = url.rstrip("/").split("=")[-1].split("/")[-1][:11]
    return vid, next(iter(sorted((BIN.parent / "workspace" / "anime").glob(f"{vid}*/source*.mp4"))), None)


def _info_local(vid, fonte):
    """30/10 (Fable): metadado SEM YouTube pra fonte que já está no PC (IP de casa e proxy barrados): título da fila da
    dona / ficha, duração pelo ffprobe; views ficam None (completar depois com --views)."""
    titulo = None
    try:
        fd = json.loads(Path(r"D:\recapd-ambientes\producao\colab\fila_dona.json").read_text(encoding="utf-8"))
        titulo = next((i.get("titulo") for i in fd.get("itens", []) if i.get("vid") == vid and i.get("titulo")), None)
    except (OSError, ValueError):
        pass
    if not titulo:
        n = next(iter(Path(r"D:\hipercool-materiais\animes recap\na_nuvem").glob(f"{vid}*/nuvem.json")), None)
        try:
            titulo = json.loads(n.read_text(encoding="utf-8")).get("titulo") if n else None
        except (OSError, ValueError):
            titulo = None
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(fonte)], capture_output=True, text=True, timeout=60).stdout.strip())
    except (ValueError, subprocess.SubprocessError):
        dur = None
    return {"id": vid, "title": titulo or Path(fonte).parent.name[12:], "channel": None, "view_count": None,
            "duration": dur, "_sem_youtube": True}


def analisar(url, obs=""):
    vid0, fonte_local = _local(url)
    if fonte_local and (ytdlp_vez.pausado() or os.environ.get("ENG_REVERSA_LOCAL") == "1"):
        info = _info_local(vid0, fonte_local)
    else:
        info = _info(url)
    vid = info["id"]
    pasta = AQUI / "referencias" / vid
    pasta.mkdir(parents=True, exist_ok=True)
    if not info.get("_sem_youtube"):
        anime_fetch.fetch_captions(url, pasta, langs=("pt",))
    cues = json.loads((pasta / "legenda_tempos.json").read_text(encoding="utf-8")) \
        if (pasta / "legenda_tempos.json").exists() else []
    inicio = _baixar_inicio(url, pasta)
    trocas = anime_segments._analise_fonte(str(inicio)).get("trocas") or []
    if not cues:
        cues = _whisper(inicio, pasta)
    dur = float(info.get("duration") or (cues[-1][0] if cues else 0))
    if not (pasta / "legenda_tempos.json").exists():
        dur = min(dur, MIN_VIDEO * 60)  # só temos a fala dos primeiros minutos
    meta = {k: info.get(k) for k in ("title", "channel", "view_count", "like_count", "comment_count", "duration",
                                     "upload_date", "description", "tags")}
    meta["capitulos"] = [[round(c["start_time"]), c["title"]] for c in info.get("chapters") or []]
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    abertura = "\n".join(f"{s:7.1f}s {t}" for s, t in cues if s < 240)
    ritmo = (f"cortes de cena nos primeiros {MIN_VIDEO} min: {len(trocas)} "
             f"(1 a cada {MIN_VIDEO * 60 / max(1, len(trocas)):.1f} s); primeiros 60 s: {sum(1 for t in trocas if t < 60)}")
    prompt = (
        "Você é analista de retenção de YouTube. Faça a ENGENHARIA REVERSA deste vídeo que estourou, pra copiarmos o que "
        "funciona nos nossos recaps longos narrados de manhwa/anime em PT-BR (voz clonada, mascote, efeitos, memes).\n"
        f"OBSERVAÇÃO DA DONA: {obs or '(nenhuma)'}\n\nDADOS:\n{json.dumps(meta, ensure_ascii=False)[:4000]}\n{ritmo}\n\n"
        f"ABERTURA (4 primeiros min, legenda com tempo):\n{abertura[:9000]}\n\nPOR MINUTO (palavras, cortes, o que é dito):\n"
        f"{_por_minuto(cues, trocas, dur)[:30000]}\n\n"
        "Responda em DUAS partes separadas pela linha ===LINHA_DO_TEMPO===.\n"
        "Parte 1 (ANÁLISE, markdown): por que estourou — título e promessa, gancho dos primeiros 30 s (palavra por "
        "palavra), estrutura (atos, viradas, onde reengaja), ritmo (palavras/min, cortes/min e como mudam), pedidos de "
        "inscrição/like (onde e como), recursos (humor, suspense, perguntas ao público), e no fim uma lista 'COPIAR NO "
        "NOSSO LONGO' com 5 a 10 mudanças concretas e testáveis.\n"
        "Parte 2 (LINHA DO TEMPO, tabela markdown): | tempo | o que acontece | técnica | — dos momentos que seguram o "
        "público (gancho, viradas, cliffhangers, CTAs, picos de ritmo)." + _ja_temos())
    import claude_client
    # 28/10: "antigravity/gemini-3.8-flash-tiered" travado (nem "ok" em 150 s); a fila própria do 3.8 respondeu em 2 s
    resp = claude_client.generate_text(prompt, max_tokens=6000, temperature=0.4, timeout=400,
                                       model=os.environ.get("ENG_REVERSA_MODELO", "gemini-fila")) or ""
    if "===LINHA_DO_TEMPO===" not in resp:
        raise RuntimeError(f"a IA não devolveu a análise ({len(resp)} letras)")
    analise, _, linha = resp.partition("===LINHA_DO_TEMPO===")
    cab = (f"# {meta['title']}\n{url} · {meta['channel']} · {meta['view_count']} views · "
           f"{int((info.get('duration') or dur) // 60)} min\n\n")
    (pasta / "ANALISE.md").write_text(cab + analise.strip() + "\n", encoding="utf-8")
    (pasta / "LINHA_DO_TEMPO.md").write_text(cab + linha.strip() + "\n", encoding="utf-8")
    for f in pasta.glob("inicio.*"):
        f.unlink()  # só servia pros cortes de cena
    print(f"{vid}: {pasta / 'ANALISE.md'} ({len(cues)} falas, {len(trocas)} cortes)", flush=True)
    return pasta


def _marcar(url, situacao, pasta=None):
    linhas = [json.loads(l) for l in REFS.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in linhas:
        if r.get("url") == url:
            r["situacao"] = situacao
            if pasta:
                r["analise"] = str(pasta / "ANALISE.md")
            r["analisado_em"] = datetime.now().isoformat(timespec="seconds")
    REFS.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in linhas), encoding="utf-8")


def comum():
    """29/10 noite (Fable; dona: "esses vídeos têm milhões de views, alguma coisa muito certa ele está fazendo"): lê TODAS
    as ANALISE.md + meta.json de referencias\\ e pede o que se REPETE nos que estouraram (título, capa, gancho, ritmo,
    estrutura, CTA) -> referencias\\PADROES_COMUNS.md, com a lista do que copiar no nosso longo em ordem de impacto."""
    pastas = sorted(p for p in (AQUI / "referencias").iterdir() if (p / "ANALISE.md").exists())
    if len(pastas) < 2:
        print("menos de 2 análises — nada a comparar")
        return
    blocos = []
    for p in pastas:
        m = json.loads((p / "meta.json").read_text(encoding="utf-8")) if (p / "meta.json").exists() else {}
        blocos.append(f"### {m.get('title')} — {m.get('channel')} — {m.get('view_count')} views — "
                      f"{int((m.get('duration') or 0) // 60)} min\n{(p / 'ANALISE.md').read_text(encoding='utf-8')[:6000]}")
    prompt = ("Abaixo estão análises de vídeos de recap longo de manhwa/anime que estouraram (views na linha de cada um). "
              "Encontre o que SE REPETE nos que têm mais views e falta nos que têm menos: título (palavras, tamanho, "
              "promessa), capa, gancho dos primeiros 30 s, ritmo (palavras/min, cortes/min), estrutura e viradas, onde e "
              "como pedem inscrição, duração. Responda em markdown: 1) PADRÕES (cada um com quantos vídeos têm e os views "
              "deles); 2) O QUE NÃO IMPORTA (varia sem relação com views); 3) COPIAR NO NOSSO LONGO: até 10 mudanças "
              "concretas e testáveis em ordem de impacto esperado." + _ja_temos() + "\n\n" + "\n\n".join(blocos))[:120000]
    import claude_client
    resp = claude_client.generate_text(prompt, max_tokens=6000, temperature=0.3, timeout=600,
                                       model=os.environ.get("ENG_REVERSA_MODELO", "gemini-fila")) or ""
    if len(resp) < 500:
        raise RuntimeError(f"a IA não devolveu os padrões ({len(resp)} letras)")
    saida = AQUI / "referencias" / "PADROES_COMUNS.md"
    saida.write_text(f"# Padrões comuns de {len(pastas)} vídeos de referência ({datetime.now():%d/%m %H:%M})\n\n"
                     + resp.strip() + "\n", encoding="utf-8")
    print(f"padrões: {saida}")


def views():
    """30/10: completa view_count/canal/título dos analisados sem YouTube (meta.json com view_count None), 1 por minuto,
    pelo proxy (rótulo "metadado"); para no 1º bloqueio. Depois rode `comum` de novo."""
    import time
    for mj in sorted((AQUI / "referencias").glob("*/meta.json")):
        m = json.loads(mj.read_text(encoding="utf-8"))
        if m.get("view_count") is not None:
            continue
        if ytdlp_vez.pausado():
            print("yt-dlp em pausa — paro (rode de novo depois)")
            return
        try:
            info = _info(f"https://www.youtube.com/watch?v={mj.parent.name}")
        except Exception as e:  # noqa: BLE001
            if ytdlp_vez.bloqueio(str(e)) or "not a bot" in str(e):
                ytdlp_vez.pausar("engenharia reversa views: " + str(e)[-120:])
                print("YouTube barrou — paro")
                return
            print(f"{mj.parent.name}: {type(e).__name__}")
            continue
        for k in ("title", "channel", "view_count", "like_count", "comment_count", "upload_date", "description", "tags"):
            m[k] = info.get(k, m.get(k))
        mj.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        an = mj.with_name("ANALISE.md")
        if an.exists():
            t = an.read_text(encoding="utf-8").split("\n", 2)
            if len(t) == 3:
                an.write_text(f"# {m['title']}\n{t[1].replace('None views', str(m['view_count']) + ' views').replace(' · None · ', ' · ' + str(m.get('channel')) + ' · ')}\n{t[2]}",
                              encoding="utf-8")
        print(f"{mj.parent.name}: {m['view_count']} views ({m.get('channel')})", flush=True)
        time.sleep(60)


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "fila"
    if alvo == "views":
        views()
    elif alvo == "comum":
        comum()
    elif alvo == "fila":
        for r in [json.loads(l) for l in REFS.read_text(encoding="utf-8").splitlines() if l.strip()] if REFS.exists() else []:
            if r.get("situacao") != "na fila" or (ytdlp_vez.pausado() and not _local(r["url"])[1]):
                continue  # 30/10: com o yt-dlp em pausa, só os que já têm a fonte no PC
            try:
                _marcar(r["url"], "analisado", analisar(r["url"], r.get("obs", "")))
            except Exception as e:  # noqa: BLE001
                # 30/10 (Fable): bloqueio do YouTube = PARA TUDO (regra: sem rajada) e o vídeo continua na fila
                if ytdlp_vez.bloqueio(str(e)) or "not a bot" in str(e):
                    ytdlp_vez.pausar("engenharia reversa: " + str(e)[-150:])
                    print(f"YouTube barrou ({str(e)[-100:]}) — fila parada, o resto continua na fila", flush=True)
                    break
                _marcar(r["url"], f"falhou: {type(e).__name__}: {str(e)[:120]}")
    else:
        analisar(_mais_visto_porao() if alvo == "porao" else alvo)
